"""X-Ray AI Service Adapter for MEDVISION-AI
Starts the Multi-Region X-Ray Analysis AI FastAPI service on port 8002 without modifying
any original files in the xray-ai project.
Also provides a patient-linked endpoint for the Central Express Gateway.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path so original imports (backend.*, models.*) resolve naturally
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Import original FastAPI app and router functions
from backend.main import app as original_app
from backend.routers.analysis import analyze_xray

PORT = int(os.getenv("PORT", 8002))
HOST = os.getenv("HOST", "127.0.0.1")

@original_app.post("/api/adapter/analyze_xray")
async def adapter_analyze_xray(
    file: UploadFile = File(...),
    patient_id: str = Form("guest_patient")
):
    """
    Adapter endpoint accepting multipart file + patient_id:
    Invokes original analyze_xray and wraps output with patient_id.
    """
    try:
        raw_res = await analyze_xray(file=file)
        # raw_res is JSONResponse
        content = raw_res.body
        import json
        data = json.loads(content.decode("utf-8"))
        data["patient_id"] = patient_id
        data["modality"] = "xray"
        data["status"] = "completed"

        # Provide absolute URL prefix for specimens and reports if needed
        return JSONResponse(content={
            "status": "success",
            "data": data
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"X-Ray analysis pipeline error: {str(exc)}")


def main():
    print(f"\n==========================================================")
    print(f" MEDVISION-AI: Multi-Region X-Ray AI Microservice")
    print(f" Running on http://{HOST}:{PORT}")
    print(f"==========================================================\n")
    uvicorn.run(original_app, host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()

