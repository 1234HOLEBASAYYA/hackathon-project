"""FastAPI application for prescription OCR."""


import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import io
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
import numpy as np
import json
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, Request, Response, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.extractor import extract_prescription_fields
from src.ocr_engine import OCRPipeline
from src.preprocessor import preprocess_array
from src.validator import validate_medicines

from src.auth_routes import router as auth_router, get_current_user
from src.db import get_extractions_collection


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Doctor Prescription OCR API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

BATCH_RESULTS: dict[str, dict[str, Any]] = {}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load YAML configuration.

    Args:
        config_path: Optional config path.

    Returns:
        Parsed configuration dictionary.
    """
    path = config_path or Path.cwd() / "config.yaml"
    if not path.exists():
        logger.warning("Config file not found at %s; using defaults.", path)
        return {}
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML is not installed; using default configuration.")
        return {}
    with path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    return loaded if isinstance(loaded, dict) else {}


def merge_settings(config: dict[str, Any], settings_str: str | None) -> dict[str, Any]:
    """Merge custom settings JSON into the configuration dictionary."""
    if not settings_str:
        return config
    try:
        custom_settings = json.loads(settings_str)
        if isinstance(custom_settings, dict):
            for key, val in custom_settings.items():
                if isinstance(val, dict) and key in config and isinstance(config[key], dict):
                    config[key].update(val)
                else:
                    config[key] = val
    except Exception as exc:
        logger.warning("Failed to parse custom settings: %s", exc)
    return config


def get_rate_limit() -> str:
    """Get rate limit string from configuration.

    Returns:
        Rate limit string (e.g. "20/minute").
    """
    config = load_config()
    limit = config.get("api", {}).get("rate_limit_per_minute", 20)
    return f"{limit}/minute"


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add a unique request ID (UUID) to request state and response headers.

    Args:
        request: Request object.
        call_next: Next request handler in pipeline.

    Returns:
        Response object with X-Request-ID header.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def extension_for_upload(upload: UploadFile) -> str:
    """Get normalized file extension from an upload.

    Args:
        upload: Uploaded file.

    Returns:
        Lowercase extension without dot.
    """
    return Path(upload.filename or "").suffix.lower().lstrip(".")


def validate_upload_metadata(upload: UploadFile, config: dict[str, Any]) -> None:
    """Validate upload filename and extension.

    Args:
        upload: Uploaded file.
        config: Application configuration.

    Raises:
        HTTPException: If the extension is not allowed.
    """
    allowed = {str(value).lower() for value in config.get("api", {}).get("allowed_formats", ["jpg", "png", "pdf"])}
    extension = extension_for_upload(upload)
    normalized = "jpg" if extension == "jpeg" else extension
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {extension}")


async def read_limited_upload(upload: UploadFile, max_size_mb: int) -> bytes:
    """Read an upload while enforcing maximum size.

    Args:
        upload: Uploaded file.
        max_size_mb: Maximum accepted file size in megabytes.

    Returns:
        Uploaded bytes.

    Raises:
        HTTPException: If the file exceeds the configured size.
    """
    max_bytes = max_size_mb * 1024 * 1024
    content = await upload.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {max_size_mb} MB limit")
    return content


def decode_image(content: bytes, extension: str) -> np.ndarray:
    """Decode uploaded bytes into an OpenCV image, handling EXIF orientation.

    Args:
        content: Uploaded file bytes.
        extension: File extension without dot.

    Returns:
        Decoded BGR image.

    Raises:
        HTTPException: If decoding fails or image is completely black.
    """
    if extension == "pdf":
        return decode_pdf_first_page(content)

    try:
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(content)) as pil_img:
            temp_arr = np.array(pil_img)
            if temp_arr.size > 0 and np.all(temp_arr == 0):
                raise HTTPException(status_code=400, detail="Uploaded image is completely black")
            corrected_pil = ImageOps.exif_transpose(pil_img)
            rgb = np.array(corrected_pil.convert("RGB"))
            image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Pillow decoding or EXIF transposition failed: %s, trying OpenCV", exc)
        buffer = np.frombuffer(content, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode uploaded image")
        if np.all(image == 0):
            raise HTTPException(status_code=400, detail="Uploaded image is completely black")

    return image


def decode_pdf_first_page(content: bytes) -> np.ndarray:
    """Decode the first page of a PDF into an OpenCV image.

    Args:
        content: PDF bytes.

    Returns:
        First page as a BGR image.

    Raises:
        HTTPException: If PDF conversion is unavailable or fails.
    """
    try:
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="PDF support requires pdf2image") from exc

    try:
        pages = convert_from_bytes(content, first_page=1, last_page=1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not decode PDF") from exc
    if not pages:
        raise HTTPException(status_code=400, detail="PDF contains no pages")
    rgb = np.array(pages[0].convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _get_dpi(content: bytes, extension: str) -> float | None:
    """Extract DPI from image or PDF bytes if available.

    Args:
        content: Uploaded file bytes.
        extension: File extension.

    Returns:
        Estimated or actual DPI, or None.
    """
    if extension == "pdf":
        return 200.0
    try:
        from PIL import Image
        with Image.open(io.BytesIO(content)) as img:
            dpi_tuple = img.info.get("dpi")
            if dpi_tuple:
                return float(dpi_tuple[0])
    except Exception:
        pass
    return None


def process_image_array(image: np.ndarray, config: dict[str, Any], dpi: float | None = None) -> dict[str, Any]:
    """Run preprocessing, OCR, extraction, and validation.

    Args:
        image: Input BGR image.
        config: Application config.
        dpi: Optional resolution DPI.

    Returns:
        Full OCR response.
    """
    llm_config = config.get("llm", {})
    if llm_config.get("enabled") and llm_config.get("mode") == "direct_vision":
        import base64
        try:
            from src.llm import extract_prescription_with_vision
            logger.info("Executing direct Vision LLM prescription extraction from image array...")
            _, buffer = cv2.imencode(".jpg", image)
            content_base64 = base64.b64encode(buffer).decode("utf-8")
            
            vlm_result = extract_prescription_with_vision(content_base64, config)
            if vlm_result:
                medicine_names = [med["name"] for med in vlm_result.get("medicines", []) if med.get("name")]
                validation = validate_medicines(medicine_names)
                
                processed_image_url = f"data:image/jpeg;base64,{content_base64}"
                return {
                    "extracted_fields": vlm_result,
                    "ocr": {
                        "raw_text": vlm_result.get("notes", "") or "Vision extraction bypassed raw text.",
                        "confidence": vlm_result.get("confidences", {}).get("medicines", 1.0) * 100,
                        "engine_used": f"VLM ({llm_config.get('provider', 'openai')}: {llm_config.get('model')})",
                        "word_boxes": []
                    },
                    "preprocessing": {
                        "original_shape": list(image.shape[:2]),
                        "processed_shape": list(image.shape[:2]),
                        "processed_image_url": processed_image_url,
                        "confidence": 100.0,
                        "clahe_applied": False,
                        "denoise_applied": False,
                        "deskew_applied": False,
                        "adaptive_threshold_applied": False,
                        "morphology_applied": False
                    },
                    "medicine_validation": validation,
                    "confidence": {
                        "ocr": vlm_result.get("confidences", {}).get("medicines", 1.0) * 100,
                        "preprocessing": 100.0
                    }
                }
            else:
                logger.warning("Direct Vision LLM extraction returned None. Falling back to OCR pipeline...")
        except Exception as exc:
            logger.exception("Direct Vision LLM extraction failed: %s. Falling back to OCR pipeline...", exc)

    preprocessed = preprocess_array(image, config)
    ocr_result = OCRPipeline(config).recognize(preprocessed["image"], dpi=dpi)
    extracted = extract_prescription_fields(ocr_result["raw_text"], config)
    medicine_names = [medicine["name"] for medicine in extracted["medicines"] if medicine["name"]]
    validation = validate_medicines(medicine_names)

    import base64
    try:
        _, buffer = cv2.imencode(".png", preprocessed["image"])
        processed_base64 = base64.b64encode(buffer).decode("utf-8")
        processed_image_url = f"data:image/png;base64,{processed_base64}"
    except Exception as exc:
        logger.warning("Failed to encode preprocessed image: %s", exc)
        processed_image_url = None

    return {
        "extracted_fields": extracted,
        "ocr": ocr_result,
        "preprocessing": {
            **preprocessed["metadata"],
            "processed_image_url": processed_image_url
        },
        "medicine_validation": validation,
        "confidence": {
            "ocr": ocr_result["confidence"],
            "preprocessing": preprocessed["metadata"]["confidence"],
        },
    }


async def process_upload(upload: UploadFile, config: dict[str, Any], request_id: str) -> dict[str, Any]:
    """Process a single uploaded prescription file.

    Args:
        upload: Uploaded image or PDF.
        config: Application config.
        request_id: Unique request ID.

    Returns:
        Full OCR response.
    """
    validate_upload_metadata(upload, config)
    max_size_mb = int(config.get("api", {}).get("max_file_size_mb", 10))
    content = await read_limited_upload(upload, max_size_mb)
    extension = extension_for_upload(upload)
    extension = "jpg" if extension == "jpeg" else extension
    image = decode_image(content, extension)

    dpi = _get_dpi(content, extension)

    return await asyncio.to_thread(process_image_array, image, config, dpi)


def process_batch_job(job_id: str, files: list[tuple[str, bytes]], config: dict[str, Any]) -> None:
    """Run a batch OCR job in the background.

    Args:
        job_id: Batch job identifier.
        files: File name and bytes pairs.
        config: Application config.
    """
    BATCH_RESULTS[job_id] = {"status": "processing", "results": []}
    results: list[dict[str, Any]] = []
    for filename, content in files:
        extension = Path(filename).suffix.lower().lstrip(".")
        extension = "jpg" if extension == "jpeg" else extension
        try:
            image = decode_image(content, extension)
            dpi = _get_dpi(content, extension)
                
            result = process_image_array(image, config, dpi)
            results.append({"filename": filename, "result": result})
        except Exception as exc:
            logger.exception("Batch file failed: %s", filename)
            results.append({"filename": filename, "error": str(exc)})
    BATCH_RESULTS[job_id] = {"status": "completed", "results": results}


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health.

    Returns:
        Health status payload.
    """
    return {"status": "ok"}


