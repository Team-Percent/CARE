"""
Mock MedGemma AI service for hackathon demo.
Returns realistic structured JSON responses without running the actual model.
Includes hardcoded clinical data for patient Devaganesh S.
"""

import random
import time
import uuid


# ─── PATIENT: DEVAGANESH S — Hardcoded Clinical Records ───────────────
DEVAGANESH_CLINICAL_DATA = {
    "patient": {
        "name": "Devaganesh S",
        "abha_id": "91-1234-5678-9012",
        "age": 28,
        "gender": "Male",
        "blood_group": "O+",
        "bmi": 26.3,
        "height_cm": 175,
        "weight_kg": 80.5,
        "phone": "+91-9876543210",
        "address": "42, Anna Nagar, Chennai, Tamil Nadu 600040",
        "emergency_contact": "Subramanian S (Father) +91-9876543211",
    },
    "vitals": {
        "bp": "128/84 mmHg",
        "heart_rate": "76 bpm",
        "temp": "98.2°F",
        "spo2": "98%",
        "respiratory_rate": "16/min",
    },
    "lab_reports": {
        "cbc": {
            "hemoglobin": {"value": "12.8 g/dL", "status": "NORMAL", "reference": "13.0-17.0 g/dL"},
            "wbc": {"value": "7,400/µL", "status": "NORMAL", "reference": "4,000-11,000/µL"},
            "platelets": {"value": "2,45,000/µL", "status": "NORMAL", "reference": "1,50,000-4,00,000/µL"},
            "mcv": {"value": "86 fL", "status": "NORMAL", "reference": "80-100 fL"},
        },
        "lft": {
            "alt": {"value": "92 U/L", "status": "HIGH", "reference": "7-56 U/L"},
            "ast": {"value": "78 U/L", "status": "HIGH", "reference": "10-40 U/L"},
            "ggt": {"value": "68 U/L", "status": "HIGH", "reference": "9-48 U/L"},
            "alp": {"value": "85 U/L", "status": "NORMAL", "reference": "44-147 U/L"},
            "total_bilirubin": {"value": "0.8 mg/dL", "status": "NORMAL", "reference": "0.1-1.2 mg/dL"},
            "albumin": {"value": "4.2 g/dL", "status": "NORMAL", "reference": "3.5-5.5 g/dL"},
        },
        "rft": {
            "creatinine": {"value": "0.9 mg/dL", "status": "NORMAL", "reference": "0.7-1.3 mg/dL"},
            "bun": {"value": "14 mg/dL", "status": "NORMAL", "reference": "7-20 mg/dL"},
            "uric_acid": {"value": "6.2 mg/dL", "status": "NORMAL", "reference": "3.4-7.0 mg/dL"},
        },
        "metabolic": {
            "hba1c": {"value": "6.1%", "status": "HIGH", "reference": "< 5.7%"},
            "fbs": {"value": "118 mg/dL", "status": "HIGH", "reference": "70-100 mg/dL"},
            "ppbs": {"value": "156 mg/dL", "status": "HIGH", "reference": "< 140 mg/dL"},
        },
        "lipid_panel": {
            "total_cholesterol": {"value": "228 mg/dL", "status": "HIGH", "reference": "< 200 mg/dL"},
            "ldl": {"value": "148 mg/dL", "status": "HIGH", "reference": "< 100 mg/dL"},
            "hdl": {"value": "38 mg/dL", "status": "LOW", "reference": "> 40 mg/dL"},
            "triglycerides": {"value": "210 mg/dL", "status": "HIGH", "reference": "< 150 mg/dL"},
        },
        "liver_ultrasound": {
            "finding": "Grade II hepatic steatosis (fatty liver). No focal lesion. Normal CBD.",
            "impression": "Non-Alcoholic Fatty Liver Disease (NAFLD)",
        },
    },
    "conditions": [
        {"name": "Pre-Diabetes (IFG + IGT)", "icd10": "R73.03", "onset": "2025-08-15"},
        {"name": "Non-Alcoholic Fatty Liver Disease", "icd10": "K76.0", "onset": "2025-11-20"},
        {"name": "Dyslipidemia", "icd10": "E78.5", "onset": "2025-11-20"},
    ],
    "medications": [
        {"name": "Metformin 500mg", "dose": "BD (twice daily)", "reason": "Pre-diabetes"},
        {"name": "Atorvastatin 10mg", "dose": "OD at night", "reason": "Dyslipidemia"},
        {"name": "Pantoprazole 40mg", "dose": "OD before breakfast", "reason": "Gastric protection"},
        {"name": "Ursodeoxycholic Acid 300mg", "dose": "BD", "reason": "NAFLD"},
        {"name": "Vitamin E 400IU", "dose": "OD", "reason": "NAFLD antioxidant therapy"},
    ],
    "allergies": [
        {"substance": "Sulfonamides", "reaction": "Skin rash, urticaria", "severity": "MODERATE"},
    ],
}


