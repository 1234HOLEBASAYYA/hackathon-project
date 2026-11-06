"""Language-model helpers for prescription extraction."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PRESCRIPTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "patient_name": {"type": ["string", "null"]},
        "patient_age": {"type": ["string", "null"]},
        "date": {"type": ["string", "null"]},
        "doctor_name": {"type": ["string", "null"]},
        "diagnosis": {"type": ["string", "null"]},
        "notes": {"type": ["string", "null"]},
        "medicines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "dosage": {"type": ["string", "null"]},
                    "frequency": {"type": ["string", "null"]},
                    "duration": {"type": ["string", "null"]},
                    "confidence": {"type": "number"},
                    "confidences": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "number"},
                            "dosage": {"type": "number"},
                            "frequency": {"type": "number"},
                            "duration": {"type": "number"},
                        },
                        "required": ["name", "dosage", "frequency", "duration"],
                    },
                },
                "required": ["name", "dosage", "frequency", "duration", "confidence", "confidences"],
            },
        },
        "confidences": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "patient_name": {"type": "number"},
                "patient_age": {"type": "number"},
                "date": {"type": "number"},
                "doctor_name": {"type": "number"},
                "diagnosis": {"type": "number"},
                "notes": {"type": "number"},
                "medicines": {"type": "number"},
            },
            "required": ["patient_name", "patient_age", "date", "doctor_name", "diagnosis", "notes", "medicines"],
        },
    },
    "required": [
        "patient_name",
        "patient_age",
        "date",
        "doctor_name",
        "diagnosis",
        "notes",
        "medicines",
        "confidences",
    ],
}


@lru_cache(maxsize=1)
def load_llm_pipeline() -> Any:
    """Load the local language pipeline used for entity extraction."""
    try:
        import spacy

        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model en_core_web_sm not installed; using blank English pipeline.")
            return spacy.blank("en")
    except ImportError:
        logger.warning("spaCy is not installed; language-model fallback is disabled.")
        return None


def extract_person_entities(text: str, llm: Any | None = None) -> list[tuple[str, int, int]]:
    """Extract person entities from text using the configured language pipeline."""
    pipeline = llm if llm is not None else load_llm_pipeline()
    if pipeline is None:
        return []

    doc = pipeline(text[:500])
    return [
        (entity.text, entity.start_char, entity.end_char)
        for entity in getattr(doc, "ents", [])
        if entity.label_ == "PERSON"
    ]


def should_use_openai(config: dict[str, Any] | None) -> bool:
    """Return whether LLM extraction is enabled by config and environment."""
    llm_config = (config or {}).get("llm", {})
    provider = str(llm_config.get("provider", "local")).lower()
    
    if provider == "local":
        return False
    elif provider == "ollama":
        return True  # Ollama is local, doesn't need an API key check
        
    api_key_env = str(llm_config.get("api_key_env", "OPENAI_API_KEY"))
    return provider in {"openai", "nvidia"} and (bool(os.getenv(api_key_env)) or bool(llm_config.get("api_key")))


def validate_and_repair_json(content: str, schema: dict[str, Any]) -> dict[str, Any] | None:
    """Attempt to parse content as JSON, extract it from markdown code blocks, and validate/repair it."""
    content = content.strip()
    if content.startswith("```json"):
        content = content.split("```json")[1].split("```")[0].strip()
    elif content.startswith("```"):
        content = content.split("```")[1].split("```")[0].strip()
    
    try:
        data = json.loads(content)
    except Exception as exc:
        logger.warning("JSON parsing failed: %s", exc)
        return None

    if not isinstance(data, dict):
        return None

    # Make sure required root keys exist
    for key in schema.get("required", []):
        if key not in data:
            data[key] = None if schema["properties"][key]["type"] != "array" else []

    # Clean medicines
    if "medicines" in data and isinstance(data["medicines"], list):
        cleaned_meds = []
        for med in data["medicines"]:
            if not isinstance(med, dict):
                continue
            # Ensure required keys exist
            for sub_key in ["name", "dosage", "frequency", "duration"]:
                if sub_key not in med:
                    med[sub_key] = None
            if "confidence" not in med:
                med["confidence"] = 1.0
            if "confidences" not in med or not isinstance(med["confidences"], dict):
                med["confidences"] = {"name": 1.0, "dosage": 1.0, "frequency": 1.0, "duration": 1.0}
            cleaned_meds.append(med)
        data["medicines"] = cleaned_meds
    else:
        data["medicines"] = []

    # Ensure root confidences
    if "confidences" not in data or not isinstance(data["confidences"], dict):
        data["confidences"] = {
            "patient_name": 1.0,
            "patient_age": 1.0,
            "date": 1.0,
            "doctor_name": 1.0,
            "diagnosis": 1.0,
            "notes": 1.0,
            "medicines": 1.0
        }
    else:
        for key in ["patient_name", "patient_age", "date", "doctor_name", "diagnosis", "notes", "medicines"]:
            if key not in data["confidences"]:
                data["confidences"][key] = 1.0

    return data


def extract_prescription_with_openai(
    raw_text: str,
    baseline: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract prescription fields with OpenAI, NVIDIA NIM, or Ollama API.

    Returns None when LLM is not configured or the request fails, allowing
    callers to keep using deterministic local extraction as a fallback.
    """
    llm_config = (config or {}).get("llm", {})
    provider = str(llm_config.get("provider", "local")).lower()
    
    # Determine URL and Headers
    if provider == "openai":
        api_key = llm_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        model = str(llm_config.get("model", "gpt-4o-mini"))
    elif provider == "nvidia":
        api_key = llm_config.get("api_key") or os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return None
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        model = str(llm_config.get("model", "meta/llama-3.1-70b-instruct"))
    elif provider == "ollama":
        api_url = str(llm_config.get("api_url", "http://localhost:11434/v1")).rstrip("/")
        url = f"{api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        model = str(llm_config.get("model", "llama3.2"))
    else:
        return None

    timeout_seconds = float(llm_config.get("timeout_seconds", 25))
    max_chars = int(llm_config.get("max_input_chars", 6000))
    temperature = float(llm_config.get("temperature", 0.1))

    clinical_context = llm_config.get("clinical_context")
    context_str = (
        f"Clinical Context / Patient Symptoms:\n{clinical_context}\n"
        "Use this context to resolve poor handwriting or ambiguous characters.\n\n"
        if clinical_context else ""
    )

    system_prompt = (
        "You are an expert clinical data extraction assistant. "
        "Your task is to extract medical prescription OCR into strict JSON matching this schema:\n"
        f"{json.dumps(PRESCRIPTION_SCHEMA, indent=2)}\n"
        "Do not invent patient, doctor, or medicine details. Use null if a value is completely missing. "
        "Format frequencies to readable terms (e.g. 'Once daily' instead of 'qd')."
    )

    user_prompt = (
        "Extract prescription fields from OCR text.\n\n"
        f"{context_str}"
        f"Baseline JSON:\n{json.dumps(baseline, ensure_ascii=True)}\n\n"
        f"OCR text:\n{raw_text[:max_chars]}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }

    if provider == "openai":
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "prescription_fields",
                "strict": True,
                "schema": PRESCRIPTION_SCHEMA
            }
        }
    elif provider == "ollama":
        payload["format"] = "json"

    # Retry loop with self-correction
    last_error = ""
    for attempt in range(2):
        if attempt > 0:
            logger.info("Retrying LLM extraction call (attempt %d/2) with correction...", attempt + 1)
            payload["messages"].append({"role": "assistant", "content": last_error})
            payload["messages"].append({
                "role": "user", 
                "content": f"The previous response failed schema validation. Please output the valid JSON matching the schema correctly. Error: {last_error}"
            })

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            res_json = response.json()
            content = res_json["choices"][0]["message"]["content"]
            
            parsed = validate_and_repair_json(content, PRESCRIPTION_SCHEMA)
            if parsed:
                return parsed
            
            last_error = "Invalid JSON structure or schema properties mismatch."
        except Exception as exc:
            logger.warning("LLM call attempt %d failed: %s", attempt + 1, exc)
            last_error = str(exc)

    return None


