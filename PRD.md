# PRD — Universal Health Interface (UHI) Platform
**Product**: HealthBridge / OHC UHI Extension  
**Status**: Pre-Development  
**Maintainer**: Antigravity Team  
**Last Updated**: 2026-03-02

---

## 1. Executive Summary

We are extending the Open Healthcare Network (OHC) CARE EMR platform — a battle-tested, DPG-verified, FHIR R5-native EMR deployed across 10+ Indian states — with a **Universal Health Interface (UHI)** layer. This creates a bidirectional, consent-gated data corridor between:

- Hospitals ↔ Patients
- Hospital ↔ Hospital
- Patient ↔ AI (on-device, private)

The patient-facing surface is a **Flutter mobile app** (HealthWallet) featuring a downloadable on-device Gemma (~1.5GB) model for private AI health queries. The doctor-facing surface is a **CARE EMR plugin** powered by MedGemma for faster, contextual diagnosis.

The glue between all of these is the **UHI Switch Server** — a new service we are building.

---

## 2. Problem Statement

| Problem | Who Feels It | Severity |
|---|---|---|
| Patient records scattered across hospitals, labs, clinics | Patient | Critical |
| Doctors repeat intake from scratch every visit | Doctor | High |
| No interoperability between hospital EMR systems | Hospital CTO | Critical |
| Patients cannot query their own health history intelligently | Patient | High |
| Research data siloed; no privacy-safe aggregation | Health System | Medium |
| Rural hospitals go offline; data sync breaks | Hospital Staff | High |

---

## 3. Goals & Non-Goals

### Goals
- Give patients a single, portable, encrypted medical timeline
- Enable consent-gated, FHIR R5-compliant data sharing between CARE instances
- Ship an on-device AI (Gemma) that reads the patient's actual FHIR records via RAG
- Provide doctors a MedGemma-powered plugin inside CARE EMR for faster diagnosis
- Build a UHI Switch Server that brokers all data exchange with an immutable audit trail
- Achieve ABDM M1-M3 certification compliance

### Non-Goals (v1)
- Federated Learning for MedGemma (v2)
- Zero-Knowledge Proofs for consent (v2)
- Wearable / IoT BLE sync (v2)
- Gamified health quests (v2)
- Differential privacy research pipelines (v2)

---

## 4. Users & Personas

### 4.1 Riya (Patient, 34, Kochi)
- Manages health records for herself + elderly mother
- Visits 3 different hospitals in a year
- Frustrated by re-filling forms every visit
- Wants to understand her own lab results without Googling
- **Needs**: Single app with full history, AI that explains results, easy consent control

### 4.2 Dr. Arvind (General Physician, Govt Hospital, Tamil Nadu)
- Sees 80+ patients/day
- Currently spends 30% of consultation time on data entry
- Has no access to patient's history from other hospitals
- **Needs**: Auto-filled EMR, prior records surfaced instantly, drug interaction alerts

### 4.3 Admin (Hospital CTO, Multi-Branch Network)
- Needs ABDM compliance certification
- Wants interoperability with other hospital systems
- Concerned about data sovereignty and audit trails
- **Needs**: FHIR R5 data pipeline, OpenTelemetry observability, BOLA-safe APIs

---

## 5. Feature Requirements

### 5.1 HealthWallet (Flutter App)

| ID | Feature | Priority | Notes |
|---|---|---|---|
| HW-01 | ABDM-linked patient identity (ABHA ID) | P0 | Required for UHI |
| HW-02 | Complete FHIR R5 medical timeline | P0 | Pull from CARE via consent |
| HW-03 | On-device Gemma model download (~1.5GB) | P0 | Offline AI |
| HW-04 | On-device RAG over patient's FHIR records | P0 | sqlite-vss or LanceDB |
| HW-05 | Granular consent management (DEPA model) | P0 | Time/scope/purpose bound |
| HW-06 | Family account management (dependents) | P1 | Parents + children |
| HW-07 | OCR prescription digitizer (camera) | P1 | MediaPipe or Moondream |
| HW-08 | Push notifications for access events | P1 | Break-glass alerts |
| HW-09 | Multilingual AI responses | P1 | Hindi, Tamil, Telugu, Bengali |
| HW-10 | Consent revocation (one tap) | P0 | Immediate effect |

### 5.2 UHI Switch Server (New Build)

| ID | Feature | Priority | Notes |
|---|---|---|---|
| SW-01 | Patient identity resolution & deduplication | P0 | ABHA ID + fuzzy match |
| SW-02 | Consent artifact issuance & validation | P0 | DEPA compliant |
| SW-03 | FHIR R5 data brokering between CARE instances | P0 | Core routing |
| SW-04 | Immutable audit log (cryptographically chained) | P0 | Break-glass compliance |
| SW-05 | Rate limiting & quota per hospital/patient | P0 | Gateway protection |
| SW-06 | Break-glass emergency access protocol | P1 | ER override + notification |
| SW-07 | OpenTelemetry tracing across full request path | P0 | SRE requirement |
| SW-08 | BOLA-safe resource authorization | P0 | Security critical |

### 5.3 CARE EMR Plugin (MedGemma)

| ID | Feature | Priority | Notes |
|---|---|---|---|
| MP-01 | MedGemma report analysis sidebar | P0 | Doctor-facing |
| MP-02 | Ambient voice scribing → SOAP note autofill | P1 | LiveKit integration |
| MP-03 | Drug-drug interaction (DDI) checker | P1 | On-prescription trigger |
| MP-04 | Patient history fetch via UHI on consult open | P0 | Cached + invalidated |
| MP-05 | Consent-gated cross-hospital record view | P0 | Requires SW-02 |

### 5.4 CARE Backend (Extensions)

| ID | Feature | Priority | Notes |
|---|---|---|---|
| CB-01 | UHI Switch Server webhook endpoints | P0 | Inbound consent events |
| CB-02 | FHIR R5 export endpoint per patient | P0 | Paginated, filtered |
| CB-03 | Offline-first CRDT sync for rural hospitals | P1 | Conflict resolution |
| CB-04 | ABDM M1-M3 compliance audit endpoints | P0 | Certification requirement |

---

## 6. Consent Model (DEPA)

Every data share event must carry a **Consent Artifact** with:
```
{
  "patient_id": "ABHA:xxxx",
  "requester": "hospital_id | patient_app",
  "purpose": "second_opinion | diagnosis | research",
  "scope": ["LabReport", "Prescription"],   // FHIR resource types
  "exclude": ["MentalHealthRecord"],
  "valid_from": "ISO8601",
  "valid_until": "ISO8601",
  "granted_at": "ISO8601",
  "signature": "patient_signed_JWT"
}
```

---

## 7. Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| Patient app installs | 10,000 (6 months) | App store analytics |
| Consent grants per day | 500+ | Switch server logs |
| Doctor time-to-consult reduction | -30% | EMR session telemetry |
| ABDM M1 certification | Before launch | Cert authority |
| Cross-hospital record fetch p95 latency | < 2 seconds | OpenTelemetry |
| Zero BOLA incidents | 0 | Security audit |

---

## 8. Timeline (Rough)

| Phase | Scope | Duration |
|---|---|---|
| Phase 0 | FHIR R5 pipeline + consent model + BOLA audit | 6 weeks |
| Phase 1 | Switch Server core + HealthWallet v1 + CARE plugin v1 | 10 weeks |
| Phase 2 | On-device RAG + MedGemma scribing + DDI checker | 8 weeks |
| Phase 3 | ABDM certification + offline CRDT + observability | 6 weeks |
| Phase 4 | Federated learning, ZKP, wearables | Post-PMF |
