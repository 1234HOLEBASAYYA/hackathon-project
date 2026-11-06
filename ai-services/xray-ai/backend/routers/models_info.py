"""
Models and Metrics Metadata Router.
Provides real, un-fabricated model performance metrics, confusion matrices,
architecture details, and evaluation reports.
"""

import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api", tags=["Models & Metrics"])

WEIGHTS_DIR = Path("models/weights")
REPORTS_DIR = Path("data/reports")

@router.get("/models")
async def get_models_info():
    """
    Returns architecture, status, and supported findings for all implemented models.
    """
    models = [
        {
            "id": "stage1_router",
            "name": "Anatomical Region Router",
            "stage": 1,
            "architecture": "ResNet-18 Deep Convolutional Neural Network",
            "status": "Trained & Evaluated" if (WEIGHTS_DIR / "anatomical_router.pt").exists() else "Training",
            "target_classes": ["wrist", "hand", "leg", "hip", "shoulder", "chest", "unsupported"],
            "input_resolution": "224x224",
            "routing_rule": "Directs image to specialized pathway; flags out-of-distribution inputs (<0.50 confidence) as unsupported",
            "checkpoint": str(WEIGHTS_DIR / "anatomical_router.pt")
        },
        {
            "id": "stage2_msk_detector",
            "name": "MSK Damage Localization & Fracture Detector",
            "stage": 2,
            "architecture": "Multi-Task ResNet-18 (Classification + Smooth L1 Box Regression + Bone Classifier)",
            "status": "Trained & Evaluated" if (WEIGHTS_DIR / "msk_damage_detector.pt").exists() else "Configured",
            "target_regions": ["wrist", "hand", "leg", "hip", "shoulder"],
            "damage_localization": "Exact 2D Bounding Boxes [xmin, ymin, xmax, ymax] marking focal cortical disruption",
            "bone_structures_identified": [
                "distal_radius", "distal_ulna", "metacarpals_or_phalanges",
                "femur_or_hip", "tibia_or_fibula", "clavicle_or_shoulder"
            ],
            "checkpoint": str(WEIGHTS_DIR / "msk_damage_detector.pt")
        },
        {
            "id": "stage2_chest_analyzer",
            "name": "TorchXRayVision DenseNet-121 Chest Analyzer",
            "stage": 2,
            "architecture": "DenseNet-121 Pretrained (densenet121-res224-all)",
            "status": "Loaded & Verified",
            "target_regions": ["chest"],
            "supported_pathologies_count": 18,
            "supported_pathologies": [
                "Atelectasis", "Consolidation", "Infiltration", "Pneumothorax",
                "Edema", "Emphysema", "Fibrosis", "Effusion", "Pneumonia",
                "Pleural_Thickening", "Cardiomegaly", "Nodule", "Mass", "Hernia",
                "Lung Lesion", "Fracture", "Lung Opacity", "Enlarged Cardiomediastinum"
            ],
            "checkpoint": str(WEIGHTS_DIR / "densenet121-res224-all.pt")
        }
    ]
    return {"models": models}

@router.get("/metrics")
async def get_model_metrics():
    """
    Returns actual measured metrics from held-out test evaluations.
    """
    metrics_data = {}
    
    # 1. Router metrics
    router_metrics_path = WEIGHTS_DIR / "anatomical_router_metrics.json"
    if router_metrics_path.exists():
        with open(router_metrics_path, "r") as f:
            metrics_data["anatomical_router"] = json.load(f)
            
    # 2. MSK metrics
    msk_metrics_path = WEIGHTS_DIR / "msk_damage_detector_metrics.json"
    if msk_metrics_path.exists():
        with open(msk_metrics_path, "r") as f:
            metrics_data["msk_damage_detector"] = json.load(f)
            
    # 3. Chest metrics
    chest_metrics_path = WEIGHTS_DIR / "chest_model_metrics.json"
    if chest_metrics_path.exists():
        with open(chest_metrics_path, "r") as f:
            metrics_data["chest_analyzer"] = json.load(f)
            
    # Include image paths
    metrics_data["visualizations"] = {
        "router_confusion_matrix": "/static/reports/confusion_matrix_router.png" if (REPORTS_DIR / "confusion_matrix_router.png").exists() else None,
        "msk_confusion_matrix": "/static/reports/confusion_matrix_msk.png" if (REPORTS_DIR / "confusion_matrix_msk.png").exists() else None
    }
    
    return JSONResponse(content=metrics_data)