def _devaganesh_report_summary(input_data):
    """Report summary specific to Devaganesh S's clinical records."""
    return {
        "summary": (
            "Patient Devaganesh S (28M, ABHA: 91-1234-5678-9012) presents with "
            "significantly elevated liver enzymes — ALT 92 U/L (ref <56), AST 78 U/L "
            "(ref <40), and GGT 68 U/L (ref <48) — consistent with Grade II NAFLD "
            "confirmed on ultrasound. Metabolic panel reveals pre-diabetic state with "
            "HbA1c 6.1% and FBS 118 mg/dL. Lipid profile shows atherogenic pattern: "
            "LDL 148 mg/dL, low HDL 38 mg/dL, and elevated triglycerides 210 mg/dL. "
            "Current management with Metformin, Atorvastatin, UDCA, and Vitamin E is "
            "appropriate. Recommend lifestyle modification as primary intervention."
        ),
        "flags": [
            "ELEVATED_ALT", "ELEVATED_AST", "NAFLD_GRADE_II",
            "PRE_DIABETIC_HBA1C", "HIGH_LDL", "LOW_HDL", "HIGH_TRIGLYCERIDES",
        ],
        "suggested_questions": [
            "Has Devaganesh started regular physical exercise (30 min, 5x/week)?",
            "What is his current dietary pattern — specifically refined carb and sugar intake?",
            "Has a fibroscan been considered to assess liver fibrosis staging?",
            "Is there a family history of Type 2 Diabetes or cardiovascular disease?",
            "Should Pioglitazone be considered for its NASH-specific benefits?",
        ],
        "key_findings": [
            {"parameter": "ALT (SGPT)", "value": "92 U/L", "status": "HIGH", "reference": "7-56 U/L"},
            {"parameter": "AST (SGOT)", "value": "78 U/L", "status": "HIGH", "reference": "10-40 U/L"},
            {"parameter": "GGT", "value": "68 U/L", "status": "HIGH", "reference": "9-48 U/L"},
            {"parameter": "HbA1c", "value": "6.1%", "status": "HIGH", "reference": "< 5.7%"},
            {"parameter": "Fasting Blood Sugar", "value": "118 mg/dL", "status": "HIGH", "reference": "70-100 mg/dL"},
            {"parameter": "LDL Cholesterol", "value": "148 mg/dL", "status": "HIGH", "reference": "< 100 mg/dL"},
            {"parameter": "HDL Cholesterol", "value": "38 mg/dL", "status": "LOW", "reference": "> 40 mg/dL"},
            {"parameter": "Triglycerides", "value": "210 mg/dL", "status": "HIGH", "reference": "< 150 mg/dL"},
            {"parameter": "Hemoglobin", "value": "12.8 g/dL", "status": "NORMAL", "reference": "13.0-17.0 g/dL"},
            {"parameter": "Creatinine", "value": "0.9 mg/dL", "status": "NORMAL", "reference": "0.7-1.3 mg/dL"},
        ],
        "confidence": 0.94,
    }


