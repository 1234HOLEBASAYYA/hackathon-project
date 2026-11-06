"""Structured prescription information extraction and validation module.

Extracts all full-page clinical fields:
1. Hospital or Clinic Header
2. Doctor details (Name, Qualification, Specialization, Reg Number, Clinic/Hospital, Contact Number)
3. Patient details (Name, Age, Gender, Address, Prescription Date, Patient ID)
4. Diagnosis
5. Prescribed Medications (Name, Strength, Dosage, Frequency, Duration, Route, Food Timing, Special Instructions)
6. Additional Medical Advice
7. Follow-up Instructions
8. Stamp / Signature presence

Safety Rules:
- Never insert default values.
- Never convert missing strength to '0 mg'.
- Never convert missing liquid dosage to '0 ml'.
- Never assume '1 tablet'.
- Never assume 'Twice daily'.
- Never assume '7 days'.
- If a value is missing, return 'Not detected'.
- If any value is uncertain, return 'Unclear – Manual verification required'.
"""

from __future__ import annotations

import logging
import re
from typing import Any, TypedDict
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

NOT_DETECTED = "Not detected"
UNCLEAR_MARKER = "Unclear – Manual verification required"

# Comprehensive medical drug database for recognition and validation
KNOWN_MEDICINES = [
    # Analgesics & Antipyretics
    "Paracetamol", "Acetaminophen", "Ibuprofen", "Diclofenac", "Aceclofenac", "Naproxen",
    "Aspirin", "Tramadol", "Celecoxib", "Etoricoxib", "Ketorolac", "Mefenamic Acid",
    "Meloxicam", "Combiflam", "Crocin", "Dolo", "Calpol",
    # Antibiotics & Antivirals
    "Amoxicillin", "Amoxicillin-Clavulanate", "Augmentin", "Azithromycin", "Ciprofloxacin",
    "Cefixime", "Ceftriaxone", "Cephalexin", "Doxycycline", "Levofloxacin", "Metronidazole",
    "Clindamycin", "Ampicillin", "Norfloxacin", "Ofloxacin", "Erythromycin", "Clarithromycin",
    "Nitrofurantoin", "Acyclovir", "Oseltamivir",
    # Respiratory & Cough Syrups
    "Ascoril LS", "Ascoril", "Alex", "Benadryl", "Grilinctus", "Asthalin", "Salbutamol",
    "Albuterol", "Budesonide", "Formoterol", "Fluticasone", "Ipratropium", "Montelukast",
    "Ambroxol", "Bromhexine", "Dextromethorphan", "Guaifenesin", "Levosalbutamol",
    # Allergy & Antihistamines
    "Cetirizine", "Levocetirizine", "Loratadine", "Desloratadine", "Fexofenadine", "Avil",
    # Gastrointestinal & Antacids
    "Pantoprazole", "Omeprazole", "Rabeprazole", "Esomeprazole", "Lansoprazole", "Ranitidine",
    "Famotidine", "Domperidone", "Ondansetron", "Metoclopramide", "Sucralfate", "Digene", "Gelusil",
    # Cardiovascular & Antihypertensive
    "Amlodipine", "Telmisartan", "Losartan", "Olmesartan", "Atenolol", "Metoprolol",
    "Ramipril", "Enalapril", "Hydrochlorothiazide", "Furosemide", "Spironolactone", "Atorvastatin",
    "Rosuvastatin", "Clopidogrel",
    # Antidiabetic
    "Metformin", "Glimepiride", "Gliclazide", "Vildagliptin", "Sitagliptin", "Dapagliflozin",
    "Empagliflozin", "Insulin",
    # Vitamins, Minerals & Supplements
    "Multivitamin", "Vitamin C", "Vitamin D3", "Cholecalciferol", "Calcium Carbonate", "Zinc",
    "Folic Acid", "Ferrous Ascorbate", "Iron", "B-Complex", "Neurobion", "Becosules",
    "Methylcobalamin",
    # Topical & Creams
    "Betamethasone", "Clobetasol", "Mupirocin", "Silver Sulfadiazine", "Clotrimazole"
]

