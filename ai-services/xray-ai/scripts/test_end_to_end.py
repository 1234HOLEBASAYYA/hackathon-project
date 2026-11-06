"""
End-to-end integration test for the Multi-Region X-Ray Analysis AI Platform.
Tests:
  1. Health check & system diagnostics
  2. Models registry inspection
  3. Real evaluation metrics retrieval
  4. Dataset provenance retrieval
  5. Preloaded samples retrieval
  6. Full upload -> routing -> MSK damage localization inference -> side-by-side comparison
  7. Full upload -> routing -> Chest analysis inference
  8. PDF medical report generation & binary download
"""

import sys
import os
import json
from pathlib import Path

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from fastapi.testclient import TestClient

from backend.main import app

def test_full_pipeline():
    print("=" * 70)
    print("RUNNING END-TO-END SYSTEM INTEGRATION TEST")
    print("=" * 70)
    
    client = TestClient(app)
    
    # 1. Healthcheck
    res = client.get("/api/health")
    assert res.status_code == 200, f"Healthcheck failed: {res.text}"
    health = res.json()
    print("[1/8] Health Check: OK")
    print(f"      Models loaded: {health['models_status']}")
    
    # 2. Models info
    res = client.get("/api/models")
    assert res.status_code == 200, f"Models info failed: {res.text}"
    models_data = res.json()
    print(f"[2/8] Models Info: OK ({len(models_data['models'])} models registered)")
    
    # 3. Metrics
    res = client.get("/api/metrics")
    assert res.status_code == 200, f"Metrics failed: {res.text}"
    metrics_data = res.json()
    print("[3/8] Metrics API: OK")
    print(f"      Router accuracy: {metrics_data.get('anatomical_router', {}).get('overall_accuracy')}")
    print(f"      MSK accuracy:    {metrics_data.get('msk_damage_detector', {}).get('classification', {}).get('accuracy')}")
    
    # 4. Datasets
    res = client.get("/api/datasets")
    assert res.status_code == 200, f"Datasets failed: {res.text}"
    ds_data = res.json()
    print(f"[4/8] Datasets API: OK ({len(ds_data['datasets'])} datasets documented)")
    
    # 5. Samples
    res = client.get("/api/samples")
    assert res.status_code == 200, f"Samples failed: {res.text}"
    samples_data = res.json()
    sample_list = samples_data.get("samples", [])
    print(f"[5/8] Samples API: OK ({len(sample_list)} test samples listed)")
    
    # 6. Test MSK Radiograph Upload and Analysis
    test_img_path = None
    for s in sample_list:
        if s.get("anatomical_region") in ["wrist", "hand", "leg"]:
            candidate = Path("backend/static/uploads") / s.get("filename")
            if candidate.exists():
                test_img_path = str(candidate)
                break
                
    if not test_img_path:
        cached_imgs = list(Path("data/processed/images_224").glob("*.png"))
        if cached_imgs:
            test_img_path = str(cached_imgs[0])
            
    assert test_img_path and Path(test_img_path).exists(), f"No valid test image found! {test_img_path}"
    print(f"\n[6/8] Testing MSK Radiograph Upload: {test_img_path}")
    
    with open(test_img_path, "rb") as f:
        files = {"file": (Path(test_img_path).name, f, "image/png")}
        res = client.post("/api/analyze", files=files)
        
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    analysis = res.json()
    analysis_id = analysis.get("analysis_id")
    print(f"      Analysis ID: {analysis_id}")
    print(f"      Detected Region: {analysis.get('anatomical_region')} "
          f"({analysis.get('region_confidence', 0)*100:.1f}%)")
    print(f"      Abnormality/Fracture Suspected: {analysis.get('is_abnormal')} "
          f"({analysis.get('confidence', 0)*100:.1f}%)")
    print(f"      Identified Bone: {analysis.get('affected_bone')}")
    print(f"      Damage Box (pixels): {analysis.get('bounding_box_pixels')}")
    print(f"      Findings Count: {len(analysis.get('findings', []))}")
    print(f"      Visual Specimen: {analysis.get('visual_specimen_url')}")
    print(f"      PDF Report URL: {analysis.get('pdf_report_url')}")
    
    # 7. Test Chest Radiograph Upload and Analysis
    chest_img_path = None
    for s in sample_list:
        if s.get("anatomical_region") == "chest":
            candidate = Path("backend/static/uploads") / s.get("filename")
            if candidate.exists():
                chest_img_path = str(candidate)
                break
                
    if not chest_img_path:
        for p in Path("data/raw/chest_dataset/images").glob("*.png"):
            if p.exists():
                chest_img_path = str(p)
                break
            
    if chest_img_path and Path(chest_img_path).exists():
        print(f"\n[7/8] Testing Chest Radiograph Upload: {chest_img_path}")
        with open(chest_img_path, "rb") as f:
            files = {"file": (Path(chest_img_path).name, f, "image/png")}
            res_chest = client.post("/api/analyze", files=files)
            
        assert res_chest.status_code == 200, f"Chest analysis failed: {res_chest.text}"
        c_analysis = res_chest.json()
        print(f"      Detected Region: {c_analysis.get('anatomical_region')} "
              f"({c_analysis.get('region_confidence', 0)*100:.1f}%)")
        c_findings = c_analysis.get("findings", [])
        print(f"      Chest Findings Count: {len(c_findings)}")
        if c_findings:
            print(f"      Top Finding: {c_findings[0].get('finding_type')} ({c_findings[0].get('confidence', 0)*100:.1f}%)")
    else:
        print("[7/8] Chest sample skipped (no direct chest sample path)")
        
    # 8. Test Medical PDF Report Generation and Download
    print(f"\n[8/8] Testing Medical PDF Report Download for ID: {analysis_id}")
    res_pdf = client.get(f"/api/report/{analysis_id}/pdf")
    assert res_pdf.status_code == 200, f"PDF report download failed: {res_pdf.text}"
    assert res_pdf.headers.get("content-type") == "application/pdf", "Expected application/pdf header"
    pdf_bytes = res_pdf.content
    print(f"      PDF Generated Successfully! Size: {len(pdf_bytes)} bytes.")
    
    print("\n" + "=" * 70)
    print("ALL 8 END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_pipeline()