def _devaganesh_trend_analysis(input_data):
    """Trend analysis specific to Devaganesh S."""
    return {
        "summary": (
            "Longitudinal analysis of Devaganesh's records over the past 6 months shows "
            "progressive worsening of liver enzymes (ALT: 45→68→92 U/L) correlating with "
            "weight gain (74→77→80.5 kg). HbA1c has trended upward from 5.6% to 6.1%, "
            "crossing the pre-diabetic threshold. Lipid panel deterioration noted. "
            "Current interventions need reinforcement with lifestyle changes."
        ),
        "trends": [
            {
                "parameter": "ALT (SGPT)",
                "direction": "INCREASING",
                "severity": "CONCERNING",
                "data_points": [
                    {"date": "2025-08-15", "value": "45 U/L"},
                    {"date": "2025-11-20", "value": "68 U/L"},
                    {"date": "2026-02-28", "value": "92 U/L"},
                ],
            },
            {
                "parameter": "HbA1c",
                "direction": "INCREASING",
                "severity": "CONCERNING",
                "data_points": [
                    {"date": "2025-08-15", "value": "5.6%"},
                    {"date": "2025-11-20", "value": "5.9%"},
                    {"date": "2026-02-28", "value": "6.1%"},
                ],
            },
            {
                "parameter": "Body Weight",
                "direction": "INCREASING",
                "severity": "CONCERNING",
                "data_points": [
                    {"date": "2025-08-15", "value": "74 kg"},
                    {"date": "2025-11-20", "value": "77 kg"},
                    {"date": "2026-02-28", "value": "80.5 kg"},
                ],
            },
            {
                "parameter": "LDL Cholesterol",
                "direction": "INCREASING",
                "severity": "CONCERNING",
                "data_points": [
                    {"date": "2025-08-15", "value": "120 mg/dL"},
                    {"date": "2025-11-20", "value": "135 mg/dL"},
                    {"date": "2026-02-28", "value": "148 mg/dL"},
                ],
            },
        ],
        "flags": ["ALT_TRENDING_UP", "PREDIABETES_PROGRESSION", "WEIGHT_GAIN", "LDL_RISING"],
        "suggested_questions": [
            "Should a fibroscan be ordered to assess NAFLD progression to NASH?",
            "Is Metformin dose escalation (to 1000mg BD) warranted given HbA1c trajectory?",
            "Has the patient been referred to a dietitian?",
        ],
        "confidence": 0.91,
    }


def _devaganesh_ddi_check(input_data):
    """DDI check for Devaganesh's medication list."""
    return {
        "summary": (
            "Analysis of Devaganesh's current medications: Metformin 500mg, Atorvastatin 10mg, "
            "Pantoprazole 40mg, UDCA 300mg, Vitamin E 400IU. No severe interactions detected. "
            "Note: Pantoprazole may reduce Metformin absorption — take at different times. "
            "Allergy flag: Patient is allergic to Sulfonamides — avoid sulfonylureas if "
            "diabetes management is escalated."
        ),
        "interactions": [
            {
                "drug_a": "Pantoprazole 40mg",
                "drug_b": "Metformin 500mg",
                "severity": "MILD",
                "mechanism": "PPIs may alter gastric pH affecting metformin absorption",
                "recommendation": "Take Pantoprazole 30 min before meals; Metformin with meals",
            },
        ],
        "safe_combinations": [
            {"drug_a": "Metformin 500mg", "drug_b": "Atorvastatin 10mg", "status": "SAFE"},
            {"drug_a": "Metformin 500mg", "drug_b": "UDCA 300mg", "status": "SAFE"},
            {"drug_a": "Atorvastatin 10mg", "drug_b": "Vitamin E 400IU", "status": "SAFE"},
            {"drug_a": "UDCA 300mg", "drug_b": "Vitamin E 400IU", "status": "SAFE"},
        ],
        "allergy_alerts": [
            {
                "allergen": "Sulfonamides",
                "reaction": "Skin rash, urticaria",
                "avoid": ["Sulfonylureas (Glipizide, Glyburide)", "Sulfasalazine", "Co-trimoxazole"],
                "safe_alternatives_for_diabetes": ["DPP-4 inhibitors", "GLP-1 agonists", "SGLT2 inhibitors"],
            },
        ],
        "flags": ["SULFONAMIDE_ALLERGY_FLAG", "TIMING_ADVISORY_PPI_METFORMIN"],
        "suggested_questions": [
            "If stepping up diabetes therapy, avoid sulfonylureas — consider Empagliflozin?",
            "Is the patient taking Pantoprazole at the recommended time (empty stomach)?",
        ],
        "confidence": 0.93,
    }


