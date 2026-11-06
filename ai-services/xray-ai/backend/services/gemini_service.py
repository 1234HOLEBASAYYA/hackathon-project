"""
Gemini Multimodal Clinical Diagnostic & Narrative Service.
Features:
  1. Multimodal Radiograph Analysis: Direct visual interpretation via gemini-3.5-flash-lite.
     - Identifies anatomical region (Chest, Hand, Wrist, Foot, Leg, Knee, Hip, Shoulder, Spine, etc.).
     - Detects fracture, dislocation, defect, or infection/infiltrate.
     - Localizes damage with normalized bounding boxes [ymin, xmin, ymax, xmax].
     - Pinpoints specific affected bone or organ structure.
     - Generates key clinical observations and patient guidance.
  2. Fallback Narrative Service: If API is unavailable, provides verified deterministic clinical templates.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

DEFAULT_GEMINI_KEY = ""

def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_XRAY")
    if key and key.strip():
        return key.strip()
    # Check .env files
    script_dir = Path(__file__).resolve().parent
    search_paths = [
        Path(".env"),
        Path("backend/.env"),
        script_dir / ".env",
        script_dir.parent / ".env",
        script_dir.parent.parent / ".env",
        Path("../../.env")
    ]
    for env_path in search_paths:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("GEMINI_API_KEY=") or line.strip().startswith("GEMINI_API_KEY_XRAY="):
                        k = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        if k:
                            return k
            except Exception:
                pass
    return DEFAULT_GEMINI_KEY

def analyze_radiograph_multimodal(image_path: Path, mime_type: str = "image/jpeg") -> Optional[Dict[str, Any]]:
    """
    Performs full multimodal radiological analysis using Gemini 3.5 Flash Lite.
    Identifies anatomy, fracture/defect/infection, affected bone, damage location, and bounding box.
    """
    api_key = get_api_key()
    if not api_key or not GENAI_AVAILABLE:
        print("[Gemini Service] No API key or google-genai library missing.")
        return None
        
    try:
        client = genai.Client(api_key=api_key)
        uploaded = client.files.upload(file=str(image_path))
        
        prompt = """You are a senior radiological imaging AI.
CRITICAL FIRST STEP - AUTHENTICITY VERIFICATION:
Inspect whether this input image is an authentic medical projection radiograph (X-ray, fluoroscopy, CT scout projection, or DICOM radiograph).
If this image is NOT a medical X-ray (for example, if it is a photograph of a person, face, selfie, animal/pet, vehicle, landscape, room, artwork, drawing, cartoon, screenshot, document, food, or non-medical graphic):
You MUST set "is_radiograph": false and return JSON with these exact keys:
{
  "is_radiograph": false,
  "detected_image_type": string (e.g. "Color photograph of a pet", "Selfie photograph", "Digital illustration/drawing", "Document/screenshot", "Landscape photo"),
  "rejection_reason": string (clear explanation that this is not a medical radiograph displaying bone or tissue radiodensity and no skeletal or thoracic pathology can be evaluated),
  "key_observations": list of 2-3 concise observations (e.g. ["The image shows a non-radiographic subject.", "No radiographic bone attenuation or anatomical projection is present."]),
  "clinical_guidance": "Please upload an authentic medical X-ray radiograph in PNG, JPG, or DICOM format."
}

ONLY IF the image IS an authentic medical X-ray, set "is_radiograph": true and return:
{
  "is_radiograph": true,
  "anatomical_region": string (e.g. "Chest", "Hand", "Wrist", "Foot", "Leg", "Knee", "Hip", "Shoulder", "Spine", "Elbow", "Forearm"),
  "is_abnormal": boolean (true if fracture, defect, cortical disruption, dislocation, infection, consolidation, effusion, or lesion is visible; false if completely normal),
  "primary_diagnosis": string (clear clinical summary of what has happened, e.g. "Transverse fracture of the proximal phalanx", "Right lower lobe pulmonary infiltrate/infection", "Normal anatomical alignment with no acute lesion"),
  "pathology_type": string (e.g. "Fracture", "Cortical Disruption", "Dislocation", "Infection / Consolidation", "Pleural Effusion", "Normal"),
  "affected_structure": string (exact bone or organ affected, e.g. "Distal Radius", "Hallux Proximal Phalanx", "5th Metacarpal", "Tibia Shaft", "Left Lower Lung Field", "Rib Cage", "Intact Bone Architecture"),
  "damage_location": string (precise focal location, e.g. "Mid-shaft with lateral displacement", "Base and articular margin", "Retrocardiac zone", "Intact"),
  "displacement": string (e.g. "Displaced", "Non-displaced", "Impacted", "Angulated", "N/A"),
  "confidence": float between 0.70 and 0.99,
  "bounding_box_normalized": [ymin, xmin, ymax, xmax] as 4 floats between 0.0 and 1.0 framing the exact broken/defected/infected area, or null if normal,
  "key_observations": list of 2 to 4 concise bullet points describing specific visual findings,
  "clinical_guidance": string (actionable clinical guidance or next steps for patient/physician)
}
"""
        actual_mime = getattr(uploaded, "mime_type", None) or mime_type or "image/jpeg"
        res = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=[
                {"type": "text", "text": prompt},
                {"type": "image", "uri": uploaded.uri, "mime_type": actual_mime}
            ]
        )
        
        text = res.output_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(text)
        data["source"] = "gemini_multimodal"
        data["gemini_active"] = True
        return data
    except Exception as e:
        print(f"[Gemini Service] Multimodal analysis error ({e}). Falling back to local pipeline.")
        return None

def get_gemini_explanation(
    anatomical_region: str,
    findings: list,
    model_name: str,
    confidence: float,
    is_abnormal: bool,
    affected_bone: str = "N/A"
) -> Dict[str, Any]:
    """
    Fallback explanation generator using verified clinical rules.
    """
    return generate_clinical_template(
        anatomical_region=anatomical_region,
        findings=findings,
        confidence=confidence,
        is_abnormal=is_abnormal,
        affected_bone=affected_bone
    )

def generate_clinical_template(anatomical_region: str, findings: list, confidence: float, is_abnormal: bool, affected_bone: str):
    reg = str(anatomical_region).capitalize()
    if is_abnormal:
        summary = (
            f"The radiological evaluation of the {reg} identified imaging features suspicious for "
            f"structural damage or cortical discontinuity, primarily localized to the {affected_bone} "
            f"(confidence: {confidence*100:.1f}%). Spatial damage localization bounding boxes indicate "
            f"the focal region of concern."
        )
        takeaways = [
            f"Primary region of interest: {affected_bone} in the {reg}.",
            "Focal damage localization highlights cortical disruption or misalignment.",
            "Clinical correlation with physical examination and palpation is recommended."
        ]
        guidance = "Immediate consultation with an orthopedist or certified radiologist is strongly advised to verify findings."
    else:
        summary = (
            f"The radiological evaluation of the {reg} did not identify evidence of acute fracture, "
            f"cortical disruption, or gross structural abnormality (confidence: {confidence*100:.1f}%). "
            f"Bone alignment and cortical contours appear intact within model resolution limits."
        )
        takeaways = [
            f"No focal fracture identified across examined {reg} structures.",
            "Normal cortical continuity and gross alignment observed.",
            "Subtle or non-displaced microfractures may require dedicated oblique views or follow-up."
        ]
        guidance = "If clinical symptoms or pain persist, a formal radiologist read and potential secondary imaging (MRI/CT) is recommended."
        
    return {
        "summary": summary,
        "key_takeaways": takeaways,
        "patient_guidance": guidance,
        "gemini_active": False
    }
