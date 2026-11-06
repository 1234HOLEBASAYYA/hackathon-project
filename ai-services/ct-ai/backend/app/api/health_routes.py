import os
import json
import torch
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter

try:
    from app.services.prediction_service import prediction_service
except (ImportError, ModuleNotFoundError):
    from backend.app.services.prediction_service import prediction_service

router = APIRouter(tags=["System Health & Info"])

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BACKEND_DIR / "model" / "model_config.json"


@router.get("/health")
async def health_check():
    """System health check and runtime capabilities."""
    is_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if is_cuda else "CPU"

    return {
        "status": "healthy",
        "service": "Medical Image-Based Abnormality Detection API",
        "version": "1.0.0",
        "model_loaded": prediction_service.model is not None,
        "device": device_name,
        "is_cuda": is_cuda,
        "classes": prediction_service.classes,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/api/config")
async def get_system_config():
    """Retrieves model architecture and training hyperparameters."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "model_architecture": "resnet18",
        "classes": ["NORMAL", "PNEUMONIA"],
        "status": "Config file pending training finalization"
    }
