"""
FHIR R5 bundle generation utilities.
Builds FHIR R5-compliant Bundle resources from CARE EMR data.
"""

import uuid
from datetime import datetime


def create_fhir_bundle(patient_data, resource_entries=None, bundle_type="searchset"):
    """
    Create a FHIR R5 Bundle from patient data and resource entries.

    Args:
        patient_data: dict with patient info (name, abha_id, dob, gender)
        resource_entries: list of FHIR resource dicts to include
        bundle_type: one of 'searchset', 'document', 'collection'

    Returns:
        dict representing a FHIR R5 Bundle
    """
    entries = []

    # Patient resource
    patient_resource = {
        "fullUrl": f"urn:uuid:{uuid.uuid4()}",
        "resource": {
            "resourceType": "Patient",
            "id": patient_data.get("abha_id", str(uuid.uuid4())),
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"],
            },
            "identifier": [
                {
                    "system": "https://healthid.ndhm.gov.in",
                    "value": patient_data.get("abha_id", ""),
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical Record Number",
                            }
                        ]
                    },
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": patient_data.get("name", "Unknown Patient"),
                    "family": patient_data.get("family_name", ""),
                    "given": [patient_data.get("given_name", "")],
                }
            ],
            "gender": patient_data.get("gender", "unknown"),
            "birthDate": patient_data.get("dob", ""),
        },
    }
    entries.append(patient_resource)

    # Add resource entries
    if resource_entries:
        for entry in resource_entries:
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                    "resource": entry,
                }
            )

    bundle = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "meta": {
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
        },
        "type": bundle_type,
        "total": len(entries),
        "entry": entries,
    }

    return bundle


def create_observation(code, value, unit, status="final", effective_date=None):
    """Create a FHIR R5 Observation resource."""
    return {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "status": status,
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": code,
                    "display": code,
                }
            ]
        },
        "valueQuantity": {
            "value": value,
            "unit": unit,
            "system": "http://unitsofmeasure.org",
        },
        "effectiveDateTime": (effective_date or datetime.utcnow()).isoformat() + "Z",
    }


def create_diagnostic_report(title, conclusion, observations=None, status="final"):
    """Create a FHIR R5 DiagnosticReport resource."""
    report = {
        "resourceType": "DiagnosticReport",
        "id": str(uuid.uuid4()),
        "status": status,
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": title,
                }
            ]
        },
        "conclusion": conclusion,
        "effectiveDateTime": datetime.utcnow().isoformat() + "Z",
    }

    if observations:
        report["result"] = [
            {"reference": f"Observation/{obs['id']}"} for obs in observations
        ]

    return report


def create_condition(code, display, clinical_status="active"):
    """Create a FHIR R5 Condition resource."""
    return {
        "resourceType": "Condition",
        "id": str(uuid.uuid4()),
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": clinical_status,
                }
            ]
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": code,
                    "display": display,
                }
            ]
        },
        "recordedDate": datetime.utcnow().isoformat() + "Z",
    }


def create_medication_request(medication_name, dosage, frequency, status="active"):
    """Create a FHIR R5 MedicationRequest resource."""
    return {
        "resourceType": "MedicationRequest",
        "id": str(uuid.uuid4()),
        "status": status,
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "display": medication_name,
                }
            ],
            "text": medication_name,
        },
        "dosageInstruction": [
            {
                "text": f"{dosage} {frequency}",
                "timing": {
                    "code": {
                        "text": frequency,
                    }
                },
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": dosage,
                            "unit": "mg",
                        }
                    }
                ],
            }
        ],
        "authoredOn": datetime.utcnow().isoformat() + "Z",
    }


