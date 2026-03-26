"""
Real MedGemma analysis engine via local Ollama server.

This replaces mock_medgemma when MEDGEMMA_MOCK_MODE=False.
Connects to a local Ollama instance running the CareAnalyzer model,
keeping all patient data on-premise — no cloud egress.
"""

import json
import logging
import time
import uuid

import requests

from care_medgemma.settings import plugin_settings

logger = logging.getLogger(__name__)

# ─── Analysis Presets (from analyzer.py) ──────────────────────────────────

PRESETS = {
    "comprehensive": """
Analyze all provided patient reports and images to determine the underlying conditions. Provide:
- CLINICAL IMPRESSION: Deduce the primary and secondary diagnoses and their current stages or severity.
- ICD-11 MAPPING: Exact codes for the deduced conditions.
- COMPREHENSIVE CARE PLAN: Required interventions, pharmacological needs, and specialist referrals.
- NUTRITIONAL PROTOCOL: Clinically tailored diet constraints.
- ACTIONABLE PATIENT DIRECTIVES: Immediate next steps and lifestyle modifications.
""",
    "summary": """
Read the provided patient reports and images to provide a fast, high-level clinical overview:
- PATIENT PROFILE: Age, sex, and primary reason for historical visits.
- ACTIVE ISSUES: A bulleted list of the major ongoing medical problems.
- CURRENT MEDICATIONS: Extracted list of known active prescriptions.
- RECENT CHANGES: Note any recent deteriorations or improvements in their health.
""",
    "critical": """
Scan all provided patient documents and images strictly for immediate threats and provide:
- RED FLAGS: Highlight any critical lab values, severe symptoms, image abnormalities, or disease progressions that require urgent intervention.
- CONTRAINDICATIONS: List any known drug allergies or dangerous drug interactions based on their history.
- EMERGENCY ACTION PLAN: What must be done for this patient within the next 24 to 48 hours.
""",
    "timeline": """
Extract a structured chronological timeline of the patient's medical history based on the provided documents and images.
Format the output strictly by Date/Year, listing the major symptoms, diagnoses, surgeries, or treatments that occurred at that time. Do not invent dates; use only what is in the text.
""",
    # Standard analysis types — direct pass-through prompts
    "report_summary": """
Analyze the provided patient data and lab reports. Provide a structured clinical summary including:
- Key findings with status (NORMAL/HIGH/LOW) and reference ranges
- Clinical flags that need attention
- Suggested follow-up questions for the treating physician
- Overall confidence assessment
""",
    "trend_analysis": """
Analyze the longitudinal patient data provided and identify:
- Parameters that are trending in a concerning direction
- Data points over time for each trending parameter
- Overall assessment of disease progression or improvement
- Suggested clinical interventions based on trends
""",
    "ddi_check": """
Review the patient's current medication list and check for:
- Drug-drug interactions with severity ratings (MILD/MODERATE/SEVERE)
- Known allergy contraindications
- Safe combination confirmations
- Alternative medication suggestions where interactions exist
""",
    "differential_diagnosis": """
Based on the presenting symptoms and clinical data provided:
- List differential diagnoses ordered by probability (HIGH/MODERATE/LOW)
- Supporting evidence for each differential
- Recommended diagnostic tests to confirm or rule out each condition
""",
    "soap_autofill": """
Generate a complete SOAP note from the provided clinical encounter data:
- Subjective: Chief complaint, history of present illness, review of systems
- Objective: Vitals, physical examination findings, lab results
- Assessment: Numbered problem list with clinical reasoning
- Plan: Specific interventions, medications, follow-up schedule
""",
}