def _devaganesh_soap(input_data):
    """SOAP autofill for Devaganesh S."""
    return {
        "summary": "Auto-generated SOAP note for Devaganesh S — follow-up visit for NAFLD and metabolic syndrome.",
        "soap": {
            "subjective": (
                "Devaganesh S, 28M, presents for 3-month follow-up of NAFLD and pre-diabetes. "
                "Reports mild fatigue, especially post-meals. No abdominal pain. Denies alcohol use. "
                "Diet: predominantly South Indian vegetarian with high refined carb intake (rice 3x/day). "
                "Exercise: sedentary, desk job, no regular physical activity. Sleep: 6 hours, irregular. "
                "Medications: compliant with all prescribed medications. No new complaints."
            ),
            "objective": (
                "Vitals: BP 128/84 mmHg, HR 76 bpm, Temp 98.2°F, SpO2 98%.\n"
                "Height: 175 cm, Weight: 80.5 kg, BMI: 26.3 kg/m².\n"
                "General: Alert, oriented, mild central obesity.\n"
                "Abdomen: Soft, non-tender, liver palpable 2cm below costal margin.\n"
                "CVS: S1S2 normal, no murmurs. RS: Clear.\n\n"
                "Labs (2026-02-28):\n"
                "ALT 92 U/L↑, AST 78 U/L↑, GGT 68 U/L↑, ALP 85 U/L, Bilirubin 0.8\n"
                "HbA1c 6.1%↑, FBS 118↑, PPBS 156↑\n"
                "LDL 148↑, HDL 38↓, TG 210↑, TC 228↑\n"
                "Creatinine 0.9, Hb 12.8\n"
                "USG Abdomen: Grade II hepatic steatosis, no focal lesion"
            ),
            "assessment": (
                "1. Non-Alcoholic Fatty Liver Disease (NAFLD) — Grade II steatosis, "
                "worsening ALT trend (45→68→92), needs fibrosis assessment\n"
                "2. Pre-Diabetes (IFG + IGT) — HbA1c 6.1%, progressing from 5.6% in Aug 2025\n"
                "3. Atherogenic Dyslipidemia — elevated LDL, TG; low HDL; statin dose may need uptitration\n"
                "4. Overweight — BMI 26.3, 6.5 kg weight gain in 6 months\n"
                "5. Sulfonamide allergy — documented, avoid sulfonylureas"
            ),
            "plan": (
                "1. NAFLD: Continue UDCA 300mg BD + Vitamin E 400IU OD; order Fibroscan for fibrosis staging\n"
                "2. Pre-Diabetes: Increase Metformin to 1000mg BD; add lifestyle modification Rx\n"
                "3. Dyslipidemia: Uptitrate Atorvastatin from 10mg → 20mg; recheck lipids in 6 weeks\n"
                "4. Weight Management: Target 5-7% weight loss over 6 months; refer to dietitian\n"
                "   - Reduce refined carbs (rice → brown rice/millets)\n"
                "   - Brisk walking 30 min x 5 days/week\n"
                "5. Labs in 3 months: LFT, HbA1c, lipid panel, urine microalbumin\n"
                "6. If HbA1c > 6.5% at next visit, consider adding Empagliflozin 10mg "
                "(dual benefit: glycemic + hepatic + renal)\n"
                "7. Follow-up: 6 weeks for lipid recheck + Fibroscan results"
            ),
        },
        "flags": ["NAFLD_PROGRESSION", "PREDIABETES", "ATHEROGENIC_DYSLIPIDEMIA", "SULFONAMIDE_ALLERGY"],
        "suggested_questions": [],
        "confidence": 0.95,
    }


# Devaganesh-specific handlers
DEVAGANESH_HANDLERS = {
    "report_summary": _devaganesh_report_summary,
    "trend_analysis": _devaganesh_trend_analysis,
    "ddi_check": _devaganesh_ddi_check,
    "soap_autofill": _devaganesh_soap,
}


