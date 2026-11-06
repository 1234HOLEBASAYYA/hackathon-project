"""
Datasets Information Router.
Surfaces dataset manifests, provenance, licensing, patient separation,
and sample distributions for the platform's Dataset page.
"""

import os
import json
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["Datasets"])

MANIFEST_PATH = Path("data/manifests/dataset_manifest.json")
STATS_PATH = Path("data/reports/dataset_statistics.json")

@router.get("/datasets")
async def get_datasets_info():
    stats = {}
    if STATS_PATH.exists():
        with open(STATS_PATH, "r") as f:
            stats = json.load(f)
            
    datasets_overview = [
        {
            "name": "FracAtlas",
            "full_title": "A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs",
            "doi": "10.6084/m9.figshare.22363012",
            "license": "CC BY 4.0 (Open Access)",
            "selected_samples": stats.get("by_dataset", {}).get("FracAtlas", 1000),
            "regions_covered": ["hand", "leg", "hip", "shoulder"],
            "annotation_types": ["Binary Fracture Classification", "PASCAL VOC Bounding Boxes", "COCO Segmentation Masks"],
            "patient_separation": "Official train/valid/test partition preserved; non-fractured cases sampled proportionally",
            "status": "Acquired, Validated & Ingested"
        },
        {
            "name": "GRAZPEDWRI-DX",
            "full_title": "Grazer Pediatric Wrist Radiographs Dataset with Multi-Pathology Bounding Boxes",
            "doi": "10.6084/m9.figshare.14825193",
            "license": "CC BY 4.0 (Open Access)",
            "selected_samples": stats.get("by_dataset", {}).get("GRAZPEDWRI-DX", 390),
            "regions_covered": ["wrist (pediatric)"],
            "annotation_types": ["Fracture & Metal Bounding Boxes", "AO Classification Codes", "Pediatric Age & Gender"],
            "patient_separation": "Strict patient-level splitting (no cross-contamination across train, val, test)",
            "status": "Acquired, Validated & Ingested"
        },
        {
            "name": "VinDr-CXR",
            "full_title": "An Open Dataset of Chest X-Rays with Radiologist Annotations (PhysioNet v1.0.0)",
            "doi": "10.13026/3gat-v008",
            "license": "PhysioNet Credentialed Health Data License 1.5.0",
            "selected_samples": "External Credentialed / Evaluated via Pretrained Benchmark",
            "regions_covered": ["chest"],
            "annotation_types": ["Consensus Radiologist Labels", "Local Rectangles for 22 Pathologies"],
            "patient_separation": "PhysioNet official train/test study partition",
            "status": "Credentialing Guided (TorchXRayVision Ingested)"
        },
        {
            "name": "MURA (Stanford)",
            "full_title": "MURA: Musculoskeletal Radiographs for Radiologist-Level Abnormality Detection",
            "doi": "10.71718/cwh3-0p32",
            "license": "Stanford AIMI Research Data Use Agreement",
            "selected_samples": "Academic Agreement Protected",
            "regions_covered": ["wrist", "elbow", "shoulder", "finger", "forearm", "humerus", "hand"],
            "annotation_types": ["Normal / Abnormal Binary Study Labels"],
            "patient_separation": "Patient-study hierarchy preserved",
            "status": "Registration Guided"
        }
    ]
    
    return JSONResponse(content={
        "datasets": datasets_overview,
        "global_statistics": stats,
        "total_active_manifest_samples": stats.get("total_samples", 0),
        "split_counts": stats.get("split_counts", {})
    })