def create_sample_bundle(abha_id, patient_name="Demo Patient"):
    """
    Create a sample FHIR R5 bundle with realistic demo data.
    Used for hackathon demonstrations.
    """
    observations = [
        create_observation("4548-4", 8.2, "%"),       # HbA1c
        create_observation("2339-0", 165, "mg/dL"),    # Fasting glucose
        create_observation("2089-1", 142, "mg/dL"),    # LDL
        create_observation("8480-6", 130, "mmHg"),     # Systolic BP
        create_observation("8462-4", 82, "mmHg"),      # Diastolic BP
        create_observation("718-7", 10.8, "g/dL"),     # Hemoglobin
    ]

    diagnostic_report = create_diagnostic_report(
        title="Comprehensive Metabolic Panel",
        conclusion="Elevated HbA1c and fasting glucose indicate suboptimal glycemic control. LDL above target.",
        observations=observations,
    )

    conditions = [
        create_condition("44054006", "Type 2 Diabetes Mellitus"),
        create_condition("55822004", "Hyperlipidemia"),
    ]

    medications = [
        create_medication_request("Metformin", 500, "twice daily"),
        create_medication_request("Atorvastatin", 20, "once daily"),
        create_medication_request("Amlodipine", 5, "once daily"),
    ]

    all_resources = observations + [diagnostic_report] + conditions + medications

    return create_fhir_bundle(
        patient_data={
            "abha_id": abha_id,
            "name": patient_name,
            "given_name": patient_name.split()[0] if " " in patient_name else patient_name,
            "family_name": patient_name.split()[-1] if " " in patient_name else "",
            "gender": "female",
            "dob": "1990-03-15",
        },
        resource_entries=all_resources,
        bundle_type="searchset",
    )