def _mock_report_summary(input_data):
    """Generate a mock report summary analysis."""
    conditions = [
        {
            "summary": (
                "Patient presents with elevated HbA1c at 8.2%, indicating suboptimal "
                "glycemic control. Fasting blood glucose at 165 mg/dL is above the "
                "recommended range. Lipid panel shows LDL at 142 mg/dL, warranting "
                "evaluation of current statin therapy."
            ),
            "flags": ["HIGH_HBA1C", "ELEVATED_FBS", "HIGH_LDL"],
            "suggested_questions": [
                "Has the patient's diabetes medication been adjusted in the last 3 months?",
                "Is the patient adherent to dietary recommendations?",
                "When was the last ophthalmology screening?",
            ],
            "key_findings": [
                {"parameter": "HbA1c", "value": "8.2%", "status": "HIGH", "reference": "< 7.0%"},
                {"parameter": "Fasting Blood Glucose", "value": "165 mg/dL", "status": "HIGH", "reference": "70-100 mg/dL"},
                {"parameter": "LDL Cholesterol", "value": "142 mg/dL", "status": "HIGH", "reference": "< 100 mg/dL"},
                {"parameter": "Creatinine", "value": "1.0 mg/dL", "status": "NORMAL", "reference": "0.7-1.3 mg/dL"},
            ],
        },
        {
            "summary": (
                "Complete blood count reveals mild anemia with hemoglobin at 10.8 g/dL. "
                "MCV of 72 fL suggests microcytic anemia, likely iron deficiency. "
                "Platelet count and WBC within normal limits. Recommend serum ferritin "
                "and iron studies for confirmation."
            ),
            "flags": ["LOW_HEMOGLOBIN", "MICROCYTIC_ANEMIA"],
            "suggested_questions": [
                "Has the patient reported fatigue or weakness?",
                "Is there any history of GI bleeding or heavy menstruation?",
                "What is the patient's dietary iron intake?",
            ],
            "key_findings": [
                {"parameter": "Hemoglobin", "value": "10.8 g/dL", "status": "LOW", "reference": "12.0-16.0 g/dL"},
                {"parameter": "MCV", "value": "72 fL", "status": "LOW", "reference": "80-100 fL"},
                {"parameter": "WBC", "value": "7,200/µL", "status": "NORMAL", "reference": "4,000-11,000/µL"},
                {"parameter": "Platelets", "value": "250,000/µL", "status": "NORMAL", "reference": "150,000-400,000/µL"},
            ],
        },
        {
            "summary": (
                "Liver function tests show elevated ALT at 78 U/L and AST at 65 U/L, "
                "suggesting hepatocellular injury. GGT is also elevated at 95 U/L. "
                "Bilirubin and albumin remain within normal range. Recommend ultrasound "
                "abdomen and hepatitis panel."
            ),
            "flags": ["ELEVATED_ALT", "ELEVATED_AST", "ELEVATED_GGT"],
            "suggested_questions": [
                "Does the patient consume alcohol regularly?",
                "Is the patient on any hepatotoxic medications?",
                "Has the patient been screened for hepatitis B/C?",
            ],
            "key_findings": [
                {"parameter": "ALT", "value": "78 U/L", "status": "HIGH", "reference": "7-56 U/L"},
                {"parameter": "AST", "value": "65 U/L", "status": "HIGH", "reference": "10-40 U/L"},
                {"parameter": "GGT", "value": "95 U/L", "status": "HIGH", "reference": "9-48 U/L"},
                {"parameter": "Total Bilirubin", "value": "0.9 mg/dL", "status": "NORMAL", "reference": "0.1-1.2 mg/dL"},
            ],
        },
    ]

    chosen = random.choice(conditions)
    return {
        "summary": chosen["summary"],
        "flags": chosen["flags"],
        "suggested_questions": chosen["suggested_questions"],
        "key_findings": chosen["key_findings"],
        "confidence": round(random.uniform(0.78, 0.95), 2),
    }


def _mock_trend_analysis(input_data):
    """Generate a mock trend analysis."""
    return {
        "summary": (
            "Analysis of longitudinal data shows a consistent upward trend in HbA1c "
            "over the past 6 months (6.8% → 7.4% → 8.2%), suggesting progressive "
            "deterioration of glycemic control. Blood pressure readings show improved "
            "control after medication adjustment in the last visit."
        ),
        "trends": [
            {
                "parameter": "HbA1c",
                "direction": "INCREASING",
                "severity": "CONCERNING",
                "data_points": [
                    {"date": "2025-09-15", "value": "6.8%"},
                    {"date": "2025-12-10", "value": "7.4%"},
                    {"date": "2026-03-01", "value": "8.2%"},
                ],
            },
            {
                "parameter": "Systolic BP",
                "direction": "DECREASING",
                "severity": "IMPROVING",
                "data_points": [
                    {"date": "2025-09-15", "value": "155 mmHg"},
                    {"date": "2025-12-10", "value": "142 mmHg"},
                    {"date": "2026-03-01", "value": "130 mmHg"},
                ],
            },
        ],
        "flags": ["HBA1C_TRENDING_UP", "BP_IMPROVING"],
        "suggested_questions": [
            "Should the diabetes management plan be escalated?",
            "Is the patient eligible for GLP-1 receptor agonist therapy?",
        ],
        "confidence": round(random.uniform(0.80, 0.92), 2),
    }


