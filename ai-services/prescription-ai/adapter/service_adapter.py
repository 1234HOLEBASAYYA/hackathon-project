"""Prescription AI Service Adapter for MEDVISION-AI
Starts the Prescription AI FastAPI service on port 8001 without modifying
any original files in the prescription-ai project.
Also provides a direct multipart upload & analyze endpoint for the Central Express Gateway.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path so original imports (backend.*, ai.*) resolve naturally
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Import original FastAPI app
from backend.app import app as original_app
from backend.app import upload_prescription, analyze_prescription
from backend.schemas import AnalyzeRequest

PORT = int(os.getenv("PORT", 8001))
HOST = os.getenv("HOST", "127.0.0.1")

@original_app.post("/api/adapter/analyze_prescription")
async def adapter_analyze_prescription(
    file: UploadFile = File(...),
    patient_id: str = Form("guest_patient")
):
    """
    Direct single-step multipart endpoint for central Express backend:
    1. Runs original upload_prescription to store image & verify format
    2. Runs original analyze_prescription (preprocessing, EasyOCR, clinical extractor)
    3. Formats response cleanly with patient_id
    """
    try:
        # Step 1: Upload
        upload_res = await upload_prescription(file=file)
        presc_id = upload_res.id

        # Step 2: Analyze
        req = AnalyzeRequest(id=presc_id, apply_clahe=True, apply_deskew=False, use_gpu=True)
        res = await analyze_prescription(payload=req)
        res_dict = res.model_dump() if hasattr(res, "model_dump") else res.dict()
        res_dict["patient_id"] = patient_id
        res_dict["prescription_id"] = presc_id
        res_dict["modality"] = "prescription"
        res_dict["status"] = "completed"

        return JSONResponse(content={
            "status": "success",
            "data": res_dict
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prescription processing error: {str(exc)}")


def main():
    print(f"\n==========================================================")
    print(f" MEDVISION-AI: Prescription AI Microservice")
    print(f" Running on http://{HOST}:{PORT}")
    print(f"==========================================================\n")
    uvicorn.run(original_app, host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()

