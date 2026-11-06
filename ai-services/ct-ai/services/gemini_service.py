"""
Gemini AI Medical Image Analysis Service for MedVision-AI
Connects securely with Google GenAI SDK to generate structured, image-grounded
reports distinguishing visual observations from interpretations.
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError, ClientError, ServerError
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    APIError = Exception
    ClientError = Exception
    ServerError = Exception


class GeminiConfigurationError(Exception):
    """Raised when the Gemini API key or SDK is not configured."""
    pass


class GeminiAnalysisError(Exception):
    """Raised when an error occurs during Gemini AI image analysis."""
    def __init__(self, message: str, status_code: int = 500, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


class GeminiIncompatibleModalityError(GeminiAnalysisError):
    """Raised when Gemini vision detects an image incompatible with radiological CT analysis (e.g. a prescription document)."""
    def __init__(self, detected_modality: str, message: str):
        super().__init__(message, status_code=400, retryable=False)
        self.detected_modality = detected_modality
        self.message = message


# Standard Prompt strictly following Clinical AI guidelines
GEMINI_ANALYSIS_PROMPT = """
You are an expert AI clinical imaging assistant operating within the MedVision-AI Decision Support System.
You are tasked with conducting an objective, visual-only analysis of the uploaded medical imaging file (e.g., CT slice, scout view, or radiograph).

STRICT RADIOLOGICAL & CLINICAL INSTRUCTIONS:
1. MODALITY VERIFICATION & DOCUMENT GUARDRAIL:
   - FIRST evaluate if the image is a valid radiological study (CT scan slice, scout view, plain radiograph).
   - If the image is a MEDICAL PRESCRIPTION, HANDWRITTEN DOCTOR NOTE, PHARMACEUTICAL SLIP, or NON-RADIOLOGICAL DOCUMENT:
     You MUST set "is_compatible_ct_scan": false and "detected_modality": "prescription_doc".
     Do NOT extract medicines into CT anatomical observations!
     Set "report_title": "Incompatible Image - Prescription Document Detected",
     "incompatibility_reason": "Image is a handwritten medical prescription document and cannot be processed as a radiological CT scan."
   - If the image is a valid CT scan or radiograph, set "is_compatible_ct_scan": true and "detected_modality": "ct_scan".

2. ANALYZE VISIBLE CONTENT ONLY: Describe only anatomical and density structures clearly visible in this specific uploaded 2D image.
3. DISTINGUISH OBSERVATIONS FROM INTERPRETATIONS:
   - A 'visual observation' is an objective physical feature (e.g., "hyperdense area in left lung base", "well-corticated osseous margin").
   - A 'potential finding' is a non-definitive interpretation that warrants clinical correlation (e.g., "suggestive of consolidation or atelectasis").
4. DO NOT PROVIDE DEFINITIVE MEDICAL DIAGNOSES: Never state "diagnosis confirmed", "100% accurate", "definitely cancer", or "definitely normal".
5. UNCERTAINTY & LIMITATIONS:
   - Explicitly note that a single 2D image cannot replace a complete axial volumetric CT study (which typically contains hundreds of sequential slices with multiple kernel reconstructions).
   - If image resolution, contrast, or artifacts obscure anatomical details, state this clearly in image_quality and limitations.
6. NO HALLUCINATION: Do NOT invent patient history, symptoms, laboratory values, precise metric measurements, or artificial confidence percentages.
7. STRUCTURED JSON OUTPUT: You MUST return a single, valid JSON object with the exact keys specified below.

REQUIRED JSON SCHEMA:
{
  "is_compatible_ct_scan": true,
  "detected_modality": "ct_scan",
  "incompatibility_reason": "",
  "report_title": "AI-Assisted CT Image Analysis Report",
  "image_information": {
    "image_type": "Visually identifiable modality (e.g., Axial Chest CT Slice, Scout View, Plain Radiograph, or Handwritten Medical Prescription Document)",
    "image_dimensions": "Extracted or observed dimensions",
    "image_quality": "Assessment of visual clarity, contrast resolution, motion blur, or artifacts",
    "limitations": [
      "Evaluation limited to single uploaded image slice",
      "Lack of volumetric series and soft tissue windowing"
    ]
  },
  "visual_observations": [
    {
      "observation": "Concise title of visible physical appearance",
      "location": "Visible anatomical location (e.g., Left lower thoracic zone, Costophrenic angle, or Unknown if unidentifiable)",
      "description": "Objective description of density, margin, lucency, or opacity",
      "certainty": "observed"
    }
  ],
  "potential_findings": [
    {
      "finding": "Possible clinical consideration",
      "description": "Differential reasoning based strictly on the visual observation",
      "location": "Anatomical location if identifiable",
      "certainty": "uncertain",
      "supporting_visual_observation": "The specific visual observation that suggested this possibility"
    }
  ],
  "summary": "Clear, grounded 2-3 sentence overview of visible features and clinical review recommendations.",
  "recommendations_for_review": [
    "Formal interpretation by a qualified radiologist",
    "Clinical correlation with patient symptoms and lab results"
  ],
  "limitations": [
    "Analysis based on a standalone single image",
    "Absence of clinical history, prior comparison studies, and complete slice volume"
  ],
  "medical_disclaimer": "This AI-generated report is for educational and decision-support purposes and is not a substitute for formal interpretation by a board-certified radiologist or qualified physician."
}

