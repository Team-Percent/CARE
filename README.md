# OHC UHI — Secure Inter-Hospital Data Exchange

A hackathon demo showing how patient health records can be **securely shared between hospitals** using encrypted FHIR bundles, patient-controlled consent, and a zero-data-storage broker. It also demonstrates how the **MedGemma** AI model works inside the EMR platform to analyze reports and provide constructive insights.

## 🏗️ System Architecture

The system is purposely built for mock purposes, consisting of three main environments:

```
┌─── System 1 (Hospital A) ───┐     ┌──── INTERNET ────┐     ┌─── System 2 (Hospital B) ───┐
│ CityCare Hospital           │     │  UHI SWITCH      │     │ Metro Radiology             │
│ Local Network               │◄───►│  Consent Broker  │◄───►│ Local Network               │
│ CARE EMR + MedGemma         │     │  No Data Storage │     │ CARE EMR + MedGemma         │
│ :9001 / :4001               │     │  :8080 (Cloud)   │     │ :9002 / :4002               │
└─────────────────────────────┘     └──────────────────┘     └─────────────────────────────┘
                                             ▲
                                             │
                                  ┌──────────┴─────────┐
                                  │ Patient Mobile App │
                                  │ (Flutter)          │
                                  └────────────────────┘
```
**Important:** Hospital A and Hospital B are on completely separate internal networks and *only* communicate with each other through the UHI-Switch.

## 📂 Repository Structure

```
├── care_medgemma/       # Django plugin — MedGemma AI + FHIR export + Consent
├── hospital-a/          # Hospital A deployment (docker-compose + setup)
├── hospital-b/          # Hospital B deployment (docker-compose + setup)
├── devaganesh-reports-hospital-1/  # Patient reports (Hospital A) - Months 1-10 Progress, Months 1-2 Imaging
├── devaganesh-reports-hospital-2/  # Patient reports (Hospital B) - Months 3-8 Imaging
├── uhi-switch/          # Central consent broker server
├── DEPLOYMENT.md        # Detailed deployment guide for 2 systems
├── CareConnect/         # Flutter mobile app 
```

## 🚀 Quick Start — Deploy on 2 Systems

### Step 1: UHI Switch
The UHI Switch application is hosted on a VPS at:
- 🌐 **Server**: https://uhi-switch-production.up.railway.app
- 📖 **API Docs**: https://uhi-switch-production.up.railway.app/docs

The python server maintains a consistent connection with the hospitals' backends and sends notifications to the admin in case of any outage.

### Step 2: Deploy Hospital A (On System 1)
Clone this repository on your first machine:
```bash
cd hospital-a
docker compose up -d

# Frontend: http://localhost:4001 (Login: admin / admin OR doctor_a / doctor_a)
# Backend: http://localhost:9001
```

### Step 3: Deploy Hospital B (On System 2)
Clone this repository on your second machine:
```bash
cd hospital-b
docker compose up -d

# Frontend: http://localhost:4002 (Login: admin / admin OR doctor_b / doctor_b)
# Backend: http://localhost:9002
```

### Step 4: The Mobile App
The Flutter application (`CareConnect/`) can be run on a mobile emulator to represent the patient. It connects to the UHI Switch to manage consents and view summary data.

## 🔐 Core Demo Flow

1. **Patient Data Initialization:** Hospital A holds mock data from `devaganesh-reports-hospital-1/` and Hospital B holds mock data from `devaganesh-reports-hospital-2/`.
2. **Analysis Request:** A doctor wants to analyze the medical reports from Month 2-8 from a single patient (ABHA ID: `91-1234-5678-9012`). 
3. **Patient Consent:** This creates a request in the patient application (HealthWallet). The patient reviews and approves the data access.
4. **Data Routing:** The UHI Switch brokers the consent and routes the encryption keys. The required data is fetched from the respective hospitals.
5. **MedGemma Dashboard:** The data shows up in the MedGemma dashboard within the EMR platform.
6. **AI Analysis:** The MedGemma model analyzes the longitudinal data (Months 2-8) and gives a constructive output (this functionality is mocked to run efficiently within RAM constraints).

**The UHI Switch NEVER stores patient data.** It only brokers consent and routes encryption keys.

See [DEPLOYMENT.md](DEPLOYMENT.md) for full reproduction steps.