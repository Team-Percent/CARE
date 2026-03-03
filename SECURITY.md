# SECURITY — Security Architecture & Threat Model
**Platform**: OHC UHI / HealthBridge  
**Classification**: Internal — Engineering  
**Maintainer**: Antigravity Team  
**Last Updated**: 2026-03-02

---

## 1. Security Philosophy

> "Consent is the surface. Architecture is the guarantee."

We are handling **Sensitive Personal Data (SPD)** under India's DPDP Act 2023 and ABDM guidelines. Our security model must hold even when:
- An internal engineer is malicious
- A hospital system is compromised
- A patient's phone is stolen
- A third-party API is breached

Security is **not a layer** applied at the end. It is a constraint enforced at every architectural decision.

---

## 2. Threat Model

### Assets to Protect
| Asset | Sensitivity | Location |
|---|---|---|
| Patient FHIR records | Critical | CARE PostgreSQL (per hospital) |
| Consent artifacts | Critical | Switch Server PostgreSQL |
| ABHA tokens (patient identity) | Critical | HealthWallet app (encrypted storage) |
| Audit logs | High | Switch Server (append-only) |
| Doctor credentials | High | CARE backend |
| AI model weights (MedGemma) | Medium | CARE server / EMR plugin |
| On-device health vectors (RAG) | High | HealthWallet app (local, encrypted) |

### Threat Actors
| Actor | Capability | Primary Attack Vector |
|---|---|---|
| Malicious outsider | Low–Medium | API enumeration, credential stuffing |
| Compromised hospital system | High | Lateral movement via Switch, over-fetching |
| Rogue employee (hospital staff) | Medium | BOLA — accessing other patients' data |
| Stolen patient device | Physical | Local data extraction |
| Nation-state / APT | High | Supply chain, zero-days |

---

## 3. Authentication & Authorization

### 3.1 Identity Layers

```
Patient Identity:    ABHA ID (NHA-issued) + OIDC token from ABDM
Doctor Identity:     NMC registration number + hospital-issued JWT
Hospital Identity:   ABDM-registered HIP/HIU ID + mTLS client cert
Switch Server:       Signs all outbound requests with ED25519 keypair
```

### 3.2 JWT Claims Structure (Patient Token)
```json
{
  "sub": "ABHA:xxxx-xxxx-xxxx",
  "role": "patient",
  "iat": 1740000000,
  "exp": 1740003600,
  "scope": ["read:own_records", "grant:consent"],
  "device_id": "sha256_of_device_fingerprint",
  "jti": "unique_token_id"
}
```
Tokens are **short-lived (1 hour)** with silent refresh. `jti` is tracked in Redis to enable revocation without waiting for expiry.

### 3.3 BOLA Prevention (Broken Object Level Authorization)
**This is the #1 security risk in healthcare APIs.**

Every API endpoint accessing patient data MUST:
```python
# CARE backend — every patient resource endpoint pattern
def get_patient_resource(request, patient_id, resource_id):
    # Step 1: Resolve requesting identity
    actor = resolve_actor(request.auth)  # patient | doctor | hospital
    
    # Step 2: Check ownership or valid consent
    if actor.type == "patient":
        assert actor.abha_id == patient_id  # Direct ownership only
    elif actor.type == "doctor":
        consent = ConsentArtifact.objects.get(
            patient_id=patient_id,
            requester_id=actor.id,
            valid_until__gt=now(),
            scope__contains=resource_type
        )
        assert consent.is_valid()
    
    # Step 3: Filter by consent scope BEFORE returning
    return filter_by_scope(resource, consent.scope)
```

**Never** trust resource IDs in URLs without explicit ownership/consent check. No sequential integer IDs for patient resources — use UUIDs v7.

### 3.4 Rate Limiting (Switch Server)
```
Per patient ABHA:      100 consent grants/day, 1000 record fetches/day
Per hospital (HIU):    10,000 record fetches/hour
Per doctor:            500 record fetches/hour
Emergency access:      5/day per doctor (triggers review if exceeded)
```
Limits enforced in Redis with sliding window. Violations → alert + potential suspension.

---

## 4. Data Encryption

### 4.1 At Rest
| Layer | Method |
|---|---|
| CARE PostgreSQL | AES-256 (disk-level + column-level for FHIR blobs) |
| Switch Server PostgreSQL | AES-256 disk encryption |
| HealthWallet app SQLite | SQLCipher (AES-256, key derived from device biometric + ABHA PIN) |
| LanceDB vectors (on-device) | Encrypted container via Flutter Secure Storage key |
| Audit log | Append-only, encrypted, hash-chained |

### 4.2 In Transit
- All external APIs: **TLS 1.3 minimum**
- Hospital ↔ Switch: **mTLS** (mutual TLS with client certificates)
- Switch ↔ CARE: **mTLS + signed request body** (ED25519)
- App ↔ HealthWallet backend: **TLS 1.3 + certificate pinning** in Flutter

