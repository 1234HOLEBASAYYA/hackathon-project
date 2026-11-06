import os
import sys
from pathlib import Path

# Automatically add backend directory and project root to sys.path
# This ensures imports like 'from app.api...' and 'from app.services...' work from any CWD
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

for p in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from app.api.health_routes import router as health_router
    from app.api.image_routes import router as image_router
    from app.api.prescription_routes import router as prescription_router
    from app.api.ct_analysis_routes import router as ct_analysis_router
    from app.services.prediction_service import prediction_service
except (ImportError, ModuleNotFoundError):
    from backend.app.api.health_routes import router as health_router
    from backend.app.api.image_routes import router as image_router
    from backend.app.api.prescription_routes import router as prescription_router
    from backend.app.api.ct_analysis_routes import router as ct_analysis_router
    from backend.app.services.prediction_service import prediction_service

UPLOADS_DIR = BACKEND_DIR / "uploads"
RESULTS_DIR = ROOT_DIR / "training" / "training_results"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Medical Image-Based Abnormality Detection & Visualization System",
    description="Transfer Learning ResNet18 Pneumonia Detection with Explainable Grad-CAM Heatmaps",
    version="1.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads and training artifacts
app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")

# Register Routers
app.include_router(health_router)
app.include_router(image_router)
app.include_router(prescription_router)
app.include_router(ct_analysis_router)


@app.on_event("startup")
async def startup_event():
    print("[Main] Booting Medical Image Abnormality Detection API...")
    prediction_service.ensure_model_loaded()
    print("[Main] Server ready to accept requests.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
