"""
Antigravity Multi-Region X-Ray Analysis AI Platform - Backend Server.
Powered by FastAPI, PyTorch, TorchXRayVision, and ReportLab.
Serves both API endpoints and the compiled React production frontend.
"""

import os
import shutil
import platform
from pathlib import Path

# Load Gemini API Key from environment or .env file
if not os.environ.get("GEMINI_API_KEY"):
    for env_path in [Path("backend/.env"), Path(".env")]:
        if env_path.exists():
            try:
                for line in env_path.read_text().splitlines():
                    if line.strip().startswith("GEMINI_API_KEY="):
                        os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        break
                if os.environ.get("GEMINI_API_KEY"):
                    break
            except Exception:
                pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from backend.routers.analysis import router as analysis_router
from backend.routers.models_info import router as models_router
from backend.routers.datasets_info import router as datasets_router

app = FastAPI(
    title="Multi-Region X-Ray Analysis AI Platform",
    description="Modular multi-model diagnostic imaging research & educational platform.",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/api/health")
async def health_check():
    return JSONResponse(content={
        "status": "ok",
        "service": "xray-ai",
        "models": ["ResNet-18 MSK", "DenseNet-121 Chest", "Gemini 3.5 Multimodal"]
    })

# Ensure static directories exist
STATIC_DIR = Path("backend/static")
STATIC_UPLOADS = STATIC_DIR / "uploads"
STATIC_RESULTS = STATIC_DIR / "results"
STATIC_REPORTS = STATIC_DIR / "reports"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
STATIC_UPLOADS.mkdir(parents=True, exist_ok=True)
STATIC_RESULTS.mkdir(parents=True, exist_ok=True)
STATIC_REPORTS.mkdir(parents=True, exist_ok=True)

# Mount static file endpoints
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount data/reports if present
REPORTS_DIR = Path("data/reports")
if REPORTS_DIR.exists():
    app.mount("/static/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports_static")

# Include API Routers
app.include_router(analysis_router)
app.include_router(models_router)
app.include_router(datasets_router)

@app.get("/api/health")
async def health_check():
    import torch
    total_disk, used_disk, free_disk = shutil.disk_usage(".")
    
    weights_dir = Path("models/weights")
    return JSONResponse(content={
        "status": "healthy",
        "system": {
            "platform": platform.platform(),
            "cpu_logical_cores": os.cpu_count(),
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "free_disk_gb": round(free_disk / (1024**3), 2),
            "gemini_api_key_configured": bool(os.environ.get("GEMINI_API_KEY"))
        },
        "models_status": {
            "anatomical_router": (weights_dir / "anatomical_router.pt").exists(),
            "msk_damage_detector": (weights_dir / "msk_damage_detector.pt").exists(),
            "chest_analyzer": (weights_dir / "densenet121-res224-all.pt").exists()
        }
    })

# Serve Frontend static build
FRONTEND_DIST = Path("frontend/dist")
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend_assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(status_code=404, content={"detail": "Not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
