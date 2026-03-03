# DEPLOYMENT — Two-System Setup for Mock Demonstration

This guide explains how to deploy the OHC UHI / HealthBridge mock demonstration. The system is purposefully built to be deployed across two separate physical or virtual systems, representing two distinct hospitals on their own internal networks. They communicate exclusively through the UHI Switch.

---

## Architecture Overview

```
┌───────────────── SYSTEM 1 (Network A) ──────────────────┐
│                                                           │
│  HOSPITAL A — CityCare Multispeciality Hospital           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐  │
│  │ CARE Backend     │  │ CARE Frontend   │  │ Postgres  │  │
│  │ :9001            │  │ :4001           │  │ :5432     │  │
│  │ + MedGemma       │  │                 │  │           │  │
│  └────────┬────────┘  └─────────────────┘  └───────────┘  │
│           │                                               │
│  Records: devaganesh-reports-hospital-1/                  │
│           (Months 1-10 progress, CT/X-ray months 1-2)     │
└───────────┼───────────────────────────────────────────────┘
            │
            │  HTTPS (internet)
            ▼
┌────────────────────── INTERNET ───────────────────────────┐
│                                                           │
│  UHI SWITCH SERVER — Consent Broker + Key Manager         │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  FastAPI (Python)                                    │ │
│  │  ⚠️  NO PATIENT DATA STORED                          │ │
│  │  (Maintains consistent connection with hospitals)    │ │
│  │  (Sends notifications to admin on outage)            │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
│  Deployed on: VPS (Railway)                               │
│  URL: https://uhi-switch-production.up.railway.app        │
└───────────┼───────────────────────────────────────────────┘
            │
            │  HTTPS (internet)
            ▼
┌───────────────── SYSTEM 2 (Network B) ──────────────────┐
│                                                           │
│  HOSPITAL B — Metro Radiology & Diagnostics Center        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐  │
│  │ CARE Backend     │  │ CARE Frontend   │  │ Postgres  │  │
│  │ :9002            │  │ :4002           │  │ :5432     │  │
│  │ + MedGemma       │  │                 │  │           │  │
│  └────────┬────────┘  └─────────────────┘  └───────────┘  │
│           │                                               │
│  Records: devaganesh-reports-hospital-2/                  │
│           (CT/X-ray months 3-8, Baseline X-ray)           │
└───────────────────────────────────────────────────────────┘
```

---

## 1. Prerequisites

You need two separate machines (System 1 and System 2). Both require:
- Docker and Docker Compose installed.
- At least 4GB RAM (and high swap space recommended for the MedGemma model and frontend builds).
- Port 4001 and 9001 available on System 1.
- Port 4002 and 9002 available on System 2.

## 2. Deploy Hospital A (On System 1)

1. Clone the repository on System 1.
2. Navigate to the `hospital-a` directory:
   ```bash
   cd hospital-a/
   ```
3. The Docker setup is optimized to use your swap space to avoid RAM constraints during the mock operations. Start the services:
   ```bash
   docker compose up -d
   ```
4. Verify the deployment:
   - Frontend: `http://localhost:4001`
   - Backend Health: `http://localhost:9001/api/health`
5. **Login Credentials:**
   - Admin: `admin` / `admin`
   - Doctor: `doctor_a` / `doctor_a`

## 3. Deploy Hospital B (On System 2)

1. Clone the repository on System 2.
2. Navigate to the `hospital-b` directory:
   ```bash
   cd hospital-b/
   ```
3. Start the services:
   ```bash
   docker compose up -d
   ```
4. Verify the deployment:
   - Frontend: `http://localhost:4002`
   - Backend Health: `http://localhost:9002/api/health`
5. **Login Credentials:**
   - Admin: `admin` / `admin`
   - Doctor: `doctor_b` / `doctor_b`

## 4. The UHI Switch Server (Cloud VPS)

The UHI Switch acts as the central broker. It is already deployed on a VPS and is accessible at `https://uhi-switch-production.up.railway.app/`. 
The switch actively monitors the health of the connected hospital backends. If a connection is lost, it triggers a mock notification to the administrator.

## 5. Mock Demonstration Flow

To reproduce the hackathon scenario, follow these steps:

1. **Context:** Patient Devaganesh S (ABHA ID: `91-1234-5678-9012`) has records scattered across two hospitals.
2. **The Goal:** Analyze the medical reports from **Month 2 to Month 8**.
3. **Trigger the Request:** 
   - A doctor initiates a request within the Hospital B EMR to fetch longitudinal data for the patient.
4. **Patient Consent (HealthWallet App):**
   - The request hits the UHI Switch, which routes a notification to the patient's mobile application.
   - Using the Flutter app (`CareConnect/`), the patient reviews the request (Scope: Diagnostic Reports, Observations) and grants consent.
5. **Data Retrieval:**
   - With consent granted, the UHI Switch provides Hospital B with the necessary decryption keys and secure routing paths to pull the relevant FHIR bundles directly from Hospital A.
6. **MedGemma Analysis:**
   - The data from Month 2-8 flows into Hospital B's EMR.
   - The doctor opens the **MedGemma Dashboard** within the EMR.
   - The MedGemma model analyzes the compiled reports, evaluating the progression of the patient's condition across those months.
   - It outputs a constructive summary, highlighting trends in BP, BMI, and lipid panels (this heavy analysis is mocked to function efficiently within the demo's RAM constraints).

This demonstrates the complete lifecycle of secure, consent-driven data ingestion and AI analysis in a federated healthcare network.