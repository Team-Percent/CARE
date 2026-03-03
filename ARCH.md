# ARCH — System Architecture
**Platform**: OHC UHI / HealthBridge  
**Status**: Design Phase  
**Maintainer**: Antigravity Team  
**Last Updated**: 2026-03-02

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PATIENT LAYER                                │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │              HealthWallet (Flutter App)                       │  │
│   │                                                              │  │
│   │  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐  │  │
│   │  │  FHIR R5     │  │  On-Device RAG │  │  Consent Mgmt   │  │  │
│   │  │  Timeline UI │  │  (LanceDB +    │  │  (DEPA Model)   │  │  │
│   │  │              │  │   Gemma 1.5GB) │  │                 │  │  │
│   │  └──────────────┘  └────────────────┘  └─────────────────┘  │  │
│   └──────────────────────────────┬───────────────────────────────┘  │
└─────────────────────────────────-│─────────────────────────────────┘
                                   │ HTTPS + mTLS + JWT (ABHA)
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                     UHI SWITCH SERVER (New Build)                   │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │   Identity  │  │   Consent    │  │    Audit Log Service     │   │
│  │  Resolution │  │   Broker     │  │  (Append-only, chained)  │   │
│  │  (ABHA + FN)│  │  (DEPA std)  │  │                          │   │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘   │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │  FHIR R5    │  │  Rate Limiter│  │   OpenTelemetry          │   │
│  │  Router     │  │  + Quota     │  │   Collector              │   │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘   │
└────────────────────────┬─────────────────┬──────────────────────────┘
                         │                 │
           ┌─────────────┘                 └───────────────┐
           │                                               │
┌──────────▼──────────────┐             ┌──────────────────▼──────────┐
│   CARE Backend           │             │  CARE Backend (Hospital B)  │
│   (Hospital A)           │             │                             │
│                          │             │  ┌────────────────────────┐ │
│  ┌─────────────────────┐ │             │  │  MedGemma Plugin        │ │
│  │  CARE EMR (Django)  │ │             │  │  - Report Analysis      │ │
│  │  FHIR R5 Native     │ │             │  │  - SOAP Autofill        │ │
│  │  ABDM M1-M3         │ │             │  │  - DDI Checker          │ │
│  └─────────────────────┘ │             │  └────────────────────────┘ │
│                          │             │                             │
│  ┌─────────────────────┐ │             │  ┌────────────────────────┐ │
│  │  care_fe (React/TS) │ │             │  │  care_fe (React/TS)    │ │
│  │  EMR Frontend       │ │             │  │  EMR Frontend          │ │
│  └─────────────────────┘ │             │  └────────────────────────┘ │
└──────────────────────────┘             └─────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 care_fe (Frontend)
- **Repo**: `ohcnetwork/care_fe`
- **Stack**: React 18, TypeScript, Tailwind CSS, shadcn/ui, Vite
- **State**: Zustand + React Query (TanStack)
- **Key pages**: Patient dashboard, EMR forms, Consultation view, ABDM flow
- **Plugin system**: Care Apps are loaded as federated modules (MFE pattern)
- **MedGemma plugin entry point**: Likely a sidebar panel in the Consultation page
- **API layer**: REST over HTTPS to CARE backend; WebSocket for LiveKit (Scribe)

**Critical files to know:**
```
src/
  components/
    Patient/          # Patient record views
    Consultation/     # Doctor consultation forms (SOAP target)
    ABDM/             # ABDM consent + linking flows
  pages/
  hooks/
  redux/ or store/    # Global state
```

### 2.2 care (Backend)
- **Repo**: `ohcnetwork/care`
- **Stack**: Python 3.12+, Django 4.x, Django REST Framework, Celery, PostgreSQL, Redis
- **FHIR**: FHIR R5 resource generation (likely via `fhir.resources` lib or custom serializers)
- **ABDM**: M1-M3 compliant — HIP/HIU flows, Health Locker linking
- **Auth**: JWT-based, ABHA token integration
- **Key apps (Django apps):**
```
care/
  facility/           # Hospital, bed, ward management
  patient/            # Patient model, medical history
  abdm/               # ABDM HIP/HIU/consent flows  ← most relevant
  hcx/                # Health Claims Exchange
  users/              # Auth, roles, permissions
```

**New endpoints we will add:**
- `POST /api/uhi/consent/grant` — patient grants consent to Switch
- `GET /api/uhi/fhir/patient/{abha_id}/bundle` — FHIR R5 bundle export for Switch
- `POST /api/uhi/webhook/consent-event` — Switch notifies CARE of consent changes

### 2.3 HealthWallet Backend
- **Stack**: TBD (recommend FastAPI / Python or Go for performance)
- **Responsibilities**:
  - ABHA identity auth + token refresh
  - Proxy/cache layer between app and Switch Server
  - Push notification dispatch (FCM)
  - Family account linkage (guardian → dependent)
  - Consent artifact storage (user-owned)
- **Database**: PostgreSQL for user/consent data; no raw health data stored here (data lives in CARE)
- **Key design constraint**: HealthWallet backend must NEVER store raw FHIR clinical data. It stores pointers (consent refs, hospital IDs, fetch timestamps), not records.

### 2.4 UHI Switch Server (New Build)
- **Stack**: Go (recommended for throughput) or FastAPI
- **Responsibilities**: Identity resolution, consent brokering, FHIR routing, audit log, rate limiting
- **Database**: 
  - PostgreSQL — consent artifacts, identity mappings
  - Append-only log store (TimescaleDB or Loki) — audit chain
  - Redis — rate limiting, short-lived consent tokens
