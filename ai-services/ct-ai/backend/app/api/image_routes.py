import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

try:
    from app.services.prediction_service import prediction_service
    from app.utils.file_utils import save_upload_file
    from app.schemas.image_schema import ImageAnalysisResponse
    from services.image_preprocessing import detect_image_modality
    from services.mongo_service import mongo_service
except (ImportError, ModuleNotFoundError):
    from backend.app.services.prediction_service import prediction_service
    from backend.app.utils.file_utils import save_upload_file
    from backend.app.schemas.image_schema import ImageAnalysisResponse
    from services.image_preprocessing import detect_image_modality
    from services.mongo_service import mongo_service

router = APIRouter(prefix="/api/images", tags=["Chest X-Ray Analysis"])

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DIR = BACKEND_DIR.parent
UPLOAD_DIR = BACKEND_DIR / "uploads" / "xray"
METRICS_PATH = BASE_DIR / "training" / "training_results" / "metrics.json"


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_chest_xray(
    file: UploadFile = File(...),
    generate_gradcam: bool = Form(True),
    alpha: float = Form(0.45),
    patient_id: Optional[str] = Form("guest_patient_001")
):
    """
    Upload a Chest X-Ray image (PNG, JPG) to perform deep abnormality detection
    and generate explainable Grad-CAM heatmap overlays.
    Rejects incompatible documents and prescriptions with a clear error.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    patientId = patient_id or "guest_patient_001"

    try:
        saved_path = save_upload_file(file, UPLOAD_DIR)

        # Modality check: verify this is not a prescription or non-radiological document
        with Image.open(saved_path) as check_img:
            mod_info = detect_image_modality(check_img, file.filename)
            if mod_info["modality"] == "prescription_doc":
                raise HTTPException(
                    status_code=400,
                    detail="not a proper image to scan"
                )

        result = prediction_service.predict(
            saved_path,
            generate_cam=generate_gradcam,
            cam_alpha=alpha
        )
        analysis_id = f"cxa_{uuid.uuid4().hex[:10]}"
        result["analysis_id"] = analysis_id
        result["patient_id"] = patientId
        result["report_title"] = "Chest Radiograph Abnormality Report"
        result["modality"] = "chest_xray"
        result["filename"] = file.filename
        result["timestamp"] = datetime.utcnow().isoformat()
        result["status"] = "success"

        # Save actual analysis result in MongoDB
        mongo_service.save_analysis_result(
            analysis_id=analysis_id,
            modality="chest_xray",
            report_title="Chest Radiograph Abnormality Report",
            model_name="ResNet-18 Deep Transfer Learning",
            patient_id=patientId,
            primary_finding={
                "label": result["prediction"],
                "confidence": result["confidence"],
                "severity": result["severity"],
                "description": result["clinical_finding"]
            },
            full_report=result,
            gradcam={"available": generate_gradcam, "opacity_score": result.get("gradcam", {}).get("opacity_score", 0.0)},
            filename=file.filename
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@router.get("/sample", response_model=ImageAnalysisResponse)
async def analyze_sample_image(category: str = "PNEUMONIA"):
    """
    Instantly runs analysis on a verified sample chest X-ray from the dataset.
    Perfect for live demonstrations and testing.
    """
    test_dir = BASE_DIR / "dataset" / "chest_xray" / "test" / category.upper()
    if not test_dir.exists():
        test_dir = BASE_DIR / "chest_xray" / "test" / category.upper()

    if not test_dir.exists():
        raise HTTPException(status_code=404, detail="Test dataset directory not found.")

    files = [f for f in os.listdir(test_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not files:
        raise HTTPException(status_code=404, detail=f"No sample images found for category {category}")

    sample_path = test_dir / files[0]
    result = prediction_service.predict(str(sample_path), generate_cam=True, cam_alpha=0.45)
    result["filename"] = f"sample_{category.lower()}_{files[0]}"
    result["timestamp"] = datetime.utcnow().isoformat()
    return result


@router.get("/metrics")
async def get_model_evaluation_metrics():
    """
    Returns the real evaluated model performance metrics and confusion matrix.
    """
    if METRICS_PATH.exists():
        with open(METRICS_PATH, "r") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Model evaluation metrics not yet generated.")
