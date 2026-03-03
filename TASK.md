# TASK — Engineering Task Breakdown
**Platform**: OHC UHI / HealthBridge  
**Format**: Ordered by dependency. Complete Phase 0 before Phase 1. No skipping.  
**Maintainer**: Antigravity Team  
**Last Updated**: 2026-03-02

---

## Conventions

- **[CARE-BE]** = care backend (Django/Python)
- **[CARE-FE]** = care_fe (React/TypeScript)
- **[SWITCH]** = UHI Switch Server (new, Go/FastAPI)
- **[HW-APP]** = HealthWallet Flutter app
- **[HW-BE]** = HealthWallet backend (FastAPI/Go)
- **[INFRA]** = Infrastructure / DevOps
- **[AI]** = AI/ML work (MedGemma or Gemma)

Priority: 🔴 Blocker | 🟠 High | 🟡 Medium | 🟢 Nice-to-have

---

## Phase 0 — Foundation (No code skips this)
*Goal: Get the data pipeline and security model right before building features.*

### 0.1 FHIR R5 Audit & Gap Analysis
- 🔴 [CARE-BE] Audit all existing CARE models — map to FHIR R5 resource types
- 🔴 [CARE-BE] Identify gaps: which clinical resources lack FHIR R5 serializers?
- 🔴 [CARE-BE] Create `fhir_export/` Django app with resource serializers:
  - `Patient` → from `care.patient.PatientRegistration`
  - `Observation` → from vitals, lab values
  - `DiagnosticReport` → from investigation results
  - `MedicationRequest` → from prescriptions
  - `Condition` → from diagnoses
  - `AllergyIntolerance` → from allergy records
  - `Encounter` → from consultations
- 🔴 [CARE-BE] `GET /api/fhir/r5/Patient/{abha_id}/$everything` — returns full Bundle
- 🟠 [CARE-BE] Validate output against official FHIR R5 validators (use `fhir-py` or HL7 validator)

### 0.2 BOLA Security Audit
- 🔴 [CARE-BE] Audit every patient-data API endpoint for BOLA vulnerabilities
- 🔴 [CARE-BE] Replace all sequential integer IDs on patient resources with UUID v7
- 🔴 [CARE-BE] Implement `ResourceAccessPolicy` middleware — every request validated against:
  - Direct ownership (patient requesting own data)
  - Valid consent token (doctor/hospital requesting via Switch)
- 🔴 [CARE-BE] Write unit tests for BOLA: attempt to access patient B's data as patient A → must 403
- 🟠 [CARE-BE] Security regression test suite — run in CI on every PR touching auth/patient routes

### 0.3 ABDM Integration Review
- 🔴 [CARE-BE] Audit current `care/abdm/` app — document what M1/M2 flows already work
- 🔴 [CARE-BE] List gaps vs ABDM M1-M3 certification checklist
- 🟠 [CARE-BE] Ensure ABHA linking flow works end-to-end with NHA sandbox
- 🟠 [CARE-FE] Audit ABDM consent UI flows — ensure they are accessible and complete

### 0.4 Observability Bootstrap
- 🔴 [INFRA] Add OpenTelemetry SDK to CARE backend (Python `opentelemetry-sdk`)
- 🔴 [INFRA] Instrument all HTTP endpoints with trace context propagation
- 🟠 [INFRA] Deploy OpenTelemetry Collector → Grafana Tempo (or Jaeger) in dev
- 🟠 [INFRA] Add `traceId` to all error responses (not exposed to patient/doctor — internal only)

---

## Phase 1 — UHI Switch Server (Core)
*Goal: The Switch is the heart of the platform. Build it first.*

### 1.1 Switch Server Scaffold
- 🔴 [SWITCH] Initialize repo `ohcnetwork/uhi-switch` (Go + Chi router OR FastAPI)
- 🔴 [SWITCH] PostgreSQL schema:
  ```sql
  -- consent_artifacts
  id UUID PRIMARY KEY,
  patient_abha_id TEXT NOT NULL,
  requester_id TEXT NOT NULL,
  requester_type TEXT CHECK (requester_type IN ('doctor','hospital','patient')),
  purpose TEXT NOT NULL,
  scope JSONB NOT NULL,          -- ["DiagnosticReport", "Observation"]
  exclude JSONB DEFAULT '[]',
  granted_at TIMESTAMPTZ,
  valid_from TIMESTAMPTZ,
  valid_until TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  patient_signature TEXT NOT NULL,  -- patient-signed JWT claim
  
  -- audit_log (append-only)
  id UUID PRIMARY KEY,
  event_type TEXT NOT NULL,
  actor_id TEXT,
  patient_id TEXT,
  resource_types JSONB,
  consent_ref UUID REFERENCES consent_artifacts(id),
  timestamp TIMESTAMPTZ NOT NULL,
  prev_hash TEXT NOT NULL,
  entry_hash TEXT NOT NULL
  ```