def extract_prescription_with_vision(
    image_base64: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Extract prescription fields directly from a base64-encoded image using a Multimodal VLM."""
    llm_config = (config or {}).get("llm", {})
    provider = str(llm_config.get("provider", "local")).lower()

    if provider == "openai":
        api_key = llm_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        model = str(llm_config.get("model", "gpt-4o-mini"))
    elif provider == "ollama":
        api_url = str(llm_config.get("api_url", "http://localhost:11434/v1")).rstrip("/")
        url = f"{api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        model = str(llm_config.get("model", "llama3.2-vision"))
    else:
        logger.warning("Vision mode is only supported for 'openai' and 'ollama' providers.")
        return None

    timeout_seconds = float(llm_config.get("timeout_seconds", 35))
    temperature = float(llm_config.get("temperature", 0.1))

    # Format base64 properly
    if not image_base64.startswith("data:"):
        image_base64 = f"data:image/jpeg;base64,{image_base64}"

    clinical_context = llm_config.get("clinical_context")
    context_str = (
        f"Clinical Context / Patient Symptoms:\n{clinical_context}\n"
        "Use this context to help read and verify the medications written on the prescription.\n\n"
        if clinical_context else ""
    )

    system_prompt = (
        "You are an expert clinical OCR and data extraction system. "
        "Your task is to read the uploaded prescription image and extract its text into a strict JSON matching this schema:\n"
        f"{json.dumps(PRESCRIPTION_SCHEMA, indent=2)}\n"
        "Read patient name, age, date, physician, and all medicines (name, dosage, frequency, duration). "
        "Use null if a value is completely missing. For confidences values, rate them between 0.0 and 1.0. "
        "Return ONLY the strict JSON output."
    )

    user_content = [
        {
            "type": "text",
            "text": (
                "Extract all structured prescription fields directly from this prescription image.\n\n"
                f"{context_str}"
            )
        },
        {
            "type": "image_url",
            "image_url": {
                "url": image_base64
            }
        }
    ]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": temperature
    }

    if provider == "openai":
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "prescription_fields",
                "strict": True,
                "schema": PRESCRIPTION_SCHEMA
            }
        }
    elif provider == "ollama":
        payload["format"] = "json"

    # Retry loop with self-correction
    last_error = ""
    for attempt in range(2):
        if attempt > 0:
            logger.info("Retrying VLM extraction call (attempt %d/2)...", attempt + 1)
            payload["messages"].append({"role": "assistant", "content": last_error})
            payload["messages"].append({
                "role": "user", 
                "content": f"The previous response failed schema validation. Please output the valid JSON matching the schema correctly. Error: {last_error}"
            })

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            res_json = response.json()
            content = res_json["choices"][0]["message"]["content"]
            
            parsed = validate_and_repair_json(content, PRESCRIPTION_SCHEMA)
            if parsed:
                return parsed
            
            last_error = "Invalid JSON structure or schema properties mismatch."
        except Exception as exc:
            logger.warning("VLM call attempt %d failed: %s", attempt + 1, exc)
            last_error = str(exc)

    return None


def _extract_response_text(response_json: dict[str, Any]) -> str:
    """Get text content from a Responses API result."""
    if isinstance(response_json.get("output_text"), str):
        return response_json["output_text"]

    for item in response_json.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("Responses API result did not include text output")