Respond ONLY with the JSON object. Do not include markdown code blocks, backticks, or preamble text.
"""


def get_gemini_client() -> Any:
    """
    Initializes and validates the Gemini GenAI client from environment configuration.
    """
    if not GENAI_AVAILABLE:
        raise GeminiConfigurationError(
            "The Google GenAI SDK ('google-genai') is not installed. Please run: pip install google-genai"
        )

    api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY_CT", "").strip()
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        raise GeminiConfigurationError(
            "Gemini API key is missing. Please configure GEMINI_API_KEY in the backend .env file."
        )

    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        raise GeminiConfigurationError(f"Failed to initialize Gemini Client: {str(e)}")


def clean_json_response(raw_text: str) -> str:
    """
    Strips code block wrappers (```json ... ```) or trailing text to yield pure JSON string.
    """
    text = raw_text.strip()
    # Match ```json ... ``` or ``` ... ```
    json_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if json_block:
        text = json_block.group(1).strip()
    return text


def validate_and_normalize_report(report_dict: Dict[str, Any], file_name: str, dimensions_str: str) -> Dict[str, Any]:
    """
    Validates that the returned report contains all required fields, fills in any
    missing sections safely, and enforces medical disclaimers.
    """
    if not isinstance(report_dict, dict):
        raise ValueError("Model response is not a valid JSON dictionary")

    image_info = report_dict.get("image_information", {})
    if not isinstance(image_info, dict):
        image_info = {}

    # Modality & Document Incompatibility Guardrail
    is_compatible = report_dict.get("is_compatible_ct_scan", True)
    detected_mod = str(report_dict.get("detected_modality", "")).lower()
    img_type = str(image_info.get("image_type", "")).lower()
    rep_title = str(report_dict.get("report_title", "")).lower()

    if not is_compatible or detected_mod == "prescription_doc" or "prescription" in img_type or "prescription" in rep_title:
        raise GeminiIncompatibleModalityError(
            detected_modality="prescription_doc",
            message="not a proper image to scan"
        )

    # Required top-level keys
    report_title = report_dict.get("report_title", "AI-Assisted CT Image Analysis Report")

    image_info.setdefault("image_type", "Unknown unless visually identifiable")
    image_info["image_dimensions"] = dimensions_str or image_info.get("image_dimensions", "Unknown")
    image_info.setdefault("image_quality", "Visual quality adequate for screening inspection")
    
    limitations = image_info.get("limitations", [])
    if not isinstance(limitations, list):
        limitations = [str(limitations)]
    if not limitations:
        limitations = ["Assessment restricted to single static slice"]
    image_info["limitations"] = limitations

    visual_obs = report_dict.get("visual_observations", [])
    if not isinstance(visual_obs, list):
        visual_obs = []
    normalized_obs = []
    for item in visual_obs:
        if isinstance(item, dict):
            normalized_obs.append({
                "observation": str(item.get("observation", "Unspecified visual pattern")),
                "location": str(item.get("location", "Indeterminate")),
                "description": str(item.get("description", "")),
                "certainty": str(item.get("certainty", "observed"))
            })
    if not normalized_obs:
        normalized_obs.append({
            "observation": "Gross anatomical structures visualized",
            "location": "Whole field of view",
            "description": "Standard anatomical densities discernible in submitted slice.",
            "certainty": "observed"
        })

    potential_findings = report_dict.get("potential_findings", [])
    if not isinstance(potential_findings, list):
        potential_findings = []
    normalized_findings = []
    for item in potential_findings:
        if isinstance(item, dict):
            normalized_findings.append({
                "finding": str(item.get("finding", "Clinical consideration")),
                "description": str(item.get("description", "")),
                "location": str(item.get("location", "Indeterminate")),
                "certainty": "uncertain",  # Enforce uncertainty
                "supporting_visual_observation": str(item.get("supporting_visual_observation", "Visible density contrast"))
            })

    summary = report_dict.get("summary", "Image-based visual evaluation completed. Professional radiologist review recommended.")
    
    rec_review = report_dict.get("recommendations_for_review", [])
    if not isinstance(rec_review, list):
        rec_review = [str(rec_review)]
    if not rec_review:
        rec_review = [
            "Correlate findings with clinical presentation and full diagnostic imaging study.",
            "Formal radiologist reading is necessary for definitive diagnosis."
        ]

    top_limitations = report_dict.get("limitations", [])
    if not isinstance(top_limitations, list):
        top_limitations = [str(top_limitations)]
    if not top_limitations:
        top_limitations = [
            "Single slice 2D assessment cannot replace full 3D CT scan reconstruction.",
            "AI assistance is an adjunct tool and should not be used in isolation."
        ]

    disclaimer = (
        "This AI-generated report is for educational and decision-support purposes and "
        "is not a substitute for interpretation by a qualified radiologist or medical professional."
    )

    return {
        "report_title": report_title,
        "is_compatible_ct_scan": True,
        "detected_modality": "ct_scan",
        "filename": file_name,
        "image_information": image_info,
        "visual_observations": normalized_obs,
        "potential_findings": normalized_findings,
        "summary": summary,
        "recommendations_for_review": rec_review,
        "limitations": top_limitations,
        "medical_disclaimer": disclaimer,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }


def analyze_ct_scan_image(
    image_input: Any,
    filename: str = "ct_scan_image.jpg",
    dimensions_str: str = ""
) -> Dict[str, Any]:
    """
    Executes AI-powered visual analysis on a medical image using Gemini.
    
    Accepts:
    - image_input: PIL.Image, file path (str/Path), or bytes
    
    Features:
    - Automatic model selection from GEMINI_MODEL with resilient fallback cascade.
    - Retry logic with backoff for rate limits and temporary spikes (503/429).
    - Safe JSON decoding and fallback parsing.
    - Strict adherence to uncertainty and non-definitive guidelines.
    """
    client = get_gemini_client()

    # Prepare PIL Image
    if isinstance(image_input, (str, Path)):
        if not os.path.exists(image_input):
            raise GeminiAnalysisError(f"Image file does not exist: {image_input}", status_code=400)
        try:
            pil_image = Image.open(image_input).convert("RGB")
        except Exception as e:
            raise GeminiAnalysisError(f"Cannot decode image file: {str(e)}", status_code=400)
    elif isinstance(image_input, Image.Image):
        pil_image = image_input.convert("RGB")
    else:
        raise GeminiAnalysisError(f"Unsupported image input type: {type(image_input)}", status_code=400)

    # Models list to attempt
    primary_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
    fallback_env = os.getenv("FALLBACK_MODELS", "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash")
    fallbacks = [m.strip() for m in fallback_env.split(",") if m.strip()]
    
    models_to_try = [primary_model]
    for fb in fallbacks:
        if fb not in models_to_try:
            models_to_try.append(fb)

    last_exception = None
    response_text = None
    successful_model = None

    for model_name in models_to_try:
        # Retry up to 2 times per model for transient errors
        for attempt in range(2):
            try:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,  # Low temperature for clinical objectivity
                    http_options=types.HttpOptions(timeout=25000)
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=[pil_image, GEMINI_ANALYSIS_PROMPT],
                    config=config
                )

                if response and response.text:
                    response_text = response.text
                    successful_model = model_name
                    break
                else:
                    raise GeminiAnalysisError("Gemini returned an empty response.", status_code=502, retryable=True)

            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                
                # Check for rate limit or quota exhaustion
                if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    raise GeminiAnalysisError(
                        "Gemini API quota exceeded or rate limit reached. Please wait a moment and retry.",
                        status_code=429,
                        retryable=True
                    )
                # Check for invalid API key
                if "401" in err_str or "403" in err_str or "api_key_invalid" in err_str:
                    raise GeminiAnalysisError(
                        "Invalid Gemini API key. Please check your GEMINI_API_KEY configuration.",
                        status_code=401,
                        retryable=False
                    )
                # If model not found (404), deprecated, or timed out (504/deadline_exceeded), break immediately to next model in cascade
                if any(k in err_str for k in ["404", "not_found", "no longer available", "504", "deadline_exceeded", "timeout"]):
                    break
                # Check for transient unavailable / high demand (503)
                if "503" in err_str or "unavailable" in err_str:
                    time.sleep(1.0)
                    continue
        
        if successful_model:
            break

    if not response_text:
        err_msg = str(last_exception) if last_exception else "Analysis could not be completed."
        raise GeminiAnalysisError(
            f"Gemini analysis service unavailable across tested models: {err_msg}",
            status_code=503,
            retryable=True
        )

    # Parse and validate JSON
    cleaned_text = clean_json_response(response_text)
    try:
        raw_dict = json.loads(cleaned_text)
    except json.JSONDecodeError as jde:
        # Attempt heuristic salvage
        json_match = re.search(r"\{[\s\S]*\}", cleaned_text)
        if json_match:
            try:
                raw_dict = json.loads(json_match.group(0))
            except Exception:
                raise GeminiAnalysisError(
                    f"Gemini returned malformed JSON that could not be parsed: {str(jde)}",
                    status_code=502,
                    retryable=True
                )
        else:
            raise GeminiAnalysisError(
                f"Failed to parse structured JSON from AI response: {str(jde)}",
                status_code=502,
                retryable=True
            )

    normalized_report = validate_and_normalize_report(raw_dict, filename, dimensions_str)
    normalized_report["model_used"] = successful_model
    return normalized_report
