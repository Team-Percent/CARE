"""
Patient Data for Hospital A — CityCare Multispeciality Hospital

Devaganesh S — 24M, Patient ID: DG-2026-001
Primary Diagnosis: Hypertension with Mild Obesity
Treatment: Lifestyle-based management (10 months)
Records Here: Months 1-10 progress reports + CT/X-ray months 1-2

Data extracted from actual clinical reports in devaganesh-reports-hospital-1/
"""

HOSPITAL_A_ID = "HOSP-CITYCARE-A"
HOSPITAL_A_NAME = "CityCare Multispeciality Hospital"

DEVAGANESH_PATIENT = {
    "patient_id": "DG-2026-001",
    "abha_id": "91-1234-5678-9012",
    "name": "Devaganesh S",
    "age": 24,
    "gender": "Male",
    "blood_group": "O+",
    "referring_physician": "Dr. S. Kumar (Internal Medicine)",
    "primary_diagnosis": "Hypertension with Mild Obesity",
    "treatment_started": "2026-01-01",
    "treatment_type": "Lifestyle-Based Management",
}

# ─── 10-Month Progress Data ───────────────────────

MONTHLY_PROGRESS = [
    {
        "month": 1,
        "bp": "142/90",
        "weight_kg": 89,
        "bmi": 28.5,
        "resting_hr": 88,
        "total_cholesterol": None,
        "triglycerides": None,
        "hdl": None,
        "medication": "Amlodipine 5mg, DASH diet initiated",
        "exercise": "30 mins brisk walking",
        "assessment": "Initial response to lifestyle modifications. Blood pressure showing downward trend. Patient compliant with dietary recommendations.",
    },
    {
        "month": 2,
        "bp": "134/85",
        "weight_kg": 85,
        "bmi": 26.8,
        "resting_hr": 76,
        "total_cholesterol": None,
        "triglycerides": None,
        "hdl": None,
        "medication": "Amlodipine 5mg continued",
        "exercise": "45 mins daily (brisk walking + light gym)",
        "assessment": "Patient demonstrates continued improvement in blood pressure control and significant weight reduction. Cardiovascular endurance has improved and resting heart rate has normalized.",
    },
    {
        "month": 3,
        "bp": "124/80",
        "weight_kg": 80,
        "bmi": 25.5,
        "resting_hr": 72,
        "total_cholesterol": None,
        "triglycerides": None,
        "hdl": None,
        "medication": "Amlodipine dosage reduced",
        "exercise": "60 mins daily",
        "assessment": "Patient shows excellent improvement in cardiovascular parameters. Blood pressure has reached near-normal levels. Significant weight reduction achieved. Medication dosage reduced.",
    },
    {
        "month": 4,
        "bp": "120/78",
        "weight_kg": 77,
        "bmi": 24.5,
        "resting_hr": 70,
        "total_cholesterol": None,
        "triglycerides": None,
        "hdl": None,
        "medication": "Amlodipine DISCONTINUED – monitoring only",
        "exercise": "60 mins daily (Cardio + Strength)",
        "assessment": "Patient has achieved normal blood pressure levels and reached healthy BMI range. Medication discontinued. Stress management and sleep regulation added.",
    },
    {
        "month": 5,
        "bp": "118/76",
        "weight_kg": 75,
        "bmi": 23.8,
        "resting_hr": 68,
        "total_cholesterol": 178,
        "triglycerides": None,
        "hdl": None,
        "medication": "No antihypertensives – monitoring only",
        "exercise": "90 mins daily (Cardio + Strength)",
        "assessment": "Patient demonstrates sustained normal blood pressure without pharmacological support. Cholesterol levels have improved significantly. Weight reduction and cardiovascular fitness excellent.",
    },
    {
        "month": 6,
        "bp": "116/74",
        "weight_kg": 74,
        "bmi": 23.4,
        "resting_hr": 66,
        "total_cholesterol": 170,
        "triglycerides": 135,
        "hdl": None,
        "medication": "No medication – lifestyle management only",
        "exercise": "90 mins daily",
        "assessment": "Patient maintains stable normal blood pressure without medication. Lipid profile shows marked improvement. Diagnosis updated: Hypertension (Resolved) – Lifestyle Managed.",
    },
    {
        "month": 7,
        "bp": "114/72",
        "weight_kg": 73,
        "bmi": 23.0,
        "resting_hr": 64,
        "total_cholesterol": 165,
        "triglycerides": 120,
        "hdl": 55,
        "medication": "No medication",
        "exercise": "90 mins daily",
        "assessment": "Patient maintains optimal blood pressure and lipid profile without medication. Cardiovascular fitness excellent. Diagnosis: Hypertension – Resolved (Lifestyle Maintained).",
    },
    {
        "month": 8,
        "bp": "112/70",
        "weight_kg": 72,
        "bmi": 22.7,
        "resting_hr": 62,
        "total_cholesterol": 160,
        "triglycerides": 110,
        "hdl": 58,
        "medication": "No medication",
        "exercise": "90 mins daily",
        "assessment": "Hypertension – Fully Controlled (Lifestyle Based). All parameters within optimal range.",
    },
    {
        "month": 9,
        "bp": "110/70",
        "weight_kg": 71,
        "bmi": 22.4,
        "resting_hr": 60,
        "total_cholesterol": 155,
        "triglycerides": 105,
        "hdl": 60,
        "medication": "No medication",
        "exercise": "90 mins daily",
        "assessment": "Hypertension – Resolved (Preventive Phase). All parameters optimal. Quarterly monitoring recommended.",
    },
    {
        "month": 10,
        "bp": "108/68",
        "weight_kg": 70,
        "bmi": 22.0,
        "resting_hr": 58,
        "total_cholesterol": 150,
        "triglycerides": 95,
        "hdl": 62,
        "medication": "No medication",
        "exercise": "90 mins daily",
        "assessment": "FINAL: Patient has achieved complete normalization of blood pressure and lipid profile without pharmacological therapy. Body composition optimized with significant fat reduction. Cardiovascular risk reduced from high-risk to low.",
    },
]