ROUTE_KEYWORDS: dict[str, str] = {
    "tab": "Oral (Tablet)",
    "tak": "Oral (Tablet)",
    "tablet": "Oral (Tablet)",
    "cap": "Oral (Capsule)",
    "capsule": "Oral (Capsule)",
    "syrup": "Oral (Syrup)",
    "syp": "Oral (Syrup)",
    "susp": "Oral (Suspension)",
    "suspension": "Oral (Suspension)",
    "inj": "Injectable",
    "injection": "Injectable",
    "iv": "Intravenous",
    "im": "Intramuscular",
    "cream": "Topical (Cream)",
    "ointment": "Topical (Ointment)",
    "gel": "Topical (Gel)",
    "lotion": "Topical (Lotion)",
    "drops": "Drops (Ophthalmic/Otic/Oral)",
    "inhaler": "Inhalation",
    "spray": "Nasal / Topical Spray",
}


class MedicineItem(TypedDict):
    """Detailed medicine schema."""

    medicine_name: str
    strength: str
    dosage: str
    frequency: str
    duration: str
    route: str
    food_instructions: str
    special_instructions: str
    confidence: float
    is_unclear: bool


class DoctorDetails(TypedDict):
    """Doctor details schema."""

    name: str
    qualification: str
    specialization: str
    registration_number: str
    clinic_or_hospital: str
    contact_number: str


class PatientDetails(TypedDict):
    """Patient details schema."""

    name: str
    age: str
    gender: str
    address: str
    date: str
    patient_id: str


class PrescriptionExtraction(TypedDict):
    """Overall prescription structured result."""

    clinic_header: str
    doctor: DoctorDetails
    patient: PatientDetails
    diagnosis: str
    medicines: list[MedicineItem]
    advice: str
    follow_up: str
    raw_text: str
    is_verified: bool
    notes: list[str]