### 4.3 Consent Artifact Signing
```
Patient signs consent artifact with their ABHA private key
Switch Server verifies signature before accepting
Stored consent carries patient signature as non-repudiation proof
```

---

## 5. Immutable Audit Log

Every data access, consent grant/revoke, and emergency override is logged. The log is **cryptographically chained** — each entry contains the hash of the previous entry — making retroactive tampering detectable.

### Log Entry Schema
```json
{
  "entry_id": "uuid-v7",
  "event_type": "DATA_ACCESS | CONSENT_GRANT | CONSENT_REVOKE | EMERGENCY_ACCESS",
  "actor_id": "ABHA or doctor_id or hospital_id",
  "patient_id": "ABHA:xxxx",
  "resource_types": ["DiagnosticReport", "Observation"],
  "consent_ref": "consent_artifact_id",
  "timestamp": "ISO8601",
  "metadata": { "ip": "...", "user_agent": "..." },
  "prev_hash": "sha256_of_previous_entry",
  "entry_hash": "sha256(this_entry_content + prev_hash)"
}
```

Log store is **write-only** for application code. Reads require separate privileged service with its own audit trail. Consider TimescaleDB with row-level security or a dedicated append-only store (Loki, S3 with Object Lock).

---

## 6. Break-Glass Protocol (Emergency Access)

```
Precondition: Patient is incapacitated, cannot grant consent

Doctor triggers: POST /api/switch/emergency-access
  Body: { "doctor_id", "patient_abha_id", "hospital_id", "reason": "string" }

Switch Server:
  1. Validates doctor identity (NMC + hospital registration)
  2. Generates time-limited emergency token (4 hours, full scope, non-renewable)
  3. Writes EMERGENCY_ACCESS event to audit log (chained, irrevocable)
  4. Dispatches notifications:
     - SMS (Twilio/CDAC) to all registered emergency contacts
     - Email to registered contacts
     - APNS/FCM push to patient's HealthWallet (best-effort)
  5. Returns emergency_token to doctor
  
Post-access:
  6. Patient reviews access log in HealthWallet app
  7. Patient can flag dispute → goes to hospital ethics committee
  
Abuse detection:
  8. > 5 emergency accesses/doctor/day → automatic security review
  9. Access to patients not admitted at that hospital → immediate alert
```

---

## 7. On-Device Security (HealthWallet Flutter App)

| Threat | Mitigation |
|---|---|
| Phone stolen, data exposed | SQLCipher encryption; biometric unlock required |
| Malicious app reads local DB | Android Keystore / iOS Secure Enclave for keys |
| Network interception | TLS 1.3 + certificate pinning (fail closed) |
| Reverse engineering of app | Code obfuscation (Flutter --obfuscate), no secrets in binary |
| ABHA token stolen | Token stored in Flutter Secure Storage (hardware-backed); short TTL |
| Gemma model tampered | SHA-256 checksum verification before model load |
| LanceDB vectors leaked | Encrypted with key from Secure Enclave; vectors alone useless without model |

---

## 8. ABDM Compliance Requirements

| Requirement | Description | Status |
|---|---|---|
| M1 — Outpatient | ABHA linking, OPD record creation | Must certify pre-launch |
| M2 — Inpatient | IPD, discharge summaries, sharing via HIU | Must certify pre-launch |
| M3 — Diagnostic | Lab reports, radiology via FHIR | Phase 2 |
| HIP Registration | CARE instances registered as Health Information Providers | Required |
| HIU Registration | UHI Switch registered as Health Information User | Required |
| Consent Manager | Either use NHA's Ayushman Bharat app or implement own | Decision pending |

---

## 9. Security Review Checklist

Before any PR touching auth/consent/data flow goes to main:

- [ ] BOLA check: Does every resource endpoint verify ownership or valid consent?
- [ ] Scope check: Is the response filtered to the consented resource types?
- [ ] Token check: Are JWTs validated for signature, expiry, AND `jti` (revocation)?
- [ ] Audit: Is every data access event written to the audit log?
- [ ] Rate limit: Is the endpoint covered by rate limiting?
- [ ] Input validation: All patient/doctor IDs validated as UUIDs, not trusted as-is?
- [ ] Error messages: Do error responses leak internal IDs or stack traces?
- [ ] mTLS: Hospital-to-Switch calls using client certificates?
- [ ] Logging: Are we logging enough for forensics without logging PII in plaintext?

---

## 10. Incident Response

| Severity | Definition | Response Time | Action |
|---|---|---|---|
| P0 | Unauthorized patient data exposed | 15 min | Page on-call; isolate Switch; notify CERT-In |
| P1 | BOLA vulnerability discovered | 1 hour | Hotfix deploy; audit recent access logs |
| P2 | Emergency access abuse detected | 4 hours | Suspend doctor; notify hospital admin |
| P3 | Rate limit bypass | 24 hours | Patch + re-test |

CERT-In notification required within **6 hours** of confirmed data breach (IT Act amendment).