# ─── Imaging Reports (Hospital A has months 1-2) ───────────────────────

IMAGING_REPORTS_HOSPITAL_A = [
    {
        "month": 1,
        "type": "chest_xray",
        "technique": "PA view chest radiograph in full inspiration",
        "findings": "Lung fields clear bilaterally. No focal consolidation or infiltrates. Cardiac silhouette within normal limits. Costophrenic angles clear. No pleural effusion or pneumothorax. Bony thoracic cage normal.",
        "impression": "Normal chest radiograph. No radiographic evidence of cardiomegaly or pulmonary pathology.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 1,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen and renal arteries with multiplanar reconstructions",
        "findings": "Kidneys normal in size, shape, and position. No renal artery stenosis. Adrenal glands normal, no mass lesions. No abdominal aortic abnormalities. No secondary structural causes of hypertension.",
        "impression": "Normal CT abdomen. No radiological evidence of secondary hypertension. Supports primary (essential) hypertension diagnosis.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 2,
        "type": "chest_xray",
        "technique": "PA view chest radiograph",
        "findings": "Lung fields clear bilaterally. Cardiac silhouette stable within normal limits. No pulmonary vascular congestion. Costophrenic angles sharp.",
        "impression": "Stable chest radiograph. No interval changes compared to baseline.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 2,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen follow-up",
        "findings": "Kidneys normal. Renal arteries patent. No new adrenal or vascular findings. No interval changes.",
        "impression": "Stable CT findings. No progression of any structural abnormality.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
]

# ─── Baseline FHIR values ───────────────────────

BASELINE_VITALS = {
    "blood_pressure_systolic": 150,
    "blood_pressure_diastolic": 95,
    "weight_kg": 92,
    "height_cm": 176,
    "bmi": 29.5,
    "resting_heart_rate": 92,
    "total_cholesterol": 220,
    "triglycerides": 190,
    "hdl": 38,
}

FINAL_VITALS = {
    "blood_pressure_systolic": 108,
    "blood_pressure_diastolic": 68,
    "weight_kg": 70,
    "height_cm": 176,
    "bmi": 22.0,
    "resting_heart_rate": 58,
    "total_cholesterol": 150,
    "triglycerides": 95,
    "hdl": 62,
}