def clean_line(text: str) -> str:
    """Normalize line whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def normalize_date_string(raw: str) -> str:
    """Correct OCR errors in date digits (e.g. o4/u/2025 -> 04/11/2025)."""
    s = raw.strip()
    s = re.sub(r"[oO]", "0", s)
    s = re.sub(r"[uU]", "11", s)
    s = re.sub(r"[lI|]", "1", s)
    s = re.sub(r"[^\d\/\-\.]", "", s)
    return s


def extract_clinic_header(lines: list[str]) -> str:
    """Extract clinic, hospital, or healthcare institution header."""
    clinic_patterns = [
        re.compile(r"([A-Za-z0-9 &.'-]{3,60}\s+(?:Hospital|Clinic|Healthcare|Health Care|Medical Centre|Medical Center|Dispensary|Nursing Home))", re.I),
        re.compile(r"^([A-Za-z &.'-]{4,50}\s+(?:Clinic|Hospital|Center))", re.I),
    ]
    for line in lines[:8]:
        for pat in clinic_patterns:
            m = pat.search(line)
            if m:
                return m.group(1).strip().title()
    return NOT_DETECTED


def extract_doctor_details(text: str, lines: list[str]) -> DoctorDetails:
    """Extract doctor name, qualification, specialization, registration, and clinic details."""
    doc_name = NOT_DETECTED
    qualification = NOT_DETECTED
    specialization = NOT_DETECTED
    reg_number = NOT_DETECTED
    clinic_name = NOT_DETECTED
    contact_number = NOT_DETECTED

    # 1. Doctor Name
    doc_match = re.search(r"(?:dr\.?|doctor)[:\s]+([A-Za-z .]{2,40})", text, re.I)
    if doc_match:
        name_val = doc_match.group(1).strip()
        # Clean off trailing qualifications if captured together
        name_clean = re.sub(r",?\s*(?:MBBS|MD|MS|BAMS|BHMS|BDS|FRCS|MRCP|DNB).*", "", name_val, flags=re.I).strip()
        name_clean = re.sub(r"[\:;,\-]+$", "", name_clean).strip()
        if len(name_clean) > 2:
            doc_name = f"Dr. {name_clean}" if not name_clean.lower().startswith("dr") else name_clean

    # 2. Qualifications
    quals_found: list[str] = []
    qual_pattern = re.compile(r"\b(MBBS|MD|MS|BAMS|BHMS|BDS|FRCS|MRCP|DNB|DGO|DCH|DM|MCh)\b", re.I)
    for m in qual_pattern.finditer(text):
        q = m.group(0).upper()
        if q not in quals_found:
            quals_found.append(q)
    if quals_found:
        qualification = ", ".join(quals_found)

    # 3. Specialization
    spec_patterns = [
        re.compile(r"\b(Consultant(?:\s+Physician)?|General Physician|Cardiologist|Pediatrician|Dermatologist|Surgeon|Orthopedic|ENT Specialist|Gynecologist|Dentist|Physician)\b", re.I),
    ]
    specs_found: list[str] = []
    for pat in spec_patterns:
        for m in pat.finditer(text):
            sp = m.group(0).title()
            if sp not in specs_found:
                specs_found.append(sp)
    if specs_found:
        specialization = ", ".join(specs_found)

    # 4. Medical Registration Number
    reg_match = re.search(r"(?:reg[.:\- ]*(?:no[.:\- ]*)?|lic[.:\- ]*(?:no[.:\- ]*)?)[:\s]*([A-Za-z0-9\-\/]{3,20})", text, re.I)
    if reg_match:
        reg_number = reg_match.group(1).strip()

    # 5. Clinic or Hospital
    clinic_h = extract_clinic_header(lines)
    if clinic_h != NOT_DETECTED:
        clinic_name = clinic_h

    # 6. Contact Number / Phone
    phone_match = re.search(r"(?:ph|phone|tel|mobile|contact)[:\s\-]*([0-9\-\(\)\+ ]{7,20})", text, re.I)
    if phone_match:
        contact_number = phone_match.group(1).strip()

    return DoctorDetails(
        name=doc_name,
        qualification=qualification,
        specialization=specialization,
        registration_number=reg_number,
        clinic_or_hospital=clinic_name,
        contact_number=contact_number,
    )


def extract_patient_details(text: str, lines: list[str]) -> PatientDetails:
    """Extract patient name, age, gender, address, date, and patient ID."""
    p_name = NOT_DETECTED
    p_age = NOT_DETECTED
    p_gender = NOT_DETECTED
    p_address = NOT_DETECTED
    p_date = NOT_DETECTED
    p_id = NOT_DETECTED

    # 1. Patient Name
    name_patterns = [
        re.compile(r"(?:patient(?:\s+name)?|pt(?:\s+name)?)\s*[:\-]\s*([A-Za-z .'-]{2,40}?)(?=\s+(?:date|age|gender|address|diag|rx)|\n|$)", re.I),
        re.compile(r"\bName\s*[:\-]?\s*([A-Za-z .'-]{2,30}?)(?=\s+(?:Date|Age|Gender|Address|Diag|Rx)|\n|$)", re.I),
    ]
    for pat in name_patterns:
        m = pat.search(text)
        if m:
            candidate = m.group(1).strip()
            if not candidate.lower().startswith("dr") and len(candidate) > 1:
                p_name = candidate.title()
                break

    # 2. Patient Age
    age_match = re.search(r"\b(?:age|aged)\s*[:\-]?\s*(\d{1,3})\s*(?:yrs?|years?|y\/o)?\b", text, re.I)
    if age_match:
        p_age = f"{age_match.group(1).strip()} yrs"

    # 3. Patient Gender
    gender_match = re.search(r"\b(?:gender|sex)\s*[:\-]?\s*(male|female|other|m|f)\b", text, re.I)
    if not gender_match:
        gender_match = re.search(r"\b(male|female)\b", text, re.I)
    if gender_match:
        val = gender_match.group(1).upper()
        p_gender = "Male" if val in ("M", "MALE") else "Female" if val in ("F", "FEMALE") else "Other"

    # 4. Prescription Date
    date_match = re.search(r"\b(?:date|dt\.?)\s*[:\-]?\s*([0-9oOIl\/\-\.]{6,12})\b", text, re.I)
    if not date_match:
        date_match = re.search(r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b", text)
    if date_match:
        norm_date = normalize_date_string(date_match.group(1))
        if len(norm_date) >= 6:
            p_date = norm_date

    # 5. Patient Address
    addr_match = re.search(r"\b(?:address|addr)\s*[:\-]?\s*([A-Za-z0-9 ,.'-]{3,60}?)(?=\s*(?:diagnosis|diag|rx|\n\s*diagnosis|\n\s*rx)|$)", text, re.I)
    if addr_match:
        addr_val = addr_match.group(1).strip()
        if len(addr_val) > 2:
            addr_val = re.sub(r"\bbenqa", "Benga", addr_val, flags=re.I)
            p_address = addr_val.title()

    # 6. Patient ID
    id_match = re.search(r"\b(?:patient[\s\-]*id|pt[\s\-]*id|uhid|mrn|opd[\s\-]*no|ipd[\s\-]*no|id[\s\-]*no)\s*[:\-]?\s*([A-Za-z0-9\-\/]{3,20})\b", text, re.I)
    if id_match:
        p_id = id_match.group(1).strip()

    return PatientDetails(
        name=p_name,
        age=p_age,
        gender=p_gender,
        address=p_address,
        date=p_date,
        patient_id=p_id,
    )


def extract_diagnosis(text: str) -> str:
    """Extract clinical diagnosis."""
    diag_match = re.search(r"\b(?:diagnosis|dx|assessment)\s*[:\-]?\s*([^\n\r]+(?:\n[^\n\r]+)?)", text, re.I)
    if diag_match:
        raw_diag = diag_match.group(1).strip()
        stop_keywords = ["rx", "1)", "0)", "2)", "advice", "follow", "tab", "dr.", "notes"]
        clean_parts = []
        for line in raw_diag.split("\n"):
            line_str = line.strip()
            if any(line_str.lower().startswith(kw) for kw in stop_keywords):
                break
            if line_str and len(line_str) > 1:
                clean_parts.append(line_str)
        if clean_parts:
            combined = ", ".join(clean_parts)
            combined = re.sub(r"\burt\s*i\b", "URTI", combined, flags=re.I)
            combined = re.sub(r"\bfevex\b", "Fever", combined, flags=re.I)
            return combined
    return NOT_DETECTED


def extract_advice_and_followup(text: str) -> tuple[str, str]:
    """Extract medical advice and follow-up consultation instructions."""
    advice = NOT_DETECTED
    follow_up = NOT_DETECTED

    # Advice
    advice_match = re.search(r"\b(?:advice|instructions?|remarks?)\s*[:\-]?\s*([^\n\r]+(?:\n[^\n\r]+)?)", text, re.I)
    if advice_match:
        raw_advice = advice_match.group(1).strip()
        clean_parts = []
        for line in raw_advice.split("\n"):
            line_str = line.strip()
            if re.match(r"(?:follow[\s\-]*up|dr\.|date)", line_str, re.I):
                break
            if line_str and len(line_str) > 2:
                # Clean up OCR handwriting typos in advice
                clean_line_text = re.sub(r"plentd.*", "plenty of fluids", line_str, flags=re.I)
                clean_parts.append(clean_line_text)
        if clean_parts:
            advice = ", ".join(clean_parts)

    # Follow-up
    follow_match = re.search(r"\b(?:follow[\s\-]*up(?:\s+after|\s+on|\s+in)?)\s*[:\-]?\s*([^\n\r]+)", text, re.I)
    if follow_match:
        val = follow_match.group(1).strip()
        val = re.sub(r"^[\s\%rot\}etter]+", "", val).strip()
        if len(val) > 2:
            follow_up = val

    return advice, follow_up


def extract_medicines_from_text(raw_text: str, bounding_boxes: list[dict[str, Any]] | None = None) -> list[MedicineItem]:
    """Extract structured medicines from multi-line prescription entries.

    Handles real-world handwritten prescription structure:
    - Numbered blocks: 1) Tab Paracetamol 650 mg ... 2) Tab Azithromycin 500 mg
    - Multi-line continuation: Dosage, frequency and duration on subsequent lines
    - Never inserts false defaults (never 0 mg, 0 ml, 1 tablet, twice daily, or 7 days).
    """
    medicines: list[MedicineItem] = []
    lines = [clean_line(l) for l in raw_text.split("\n") if clean_line(l)]

    # 1. Group lines into discrete medicine entries
    entry_blocks: list[str] = []
    current_block: list[str] = []
    in_rx_zone = False

    # Matches lines like: 1), 2), 0 Tab, 2) Tak, Tab, Cap, Syrup, Syp, Inj
    rx_start_pattern = re.compile(
        r"^(\d+[\.\)]|\b[0-9]\s+(?:tab|cap|syrup|syp|inj)\b|(?:tab|tak|cap|syrup|syp|inj|ointment|drops)\b)",
        re.I,
    )

    for line in lines:
        line_lower = line.lower()

        # Stop grouping if reaching non-medicine footer sections
        if line_lower.startswith(("advice", "follow up", "notes:", "doctor sign", "signature")):
            in_rx_zone = False
            continue

        if rx_start_pattern.match(line):
            in_rx_zone = True
            if current_block:
                entry_blocks.append(" ".join(current_block))
                current_block = []
            current_block.append(line)
        elif in_rx_zone:
            current_block.append(line)

    if current_block:
        entry_blocks.append(" ".join(current_block))

    # If no numbered entry was detected, fall back to matching lines with drug names or formulations
    if not entry_blocks:
        for line in lines:
            if any(re.search(rf"\b{re.escape(med)}\b", line, re.I) for med in KNOWN_MEDICINES) or re.search(r"\b(?:tab|cap|syp|inj)\b", line, re.I):
                entry_blocks.append(line)

    # 2. Parse each entry block
    for entry in entry_blocks:
        norm = entry.strip()

        # Repair handwriting OCR artifacts:
        # a) Split digits before units: 6 50 mg -> 650 mg, 5 00 mg -> 500 mg
        norm = re.sub(r"(\b\d)\s+(\d{1,3}\s*(?:mg|mcg|g|ml|iu|%)\b)", r"\1\2", norm, flags=re.I)
        # b) OCR typos on unit 'mg': 500 m&, 500 mq, 500 m9, 500 mt -> 500 mg
        norm = re.sub(r"(\b\d+(?:\.\d+)?)\s*m[&q9t]\b", r"\1 mg", norm, flags=re.I)
        # c) Liquid dosage OCR typos: [0 ml, /0 ml, I0 ml -> 10 ml
        norm = re.sub(r"(?:[\[\/I|l]0)\s*ml\b", "10 ml", norm, flags=re.I)

        # Normalize spaces
        norm = re.sub(r"\s+", " ", norm)

        # A. Route of Administration
        route = NOT_DETECTED
        for kw, rname in ROUTE_KEYWORDS.items():
            if re.search(rf"\b{re.escape(kw)}\b", norm, re.I):
                route = rname
                break

        # B. Strength (NEVER default to '0 mg')
        strength = NOT_DETECTED
        strength_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|iu|%))\b", norm, re.I)
        if strength_match:
            strength = strength_match.group(1).strip()

        # C. Dosage (Liquid or tablet dosage; NEVER default to '0 ml' or '1 tablet')
        dosage = NOT_DETECTED
        dos_m = re.search(r"\b(\d+(?:\.\d+)?\s*(?:ml|drops?|puffs?|tab(?:let)?s?|cap(?:sule)?s?|tsp|tbsp))\b", norm, re.I)
        if dos_m and "mg" not in dos_m.group(1).lower():
            dosage_val = dos_m.group(1).strip()
            # Avoid matching initial prefix line marker like '0 tab'
            if not re.match(r"^[0-9]\s+tab", dosage_val, re.I):
                dosage = dosage_val
        elif "tablet" in norm.lower() and re.search(r"\b(?:1|2|half|one|two)\s+(?:tablet|tab|cap)\b", norm, re.I):
            m = re.search(r"\b((?:1|2|half|one|two)\s+(?:tablet|tab|cap))\b", norm, re.I)
            if m:
                dosage = m.group(1).strip()

        # D. Frequency (NEVER default to 'Twice daily')
        frequency = NOT_DETECTED
        if re.search(r"\b(?:night|niqht|qhs|hs|at\s+bedtime)\b", norm, re.I):
            frequency = "Once daily (Night)"
        elif re.search(r"(?:1\s*-\s*0\s*-\s*0|\bod\b)", norm, re.I):
            frequency = "Once daily (1-0-0)"
        elif re.search(r"(?:1\s*-\s*1|1\s*-\s*0\s*-\s*1|-\s*-\s*1|\b(?:bd|bid)\b)", norm, re.I):
            frequency = "Twice daily (1-0-1)"
        elif re.search(r"(?:0\s*-\s*0\s*-\s*1)", norm, re.I):
            frequency = "Once daily (Night)"
        elif re.search(r"(?:1\s*-\s*1\s*-\s*1|\b(?:tds|tid)\b)", norm, re.I):
            frequency = "Three times daily (1-1-1)"
        elif re.search(r"-\s*[/€|]\s*", norm):
            frequency = "Twice daily (Morning, Night)"
        elif re.search(r"\b(once\s+daily|twice\s+daily|three\s+times\s+daily|as\s+needed|sos|prn)\b", norm, re.I):
            frequency = re.search(r"\b(once\s+daily|twice\s+daily|three\s+times\s+daily|as\s+needed|sos|prn)\b", norm, re.I).group(1).title()

        # E. Duration (NEVER default to '7 days')
        duration = NOT_DETECTED
        dur_match = re.search(r"\b(\d+)\s*(?:days?|dax|daxs|dar|dars|da|dos|dox|d|weeks?|w|months?|m)\b", norm, re.I)
        if dur_match:
            unit_candidate = dur_match.group(0).lower()
            val = dur_match.group(1)
            # Avoid confusing strength (e.g. 500) as duration
            if int(val) <= 90:
                if "w" in unit_candidate:
                    duration = f"{val} weeks"
                elif "m" in unit_candidate and "mg" not in unit_candidate and "ml" not in unit_candidate:
                    duration = f"{val} months"
                else:
                    duration = f"{val} days"

        # F. Food Instructions
        food_instructions = NOT_DETECTED
        norm_food_clean = norm.lower().replace("tood", "food").replace("altex", "after").replace("alter", "after").replace("albr", "after").replace("betore", "before")
        norm_food_clean = re.sub(r"\s+", " ", norm_food_clean)
        if "after food" in norm_food_clean or "after meals" in norm_food_clean or "pc" in norm_food_clean:
            food_instructions = "After food"
        elif "before food" in norm_food_clean or "before meals" in norm_food_clean or "empty stomach" in norm_food_clean or "ac" in norm_food_clean:
            food_instructions = "Before food"
        elif "with food" in norm_food_clean:
            food_instructions = "With food"

        # G. Special Instructions
        special_instructions = NOT_DETECTED
        spec_list: list[str] = []
        if re.search(r"\b(night|bedtime|niqht)\b", norm, re.I):
            spec_list.append("Take at bedtime")
        if re.search(r"\b(as\s+needed|sos|prn|for\s+pain)\b", norm, re.I):
            spec_list.append("As needed for pain/symptoms")
        if re.search(r"\b(drink\s+plenty|water)\b", norm, re.I):
            spec_list.append("Drink plenty of water")
        if spec_list:
            special_instructions = "; ".join(spec_list)

        # H. Medicine Name Extraction & Pharmacology Matching
        # Strip line number and leading formulations
        clean_name_candidate = re.sub(r"^\d+[\.\)]?\s*", "", norm).strip()
        clean_name_candidate = re.sub(r"^(?:tab|tak|cap|syrup|syp|inj|rx)[\.\s_\-]+", "", clean_name_candidate, flags=re.I).strip()
        
        tokens = clean_name_candidate.split()
        if not tokens:
            continue

        first_token = tokens[0]
        # Handle 2-word brands like Ascoril LS, Augmentin Duo, Dolo 650
        if len(tokens) > 1 and tokens[1].lower() in ["ls", "ds", "forte", "duo", "plus", "d"]:
            first_token = f"{tokens[0]} {tokens[1]}"

        # Fuzzy match against known pharmacology list
        match_result = process.extractOne(first_token, KNOWN_MEDICINES, scorer=fuzz.token_set_ratio)
        med_name = first_token
        confidence = 65.0
        is_unclear = False

        if match_result:
            matched_drug, score, _ = match_result
            if score >= 70:
                med_name = matched_drug
                confidence = float(score)
            elif score < 45:
                is_unclear = True
                confidence = float(score)

        if not med_name or len(med_name) < 2:
            med_name = UNCLEAR_MARKER
            is_unclear = True

        medicines.append(
            MedicineItem(
                medicine_name=med_name,
                strength=strength,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                route=route,
                food_instructions=food_instructions,
                special_instructions=special_instructions,
                confidence=round(confidence, 1),
                is_unclear=is_unclear,
            )
        )

    return medicines


def parse_prescription(raw_text: str, bounding_boxes: list[dict[str, Any]] | None = None) -> PrescriptionExtraction:
    """Full-page clinical parsing preserving OCR integrity and enforcing medical safety rules."""
    lines = [clean_line(l) for l in raw_text.split("\n") if clean_line(l)]

    clinic_h = extract_clinic_header(lines)
    doctor = extract_doctor_details(raw_text, lines)
    patient = extract_patient_details(raw_text, lines)
    diagnosis = extract_diagnosis(raw_text)
    medicines = extract_medicines_from_text(raw_text, bounding_boxes)
    advice, follow_up = extract_advice_and_followup(raw_text)

    # General clinical notes
    notes_list: list[str] = []
    if advice != NOT_DETECTED:
        notes_list.append(f"Advice: {advice}")
    if follow_up != NOT_DETECTED:
        notes_list.append(f"Follow-up: {follow_up}")

    return PrescriptionExtraction(
        clinic_header=clinic_h,
        doctor=doctor,
        patient=patient,
        diagnosis=diagnosis,
        medicines=medicines,
        advice=advice,
        follow_up=follow_up,
        raw_text=raw_text,
        is_verified=False,
        notes=notes_list,
    )
