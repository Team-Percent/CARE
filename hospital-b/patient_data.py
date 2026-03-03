"""
Patient Data for Hospital B — Metro Radiology & Diagnostics Center

Devaganesh S — 24M, Patient ID: DG-2026-001 (referred from CityCare)
Referral: Radiology follow-up for Hypertension monitoring
Records Here: CT/X-ray months 3-8 + Baseline chest X-ray image

Data extracted from actual clinical reports in devaganesh-reports-hospital-2/
"""

HOSPITAL_B_ID = "HOSP-METRO-B"
HOSPITAL_B_NAME = "Metro Radiology & Diagnostics Center"

DEVAGANESH_PATIENT = {
    "patient_id": "DG-2026-001",
    "abha_id": "91-1234-5678-9012",
    "name": "Devaganesh S",
    "age": 24,
    "gender": "Male",
    "blood_group": "O+",
    "referred_by": "Dr. S. Kumar, CityCare Multispeciality Hospital",
    "referral_reason": "Radiology follow-up — Hypertension monitoring",
}

# ─── Imaging Reports (Hospital B has months 3-8) ───────────────────────

IMAGING_REPORTS_HOSPITAL_B = [
    # Month 3
    {
        "month": 3,
        "type": "chest_xray",
        "technique": "PA view chest radiograph",
        "comparison": "Compared with Month 1 (baseline) and Month 2 chest radiographs",
        "findings": "Lung fields clear bilaterally with good inspiratory effort. Cardiac silhouette within normal limits with slight reduction in transverse cardiac diameter compared to baseline. No pulmonary vascular congestion. Costophrenic angles sharp. No focal lesions or pleural abnormalities.",
        "impression": "Interval improvement noted compared to prior studies. No evidence of cardiomegaly or pulmonary pathology. Radiographic findings consistent with improved cardiovascular condition.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 3,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen follow-up with multiplanar reconstructions",
        "comparison": "Compared with Month 1-2 studies",
        "findings": "Kidneys maintain normal size and cortical thickness. Renal arteries patent. No vascular abnormalities. Mild reduction in perirenal fat compared to baseline, consistent with weight loss.",
        "impression": "Stable findings. Incidental reduction in visceral fat consistent with clinical weight loss progress.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    # Month 4
    {
        "month": 4,
        "type": "chest_xray",
        "technique": "PA view chest radiograph",
        "comparison": "Compared with prior studies",
        "findings": "Lungs clear. Cardiac silhouette normal. Continued mild reduction in cardiothoracic ratio. No acute abnormality.",
        "impression": "Progressive improvement in cardiac metrics. Normal chest radiograph.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 4,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen",
        "comparison": "Compared with Month 3 study",
        "findings": "Normal kidneys and renal arteries. Adrenals normal. Notable reduction in abdominal visceral fat. No new findings.",
        "impression": "Stable normal study. Significant visceral fat reduction consistent with lifestyle changes.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    # Month 5
    {
        "month": 5,
        "type": "chest_xray",
        "technique": "PA view chest radiograph",
        "comparison": "Serial comparison available",
        "findings": "Clear lung fields. Normal cardiac size. Cardiothoracic ratio improved to approximately 48% (reduced from baseline 52%).",
        "impression": "Significant improvement in cardiothoracic ratio. Normal chest radiograph.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 5,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen",
        "comparison": "Compared with Month 4",
        "findings": "Normal renal and adrenal anatomy. Continued reduction in visceral adipose tissue. No vascular abnormalities.",
        "impression": "Stable normal findings with continued improvement in body composition.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    # Month 6
    {
        "month": 6,
        "type": "chest_xray",
        "technique": "PA view chest radiograph",
        "comparison": "Compared with Month 5",
        "findings": "Normal cardiac silhouette. Clear lungs. No pleural abnormalities. Cardiothoracic ratio within normal limits.",
        "impression": "Normal chest radiograph. Cardiac dimensions stable and within normal limits.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 6,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen",
        "comparison": "Compared with Month 5",
        "findings": "Normal kidneys and renal vasculature. Adrenal glands normal. No interval changes. Sustained reduction in visceral fat.",
        "impression": "Normal study. No evidence of secondary hypertension etiology.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    # Month 7
    {
        "month": 7,
        "type": "chest_xray",
        "technique": "PA view chest radiograph",
        "comparison": "Serial comparison Month 1-6",
        "findings": "Clear lung fields. Normal cardiac silhouette. Cardiothoracic ratio approximately 46%, within optimal range.",
        "impression": "Continued improvement. Cardiothoracic ratio now optimal. No pulmonary pathology.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 7,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen follow-up",
        "comparison": "Compared with prior studies",
        "findings": "Kidneys and renal arteries normal. No stenosis or calcification. Adrenal glands normal. Significant improvement in visceral fat quantification compared to baseline.",
        "impression": "Normal CT abdomen. Significant improvement in body composition markers over 7 months.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    # Month 8
    {
        "month": 8,
        "type": "chest_xray",
        "technique": "PA view chest radiograph",
        "comparison": "Compared with prior studies",
        "findings": "Normal cardiac silhouette and mediastinal structures. Clear lung fields bilaterally. No thoracic abnormalities.",
        "impression": "Normal chest radiograph. Stable excellent findings.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
    {
        "month": 8,
        "type": "ct_abdomen",
        "technique": "Contrast-enhanced CT abdomen — advanced preventive monitoring",
        "comparison": "Compared with CT scans from Month 1 through Month 7",
        "findings": "Kidneys maintain normal size, contour, and cortical thickness. Renal arteries widely patent with smooth luminal margins. No evidence of vascular stenosis, calcification, or plaque formation. Adrenal glands normal with no hyperplasia or nodular changes. Abdominal aorta and branch vessels normal. No interval structural or vascular changes.",
        "impression": "Radiologically normal CT abdomen examination. Full structural and vascular stability confirmed across 8 months of monitoring.",
        "radiologist": "Dr. R. Mehta, MD (Radiology)",
    },
]

# ─── Baseline Chest X-Ray Image Analysis ───────────────────────

BASELINE_XRAY_IMAGE = {
    "filename": "WhatsApp Image 2026-03-03 at 1.25.26 AM.jpeg",
    "month": 1,
    "type": "chest_xray_image",
    "patient": "DEVAGANESH, Male",
    "clinical_indication": "Initial evaluation for elevated blood pressure (hypertension)",
    "technique": "Single PA projection",
    "findings": (
        "A mild prominence of the cardiac silhouette, which covers slightly more than ideal thoracic width. "
        "Borderline enlargement. The cardiothoracic ratio is subtly increased at approximately 52%, upper limit of normal. "
        "The lung fields appear clear bilaterally without any signs of focal consolidation, infiltration or nodules. "
        "No indication of pulmonary edema, pleural effusion or vascular congestion. "
        "Mediastinal contours are within normal limits. Bony thoracic cage and soft tissues unremarkable."
    ),
    "impression": "Borderline cardiac enlargement, baseline study for future follow-up.",
    "ctr_baseline": 0.52,
    "ctr_month5": 0.48,
    "ctr_month7": 0.46,
}
