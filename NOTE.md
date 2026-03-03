# NOTE — Engineering Notes, Decisions & Context
**Platform**: OHC UHI / HealthBridge  
**Purpose**: Things Antigravity needs to know before touching the codebase. Read this first.  
**Maintainer**: Antigravity Team  
**Last Updated**: 2026-03-02

---

## 1. What We Are Actually Building

This is not a greenfield project. We are extending **CARE** — a production EMR that real hospitals use every day across 10+ Indian states. Bugs in CARE affect real patients. Every change to `care` or `care_fe` must be treated with the same respect as changes to banking infrastructure.

The new things we are building:
- **UHI Switch Server** — fully new, no existing code, greenfield Go or FastAPI service
- **HealthWallet Flutter app** — new, though HealthWallet.me has prior art to study
- **HealthWallet backend** — new FastAPI or Go service

The things we are extending (carefully):
- **CARE backend** (`care`)— adding FHIR export endpoints, ABDM extensions, UHI webhooks
- **CARE frontend** (`care_fe`) — adding MedGemma plugin panel, cross-hospital record view

---

## 2. Key Repositories

| Repo | What It Is | Where |
|---|---|---|
| `ohcnetwork/care` | Main Django backend for CARE EMR | GitHub |
| `ohcnetwork/care_fe` | React/TypeScript frontend for CARE EMR | GitHub |
| `ohcnetwork/care_scribe` | Ambient scribing (LiveKit + AI) Care App | GitHub |
| `healthwallet.me` (reference) | Patient app for health wallet concept | healthwallet.me |
| `ohcnetwork/uhi-switch` | **NEW** — UHI Switch Server | To be created |
| `[team]/healthwallet-app` | **NEW** — Flutter patient app | To be created |
| `[team]/healthwallet-backend` | **NEW** — Patient app backend | To be created |

---

## 3. Technology Decisions & Rationale

### Why Go for the Switch Server (recommendation)?
The Switch Server is a **high-throughput routing layer**, not a business logic server. It will handle thousands of concurrent consent validations and FHIR bundle fan-outs. Go's goroutine concurrency model, low memory footprint, and fast startup time make it better suited than Django or even FastAPI at this throughput. If the team is more comfortable with Python, FastAPI + uvicorn + asyncio is an acceptable alternative, but benchmark before committing.

### Why LanceDB over sqlite-vss for on-device RAG?
`sqlite-vss` requires a native SQLite extension compiled for each platform (Android ARM64, iOS ARM, etc.). LanceDB has a Rust core with better cross-platform FFI bindings and is actively maintained for embedded/mobile use cases. Both work — LanceDB has fewer integration headaches on Flutter.

### Why NOT to use ZKPs in v1
Zero-Knowledge Proofs for consent verification sound elegant (pharmacist verifies prescription validity without seeing patient diagnosis). In practice: ZKP libraries (gnark, circom, snarkjs) require Rust/Go expertise, have a shallow talent pool in the healthcare space, and add months of engineering time. The same outcome — verifying a consent claim without exposing raw data — can be achieved with **selective disclosure JWTs** (SD-JWT, IETF draft) or **signed consent tokens** with scoped claims. Ship the simpler, battle-tested cryptographic primitive first.

### Why NOT to start with Federated Learning
Federated Learning for MedGemma improvement requires: a model aggregation server, differential privacy on gradient updates, secure aggregation protocol, and at minimum 20–30 hospital nodes participating to be statistically useful. This is a multi-quarter infrastructure project. It belongs in the roadmap, not the sprint board.

### FHIR R5 vs R4
OHC/CARE is committed to **FHIR R5**. Do not introduce R4-only dependencies. If integrating external libraries that only support R4 (common in older HAPI FHIR Java tooling), wrap them in a translation layer. R4 → R5 is mostly additive — most core resources are compatible with minor adjustments.

### ABDM vs DEPA vs our own consent model
These are complementary, not competing:
- **ABDM** provides the patient identity infrastructure (ABHA ID) and the consent manager framework
- **DEPA** provides the consent artifact data model (time/scope/purpose bound)
- **Our consent model** implements DEPA artifacts over the ABDM infrastructure
We are NOT building a consent manager from scratch. We are integrating with NHA's Ayushman Bharat app as the consent manager (or potentially linking to NDHM consent manager). Decision pending on which consent manager to integrate with.

---

## 4. CARE Codebase Notes (Before You Touch It)

### care (Backend)
- Django apps are modular. Key ones: `facility/`, `patient/`, `abdm/`, `hcx/`, `users/`
- The `abdm/` app has existing ABDM flows — understand these before adding new consent endpoints
- CARE uses **PostgreSQL with JSONB** for some clinical data fields — be careful with FHIR serialization of these
- **Celery** handles async tasks (report generation, ABDM callbacks). New UHI webhook processing should go through Celery, not synchronous request handling
- Auth is JWT-based. `users/` app handles roles. Every new endpoint needs the right `@has_permission` decorator
- Tests live in `care/tests/` — run them. The CI will fail if you skip this. Test coverage for any new endpoint must be > 80%

### care_fe (Frontend)
- React 18 + TypeScript. Strict mode on. No `any` types without a comment explaining why
- Tailwind CSS + shadcn/ui components. Don't add new UI libraries without team discussion
- State: React Query for server state, Zustand for UI state. Don't use Redux — it was migrated away from
- The **Care Apps plugin system** uses module federation. The MedGemma panel will be a Care App — look at `care_scribe` as the reference implementation for how Care Apps are structured
- API calls go through `src/Utils/request.ts` — use this, don't raw `fetch()`