- **Tracing**: OpenTelemetry SDK → Grafana Tempo or Jaeger

---

## 3. Data Flow: Patient Shares Record with Doctor

```
Patient opens HealthWallet
    │
    ▼
Selects "Share with Dr. Arvind @ Apollo"
    │
    ▼
HealthWallet App creates Consent Artifact (DEPA)
  { purpose: "diagnosis", scope: ["LabReport", "Prescription"],
    valid_until: "+24h", exclude: ["MentalHealthRecord"] }
    │
    ▼ HTTPS POST /consent/grant
UHI Switch Server
  ├── Validates patient JWT (ABHA token)
  ├── Validates requester (doctor/hospital) identity
  ├── Writes Consent Artifact → PostgreSQL
  ├── Appends to Audit Log (cryptographic chain)
  └── Returns: consent_token (short-lived, scoped)
    │
    ▼
Doctor in CARE EMR triggers "Fetch Patient History"
    │
    ▼ GET /fhir/bundle?consent_token=xxx
UHI Switch Server
  ├── Validates consent_token scope + expiry
  ├── Resolves patient ABHA ID → CARE hospital endpoints
  ├── Fans out FHIR R5 bundle requests to each CARE instance
  ├── Filters resources per consent scope (strips excluded types)
  ├── Aggregates + returns merged FHIR Bundle
  └── Appends read event to Audit Log
    │
    ▼
CARE EMR (care_fe) renders records in MedGemma sidebar
MedGemma analyzes + surfaces diagnostic suggestions
```

---

## 4. On-Device RAG Architecture (HealthWallet App)

```
HealthWallet App (Flutter)
│
├── FHIR Sync Service
│     └── On consent grant: fetches FHIR Bundle from Switch
│     └── Stores raw FHIR JSON in encrypted local SQLite
│
├── Embedding Pipeline (runs on sync)
│     └── Extracts text from FHIR resources (Observation, DiagnosticReport, etc.)
│     └── Chunks text (256 token windows, 32 overlap)
│     └── Generates embeddings via on-device MiniLM or Gemma embedding layer
│     └── Stores vectors in LanceDB (embedded, no server)
│
├── Gemma 1.5B (on-device, INT4 quantized)
│     └── Downloaded once, stored in app data dir
│     └── Loaded via llama.cpp Flutter FFI or MediaPipe LLM Inference API
│
└── Query Pipeline
      Patient types: "Why is my HbA1c trending up?"
          │
          ▼
      Vector search LanceDB → top-K relevant FHIR chunks
          │
          ▼
      Build prompt:
        [System]: You are a personal health assistant. Answer only from
                  the patient records provided. Do not speculate.
        [Context]: {retrieved FHIR chunks}
        [User]: {patient question}
          │
          ▼
      Gemma generates response (fully offline, on-device)
          │
          ▼
      Response shown with citations to source records
```

---

## 5. Break-Glass Protocol

```
ER Doctor triggers "Emergency Access" for unconscious patient
    │
    ▼ POST /emergency-access  { doctor_id, patient_abha_id, reason }
UHI Switch Server
  ├── Validates doctor identity + hospital registration
  ├── Grants temporary 4-hour full-scope access token
  ├── Appends EMERGENCY_ACCESS event to immutable audit log
  │     { actor, patient, timestamp, reason, hospital, hash_prev_entry }
  └── Dispatches IMMEDIATE notification:
        - SMS to patient's registered emergency contacts
        - Email to patient's family guardians
        - Push notification to patient's HealthWallet (if phone reachable)
```

---

## 6. FHIR R5 Resource Types in Scope

| Resource | Used By | Direction |
|---|---|---|
| Patient | All | Read |
| Observation | App, EMR Plugin | Read/Write |
| DiagnosticReport | App, EMR Plugin | Read |
| Condition | EMR Plugin, Switch | Read |
| MedicationRequest | EMR Plugin, DDI Checker | Read/Write |
| AllergyIntolerance | DDI Checker | Read |
| Encounter | EMR, Switch | Read |
| Consent | Switch Server | Read/Write |
| Bundle | Switch (transport) | Read/Write |
| AuditEvent | Switch (audit log) | Write |

---

## 7. Tech Stack Summary

| Component | Language | Framework | DB | Infra |
|---|---|---|---|---|
| care_fe | TypeScript | React 18, Vite | — | Docker, Nginx |
| care backend | Python 3.12 | Django 4, DRF | PostgreSQL, Redis | Docker, Celery |
| HealthWallet backend | Go / Python | Gin / FastAPI | PostgreSQL, Redis | Docker |
| UHI Switch Server | Go | Gin / Chi | PostgreSQL, TimescaleDB, Redis | Docker, K8s |
| HealthWallet app | Dart | Flutter 3.x | SQLite, LanceDB | Android/iOS |
| AI (on-device) | C++ / Dart | llama.cpp FFI / MediaPipe | LanceDB | On-device |
| AI (server) | Python | FastAPI | — | GPU instance |
| Observability | — | OpenTelemetry | Grafana, Tempo, Loki | K8s sidecar |

---

## 8. Deployment Model

```
Production (K8s)
├── care-backend (deployment, 3 replicas min)
├── care-fe (static, CDN served)
├── uhi-switch-server (deployment, 5 replicas, HPA enabled)
├── healthwallet-backend (deployment, 2 replicas)
├── postgresql (StatefulSet or managed RDS)
├── redis (StatefulSet or ElastiCache)
├── opentelemetry-collector (DaemonSet)
└── grafana-stack (monitoring namespace)
```

Each hospital CARE instance runs independently and registers with the Switch Server. The Switch Server never holds health data — it is a routing + consent + audit layer only.