def _format_patient_data(input_data):
    """Format input_data dict into a readable clinical text block."""
    if isinstance(input_data, str):
        return input_data

    if not isinstance(input_data, dict):
        return json.dumps(input_data, indent=2)

    sections = []

    # Patient demographics
    if "patient" in input_data:
        p = input_data["patient"]
        sections.append(f"Patient: {p.get('name', 'Unknown')}, "
                       f"Age: {p.get('age', 'N/A')}, "
                       f"Gender: {p.get('gender', 'N/A')}")

    # Vitals
    if "vitals" in input_data:
        vitals = input_data["vitals"]
        v_str = ", ".join(f"{k}: {v}" for k, v in vitals.items())
        sections.append(f"Vitals: {v_str}")

    # Lab reports
    if "lab_reports" in input_data:
        sections.append("Lab Reports:")
        for category, tests in input_data["lab_reports"].items():
            if isinstance(tests, dict):
                if "value" in tests:
                    sections.append(f"  {category}: {tests['value']} "
                                  f"({tests.get('status', '')}) "
                                  f"[ref: {tests.get('reference', 'N/A')}]")
                else:
                    for test_name, test_data in tests.items():
                        if isinstance(test_data, dict) and "value" in test_data:
                            sections.append(
                                f"  {test_name}: {test_data['value']} "
                                f"({test_data.get('status', '')}) "
                                f"[ref: {test_data.get('reference', 'N/A')}]"
                            )
                        else:
                            sections.append(f"  {test_name}: {test_data}")

    # Conditions
    if "conditions" in input_data:
        sections.append("Active Conditions:")
        for c in input_data["conditions"]:
            sections.append(f"  - {c.get('name', '')} "
                          f"(ICD: {c.get('icd10', 'N/A')}, "
                          f"onset: {c.get('onset', 'N/A')})")

    # Medications
    if "medications" in input_data:
        sections.append("Current Medications:")
        for m in input_data["medications"]:
            sections.append(f"  - {m.get('name', '')} {m.get('dose', '')} "
                          f"— {m.get('reason', '')}")

    # Allergies
    if "allergies" in input_data:
        sections.append("Allergies:")
        for a in input_data["allergies"]:
            sections.append(f"  - {a.get('substance', '')}: "
                          f"{a.get('reaction', '')} "
                          f"(Severity: {a.get('severity', 'N/A')})")

    # If nothing was extracted, dump the whole dict
    if not sections:
        return json.dumps(input_data, indent=2, default=str)

    return "\n".join(sections)


def _parse_ai_response(raw_text, analysis_type):
    """
    Parse the raw AI text response into structured format.
    Returns a dict matching the mock_medgemma response schema.
    """
    result = {
        "summary": raw_text[:2000] if len(raw_text) > 2000 else raw_text,
        "flags": [],
        "suggested_questions": [],
    }

    # Try to extract structured sections from the response
    lines = raw_text.strip().split("\n")
    current_section = None
    findings = []

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        line_upper = line_stripped.upper()

        # Detect section headers
        if any(kw in line_upper for kw in ["RED FLAG", "CRITICAL", "ALERT", "WARNING"]):
            current_section = "flags"
        elif any(kw in line_upper for kw in ["QUESTION", "FOLLOW-UP", "CONSIDER"]):
            current_section = "questions"
        elif any(kw in line_upper for kw in ["FINDING", "RESULT", "VALUE"]):
            current_section = "findings"

        # Collect items
        if line_stripped.startswith(("-", "•", "*", "→")):
            item = line_stripped.lstrip("-•*→ ").strip()
            if current_section == "flags":
                flag = item.upper().replace(" ", "_")[:40]
                result["flags"].append(flag)
            elif current_section == "questions":
                result["suggested_questions"].append(item)
            elif current_section == "findings":
                findings.append(item)

    if findings:
        result["key_findings"] = [
            {"parameter": f, "value": "", "status": "REVIEW", "reference": ""}
            for f in findings[:10]
        ]

    # Add SOAP structure for soap_autofill type
    if analysis_type == "soap_autofill":
        soap = {"subjective": "", "objective": "", "assessment": "", "plan": ""}
        current_soap = None
        for line in lines:
            line_upper = line.strip().upper()
            if "SUBJECTIVE" in line_upper or "S:" in line_upper:
                current_soap = "subjective"
                continue
            elif "OBJECTIVE" in line_upper or "O:" in line_upper:
                current_soap = "objective"
                continue
            elif "ASSESSMENT" in line_upper or "A:" in line_upper:
                current_soap = "assessment"
                continue
            elif "PLAN" in line_upper or "P:" in line_upper:
                current_soap = "plan"
                continue
            if current_soap and line.strip():
                soap[current_soap] += line.strip() + "\n"

        if any(v.strip() for v in soap.values()):
            result["soap"] = {k: v.strip() for k, v in soap.items()}

    # Add trend structure for trend_analysis type
    if analysis_type == "trend_analysis":
        result["trends"] = []

    return result