---

## 5. The Identity Problem (Most Underestimated Challenge)

When patient "Priya Menon" visits Apollo Chennai, she's registered as:
- Apollo: `PRIYA MENON, DOB: 1990-03-15, phone: 9876543210`

When she visits Govt. Medical College Kochi, she's:
- GMC Kochi: `P. Menon, DOB: 1990-03-15, phone: 9876543xxx (old number)`

Without ABHA linking, these are two different patients in two different systems. The UHI Switch must canonicalize on ABHA ID. But:
- Not all patients have ABHA IDs yet
- Not all hospitals have ABHA-linked records for all patients
- ABHA enrollment is still ongoing

**Resolution strategy for v1:**
- Primary: ABHA ID (if both patient and hospital record are ABHA-linked)
- Fallback: Manual linking by patient (patient claims the record in HealthWallet app)
- Do NOT auto-link on name+DOB — too many false positives in Indian names

This problem will consume engineering time. Budget for it.

---

## 6. Rate Limiting & Caching Strategy

The Switch Server MUST NOT become a bottleneck. Design:

```
Hospital A opens consultation for Patient X
  └── Triggers: GET /fhir/bundle?consent_token=xxx

Switch Server:
  1. Check Redis cache: bundle:{patient_abha}:{consent_id} → HIT? Return cached
  2. Miss → Fan out to all hospitals with patient records
  3. Merge + filter bundles (strip non-consented resource types)
  4. Cache result in Redis, TTL: 15 minutes
  5. Return to requester

Cache invalidation triggers:
  - New consent granted/revoked
  - CARE backend pushes webhook "new record added for patient X"
  - TTL expiry
```

Without caching, every page load in the doctor's EMR hitting the Switch will cascade into N FHIR requests to N hospitals. That does not scale.

---

## 7. What MedGemma Can and Cannot Do

**Can do (validated clinical AI tasks):**
- Summarize diagnostic reports in plain language
- Identify abnormal values in lab panels (flag out-of-range)
- Surface relevant prior history for current complaint
- Suggest SOAP note structure from free-form notes

**Cannot do (do NOT present these to doctors as AI outputs):**
- Make definitive diagnoses
- Prescribe medications
- Replace clinical judgment
- Handle rare diseases reliably (training data skews to common conditions)

Every MedGemma output in the CARE UI must carry a visible disclaimer: *"AI-generated suggestion. Verify clinically."* This is not optional — it's a medico-legal requirement.

---

## 8. Offline Strategy for Rural Hospitals

Many CARE deployments are in rural areas with intermittent connectivity. The offline strategy:

**What must work offline:**
- Creating new patient records and consultations
- Recording vitals and observations
- Writing prescriptions
- Viewing records already synced to this facility

**What requires connectivity:**
- Cross-hospital record fetch via Switch Server
- Consent grant/revoke (these modify distributed state)
- ABDM operations
- AI analysis (MedGemma server-side)

**CRDT rules:**
- Observations, Vitals, Notes → CRDT-safe (last-write-wins per field is acceptable)
- Prescriptions → NOT CRDT-safe (concurrent writes from two doctors require conflict UI)
- Consent artifacts → NEVER offline (must be verified against Switch in real-time)

Use **Yjs (yrs Rust port for Python/Go)** or **Automerge** for CRDT implementation. Do not invent your own.

---

## 9. Open Questions (Decisions Pending)

| Question | Options | Decision Owner | Deadline |
|---|---|---|---|
| Switch Server language | Go or FastAPI | Tech Lead | Sprint 0 |
| Consent manager | NHA ABDM or build own | Product + Legal | Sprint 0 |
| On-device embedding model | Gemma embedding or MiniLM | ML Lead | Sprint 2 |
| MedGemma hosting | Self-hosted GPU or Google Vertex | Infra + Cost | Sprint 1 |
| Audit log store | TimescaleDB or S3+Object Lock | Infra | Sprint 1 |
| Flutter local DB | SQLCipher+LanceDB or ObjectBox | Mobile Lead | Sprint 2 |

---

## 10. Definitions & Glossary

| Term | Meaning |
|---|---|
| ABHA | Ayushman Bharat Health Account — India's national patient identity |
| ABDM | Ayushman Bharat Digital Mission — NHA's digital health initiative |
| DEPA | Data Empowerment and Protection Architecture — consent model standard |
| FHIR R5 | HL7 Fast Healthcare Interoperability Resources, version 5 |
| HIP | Health Information Provider — a hospital/lab that holds records |
| HIU | Health Information User — a party that requests records (doctor, Switch) |
| SOAP | Subjective, Objective, Assessment, Plan — standard clinical note structure |
| DDI | Drug-Drug Interaction — adverse reaction between two medications |
| BOLA | Broken Object Level Authorization — OWASP API Security #1 risk |
| DPG | Digital Public Good — UN-recognized open-source global public benefit software |
| CARE | Clinical care platform by OHC — the core EMR we are extending |
| Switch Server | The new UHI routing + consent broker we are building |
| RAG | Retrieval-Augmented Generation — AI answers grounded in retrieved documents |
| CRDT | Conflict-free Replicated Data Type — data structure enabling offline-first sync |
| mTLS | Mutual TLS — both client and server authenticate with certificates |
