"""
FastAPI Router for MedVision-AI CT Scan Analysis and Reporting
Connects with Gemini 3.8 Flash Clinical Vision and ReportLab PDF Service.
"""

import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure root directory is accessible for services import
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.image_preprocessing import preprocess_ct_image, ImageValidationError, IncompatibleImageModalityError
from services.gemini_service import analyze_ct_scan_image, GeminiAnalysisError, GeminiConfigurationError, GeminiIncompatibleModalityError
from services.report_service import generate_pdf_report
from services.mongo_service import mongo_service

router = APIRouter(tags=["MedVision-AI CT Scan Analysis"])

UPLOAD_DIR = ROOT_DIR / "uploads"
REPORT_DIR = ROOT_DIR / "generated_reports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class GenerateReportRequest(BaseModel):
    report: Dict[str, Any]
    server_image_id: Optional[str] = None


@router.get("/api/health")
async def health_check():
    """System health check and Gemini configuration verification."""
    api_key_configured = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "YOUR_GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    return {
        "status": "healthy",
        "service": "MedVision-AI CT Scan Image Analyzer",
        "version": "2.0.0",
        "framework": "FastAPI",
        "gemini": {
            "api_key_configured": api_key_configured,
            "configured_model": model_name,
            "client_status": "ready" if api_key_configured else "unconfigured"
        }
    }


@router.post("/api/analyze")
async def analyze_ct_image(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form("guest_patient_001")
):
    """
    Accepts an uploaded CT scan image, performs validation and preprocessing,
    and returns a structured Gemini AI radiological decision support report.
    Rejects incompatible prescription documents and non-radiological images.
    Persists actual results to MongoDB with patientId.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No valid file uploaded.")

    patientId = patient_id or "guest_patient_001"
    filename = file.filename
    clean_stem = Path(filename).stem[:40]
    ext = Path(filename).suffix.lower()
    safe_filename = f"{uuid.uuid4().hex[:10]}_{clean_stem}{ext}"
    saved_path = UPLOAD_DIR / safe_filename

    try:
        # Save uploaded bytes
        content = await file.read()
        with open(saved_path, "wb") as f:
            f.write(content)

        # Preprocess image and enforce CT modality check
        prep_result = preprocess_ct_image(
            str(saved_path),
            output_dir=str(UPLOAD_DIR),
            enforce_ct_modality=True
        )
        dimensions_str = prep_result["original_dimensions"]["formatted"]

        # Run Gemini Vision Analysis
        analysis_report = analyze_ct_scan_image(
            image_input=prep_result["processed_path"],
            filename=filename,
            dimensions_str=dimensions_str
        )

        analysis_id = f"cxa_{uuid.uuid4().hex[:10]}"
        analysis_report["analysis_id"] = analysis_id
        analysis_report["patient_id"] = patientId
        analysis_report["modality"] = "ct_scan"
        analysis_report["status"] = "success"

        analysis_report["image_preprocessing"] = {
            "original_dimensions": prep_result["original_dimensions"],
            "processed_dimensions": prep_result["processed_dimensions"],
            "file_size": prep_result["file_size_formatted"],
            "server_image_id": safe_filename
        }

        # Save actual CT analysis result into MongoDB
        mongo_service.save_analysis_result(
            analysis_id=analysis_id,
            modality="ct_scan",
            report_title=analysis_report.get("report_title", "AI-Assisted CT Image Analysis Report"),
            model_name=analysis_report.get("model_used", "gemini-3.5-flash"),
            patient_id=patientId,
            primary_finding=(analysis_report.get("potential_findings") or [{}])[0],
            full_report=analysis_report,
            filename=filename
        )

        return {
            "status": "success",
            "data": analysis_report
        }

    except IncompatibleImageModalityError as ime:
        raise HTTPException(
            status_code=400,
            detail=ime.message
        )
    except GeminiIncompatibleModalityError as gme:
        raise HTTPException(
            status_code=400,
            detail=gme.message
        )
    except ImageValidationError as ive:
        raise HTTPException(status_code=400, detail=str(ive))
    except GeminiConfigurationError as gce:
        raise HTTPException(status_code=503, detail=str(gce))
    except GeminiAnalysisError as gae:
        raise HTTPException(status_code=gae.status_code, detail=gae.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during image analysis: {str(e)}")


@router.get("/api/records/{analysis_id}")
async def get_record_by_id(analysis_id: str):
    """Retrieves an analysis result directly from MongoDB by analysisId."""
    record = mongo_service.get_analysis_by_id(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found in MongoDB.")
    return {"status": "success", "record": record}


@router.get("/api/records/patient/{patient_id}")
async def get_records_for_patient(patient_id: str):
    """Retrieves all medical records for a specific patientId from MongoDB."""
    records = mongo_service.get_records_by_patient(patient_id)
    return {"status": "success", "patientId": patient_id, "count": len(records), "records": records}


@router.post("/api/generate-report")
async def generate_report_api(req: GenerateReportRequest):
    """Generates a downloadable ReportLab PDF medical report from structured JSON analysis."""
    report_data = req.report
    server_image_id = req.server_image_id or report_data.get("image_preprocessing", {}).get("server_image_id")

    image_path = None
    if server_image_id:
        candidate = UPLOAD_DIR / server_image_id
        if candidate.exists():
            image_path = str(candidate)

    try:
        pdf_path = generate_pdf_report(
            report_data=report_data,
            image_path=image_path,
            output_dir=str(REPORT_DIR)
        )
        pdf_filename = Path(pdf_path).name

        return {
            "status": "success",
            "filename": pdf_filename,
            "download_url": f"/api/reports/download/{pdf_filename}",
            "message": "PDF report generated successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/api/reports/download/{filename}")
async def download_report_api(filename: str):
    """Serves the generated PDF report for direct browser download."""
    safe_name = Path(filename).name
    report_file = REPORT_DIR / safe_name
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Requested report not found.")

    return FileResponse(
        path=str(report_file),
        media_type="application/pdf",
        filename=safe_name
    )


@router.get("/api/sample")
async def get_sample_image():
    """Serves a test medical scan for instant evaluation."""
    sample_path = ROOT_DIR / "dataset" / "chest_xray" / "test" / "PNEUMONIA" / "person1_virus_6.jpeg"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample dataset image not found.")
    return FileResponse(path=str(sample_path), media_type="image/jpeg")
