import uuid
import os
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from typing import Optional
from pathlib import Path

try:
    from app.services.prescription_service import prescription_service
    from app.schemas.prescription_schema import PrescriptionAnalysisRequest, PrescriptionAnalysisResponse
    from services.mongo_service import mongo_service
except (ImportError, ModuleNotFoundError):
    from backend.app.services.prescription_service import prescription_service
    from backend.app.schemas.prescription_schema import PrescriptionAnalysisRequest, PrescriptionAnalysisResponse
    from services.mongo_service import mongo_service

router = APIRouter(prefix="/api/prescriptions", tags=["Prescription Analysis"])
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BACKEND_DIR / "uploads" / "prescriptions"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/analyze", response_model=PrescriptionAnalysisResponse)
async def analyze_prescription(
    request: Request,
    file: Optional[UploadFile] = File(None),
    patient_id: Optional[str] = Form("guest_patient_001")
):
    """
    Analyzes prescription text, clinical notes, or uploaded prescription document images (PNG, JPG)
    to extract medications, dosages, contraindications, and clinical safety alerts.
    """
    input_text = ""
    filename = ""
    patientId = patient_id or "guest_patient_001"

    # Check for direct file upload parameter
    if file and file.filename:
        filename = file.filename
        content = await file.read()
        saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{filename}"
        with open(saved_path, "wb") as f:
            f.write(content)
        input_text = prescription_service.extract_text_from_prescription_image(str(saved_path))
    else:
        # Check form data or json body
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            try:
                form = await request.form()
                form_file = form.get("file") or form.get("prescription")
                if form_file and hasattr(form_file, "filename") and form_file.filename:
                    filename = form_file.filename
                    content = await form_file.read()
                    saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{filename}"
                    with open(saved_path, "wb") as f:
                        f.write(content)
                    input_text = prescription_service.extract_text_from_prescription_image(str(saved_path))
                else:
                    input_text = str(form.get("text", "") or form.get("prescription_text", ""))
                    patientId = str(form.get("patient_id") or form.get("patientId") or patientId)
            except Exception as e:
                print(f"[PrescriptionRouter] Form parse error: {e}")
        elif "application/json" in content_type:
            try:
                body = await request.json()
                input_text = body.get("text", "")
                patientId = body.get("patient_id") or body.get("patientId") or patientId
            except Exception:
                input_text = ""
        else:
            try:
                raw_bytes = await request.body()
                input_text = raw_bytes.decode("utf-8", errors="ignore")
            except Exception:
                input_text = ""

    if not input_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Prescription text or image file must be provided. Please upload a prescription image or provide prescription notes."
        )

    try:
        result = prescription_service.analyze_prescription_text(input_text)
        rx_id = f"rx_{uuid.uuid4().hex[:10]}"
        result["prescription_id"] = rx_id
        result["analysis_id"] = rx_id
        result["medications"] = result.get("detected_medications", [])
        result["patient_id"] = patientId
        result["report_title"] = "Clinical Prescription Analysis Report"
        result["modality"] = "prescription_doc"
        result["status"] = "success"

        # Persist to MongoDB
        mongo_service.save_prescription_record(
            prescription_id=rx_id,
            patient_id=patientId,
            raw_text=input_text,
            extracted_medications=result.get("detected_medications", []),
            clinical_warnings=result.get("clinical_warnings", []),
            doctor_guidance=result.get("doctor_guidance", []),
            filename=filename
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prescription analysis error: {str(e)}")


@router.get("/sample", response_model=PrescriptionAnalysisResponse)
async def get_sample_prescription():
    """
    Returns an analyzed clinical respiratory sample prescription.
    """
    sample_text = (
        "Patient presents with fever of 38.9C, productive cough with purulent sputum, and right lower lobe crackles. "
        "Chest X-Ray shows right lower lobe consolidation consistent with bacterial community-acquired pneumonia. "
        "Rx:\n"
        "1. Amoxicillin 500mg TID for 7 days.\n"
        "2. Azithromycin 250mg once daily for 5 days.\n"
        "3. Paracetamol 650mg as needed for fever and pleuritic discomfort.\n"
        "4. Albuterol inhaler 2 puffs every 6 hours PRN.\n"
        "Patient notes mild past stomach sensitivity with NSAIDs."
    )
    return prescription_service.analyze_prescription_text(sample_text)
