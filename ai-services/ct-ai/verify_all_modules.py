"""
End-to-End Verification of MedVision-AI:
1. Prescription Reader (Real prescription document -> Gemini OCR & Analysis -> MongoDB)
2. Chest X-Ray (Real chest X-ray image -> ResNet-18 + GradCAM -> MongoDB)
3. CT Scan Analysis (Real CT image -> Gemini 3.5 Flash clinical analysis -> MongoDB)
4. Negative CT Modality Rejection (Prescription document uploaded to CT scan -> HTTP 400 rejection)
"""

import os
import sys
import json
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load .env
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

from fastapi.testclient import TestClient
from backend.app.main import app as fastapi_app
from services.mongo_service import mongo_service

client = TestClient(fastapi_app)

def run_tests():
    print("=" * 70)
    print("MEDVISION-AI COMPREHENSIVE END-TO-END VERIFICATION")
    print("=" * 70)

    results = {}

    # -------------------------------------------------------------
    # TEST 1: PRESCRIPTION READER (Real Prescription Document)
    # -------------------------------------------------------------
    print("\n--- TEST 1: Prescription Reader ---")
    rx_path = Path("C:/Users/HP/Downloads/2priscrition.png")
    if not rx_path.exists():
        rx_path = ROOT_DIR / "sample_data" / "prescriptions" / "sample_prescription.jpg"
    
    print(f"Uploading file: {rx_path}")
    patient_id_1 = "test_patient_rx_001"

    with open(rx_path, "rb") as f:
        response = client.post(
            "/api/prescriptions/analyze",
            files={"file": (rx_path.name, f, "image/png")},
            data={"patient_id": patient_id_1}
        )
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    rx_data = response.json()
    print("Response Keys:", list(rx_data.keys()))
    print("Report Title:", rx_data.get("report_title"))
    print("Modality:", rx_data.get("modality"))
    print("Extracted Medications Count:", len(rx_data.get("medications", [])))
    print("Medications Found:", [m.get("name") for m in rx_data.get("medications", [])])
    print("Patient ID:", rx_data.get("patient_id"))
    print("Analysis ID:", rx_data.get("analysis_id"))

    assert rx_data.get("modality") == "prescription_doc", f"Wrong modality: {rx_data.get('modality')}"
    assert "Prescription" in rx_data.get("report_title", ""), f"Wrong report title: {rx_data.get('report_title')}"
    assert len(rx_data.get("medications", [])) > 0, "No medications extracted!"

    # Verify MongoDB persistence
    db_rx = mongo_service.get_analysis_by_id(rx_data["analysis_id"])
    assert db_rx is not None, "Record not found in MongoDB analysisresults collection!"
    print(f"MongoDB Verification: Record successfully retrieved for ID {rx_data['analysis_id']}")
    print(f"MongoDB Stored patientId: {db_rx.get('patientId')}")
    assert db_rx.get("patientId") == patient_id_1, f"Mismatch in DB patientId: {db_rx.get('patientId')}"
    results["Prescription Reader"] = "PASSED"

    # -------------------------------------------------------------
    # TEST 2: CHEST X-RAY (Real Chest X-Ray Image -> ResNet-18)
    # -------------------------------------------------------------
    print("\n--- TEST 2: Chest X-Ray Analysis (ResNet-18) ---")
    cxr_path = ROOT_DIR / "sample_data" / "chest_xray" / "cxr_pneumonia.jpg"
    print(f"Uploading file: {cxr_path}")
    patient_id_2 = "test_patient_cxr_002"

    with open(cxr_path, "rb") as f:
        response = client.post(
            "/api/images/analyze",
            files={"file": (cxr_path.name, f, "image/jpeg")},
            data={"patient_id": patient_id_2, "generate_gradcam": "true", "alpha": "0.45"}
        )
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    cxr_data = response.json()
    print("Response Keys:", list(cxr_data.keys()))
    print("Report Title:", cxr_data.get("report_title"))
    print("Modality:", cxr_data.get("modality"))
    prediction_val = cxr_data.get("prediction")
    print("Prediction:", prediction_val)
    print("Confidence:", cxr_data.get("confidence"))
    print("Grad-CAM Available:", bool(cxr_data.get("gradcam")))
    print("Patient ID:", cxr_data.get("patient_id"))
    print("Analysis ID:", cxr_data.get("analysis_id"))

    assert cxr_data.get("modality") == "chest_xray", f"Wrong modality: {cxr_data.get('modality')}"
    assert "Chest" in cxr_data.get("report_title", ""), f"Wrong report title: {cxr_data.get('report_title')}"
    assert prediction_val in ["NORMAL", "PNEUMONIA"], f"Unexpected prediction: {prediction_val}"

    # Verify MongoDB persistence
    db_cxr = mongo_service.get_analysis_by_id(cxr_data["analysis_id"])
    assert db_cxr is not None, "Record not found in MongoDB analysisresults collection!"
    print(f"MongoDB Verification: Record successfully retrieved for ID {cxr_data['analysis_id']}")
    print(f"MongoDB Stored patientId: {db_cxr.get('patientId')}")
    assert db_cxr.get("patientId") == patient_id_2, f"Mismatch in DB patientId: {db_cxr.get('patientId')}"
    results["Chest X-Ray Analysis"] = "PASSED"

    # -------------------------------------------------------------
    # TEST 3: CT SCAN ANALYSIS (Real CT Image -> Gemini 3.5 Flash)
    # -------------------------------------------------------------
    print("\n--- TEST 3: CT Scan Analysis (Gemini 3.5 Flash) ---")
    ct_path = ROOT_DIR / "sample_data" / "ct_scans" / "ct_nodule.jpg"
    print(f"Uploading file: {ct_path}")
    patient_id_3 = "test_patient_ct_003"

    with open(ct_path, "rb") as f:
        response = client.post(
            "/api/analyze",
            files={"file": (ct_path.name, f, "image/jpeg")},
            data={"patient_id": patient_id_3}
        )
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    ct_raw = response.json()
    ct_data = ct_raw.get("data", ct_raw)
    print("Response Keys:", list(ct_data.keys()))
    print("Report Title:", ct_data.get("report_title"))
    print("Detected Modality:", ct_data.get("image_type") or ct_data.get("modality"))
    print("Visual Observations Count:", len(ct_data.get("visual_observations", [])))
    print("Potential Findings Count:", len(ct_data.get("potential_findings", [])))
    print("Patient ID:", ct_data.get("patient_id"))
    print("Analysis ID:", ct_data.get("analysis_id"))

    assert ct_data.get("modality") == "ct_scan", f"Wrong modality: {ct_data.get('modality')}"
    assert "CT" in ct_data.get("report_title", ""), f"Wrong report title: {ct_data.get('report_title')}"
    assert ct_data.get("is_compatible_ct_scan") is True, "CT Scan should be recognized as compatible!"

    # Verify MongoDB persistence
    analysis_id = ct_data["analysis_id"]
    db_ct = mongo_service.get_analysis_by_id(analysis_id)
    assert db_ct is not None, "Record not found in MongoDB analysisresults collection!"
    print(f"MongoDB Verification: Record successfully retrieved for ID {analysis_id}")
    print(f"MongoDB Stored patientId: {db_ct.get('patientId')}")
    assert db_ct.get("patientId") == patient_id_3, f"Mismatch in DB patientId: {db_ct.get('patientId')}"
    results["CT Scan Analysis"] = "PASSED"

    # -------------------------------------------------------------
    # TEST 4: NEGATIVE TEST (Upload Prescription to CT Analysis)
    # -------------------------------------------------------------
    print("\n--- TEST 4: Negative Test - Prescription Uploaded to CT Module ---")
    print(f"Uploading incompatible prescription file {rx_path} to /api/analyze")

    with open(rx_path, "rb") as f:
        neg_response = client.post(
            "/api/analyze",
            files={"file": (rx_path.name, f, "image/png")},
            data={"patient_id": "bad_rx_to_ct"}
        )
    
    print(f"Negative Test Status Code: {neg_response.status_code}")
    print(f"Negative Test Response: {neg_response.text}")

    assert neg_response.status_code == 400, f"Expected 400 rejection, got {neg_response.status_code}"
    assert "Incompatible image" in neg_response.json().get("detail", ""), "Expected detail message regarding incompatible image"
    print("SUCCESS: Incompatible prescription document was strictly rejected by CT service with 400 Bad Request.")
    results["Prescription-to-CT Rejection"] = "PASSED"

    # -------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    for test_name, status in results.items():
        print(f"[{status}] - {test_name}")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

