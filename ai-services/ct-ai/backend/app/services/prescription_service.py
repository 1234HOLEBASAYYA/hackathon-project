import re
from pathlib import Path
from typing import Dict, List, Any


class PrescriptionService:
    """
    Intelligent medical prescription & clinical notes analyzer.
    Extracts medications, dosages, frequency, clinical contraindications,
    and patient safety warnings.
    """
    KNOWN_DRUGS = {
        "amoxicillin": {"class": "Antibiotic (Penicillin)", "common_use": "Bacterial pneumonia, respiratory infections"},
        "azithromycin": {"class": "Macrolide Antibiotic", "common_use": "Atypical pneumonia, bronchitis, respiratory infection"},
        "ceftriaxone": {"class": "Cephalosporin Antibiotic", "common_use": "Moderate to severe pneumonia"},
        "levofloxacin": {"class": "Fluoroquinolone Antibiotic", "common_use": "Hospital/Community-acquired pneumonia"},
        "albuterol": {"class": "Bronchodilator (Beta-2 Agonist)", "common_use": "Bronchospasm, wheezing, COPD/Asthma"},
        "prednisone": {"class": "Corticosteroid", "common_use": "Pulmonary inflammation, acute exacerbations"},
        "paracetamol": {"class": "Antipyretic / Analgesic", "common_use": "Fever, pleuritic chest discomfort"},
        "acetaminophen": {"class": "Antipyretic / Analgesic", "common_use": "Fever reduction, pain management"},
        "ibuprofen": {"class": "NSAID", "common_use": "Inflammation, chest pain, fever"},
        "guaifenesin": {"class": "Expectorant", "common_use": "Productive cough, chest congestion"},
        "dextromethorphan": {"class": "Antitussive", "common_use": "Dry, hacking cough relief"},
        "levocetirizine": {"class": "Antihistamine (2nd Gen)", "common_use": "Allergic rhinitis, cough, rhinorrhea"},
        "pantoprazole": {"class": "Proton Pump Inhibitor (PPI)", "common_use": "Gastric acid suppression, gastroprotection"},
        "ambroxol": {"class": "Mucolytic Agent", "common_use": "Productive cough, mucus thinning and clearance"},
        "cefixime": {"class": "3rd Gen Cephalosporin", "common_use": "Bacterial respiratory and urinary infections"},
        "clavulanate": {"class": "Beta-Lactamase Inhibitor", "common_use": "Penicillin enhancement for resistant bacteria"}
    }

    def analyze_prescription_text(self, text: str) -> Dict[str, Any]:
        """
        Parses clinical notes or prescription text to extract medical entities.
        """
        text_lower = text.lower()
        extracted_medications = []
        warnings = []
        recommendations = []

        # Find drugs
        for drug_name, details in self.KNOWN_DRUGS.items():
            if re.search(r"\b" + re.escape(drug_name) + r"\b", text_lower):
                # Look for dosage patterns near the drug
                dosage_match = re.search(
                    re.escape(drug_name) + r"[\s:]+([0-9]+(?:\.[0-9]+)?\s*(?:mg|g|mcg|ml))\b",
                    text_lower
                )
                dosage = dosage_match.group(1) if dosage_match else "Standard clinical dose"

                freq_match = re.search(
                    r"\b(once daily|twice daily|bid|tid|qid|every \d+ hours|prn|as needed)\b",
                    text_lower
                )
                frequency = freq_match.group(1).upper() if freq_match else "As directed by physician"

                extracted_medications.append({
                    "name": drug_name.capitalize(),
                    "class": details["class"],
                    "indicated_for": details["common_use"],
                    "dosage": dosage,
                    "frequency": frequency
                })

        # Check for pneumonia / respiratory related keywords
        respiratory_signs = []
        keywords = {
            "fever": "Pyrexia / elevated body temperature",
            "cough": "Tussive presentation",
            "sputum": "Productive airway secretions",
            "shortness of breath": "Dyspnea / respiratory distress",
            "dyspnea": "Shortness of breath on exertion or rest",
            "crackles": "Adventitious lung sound indicating alveolar fluid",
            "consolidation": "Radiographic lung tissue solidification"
        }
        for kw, desc in keywords.items():
            if kw in text_lower:
                respiratory_signs.append({"keyword": kw.capitalize(), "significance": desc})

        # Clinical warnings
        if any(d["name"].lower() in ["amoxicillin", "ceftriaxone"] for d in extracted_medications):
            if "allergy" in text_lower or "allergic" in text_lower or "penicillin" in text_lower:
                warnings.append("Caution: Patient file mentions potential allergy sensitivity. Verify beta-lactam safety before dispensing.")

        if any(d["name"].lower() in ["ibuprofen", "prednisone"] for d in extracted_medications):
            warnings.append("Co-administration of NSAID with systemic corticosteroid increases risk of gastrointestinal mucosal irritation. Consider gastroprotective agent.")

        # Default clinical guidance
        recommendations.append("Ensure adequate hydration (2-3 L daily) to facilitate liquefaction of bronchial secretions.")
        recommendations.append("Complete full antimicrobial course even if symptoms resolve earlier to prevent resistance.")
        recommendations.append("Seek immediate medical evaluation if pulse oximetry SpO2 drops below 94% or severe breathlessness develops.")

        return {
            "raw_text": text,
            "detected_medications": extracted_medications,
            "respiratory_signs": respiratory_signs,
            "clinical_warnings": warnings,
            "doctor_guidance": recommendations,
            "summary": f"Detected {len(extracted_medications)} medication(s) and {len(respiratory_signs)} respiratory clinical marker(s)."
        }

    def extract_text_from_prescription_image(self, image_input: Any) -> str:
        """
        Extracts medical text, patient demographics, and medication orders from a prescription image
        using Gemini Multimodal Vision API.
        """
        import os
        from PIL import Image
        from services.gemini_service import get_gemini_client

        if isinstance(image_input, (str, Path)):
            pil_image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_image = image_input.convert("RGB")
        else:
            raise ValueError(f"Unsupported image input: {type(image_input)}")

        client = get_gemini_client()
        ocr_prompt = (
            "You are an expert clinical pharmacologist and medical document reader. "
            "Extract all handwritten and printed medical prescription details verbatim from this image: "
            "Patient name, age, date, doctor details, diagnosis/symptoms, and all prescribed medications "
            "(drug name, dosage, frequency, duration, instructions). "
            "Output the extraction clearly as plain clinical notes."
        )

        primary_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
        fallback_env = os.getenv("FALLBACK_MODELS", "gemini-3.5-flash,gemini-3.1-flash-lite,gemini-flash-lite-latest,gemini-3.8-flash")
        fallbacks = [m.strip() for m in fallback_env.split(",") if m.strip()]
        models_to_try = [primary_model]
        for fb in fallbacks:
            if fb not in models_to_try:
                models_to_try.append(fb)

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[pil_image, ocr_prompt]
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[PrescriptionService] Gemini OCR failed on {model_name}: {e}")
                continue

        # Fallback to pytesseract if installed
        try:
            import pytesseract
            return pytesseract.image_to_string(pil_image)
        except Exception:
            return ""


prescription_service = PrescriptionService()
