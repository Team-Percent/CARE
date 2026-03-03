# OHC UHI — Secure Inter-Hospital Data Exchange

A hackathon demo showing how patient health records can be **securely shared between hospitals** using encrypted FHIR bundles, patient-controlled consent, and a zero-data-storage broker.

## 🏗️ System Architecture

```
┌─── PC-1 (Hospital A) ───┐     ┌──── INTERNET ────┐     ┌─── PC-2 (Hospital B) ───┐
│ CityCare Hospital        │     │  UHI SWITCH       │     │ Metro Radiology          │
│ CARE EMR + MedGemma      │◄───►│  Consent Broker   │◄───►│ CARE EMR + MedGemma      │
│ :9000 / :4000            │     │  S3 Storage       │     │ :9001 / :4001            │
│                          │     │  ⚠️ NO DATA STORED │     │                          │
└──────────────────────────┘     │  :8080            │     └──────────────────────────┘
                                 └───────────────────┘
```

## 📂 Repository Structure

```
├── care_medgemma/       # Django plugin — MedGemma AI + FHIR export
├── hospital-a/          # Hospital A deployment (docker-compose + setup)
├── hospital-b/          # Hospital B deployment (docker-compose + setup)
├── devaganesh-reports-hospital-1/  # Patient reports (Hospital A)
├── devaganesh-reports-hospital-2/  # Patient reports (Hospital B)
├── DEPLOYMENT.md        # Detailed deployment guide
├── ARCH.md / PRD.md / SECURITY.md / TASK.md / NOTE.md  # Design docs
```

**Separate repos:**
- [uhi-switch](https://github.com/Team-Percent/uhi-switch) — UHI Switch Server
- [CareConnect](https://github.com/Team-Percent/CareConnect) — Flutter mobile app

## 🚀 Quick Start — Deploy Everything

### Step 1: Clone This Repo
```bash
git clone https://github.com/Team-Percent/care-uhi.git
cd care-uhi
```

### Step 2: Deploy UHI Switch (Internet Server)
```bash
git clone https://github.com/Team-Percent/uhi-switch.git
cd uhi-switch
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080

# API Docs: http://localhost:8080/docs
```

### Step 3: Deploy Hospital A (PC-1)
```bash
cd hospital-a
chmod +x setup.sh
./setup.sh

# Frontend: http://localhost:4000
# MedGemma: http://localhost:4000/medgemma
```

### Step 4: Deploy Hospital B (PC-2)
```bash
cd hospital-b
chmod +x setup.sh
./setup.sh

# Frontend: http://localhost:4001
# MedGemma: http://localhost:4001/medgemma
```

### Step 5: Connect Everything
```bash
UHI=http://localhost:8080

# Register hospitals
curl -X POST $UHI/hospital/register -H "Content-Type: application/json" \
  -d '{"name":"CityCare Hospital","endpoint_url":"http://localhost:9000","city":"Chennai","state":"Tamil Nadu"}'

curl -X POST $UHI/hospital/register -H "Content-Type: application/json" \
  -d '{"name":"Metro Radiology","endpoint_url":"http://localhost:9001","city":"Mumbai","state":"Maharashtra"}'
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full data sharing flow and demo script.

## 🔐 How It Works

1. **Hospital A** creates a FHIR bundle → encrypts it → uploads to S3 bucket via UHI Switch
2. **Patient** grants consent from mobile app (HealthWallet)
3. **Hospital B** requests access → Switch validates consent → **Hospital A** shares presigned URL + decryption key
4. **Hospital B** downloads encrypted bundle → decrypts locally
5. **S3 bucket** auto-deletes after expiry

**The UHI Switch NEVER stores patient data.** It only brokers consent and routes encryption keys.

## 👤 Demo Patient

**Devaganesh S** — 24M, ABHA: 91-1234-5678-9012
- Primary Diagnosis: Hypertension with Mild Obesity
- 10-month lifestyle transformation: BP 150/95 → 108/68, BMI 29.5 → 22.0
- Hospital A: Progress reports + CT/X-ray months 1-2
- Hospital B: CT/X-ray months 3-8 + baseline chest X-ray

## 📄 License

Hackathon demo — built on [CARE by Open Healthcare Network](https://github.com/ohcnetwork/care)