def generate_devaganesh_bundle():
    """
    Generate a FHIR R5 Bundle with Devaganesh S's real clinical records.
    Used for hackathon demo to show realistic patient data flow.
    """
    observations = [
        # LFT
        create_observation("1742-6", 92, "U/L"),       # ALT (SGPT)
        create_observation("1920-8", 78, "U/L"),       # AST (SGOT)
        create_observation("2324-2", 68, "U/L"),       # GGT
        create_observation("6768-6", 85, "U/L"),       # ALP
        create_observation("1975-2", 0.8, "mg/dL"),    # Total Bilirubin
        create_observation("1751-7", 4.2, "g/dL"),     # Albumin
        # Metabolic
        create_observation("4548-4", 6.1, "%"),        # HbA1c
        create_observation("2339-0", 118, "mg/dL"),    # FBS
        create_observation("2345-7", 156, "mg/dL"),    # PPBS
        # Lipid Panel
        create_observation("2093-3", 228, "mg/dL"),    # Total Cholesterol
        create_observation("2089-1", 148, "mg/dL"),    # LDL
        create_observation("2085-9", 38, "mg/dL"),     # HDL
        create_observation("2571-8", 210, "mg/dL"),    # Triglycerides
        # CBC
        create_observation("718-7", 12.8, "g/dL"),     # Hemoglobin
        create_observation("6690-2", 7400, "/µL"),     # WBC
        create_observation("777-3", 245000, "/µL"),    # Platelets
        # RFT
        create_observation("2160-0", 0.9, "mg/dL"),   # Creatinine
        create_observation("3094-0", 14, "mg/dL"),     # BUN
        # Vitals
        create_observation("8480-6", 128, "mmHg"),     # Systolic BP
        create_observation("8462-4", 84, "mmHg"),      # Diastolic BP
        create_observation("8867-4", 76, "/min"),      # Heart Rate
        create_observation("2710-2", 98, "%"),         # SpO2
        create_observation("29463-7", 80.5, "kg"),     # Body Weight
        create_observation("8302-2", 175, "cm"),       # Body Height
        create_observation("39156-5", 26.3, "kg/m2"),  # BMI
    ]

    # Diagnostic Reports
    lft_report = create_diagnostic_report(
        title="Liver Function Tests",
        conclusion=(
            "Elevated ALT (92 U/L) and AST (78 U/L) with elevated GGT (68 U/L). "
            "Bilirubin and Albumin within normal limits. Findings consistent with "
            "Non-Alcoholic Fatty Liver Disease. Recommend ultrasound abdomen."
        ),
        observations=observations[:6],
    )

    metabolic_report = create_diagnostic_report(
        title="Metabolic Panel",
        conclusion=(
            "HbA1c 6.1% indicates pre-diabetic state (IFG + IGT). FBS 118 mg/dL "
            "and PPBS 156 mg/dL both elevated. Recommend lifestyle modification "
            "and Metformin continuation."
        ),
        observations=observations[6:9],
    )

    lipid_report = create_diagnostic_report(
        title="Lipid Panel",
        conclusion=(
            "Atherogenic dyslipidemia: elevated LDL 148 mg/dL, Total Cholesterol "
            "228 mg/dL, Triglycerides 210 mg/dL. Low HDL 38 mg/dL. High cardiovascular "
            "risk. Consider statin dose uptitration."
        ),
        observations=observations[9:13],
    )

    usg_report = create_diagnostic_report(
        title="Ultrasound Abdomen",
        conclusion=(
            "Grade II hepatic steatosis (fatty liver). No focal lesion detected. "
            "Normal CBD. Impression: Non-Alcoholic Fatty Liver Disease (NAFLD)."
        ),
    )

    conditions = [
        create_condition("R73.03", "Pre-Diabetes (Impaired Fasting Glucose + Impaired Glucose Tolerance)"),
        create_condition("K76.0", "Non-Alcoholic Fatty Liver Disease (NAFLD)"),
        create_condition("E78.5", "Dyslipidemia (Mixed Hyperlipidemia)"),
    ]

    medications = [
        create_medication_request("Metformin", 500, "twice daily (BD)"),
        create_medication_request("Atorvastatin", 10, "once daily at night"),
        create_medication_request("Pantoprazole", 40, "once daily before breakfast"),
        create_medication_request("Ursodeoxycholic Acid (UDCA)", 300, "twice daily (BD)"),
        create_medication_request("Vitamin E", 400, "once daily"),
    ]

    # AllergyIntolerance
    allergy = {
        "resourceType": "AllergyIntolerance",
        "id": str(uuid.uuid4()),
        "clinicalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
        },
        "verificationStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", "code": "confirmed"}]
        },
        "type": "allergy",
        "category": ["medication"],
        "criticality": "high",
        "code": {
            "coding": [{"system": "http://snomed.info/sct", "code": "387406002", "display": "Sulfonamide"}],
            "text": "Sulfonamides",
        },
        "reaction": [{"manifestation": [{"concept": {"text": "Skin rash, urticaria"}}], "severity": "moderate"}],
    }

    all_resources = (
        observations
        + [lft_report, metabolic_report, lipid_report, usg_report]
        + conditions
        + medications
        + [allergy]
    )

    return create_fhir_bundle(
        patient_data={
            "abha_id": "91-1234-5678-9012",
            "name": "Devaganesh S",
            "given_name": "Devaganesh",
            "family_name": "S",
            "gender": "male",
            "dob": "1997-06-15",
        },
        resource_entries=all_resources,
        bundle_type="searchset",
    )


def filter_bundle_by_scope(bundle, scope, exclude=None):
    """
    Filter a FHIR bundle to only include resources matching the consent scope.
    Removes any resource types in the exclude list.

    Args:
        bundle: FHIR Bundle dict
        scope: list of allowed resource types, e.g. ["DiagnosticReport", "Observation"]
        exclude: list of excluded resource types, e.g. ["MentalHealthRecord"]

    Returns:
        Filtered bundle
    """
    if not scope and not exclude:
        return bundle

    exclude = exclude or []
    filtered_entries = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType", "")

        # Patient resource is always included
        if resource_type == "Patient":
            filtered_entries.append(entry)
            continue

        # Check scope (if specified, only include matching types)
        if scope and resource_type not in scope:
            continue

        # Check excludes
        if resource_type in exclude:
            continue

        filtered_entries.append(entry)

    bundle["entry"] = filtered_entries
    bundle["total"] = len(filtered_entries)
    return bundle