def analyze(analysis_type, input_data, preset=None, patient_files=None):
    """
    Run real MedGemma analysis via local Ollama server.

    Args:
        analysis_type: One of the AnalysisType choices
        input_data: Dict of patient clinical data
        preset: Optional preset override (comprehensive, summary, critical, timeline)
        patient_files: Optional list of dicts from MinIO file pull:
            [{filename, mime_type, text_content, is_image, base64_data}]

    Returns:
        Dict with structured analysis results (same schema as mock_medgemma)
    """
    start_time = time.time()
    patient_files = patient_files or []

    # Determine which prompt to use
    prompt_key = preset or analysis_type
    system_prompt = PRESETS.get(prompt_key, PRESETS.get("report_summary", ""))

    # Format patient data
    patient_text = _format_patient_data(input_data)

    # Build patient info from enriched input_data
    patient_info = input_data.get("patient_info", {})
    if patient_info:
        patient_text = (
            f"Patient: {patient_info.get('name', 'Unknown')}, "
            f"ABHA: {patient_info.get('abha_id', 'N/A')}, "
            f"Gender: {patient_info.get('gender', 'N/A')}, "
            f"DOB: {patient_info.get('date_of_birth', 'N/A')}, "
            f"Blood Group: {patient_info.get('blood_group', 'N/A')}\n\n"
            + patient_text
        )

    # Append all extracted file text contents
    if patient_files:
        file_texts = []
        for i, pf in enumerate(patient_files):
            if pf.get("text_content"):
                file_texts.append(
                    f"--- FILE {i+1}: {pf['filename']} ({pf['mime_type']}) ---\n"
                    f"{pf['text_content']}\n"
                    f"--- END FILE {i+1} ---\n"
                )
        if file_texts:
            patient_text += (
                f"\n\n=== PATIENT FILES ({len(file_texts)} documents) ===\n"
                + "\n".join(file_texts)
            )

    # Build message
    user_message = f"{system_prompt}\n\nPatient Data:\n{patient_text}"
    
    # Append the trigger command for the model to output structured format
    user_message += "\n\ncareanalyze"

    # Build Ollama request
    ollama_host = getattr(
        plugin_settings, "MEDGEMMA_OLLAMA_HOST",
        "http://10.42.0.1:11434/api/chat"
    )
    ollama_model = getattr(
        plugin_settings, "MEDGEMMA_OLLAMA_MODEL",
        "CareAnalyzer"
    )
    request_timeout = getattr(
        plugin_settings, "MEDGEMMA_REQUEST_TIMEOUT",
        120
    )

    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "stream": False,
    }

    # Collect images: from input_data + from patient files
    images = input_data.get("images", []) if isinstance(input_data, dict) else []
    for pf in patient_files:
        if pf.get("is_image") and pf.get("base64_data"):
            images.append(pf["base64_data"])
    if images:
        payload["messages"][0]["images"] = images

    try:
        logger.info(
            "care_medgemma: Sending %s analysis to Ollama at %s "
            "(model: %s, files: %d, images: %d)",
            analysis_type, ollama_host, ollama_model,
            len(patient_files), len(images)
        )

        response = requests.post(
            ollama_host,
            json=payload,
            timeout=request_timeout,
        )
        response.raise_for_status()

        response_data = response.json()
        raw_text = response_data.get("message", {}).get("content", "")

        if not raw_text:
            raise ValueError("Empty response from Ollama")

        # Parse into structured format
        result = _parse_ai_response(raw_text, analysis_type)

    except requests.exceptions.ConnectionError:
        logger.error(
            "care_medgemma: Cannot connect to Ollama at %s. "
            "Mock analysis is disabled. Returning error.", ollama_host
        )
        raise Exception(f"Failed to connect to AI engine at {ollama_host}. Please ensure the MedGemma service is running.")

    except requests.exceptions.Timeout:
        logger.error(
            "care_medgemma: Ollama request timed out after %ds", request_timeout
        )
        raise Exception(f"AI analysis timed out after {request_timeout} seconds. The data might be too large or the model is overloaded.")

    except Exception as e:
        logger.error("care_medgemma: Ollama analysis failed: %s", str(e))
        raise Exception(f"AI analysis failed: {str(e)}")

    processing_time_ms = int((time.time() - start_time) * 1000)

    return {
        **result,
        "analysis_type": analysis_type,
        "preset_used": prompt_key,
        "disclaimer": "AI-generated clinical suggestion. All outputs must be verified by a qualified physician before any clinical decision.",
        "is_mock": False,
        "model_version": f"ollama-{ollama_model}",
        "processing_time_ms": processing_time_ms,
        "request_id": str(uuid.uuid4()),
        "confidence": 0.0,
        "files_analyzed": len(patient_files),
        "images_processed": len(images),
    }

