"""
Analysis Router for X-Ray Ingestion and Inference.
Endpoints:
  - POST /api/analyze: Handles image/DICOM upload, validation, and multi-stage analysis.
  - GET /api/report/{analysis_id}/pdf: Downloads the generated clinical PDF report.
  - GET /api/samples: Provides quick-test verified sample radiographs across all regions.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import pandas as pd

from backend.services.inference_service import get_inference_service

router = APIRouter(prefix="/api", tags=["Analysis"])

UPLOAD_DIR = Path("backend/static/uploads")
RESULTS_DIR = Path("backend/static/results")
REPORTS_DIR = Path("backend/static/reports")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm", ".dicom"}

@router.post("/analyze")
async def analyze_xray(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format '{ext}'. Supported: PNG, JPG, JPEG, DICOM.")
        
    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    saved_path = UPLOAD_DIR / unique_name
    
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Handle DICOM conversion if needed
    if ext in (".dcm", ".dicom"):
        try:
            import pydicom
            import numpy as np
            ds = pydicom.dcmread(saved_path)
            pix = ds.pixel_array
            # Normalize to 0-255 uint8
            pix = (pix - np.min(pix)) / (np.max(pix) - np.min(pix) + 1e-6) * 255.0
            png_name = f"{saved_path.stem}.png"
            png_path = UPLOAD_DIR / png_name
            Image.fromarray(pix.astype(np.uint8)).save(png_path)
            saved_path = png_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse DICOM image: {e}")

    try:
        service = get_inference_service()
        result = service.analyze_radiograph(saved_path)
        result["uploaded_image_url"] = f"/static/uploads/{saved_path.name}"
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference pipeline error: {str(e)}")

@router.get("/report/{analysis_id}/pdf")
async def download_report_pdf(analysis_id: str):
    pdf_path = REPORTS_DIR / f"report_{analysis_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report PDF not found.")
    return FileResponse(
        path=str(pdf_path),
        filename=f"XRay_Analysis_Report_{analysis_id}.pdf",
        media_type="application/pdf"
    )

@router.get("/samples")
async def get_test_samples():
    """
    Returns verified sample radiographs from the held-out test split
    covering each anatomical region so users can test with a single click.
    """
    test_csv = Path("data/splits/test_split.csv")
    if not test_csv.exists():
        return {"samples": []}
        
    df = pd.read_csv(test_csv)
    samples = []
    
    # Pick 1-2 representative samples per anatomical region
    regions = ["wrist", "hand", "leg", "hip", "shoulder", "chest"]
    for reg in regions:
        sub = df[df["anatomical_region"] == reg]
        if not sub.empty:
            for _, row in sub.head(2).iterrows():
                fp = Path(row["filepath"])
                sample_name = f"sample_{reg}_{fp.name}"
                dest = UPLOAD_DIR / sample_name
                if dest.exists() or fp.exists():
                    if not dest.exists() and fp.exists():
                        shutil.copyfile(fp, dest)
                        
                    samples.append({
                        "sample_id": row["sample_id"],
                        "anatomical_region": reg,
                        "dataset_source": row["dataset_source"],
                        "fracture_status": "Fractured" if row["fracture_label"] == 1 else "Normal",
                        "image_url": f"/static/uploads/{sample_name}",
                        "filename": sample_name,
                        "bone_structures": row.get("bone_structures", [])
                    })
                    
    return {"samples": samples}