- 🔴 [SWITCH] mTLS setup — hospital CARE instances register with client certificates
- 🔴 [SWITCH] OpenTelemetry instrumentation from day one

### 1.2 Consent Broker
- 🔴 [SWITCH] `POST /consent/grant` — accept consent artifact, validate patient signature, store
- 🔴 [SWITCH] `POST /consent/revoke` — patient revokes consent (immediate; invalidate token in Redis)
- 🔴 [SWITCH] `GET /consent/list` — patient lists all active consents
- 🔴 [SWITCH] Consent token issuance — short-lived JWT scoped to consent (1-hour TTL, Redis-tracked)
- 🟠 [SWITCH] Consent expiry worker — background job to mark expired consents, notify parties

### 1.3 Identity Resolution
- 🔴 [SWITCH] Hospital registry — CARE instances register their FHIR endpoint + mTLS cert
- 🔴 [SWITCH] Patient-to-hospital mapping — "Which hospitals have records for this ABHA?"
- 🟠 [SWITCH] Fuzzy identity deduplication — handle same patient across hospitals with slightly different name/DOB
- 🟠 [SWITCH] ABHA ID as canonical identifier — all lookups keyed on ABHA, not name

### 1.4 FHIR Router
- 🔴 [SWITCH] `GET /fhir/bundle?consent_token=xxx` — validate consent, fan out to CARE instances, merge Bundle
- 🔴 [SWITCH] Scope enforcement — strip FHIR resources not in `consent.scope` before returning
- 🔴 [SWITCH] Exclude enforcement — hard-remove resource types in `consent.exclude`
- 🟠 [SWITCH] Pagination — large patient histories should page, not timeout
- 🟠 [SWITCH] Caching — cache FHIR bundles per patient per consent (TTL: 15 min) to reduce CARE load

### 1.5 Audit Log
- 🔴 [SWITCH] Write AuditEvent on every: consent grant, consent revoke, data access, emergency access
- 🔴 [SWITCH] Hash-chain enforcement — each entry includes `sha256(content + prev_hash)`
- 🔴 [SWITCH] Audit log read API (privileged, separate service) — for compliance queries
- 🟠 [SWITCH] Export audit trail to S3 with Object Lock (WORM — Write Once Read Many)

### 1.6 Break-Glass
- 🟠 [SWITCH] `POST /emergency-access` — validate doctor, issue emergency token, write audit, send notifications
- 🟠 [SWITCH] SMS dispatch (Twilio or CDAC SMS gateway) for emergency notifications
- 🟠 [SWITCH] FCM push notification to patient's device
- 🟠 [SWITCH] Emergency access abuse detection (> 5/day per doctor → alert)

---

## Phase 2 — HealthWallet App & Backend

### 2.1 HealthWallet Backend
- 🔴 [HW-BE] User registration + ABHA OAuth2 flow
- 🔴 [HW-BE] Family account model (guardian ↔ dependent linkage)
- 🔴 [HW-BE] Proxy consent requests to Switch Server
- 🟠 [HW-BE] Push notification service (FCM + APNS)
- 🟠 [HW-BE] Audit log viewer endpoint (fetch from Switch, display to patient)

### 2.2 HealthWallet Flutter App — Core
- 🔴 [HW-APP] ABHA login + token management (Flutter Secure Storage)
- 🔴 [HW-APP] FHIR R5 timeline UI — chronological list of all health records
- 🔴 [HW-APP] Consent management screen:
  - List active consents with details (who, what, until when)
  - One-tap revoke
  - Grant new consent flow
- 🔴 [HW-APP] Certificate pinning for all network calls
- 🟠 [HW-APP] Family member switching (tap profile to switch between dependents)

