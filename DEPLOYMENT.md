# DEPLOYMENT — Two-Hospital Setup on Separate Networks + UHI Switch

**Platform**: OHC UHI / HealthBridge
**Last Updated**: 2026-03-03

---

## Architecture Overview

```
┌──────────────── INTERNAL NETWORK 1 (PC-1) ──────────────────┐
│                                                               │
│  HOSPITAL A — CityCare Multispeciality Hospital               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ CARE Backend     │  │ CARE Frontend   │  │ PostgreSQL   │  │
│  │ :9000            │  │ :4000           │  │ :5432        │  │
│  │ + MedGemma       │  │                 │  │              │  │
│  └────────┬────────┘  └─────────────────┘  └──────────────┘  │
│           │                                                   │
│  Records: Months 1-10 progress reports                        │
│           CT/X-ray months 1-2                                 │
└───────────┼───────────────────────────────────────────────────┘
            │
            │  HTTPS (internet)
            ▼
┌────────────────────── INTERNET ──────────────────────────────┐
│                                                               │
│  UHI SWITCH SERVER — Consent Broker + Key Manager             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  FastAPI :8080                                           │ │
│  │  ⚠️  NO PATIENT DATA STORED                              │ │
│  │                                                          │ │
│  │  Services:                                               │ │
│  │  • Hospital Registry       • Consent Management          │ │
│  │  • S3 Encrypted Storage    • Key Sharing                 │ │
│  │  • Mobile App APIs         • Audit Chain                 │ │
│  │  • Emergency Access        • Bucket Auto-Expiry          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  Deployed on: Railway / Fly.io / AWS EC2 / Any VPS            │
│  API Docs: https://your-switch.example.com/docs               │
└───────────┼───────────────────────────────────────────────────┘
            │
            │  HTTPS (internet)
            ▼
┌──────────────── INTERNAL NETWORK 2 (PC-2) ──────────────────┐
│                                                               │
│  HOSPITAL B — Metro Radiology & Diagnostics Center            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ CARE Backend     │  │ CARE Frontend   │  │ PostgreSQL   │  │
│  │ :9001            │  │ :4001           │  │ :5433        │  │
│  │ + MedGemma       │  │                 │  │              │  │
│  └────────┬────────┘  └─────────────────┘  └──────────────┘  │
│           │                                                   │
│  Records: CT/X-ray months 3-8                                 │
│           Baseline chest X-ray image (CTR 52%)                │
└───────────────────────────────────────────────────────────────┘
```

---

## 1. Prerequisites

| PC | Requirements |
|---|---|
| PC-1 (Hospital A) | Docker, 4GB RAM, ports 4000/9000/5432/6379 |
| PC-2 (Hospital B) | Docker, 4GB RAM, ports 4001/9001/5433/6380 |
| Cloud (UHI Switch) | Python 3.10+, 512MB RAM, port 8080 |

---

## 2. Deploy Hospital A (PC-1)

```bash
# On PC-1 — Internal Network 1
cd hospital-a/

# Configure (edit .env if needed)
cat .env

# Start all services
docker compose up -d

# Verify
curl http://localhost:9000/api/health
# Frontend: http://localhost:4000
```

**Patient Data Available**: Devaganesh S (DG-2026-001)
- 10 monthly progress reports (BP 150/95 → 108/68)
- CT/X-ray months 1-2 (baseline normal)
- Primary diagnosis: Hypertension with Mild Obesity

---

## 3. Deploy Hospital B (PC-2)

```bash
# On PC-2 — Internal Network 2
cd hospital-b/

# Configure (edit .env if needed)
cat .env

# Start all services
docker compose up -d

# Verify
curl http://localhost:9001/api/health
# Frontend: http://localhost:4001
```

**Patient Data Available**: Devaganesh S (referred from CityCare)
- CT/X-ray months 3-8 (progressive improvement)
- Baseline chest X-ray image (CTR 52% → 46%)

---

## 4. Deploy UHI Switch Server (Internet)

### Option A: Local Development

```bash
cd uhi-switch/
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# API Docs: http://localhost:8080/docs
```

### Option B: Docker

```bash
cd uhi-switch/
docker compose up -d --build
```

### Option C: Deploy to Internet (Production)

**Railway (Recommended — easiest):**
```bash
cd uhi-switch/
npm install -g @railway/cli
railway login
railway init
railway up
# → https://your-switch.up.railway.app
```

**Fly.io:**
```bash
cd uhi-switch/
flyctl launch --name uhi-switch
flyctl deploy
# → https://uhi-switch.fly.dev
```

