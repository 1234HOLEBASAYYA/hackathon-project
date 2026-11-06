"""FastAPI Backend Application for Standalone AI Prescription Reader."""

from __future__ import annotations

import logging
import os
import shutil
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
import torch
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

from ai.extractor import parse_prescription
from ai.ocr_engine import run_ai_ocr
from ai.pdf_processor import convert_pdf_to_images, save_first_page_preview
from ai.preprocessor import enhance_for_ocr
from backend.export import generate_prescription_csv, generate_prescription_pdf
from backend.schemas import (
    AnalyzeRequest,
    BoundingBoxSchema,
    DoctorSchema,
    HealthResponse,
    ImageQualitySchema,
    MedicineSchema,
    PatientSchema,
    PrescriptionResultSchema,
    UpdateResultRequest,
    UploadResponse,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for active sessions / analysis results
PRESCRIPTION_STORE: dict[str, dict[str, Any]] = {}
FILE_METADATA_STORE: dict[str, dict[str, Any]] = {}

# Maximum upload size: 15 MB
MAX_UPLOAD_SIZE = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


def cleanup_expired_files(max_age_seconds: int = 7200) -> None:
    """Clean up uploaded and exported files older than max_age_seconds (default 2 hours)."""
    now = time.time()
    for directory in (UPLOADS_DIR, EXPORTS_DIR):
        if not directory.exists():
            continue
        for file_path in directory.glob("*"):
            try:
                if file_path.is_file() and (now - file_path.stat().st_mtime) > max_age_seconds:
                    file_path.unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("Could not delete %s during cleanup: %s", file_path, exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_expired_files()
    gpu_status = f"CUDA ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else "CPU"
    logger.info("Prescription Reader API started successfully. Device: %s", gpu_status)
    yield


app = FastAPI(
    title="AI Prescription Reader API",
    description="Standalone AI-powered OCR and structured medicine extraction backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Check API status and inference hardware availability."""
    cuda_ok = torch.cuda.is_available()
    device_name = "cuda" if cuda_ok else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if cuda_ok else None

    return HealthResponse(
        status="ok",
        version="1.0.0",
        device=device_name,
        gpu_name=gpu_name,
        ocr_engine="EasyOCR (Deep Learning CRAFT + BiLSTM, GPU-accelerated)",
        supported_formats=["jpg", "jpeg", "png", "pdf"],
    )


@app.get("/api/samples", tags=["Prescription"])
async def get_sample_prescriptions():
    """Return available sample prescriptions for quick testing."""
    return {
        "samples": [
            {"id": "printed_multimed", "name": "Apollo Hospitals Printed Prescription", "type": "printed"},
            {"id": "actual_handwritten", "name": "City Care Clinic Handwritten Prescription", "type": "handwritten"},
            {"id": "handwritten_cursive", "name": "Dr. Watson Handwritten Script", "type": "handwritten"},
            {"id": "sample_pdf", "name": "City General Hospital Scanned PDF", "type": "pdf"},
        ]
    }


@app.post("/api/prescription/upload", response_model=UploadResponse, tags=["Prescription"])
async def upload_prescription(file: UploadFile = File(...)) -> UploadResponse:
    """Upload prescription image or PDF, validate format and size, and create preview."""
    cleanup_expired_files()

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided in upload")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {sorted(list(ALLOWED_EXTENSIONS))}",
        )

    # Read content and validate size
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes)")
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
        )

    prescription_id = str(uuid4())
    stored_filename = f"{prescription_id}{ext}"
    stored_path = UPLOADS_DIR / stored_filename

    # Save uploaded file
    with open(stored_path, "wb") as f:
        f.write(content)

    # Generate preview image if PDF or save preview for images
    preview_filename = f"{prescription_id}_preview.png"
    preview_path = UPLOADS_DIR / preview_filename

    if ext == ".pdf":
        try:
            save_first_page_preview(stored_path, preview_path, dpi=150)
        except Exception as exc:
            stored_path.unlink(missing_ok=True)
            logger.error("Failed to parse PDF: %s", exc)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid or corrupted PDF file: {exc}")
    else:
        try:
            with Image.open(stored_path) as img:
                img.verify()
            shutil.copyfile(stored_path, preview_path)
        except Exception as exc:
            stored_path.unlink(missing_ok=True)
            logger.error("Invalid image uploaded: %s", exc)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupted or invalid image file")

    FILE_METADATA_STORE[prescription_id] = {
        "id": prescription_id,
        "original_filename": file.filename,
        "stored_path": str(stored_path),
        "preview_path": str(preview_path),
        "ext": ext,
        "size_bytes": len(content),
        "uploaded_at": datetime.now().isoformat(),
    }

    return UploadResponse(
        id=prescription_id,
        filename=file.filename,
        file_type=ext.replace(".", "").upper(),
        size_bytes=len(content),
        preview_url=f"/api/prescription/image/{prescription_id}",
        message="Prescription uploaded successfully and verified.",
    )