def _mock_ddi_check(input_data):
    """Generate a mock drug-drug interaction check."""
    return {
        "summary": (
            "Potential moderate interaction detected between Metformin and "
            "Cimetidine. Cimetidine may increase metformin levels by reducing "
            "renal clearance. Consider monitoring blood glucose more frequently "
            "or substituting with an alternative H2 blocker."
        ),
        "interactions": [
            {
                "drug_a": "Metformin 500mg",
                "drug_b": "Cimetidine 400mg",
                "severity": "MODERATE",
                "mechanism": "Reduced renal tubular secretion of metformin",
                "recommendation": "Monitor blood glucose; consider ranitidine as alternative",
            },
        ],
        "safe_combinations": [
            {"drug_a": "Metformin 500mg", "drug_b": "Amlodipine 5mg", "status": "SAFE"},
            {"drug_a": "Atorvastatin 20mg", "drug_b": "Amlodipine 5mg", "status": "SAFE"},
        ],
        "flags": ["DDI_MODERATE"],
        "suggested_questions": [
            "Can the H2 blocker be changed to a PPI or alternative?",
            "Is more frequent glucose monitoring feasible for this patient?",
        ],
        "confidence": round(random.uniform(0.85, 0.95), 2),
    }


def _mock_differential_diagnosis(input_data):
    """Generate mock differential diagnosis hints."""
    return {
        "summary": (
            "Based on the presenting symptoms (persistent cough > 3 weeks, "
            "low-grade fever, night sweats, weight loss) and elevated ESR, "
            "the following differentials should be considered."
        ),
        "differentials": [
            {
                "condition": "Pulmonary Tuberculosis",
                "probability": "HIGH",
                "supporting_evidence": ["Persistent cough", "Night sweats", "Weight loss", "Elevated ESR"],
                "recommended_tests": ["Sputum AFB", "Chest X-ray", "Mantoux test", "GeneXpert"],
            },
            {
                "condition": "Community-Acquired Pneumonia",
                "probability": "MODERATE",
                "supporting_evidence": ["Persistent cough", "Low-grade fever"],
                "recommended_tests": ["Chest X-ray", "Sputum culture", "CBC"],
            },
            {
                "condition": "Lung Malignancy",
                "probability": "LOW",
                "supporting_evidence": ["Weight loss", "Persistent cough"],
                "recommended_tests": ["CT Chest", "Sputum cytology"],
            },
        ],
        "flags": ["TB_SUSPECT", "WEIGHT_LOSS"],
        "suggested_questions": [
            "Does the patient have any known TB contacts?",
            "What is the patient's smoking history?",
            "Has the patient traveled to TB-endemic areas recently?",
        ],
        "confidence": round(random.uniform(0.70, 0.88), 2),
    }