**AWS EC2 / Any VPS:**
```bash
# On the VPS:
git clone <repo> && cd uhi-switch
docker compose up -d --build

# Add Nginx reverse proxy:
sudo apt install nginx certbot
# Configure HTTPS with Let's Encrypt
```

**Production Checklist:**
- [ ] Replace SQLite → PostgreSQL
- [ ] Enable HTTPS (Nginx + Let's Encrypt)
- [ ] Set CORS_ORIGINS to hospital domains only
- [ ] Add rate limiting (Redis-backed)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure S3 lifecycle policies for auto-deletion

---

## 5. Register Hospitals with UHI Switch

```bash
UHI=https://your-switch.example.com  # or http://localhost:8080

# Register Hospital A
curl -X POST $UHI/hospital/register \
  -H "Content-Type: application/json" \
  -d '{"name":"CityCare Multispeciality Hospital","endpoint_url":"http://hospital-a:9000","city":"Chennai","state":"Tamil Nadu"}'

# Register Hospital B
curl -X POST $UHI/hospital/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Metro Radiology & Diagnostics","endpoint_url":"http://hospital-b:9001","city":"Mumbai","state":"Maharashtra"}'

# Verify
curl $UHI/hospital/list
```

---

## 6. Complete Data Sharing Flow (S3 Storage)

### Production Architecture
```
Hospital A (internal) → encrypts FHIR bundle → uploads to S3 bucket
                                                     ↓
Patient (mobile app)  → grants consent via HealthWallet
                                                     ↓
Hospital B (internal) → validates consent → gets presigned URL + key
                      → downloads encrypted bundle from S3
                      → decrypts locally
                                                     ↓
S3 bucket             → auto-deleted after expiry (set by Hospital A or patient)
```

### Step-by-Step Demo

```bash
UHI=http://localhost:8080

# ── Step 1: Hospital A encrypts and uploads FHIR bundle to S3 ──
UPLOAD=$(curl -s -X POST $UHI/storage/upload \
  -H "Content-Type: application/json" \
  -d '{
    "patient_abha_id": "91-1234-5678-9012",
    "source_hospital_id": "HOSP-CITYCARE-A",
    "encrypted_bundle": "eyJyZXNvdXJjZVR5cGUiOiJCdW5kbGUi...",
    "resource_count": 38,
    "resource_types": ["Patient","Observation","DiagnosticReport","Condition"],
    "expires_in_hours": 24,
    "max_downloads": 3
  }')
echo $UPLOAD | python3 -m json.tool
# Returns: bucket_id, presigned_token, encryption_key, presigned_url


# ── Step 2: Patient grants consent from mobile app ──
CONSENT=$(curl -s -X POST $UHI/app/consent/grant \
  -H "Content-Type: application/json" \
  -d '{
    "patient_abha_id": "91-1234-5678-9012",
    "requesting_hospital_id": "HOSP-METRO-B",
    "purpose": "second_opinion",
    "valid_hours": 24
  }')
TOKEN=$(echo $CONSENT | python3 -c "import sys,json;print(json.load(sys.stdin)['consent_token'])")
echo "Consent token: $TOKEN"


# ── Step 3: Hospital B requests bundle access ──
curl -s -X POST $UHI/bundle/request \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_abha_id\": \"91-1234-5678-9012\",
    \"requesting_hospital_id\": \"HOSP-METRO-B\",
    \"consent_token\": \"$TOKEN\"
  }" | python3 -m json.tool
# Returns: presigned_url + encryption_key


# ── Step 4: Hospital B downloads encrypted bundle from S3 ──
PRESIGNED_TOKEN=$(echo $UPLOAD | python3 -c "import sys,json;print(json.load(sys.stdin)['presigned_token'])")
curl -s "$UHI/storage/download?token=$PRESIGNED_TOKEN" | python3 -m json.tool
# Returns: encrypted_data, data_hash, resource_count


# ── Step 5: Verify audit trail ──
curl -s $UHI/audit/verify | python3 -m json.tool
curl -s $UHI/audit/log | python3 -c "
import sys,json
for e in json.load(sys.stdin):
    print(f'{e[\"action\"]:25s} | {e[\"actor\"]:20s} | {e[\"resource\"]}')
"
```

---

## 7. Mobile App (HealthWallet) API Reference

These endpoints power the Flutter HealthWallet app:

| Endpoint | Method | Description |
|---|---|---|
| `/app/patient/{abha}/bundles` | GET | List patient's data bundles across hospitals |
| `/app/patient/{abha}/consents` | GET | List all consents (active/revoked) |
| `/app/patient/{abha}/summary` | GET | Health data summary across all hospitals |
| `/app/consent/grant` | POST | Patient grants consent from mobile |
| `/app/consent/{id}/revoke` | POST | Patient revokes consent from mobile |

---

## 8. Patient: Devaganesh S — Data Distribution

| Hospital | Records | Location |
|---|---|---|
| **Hospital A** (CityCare) | 10 monthly progress reports, CT/X-ray months 1-2 | `hospital-a/patient_data.py` |
| **Hospital B** (Metro Radiology) | CT/X-ray months 3-8, baseline X-ray image | `hospital-b/patient_data.py` |
| **Reports (raw)** | PDF reports, X-ray JPEG | `devaganesh-reports-hospital-1/`, `devaganesh-reports-hospital-2/` |

**Clinical Journey**:
```
Month 1:  BP 150/95, BMI 29.5, HR 92  → Amlodipine + DASH diet
Month 4:  BP 120/78, BMI 24.5         → Medication DISCONTINUED
Month 7:  BP 114/72, BMI 23.0, HDL 55 → Lifestyle only
Month 10: BP 108/68, BMI 22.0, HDL 62 → FULLY RESOLVED ✅
X-ray:    CTR 52% (borderline) → 46% (optimal) ✅
```

---

## 9. Security — S3 Storage Flow

```
┌───────────────────────────────────────────────────────────────┐
│                    S3 ENCRYPTED STORAGE FLOW                   │
│                                                                │
│  Hospital A:                                                   │
│    FHIR Bundle → AES-256 Encrypt → POST /storage/upload        │
│                                    ↓                          │
│  UHI Switch:                                                   │
│    Creates S3 bucket → stores encrypted blob                   │
│    Generates presigned URL + encryption key                    │
│    Sets auto-expiry (24h default)                              │
│    Max downloads: 5 (configurable)                             │
│                                                                │
│  Patient (via mobile app):                                     │
│    Receives notification → POST /app/consent/grant             │
│                                                                │
│  Hospital B (with valid consent):                              │
│    POST /bundle/request → gets presigned_url + key             │
│    GET /storage/download?token=xxx → encrypted blob            │
│    Decrypts locally → FHIR bundle                              │
│                                                                │
│  After expiry:                                                 │
│    POST /storage/cleanup-expired → data WIPED                  │
│    S3 bucket → DELETED (lifecycle policy in production)        │
│                                                                │
│  Production mapping:                                           │
│    Mock presigned_token  → AWS S3 Presigned URL                │
│    SQLite storage        → AWS S3 + SSE-S3 encryption          │
│    /storage/upload       → aws s3 cp + generate-presigned-url  │
│    /storage/download     → S3 GetObject with presigned URL     │
│    /storage/cleanup      → S3 Lifecycle Policy (auto)          │
└───────────────────────────────────────────────────────────────┘
```

---

## 10. Quick Reference — All Services

| Service | Network | Port | URL |
|---|---|---|---|
| Hospital A Backend | Internal 1 | 9000 | http://pc1:9000 |
| Hospital A Frontend | Internal 1 | 4000 | http://pc1:4000 |
| Hospital B Backend | Internal 2 | 9001 | http://pc2:9001 |
| Hospital B Frontend | Internal 2 | 4001 | http://pc2:4001 |
| UHI Switch | Internet | 8080 | https://your-switch.example.com |
| Switch API Docs | Internet | 8080 | https://your-switch.example.com/docs |

---

## 11. Hackathon Demo Script

1. **Show Hospital A** → `http://pc1:4000/medgemma` → Devaganesh S patient card
2. **Show reports** → Progress months 1-10, CT/X-ray baseline
3. **Run MedGemma** → Trend analysis showing BP/BMI improvement
4. **Export FHIR** → ABHA `91-1234-5678-9012` → R5 bundle
5. **Upload to S3** → `POST /storage/upload` → encrypted bundle in S3 bucket
6. **Patient consent** → Mobile app: `POST /app/consent/grant`
7. **Hospital B requests** → `POST /bundle/request` → gets presigned URL + key
8. **Download + decrypt** → `GET /storage/download` → encrypted blob
9. **Audit trail** → `GET /audit/log` → all actions hash-chained
10. **Bucket cleanup** → `POST /storage/cleanup-expired` → data auto-wiped
11. **Show Hospital B** → `http://pc2:4001/medgemma` → referral CT/X-ray data
12. **Mobile app summary** → `GET /app/patient/{abha}/summary` → cross-hospital view