@app.get("/api/prescription/image/{id}", tags=["Prescription"])
async def get_prescription_image(id: str) -> FileResponse:
    """Retrieve the preview image for an uploaded prescription."""
    meta = FILE_METADATA_STORE.get(id)
    if not meta:
        preview_path = UPLOADS_DIR / f"{id}_preview.png"
        if preview_path.exists():
            return FileResponse(preview_path, media_type="image/png")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription image not found")

    preview_path = Path(meta["preview_path"])
    if not preview_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription preview image not found")

    return FileResponse(preview_path, media_type="image/png")


@app.post("/api/prescription/analyze", response_model=PrescriptionResultSchema, tags=["Prescription"])
async def analyze_prescription(payload: AnalyzeRequest) -> PrescriptionResultSchema:
    """Run computer vision preprocessing, AI OCR, and structured medicine extraction."""
    prescription_id = payload.id
    meta = FILE_METADATA_STORE.get(prescription_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription ID not found. Upload file first.")

    stored_path = Path(meta["stored_path"])
    if not stored_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription file is no longer on server")

    # Load image (if PDF, use rendered 300 DPI image)
    if meta["ext"] == ".pdf":
        images = convert_pdf_to_images(stored_path, dpi=300, max_pages=1)
        if not images:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not render PDF pages")
        img_bgr = cv2.cvtColor(images[0], cv2.COLOR_RGB2BGR)
    else:
        img_bgr = cv2.imread(str(stored_path))
        if img_bgr is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to read image file")

    # 1. OpenCV Preprocessing & Quality assessment
    prep_result = enhance_for_ocr(
        image_input=img_bgr,
        target_width=1800,
        apply_clahe=payload.apply_clahe,
        apply_deskew=payload.apply_deskew,
    )
    quality = prep_result["quality"]

    extraction = None
    engine_used = "EasyOCR (CRAFT + BiLSTM)"
    boxes_dicts = []

    # 2. Layer 1: Gemini 3.5 Multimodal Clinical Vision
    try:
        from ai.gemini_prescription_service import analyze_prescription_with_gemini
        gemini_result = analyze_prescription_with_gemini(stored_path)
        if gemini_result and gemini_result.get("medicines"):
            extraction = gemini_result
            engine_used = gemini_result.get("engine_used", "Gemini 3.5 Flash Multimodal Vision")
            logger.info("[analyze_prescription] Extracted %d medications via Gemini Multimodal Vision.", len(gemini_result["medicines"]))
    except Exception as exc:
        logger.warning("[analyze_prescription] Gemini multimodal error: %s. Using local EasyOCR fallback.", exc)

    # 3. Layer 2: Local AI Deep Learning OCR fallback
    if not extraction:
        logger.info("[analyze_prescription] Falling back to local EasyOCR + NLP Grammar Parser.")
        ocr_result = run_ai_ocr(
            image=prep_result["processed_image"],
            prefer_gpu=payload.use_gpu,
        )
        boxes_dicts = [dict(b) for b in ocr_result["bounding_boxes"]]
        extraction = parse_prescription(ocr_result["raw_text"], boxes_dicts)
        engine_used = ocr_result.get("engine_used", engine_used)

    now_iso = datetime.now().isoformat()
    result_data: dict[str, Any] = {
        "id": prescription_id,
        "filename": meta["original_filename"],
        "preview_url": f"/api/prescription/image/{prescription_id}",
        "clinic_header": extraction["clinic_header"],
        "doctor": extraction["doctor"],
        "patient": extraction["patient"],
        "diagnosis": extraction["diagnosis"],
        "advice": extraction["advice"],
        "follow_up": extraction["follow_up"],
        "medicines": extraction["medicines"],
        "raw_text": extraction["raw_text"],
        "quality": quality,
        "bounding_boxes": boxes_dicts,
        "is_verified": False,
        "notes": extraction.get("notes", []),
        "engine_used": engine_used,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    # Store result in memory
    PRESCRIPTION_STORE[prescription_id] = result_data

    return PrescriptionResultSchema(
        id=prescription_id,
        filename=meta["original_filename"],
        preview_url=f"/api/prescription/image/{prescription_id}",
        clinic_header=extraction["clinic_header"],
        doctor=DoctorSchema(**extraction["doctor"]),
        patient=PatientSchema(**extraction["patient"]),
        diagnosis=extraction["diagnosis"],
        advice=extraction["advice"],
        follow_up=extraction["follow_up"],
        medicines=[MedicineSchema(**m) for m in extraction["medicines"]],
        raw_text=extraction["raw_text"],
        quality=ImageQualitySchema(**quality),
        bounding_boxes=[BoundingBoxSchema(**b) for b in boxes_dicts],
        is_verified=False,
        notes=extraction.get("notes", []),
        engine_used=engine_used,
        created_at=now_iso,
        updated_at=now_iso,
    )


@app.get("/api/prescription/result/{id}", response_model=PrescriptionResultSchema, tags=["Prescription"])
async def get_prescription_result(id: str) -> PrescriptionResultSchema:
    """Retrieve current extraction results for a prescription ID."""
    result = PRESCRIPTION_STORE.get(id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription result not found")

    return PrescriptionResultSchema(
        id=result["id"],
        filename=result["filename"],
        preview_url=result["preview_url"],
        clinic_header=result.get("clinic_header", "Not detected"),
        doctor=DoctorSchema(**result["doctor"]),
        patient=PatientSchema(**result["patient"]),
        diagnosis=result.get("diagnosis", "Not detected"),
        advice=result.get("advice", "Not detected"),
        follow_up=result.get("follow_up", "Not detected"),
        medicines=[MedicineSchema(**m) for m in result["medicines"]],
        raw_text=result["raw_text"],
        quality=ImageQualitySchema(**result["quality"]) if result.get("quality") else None,
        bounding_boxes=[BoundingBoxSchema(**b) for b in result.get("bounding_boxes", [])],
        is_verified=result["is_verified"],
        notes=result.get("notes", []),
        engine_used=result.get("engine_used", "EasyOCR"),
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@app.put("/api/prescription/result/{id}", response_model=PrescriptionResultSchema, tags=["Prescription"])
async def update_prescription_result(id: str, payload: UpdateResultRequest) -> PrescriptionResultSchema:
    """Update prescription fields, correct medicines or dosage, and toggle verification state."""
    result = PRESCRIPTION_STORE.get(id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription result not found")

    if payload.clinic_header is not None:
        result["clinic_header"] = payload.clinic_header
    if payload.doctor is not None:
        result["doctor"] = payload.doctor.model_dump()
    if payload.patient is not None:
        result["patient"] = payload.patient.model_dump()
    if payload.diagnosis is not None:
        result["diagnosis"] = payload.diagnosis
    if payload.advice is not None:
        result["advice"] = payload.advice
    if payload.follow_up is not None:
        result["follow_up"] = payload.follow_up
    if payload.medicines is not None:
        result["medicines"] = [m.model_dump() for m in payload.medicines]
    if payload.raw_text is not None:
        result["raw_text"] = payload.raw_text
    if payload.is_verified is not None:
        result["is_verified"] = payload.is_verified
    if payload.notes is not None:
        result["notes"] = payload.notes

    result["updated_at"] = datetime.now().isoformat()
    PRESCRIPTION_STORE[id] = result

    return PrescriptionResultSchema(
        id=result["id"],
        filename=result["filename"],
        preview_url=result["preview_url"],
        clinic_header=result.get("clinic_header", "Not detected"),
        doctor=DoctorSchema(**result["doctor"]),
        patient=PatientSchema(**result["patient"]),
        diagnosis=result.get("diagnosis", "Not detected"),
        advice=result.get("advice", "Not detected"),
        follow_up=result.get("follow_up", "Not detected"),
        medicines=[MedicineSchema(**m) for m in result["medicines"]],
        raw_text=result["raw_text"],
        quality=ImageQualitySchema(**result["quality"]) if result.get("quality") else None,
        bounding_boxes=[BoundingBoxSchema(**b) for b in result.get("bounding_boxes", [])],
        is_verified=result["is_verified"],
        notes=result.get("notes", []),
        engine_used=result.get("engine_used", "EasyOCR"),
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@app.get("/api/prescription/export/{id}", tags=["Prescription"])
async def export_prescription(id: str, format: str = Query("pdf", pattern="^(pdf|csv)$")) -> Response:
    """Download verified extraction results as a clean PDF or CSV report."""
    result = PRESCRIPTION_STORE.get(id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription result not found")

    safe_name = Path(result["filename"]).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "csv":
        csv_content = generate_prescription_csv(result)
        download_name = f"prescription_{safe_name}_{timestamp}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )
    else:
        pdf_path = EXPORTS_DIR / f"prescription_{id}_{timestamp}.pdf"
        generate_prescription_pdf(result, pdf_path)
        download_name = f"prescription_{safe_name}_{timestamp}.pdf"
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=download_name,
        )


# Mount frontend build directory if it exists
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