@app.post("/ocr")
@limiter.limit(get_rate_limit)
async def ocr_endpoint(
    request: Request,
    file: UploadFile = File(...),
    settings: str = Form(None),
    current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """OCR a single uploaded prescription.

    Args:
        request: FastAPI request object.
        file: Multipart image or PDF upload.
        settings: Optional JSON string of custom configuration parameters.
        current_user: Currently logged in user.

    Returns:
        Extracted prescription data with confidence metadata.
    """
    config = load_config()
    config = merge_settings(config, settings)
    try:
        result = await process_upload(file, config, request.state.request_id)
        result["request_id"] = request.state.request_id

        # Save result to extractions database collection
        try:
            extractions_col = get_extractions_collection()
            await extractions_col.insert_one({
                "user_id": current_user["_id"],
                "request_id": result["request_id"],
                "result": result
            })
        except Exception as db_exc:
            logger.exception("Failed to save extraction to MongoDB database: %s", db_exc)

        return result
    except HTTPException as exc:
        raise exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("OCR processing failed")
        raise HTTPException(status_code=500, detail=str(exc))



@app.post("/ocr/batch")
@limiter.limit(get_rate_limit)
async def ocr_batch_endpoint(
    request: Request,
    files: list[UploadFile] = File(...),
    settings: str = Form(None),
    current_user: dict = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """OCR a batch of uploaded prescriptions synchronously (up to 10).

    Args:
        request: FastAPI request object.
        files: Multipart image or PDF uploads.
        settings: Optional JSON string of custom configuration parameters.
        current_user: Currently logged in user.

    Returns:
        List of results with status, filename, data, and error.
    """
    config = load_config()
    config = merge_settings(config, settings)
    max_batch_size = int(config.get("api", {}).get("max_batch_size", 10))
    if len(files) > max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum limit of {max_batch_size} files"
        )

    results = []
    max_size_mb = int(config.get("api", {}).get("max_file_size_mb", 10))
    for upload in files:
        filename = upload.filename or "unknown"
        try:
            validate_upload_metadata(upload, config)
            content = await read_limited_upload(upload, max_size_mb)
            extension = extension_for_upload(upload)
            extension = "jpg" if extension == "jpeg" else extension
            image = decode_image(content, extension)
            
            dpi = _get_dpi(content, extension)

            data = await asyncio.to_thread(process_image_array, image, config, dpi)
            results.append({
                "filename": filename,
                "status": "success",
                "data": data,
                "error": None,
                "request_id": request.state.request_id
            })
        except Exception as exc:
            logger.exception("Failed to process batch image: %s", filename)
            results.append({
                "filename": filename,
                "status": "failed",
                "data": None,
                "error": str(exc),
                "request_id": request.state.request_id
            })

    return results


@app.post("/batch")
async def batch_endpoint(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    settings: str = Form(None),
    current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """Start a background batch OCR job.

    Args:
        background_tasks: FastAPI background task manager.
        files: Multipart uploads.
        settings: Optional JSON string of custom configuration parameters.
        current_user: Currently logged in user.

    Returns:
        Accepted job identifier.
    """
    config = load_config()
    config = merge_settings(config, settings)
    max_size_mb = int(config.get("api", {}).get("max_file_size_mb", 10))
    stored_files: list[tuple[str, bytes]] = []
    for upload in files:
        validate_upload_metadata(upload, config)
        content = await read_limited_upload(upload, max_size_mb)
        stored_files.append((upload.filename or f"{uuid4()}.bin", content))

    job_id = uuid4().hex
    BATCH_RESULTS[job_id] = {"status": "queued", "results": []}
    background_tasks.add_task(process_batch_job, job_id, stored_files, config)
    return {"job_id": job_id, "status": "queued"}


@app.get("/batch/{job_id}")
async def batch_status(job_id: str) -> dict[str, Any]:
    """Return batch job status.

    Args:
        job_id: Batch job identifier.

    Returns:
        Batch status and results if complete.

    Raises:
        HTTPException: If job id is unknown.
    """
    if job_id not in BATCH_RESULTS:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return BATCH_RESULTS[job_id]


@app.get("/history")
async def history_endpoint(current_user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Return the logged-in user's past extractions."""
    try:
        extractions_col = get_extractions_collection()
        cursor = extractions_col.find({"user_id": current_user["_id"]})
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as exc:
        logger.exception("Failed to retrieve history")
        raise HTTPException(status_code=500, detail=str(exc))


# Serve frontend build static files at root
frontend_dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist_path), html=True), name="frontend")
else:
    logger.warning("Frontend static build directory not found at %s. Serve it separately or build it using 'npm run build' inside 'frontend' directory.", frontend_dist_path)



