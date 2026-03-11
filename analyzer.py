import os
import json
import base64
import requests
import pypdf

HOST_URL = "http://172.19.127.189:11434/api/chat"
MODEL_NAME = "CareAnalyzer"
DEFAULT_REPORTS_DIR = "./patient_data"

COLOR_USER = '\033[94m'
COLOR_AI = '\033[92m'
COLOR_SYS = '\033[93m'
RESET = '\033[0m'

chat_history = []

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
"""
}

def encode_image(image_path):
    with open(image_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def read_directory(dir_path):
    reports_text = ""
    encoded_images = []
    
    if not os.path.exists(dir_path):
        return reports_text, encoded_images
        
    for filename in sorted(os.listdir(dir_path)):
        file_path = os.path.join(dir_path, filename)
        
        if filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                reports_text += f"\n--- {filename} ---\n{f.read()}"
        
        elif filename.endswith(".pdf"):
            try:
                reader = pypdf.PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                reports_text += f"\n--- {filename} ---\n{text}"
            except Exception as e:
                print(f"{COLOR_SYS}Failed to read PDF {filename}: {e}{RESET}")
                
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                encoded_images.append(encode_image(file_path))
                reports_text += f"\n--- [Attached Scan: {filename}] ---\n"
            except Exception as e:
                print(f"{COLOR_SYS}Failed to load image {filename}: {e}{RESET}")
                
    return reports_text, encoded_images

print(f"{COLOR_SYS}=== C.A.R.E. Advanced Clinical Engine ==={RESET}")
print("Commands:")
print("  /analyze <preset> [folder] - Batch process PDFs, TXTs, and Images")
print("                               Presets: comprehensive, summary, critical, timeline")
print("                               Example: /analyze critical /home/shivani/icu_data")
print("  /image <path>              - Upload a single image/scan")
print("  /pdf <path>                - Upload a single PDF document")
print("  /reset                     - Clear chat history")
print("  quit                       - Exit")
print("  (Press Ctrl+C during generation to stop the AI without quitting)\n")

while True:
    try:
        user_input = input(f"\n{COLOR_USER}Doctor: {RESET}").strip()
    except KeyboardInterrupt:
        print("\nType 'quit' to exit.")
        continue
        
    if user_input.lower() == 'quit':
        break
    if not user_input:
        continue

    if user_input.lower() == '/reset':
        chat_history = []
        print(f"{COLOR_SYS}Chat history cleared.{RESET}")
        continue
        
    images = []
    
    if user_input.startswith('/image '):
        img_path = user_input.split(' ', 1)[1]
        if os.path.isfile(img_path):
            images.append(encode_image(img_path))
            user_input = input(f"{COLOR_SYS}Image loaded. Question:\n{COLOR_USER}Doctor: {RESET}").strip()
        else:
            print(f"{COLOR_SYS}Error: Image file not found.{RESET}")
            continue

    if user_input.startswith('/pdf '):
        pdf_path = user_input.split(' ', 1)[1]
        if os.path.isfile(pdf_path) and pdf_path.endswith('.pdf'):
            try:
                reader = pypdf.PdfReader(pdf_path)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() + "\n"
                
                user_question = input(f"{COLOR_SYS}PDF loaded. Question:\n{COLOR_USER}Doctor: {RESET}").strip()
                user_input = f"Based on the following PDF text:\n\n{pdf_text}\n\nAnswer this question: {user_question}"
            except Exception as e:
                print(f"{COLOR_SYS}Error reading PDF: {e}{RESET}")
                continue
        else:
            print(f"{COLOR_SYS}Error: PDF file not found or not a .pdf extension.{RESET}")
            continue

    if user_input.startswith('/analyze '):
        parts = user_input.split(' ')
        if len(parts) < 2:
            print(f"{COLOR_SYS}Please specify a preset (e.g., /analyze comprehensive){RESET}")
            continue
            
        preset_type = parts[1].lower()
        if preset_type not in PRESETS:
            print(f"{COLOR_SYS}Unknown preset. Available: {', '.join(PRESETS.keys())}{RESET}")
            continue
            
        target_dir = parts[2] if len(parts) > 2 else DEFAULT_REPORTS_DIR
        
        reports_text, folder_images = read_directory(target_dir)
        
        if not reports_text and not folder_images:
            print(f"{COLOR_SYS}No documents or images found in {target_dir}/{RESET}")
            continue
            
        user_input = f"{PRESETS[preset_type]}\n\nPatient Data:\n{reports_text}"
        images.extend(folder_images)
        print(f"{COLOR_SYS}Transmitting {preset_type} request with {len(folder_images)} images to host...{RESET}\n")

    message = {"role": "user", "content": user_input}
    if images:
        message["images"] = images
        
    chat_history.append(message)
    
    payload = {
        "model": MODEL_NAME,
        "messages": chat_history,
        "stream": True
    }
    
    print(f"{COLOR_AI}C.A.R.E. Engine: {RESET}", end="", flush=True)
    full_response = ""
    
    try:
        response = requests.post(HOST_URL, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                text_piece = chunk.get("message", {}).get("content", "")
                print(f"{COLOR_AI}{text_piece}{RESET}", end="", flush=True)
                full_response += text_piece
                
        print("\n")
        chat_history.append({"role": "assistant", "content": full_response})
        
        if len(chat_history) > 8:
            chat_history = chat_history[-8:]
            
    except KeyboardInterrupt:
        print(f"\n{COLOR_SYS}[Generation interrupted by user. Chat remains active.]{RESET}")
        chat_history.append({"role": "assistant", "content": full_response + " [Interrupted]"})
    except requests.exceptions.RequestException as e:
        print(f"\n{COLOR_SYS}[Network Error: {e}]{RESET}")
        if chat_history:
            chat_history.pop()