def _mock_soap_autofill(input_data):
    """Generate mock SOAP note content."""
    return {
        "summary": "Auto-generated SOAP note from clinical encounter data.",
        "soap": {
            "subjective": (
                "Patient presents with chief complaint of persistent fatigue and "
                "increased thirst for the past 2 weeks. Reports polyuria, especially "
                "nocturia (3-4 times/night). No history of fever, weight loss, or "
                "changes in appetite. Past medical history: Type 2 DM diagnosed 5 years ago."
            ),
            "objective": (
                "Vitals: BP 130/82 mmHg, HR 78 bpm, Temp 98.4°F, SpO2 98%. "
                "BMI 28.4 kg/m². General: Alert, oriented, no acute distress. "
                "CVS: S1S2 normal, no murmurs. RS: Clear bilateral air entry. "
                "Abdomen: Soft, non-tender. Extremities: No edema."
            ),
            "assessment": (
                "1. Type 2 Diabetes Mellitus — suboptimal control (HbA1c 8.2%)\n"
                "2. Dyslipidemia — LDL above target\n"
                "3. Rule out diabetic nephropathy — order urine microalbumin"
            ),
            "plan": (
                "1. Increase Metformin to 1000mg BD\n"
                "2. Add Empagliflozin 10mg OD (for glycemic + renal benefit)\n"
                "3. Continue Atorvastatin 20mg, consider dose increase\n"
                "4. Labs: HbA1c, renal panel, urine microalbumin in 3 months\n"
                "5. Dietary counseling referral\n"
                "6. Follow up in 4 weeks"
            ),
        },
        "flags": ["SUBOPTIMAL_GLYCEMIC_CONTROL"],
        "suggested_questions": [],
        "confidence": round(random.uniform(0.82, 0.93), 2),
    }


# Map analysis types to mock functions
MOCK_HANDLERS = {
    "report_summary": _mock_report_summary,
    "trend_analysis": _mock_trend_analysis,
    "ddi_check": _mock_ddi_check,
    "differential_diagnosis": _mock_differential_diagnosis,
    "soap_autofill": _mock_soap_autofill,
}


def analyze(analysis_type, input_data):
    """
    Run MedGemma analysis (mocked for hackathon demo).
    If patient_id is 'devaganesh' or input contains his ABHA ID,
    returns analysis specific to Devaganesh S's clinical records.

    Returns:
        dict with structured analysis results
    """
    start_time = time.time()

    # Check if this is for patient Devaganesh S
    patient_id = ""
    if isinstance(input_data, dict):
        patient_id = str(input_data.get("patient_id", "")).lower()
        abha_id = str(input_data.get("abha_id", ""))
        if abha_id == "91-1234-5678-9012":
            patient_id = "devaganesh"

    if patient_id == "devaganesh" and analysis_type in DEVAGANESH_HANDLERS:
        handler = DEVAGANESH_HANDLERS[analysis_type]
    else:
        handler = MOCK_HANDLERS.get(analysis_type, _mock_report_summary)

    result = handler(input_data)

    processing_time_ms = int((time.time() - start_time) * 1000) + random.randint(200, 800)

    # Extract DocumentReferences attached to the bundle
    documents_analyzed = []
    if isinstance(input_data, dict) and input_data.get("resourceType") == "Bundle":
        for entry in input_data.get("entry", []):
            res = entry.get("resource", {})
            if res.get("resourceType") == "DocumentReference":
                try:
                    documents_analyzed.append({
                        "id": res.get("id"),
                        "title": res.get("content", [{}])[0].get("attachment", {}).get("title", "Document"),
                        "url": res.get("content", [{}])[0].get("attachment", {}).get("url", "")
                    })
                except Exception:
                    pass

    # For hackathon demo: If the bundle didn't include actual entries but we know it's Devaganesh,
    # fetch them directly using his ABHA ID so the UI can display the "Source Documents Analyzed"
    bundle_abha = ""
    if isinstance(input_data, dict):
        bundle_abha = str(input_data.get("abha_id", ""))
    
    if not documents_analyzed and patient_id == "devaganesh" and bundle_abha:
        try:
            from care_medgemma.fhir_utils import get_document_references
            doc_refs = get_document_references(bundle_abha)
            for res in doc_refs:
                documents_analyzed.append({
                    "id": res.get("id"),
                    "title": res.get("content", [{}])[0].get("attachment", {}).get("title", "Document"),
                    "url": res.get("content", [{}])[0].get("attachment", {}).get("url", "")
                })
        except Exception as e:
            print("Error fetching mock documents:", e)
                    
    return {
        **result,
        "analysis_type": analysis_type,
        "disclaimer": "AI-generated suggestion. Verify clinically.",
        "is_mock": True,
        "model_version": "medgemma-mock-1.0",
        "processing_time_ms": processing_time_ms,
        "request_id": str(uuid.uuid4()),
        "documents_analyzed": documents_analyzed,
        **({"patient": DEVAGANESH_CLINICAL_DATA["patient"]} if patient_id == "devaganesh" else {}),
    }