### 2.3 On-Device RAG (Most complex engineering task)
- 🟠 [HW-APP] FHIR record local storage — SQLCipher encrypted SQLite, keyed by FHIR resource type
- 🟠 [HW-APP] Gemma model download manager:
  - Progress UI with pause/resume
  - SHA-256 checksum verification post-download
  - Model stored in app-private directory
- 🟠 [HW-APP] llama.cpp Flutter FFI wrapper OR MediaPipe LLM Inference API integration
- 🟠 [HW-APP] Text extraction from FHIR resources (Observation values, DiagnosticReport text, etc.)
- 🟠 [HW-APP] Chunking + embedding pipeline (run post-sync, background isolate)
- 🟠 [HW-APP] LanceDB Dart FFI integration for vector store
- 🟠 [HW-APP] Chat UI — query input → RAG retrieval → Gemma inference → response with record citations
- 🟢 [HW-APP] Multilingual output (detect device locale, prompt Gemma to respond in that language)

---

## Phase 3 — CARE EMR Plugin (MedGemma)

### 3.1 Plugin Integration
- 🔴 [CARE-FE] Create `MedGemmaPlugin` Care App entry point (federated module or sidebar panel)
- 🔴 [CARE-FE] On consultation open: trigger UHI patient history fetch (via consent token)
- 🔴 [CARE-FE] Display fetched cross-hospital records in consultation sidebar
- 🔴 [CARE-BE] New endpoint: `POST /api/medgemma/analyze` — accepts FHIR bundle, returns structured analysis

### 3.2 MedGemma Analysis
- 🟠 [AI] MedGemma inference service (FastAPI + GPU instance)
- 🟠 [AI] Prompt templates for: report summarization, trend analysis, differential diagnosis hints
- 🟠 [AI] Structured output schema — return JSON with: summary, flags, suggested_questions
- 🟠 [CARE-FE] Render MedGemma output in doctor-readable format (not raw JSON)
- 🟠 [AI] DDI (Drug-Drug Interaction) checker — on MedicationRequest write, cross-check MedGemma + knowledge graph

### 3.3 Ambient Scribing (Care Scribe)
- 🟢 [CARE-FE] LiveKit session initiation with explicit patient consent checkbox
- 🟢 [AI] Whisper or Chirp transcription service for audio stream
- 🟢 [AI] MedGemma SOAP note extraction from transcript
- 🟢 [CARE-FE] Auto-populate EMR fields with extracted SOAP content (editable, doctor confirms)

---

## Phase 4 — Reliability & Compliance

### 4.1 Offline-First EMR (CRDT)
- 🟠 [CARE-BE] Identify which FHIR resources are CRDT-safe (Observation, Vitals) vs need conflict resolution (MedicationRequest)
- 🟠 [CARE-BE] Implement CRDT-based sync layer using `pycrdt` or `yrs` (Yjs Rust port)
- 🟠 [CARE-FE] Offline detection + graceful degradation UI
- 🟠 [CARE-BE] Sync queue with retry + conflict resolution UI for disputed records

### 4.2 ABDM Certification
- 🔴 [CARE-BE] Complete M1 certification with ABDM test harness (NHA sandbox)
- 🔴 [CARE-BE] Complete M2 certification
- 🟠 [CARE-BE] M3 — diagnostic lab report sharing via FHIR

### 4.3 Load Testing & SLOs
- 🟠 [INFRA] Define SLOs: Switch p95 < 2s, consent grant < 500ms, FHIR bundle fetch < 5s
- 🟠 [INFRA] Load test Switch Server: 10,000 concurrent consent validations
- 🟠 [INFRA] Load test CARE FHIR export: 1,000 concurrent bundle requests
- 🟠 [INFRA] Chaos testing: hospital CARE instance goes down → Switch gracefully degrades

---

## Immediate First Sprint (Next 2 Weeks)

If starting tomorrow, do these in order:

1. **[CARE-BE]** Run BOLA audit — find and fix the worst 3 vulnerabilities
2. **[CARE-BE]** Build `GET /api/fhir/r5/Patient/{abha_id}/$everything` endpoint
3. **[SWITCH]** Initialize repo, PostgreSQL schema, basic HTTP server
4. **[SWITCH]** `POST /consent/grant` + `GET /consent/list` working end-to-end
5. **[INFRA]** OpenTelemetry in CARE backend + Switch, traces visible in Grafana
6. **[HW-APP]** ABHA login flow working in Flutter (no RAG yet — just auth + timeline display)
