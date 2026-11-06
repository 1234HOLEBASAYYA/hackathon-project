"""Comprehensive End-to-End Integration Verification for MEDVISION-AI
Tests all three AI models through the Central Express Gateway (Port 3000) using REAL medical inputs.
Verifies AI predictions and validates MongoDB persistence and retrieval by patientId.
"""

import os
import sys
import json
import time
from pathlib import Path
import requests
from pymongo import MongoClient

BASE_URL = "http://localhost:3000"
MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "medvision_ai"

ROOT_DIR = Path(__file__).resolve().parent

def run_tests():
    print("=" * 75)
    print("   MEDVISION-AI REAL-INPUT MULTI-MODAL INTEGRATION TEST SUITE")
    print("=" * 75)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    test_patient_id = "P-1001"
    test_patient_name = "Robert Miller"

    # Step 0: Ensure patient exists
    print(f"\n[Step 0] Ensuring Patient '{test_patient_id}' ({test_patient_name}) is registered...")
    pat_res = requests.post(f"{BASE_URL}/api/patients", json={
        "patientId": test_patient_id,
        "name": test_patient_name,
        "age": 58,
        "gender": "Male",
        "allergies": ["Penicillin"],
        "chronicConditions": ["Type 2 Diabetes", "Hypertension"]
    })
    assert pat_res.status_code in [200, 201], f"Patient registration failed: {pat_res.text}"
    print(f"         Patient {test_patient_id} ready in MongoDB.")

    # -------------------------------------------------------------
    # TEST 1: PRESCRIPTION AI (Real Prescription Document OCR)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Prescription OCR via Central Gateway...")
    rx_path = ROOT_DIR / "frontend" / "assets" / "images" / "sample_prescription.png"
    assert rx_path.exists(), f"Prescription sample missing at {rx_path}"

    with open(rx_path, "rb") as f:
        t0 = time.time()
        rx_response = requests.post(
            f"{BASE_URL}/api/analysis/prescription/analyze",
            files={"file": (rx_path.name, f, "image/png")},
            data={"patientId": test_patient_id, "patientName": test_patient_name},
            timeout=120
        )
        elapsed = time.time() - t0

    print(f"         HTTP Status: {rx_response.status_code} (took {elapsed:.2f}s)")
    assert rx_response.status_code == 200, f"Prescription analysis failed: {rx_response.text}"

    rx_json = rx_response.json()
    rx_data = rx_json.get("data", {})
    rx_analysis_id = rx_data.get("analysisId")
    medications = rx_data.get("medications", [])

    print(f"         Analysis ID:     {rx_analysis_id}")
    print(f"         Doctor Name:     {rx_data.get('doctor', {}).get('name')}")
    print(f"         Clinic:          {rx_data.get('clinicHeader')}")
    print(f"         Medications ({len(medications)}): {[m.get('medicineName') for m in medications]}")

    # Real predictions verification
    assert len(medications) >= 2, f"Expected at least 2 medications, got {len(medications)}"
    med_names = [m.get("medicineName").lower() for m in medications]
    assert any("atorvastatin" in name for name in med_names), "Expected Atorvastatin to be detected"
    assert any("metformin" in name for name in med_names), "Expected Metformin to be detected"

    # Verify MongoDB persistence
    print("         Verifying MongoDB Persistence...")
    db_rx_analysis = db["analysisresults"].find_one({"analysisId": rx_analysis_id})
    db_rx_record = db["prescriptions"].find_one({"analysisId": rx_analysis_id})

    assert db_rx_analysis is not None, "Prescription not found in 'analysisresults' collection!"
    assert db_rx_record is not None, "Prescription not found in 'prescriptions' collection!"
    assert db_rx_analysis["patientId"] == test_patient_id, f"PatientId mismatch in DB: {db_rx_analysis['patientId']}"
    print(f"         SUCCESS: Prescription record saved with patientId '{test_patient_id}' and retrieved from MongoDB.")

    # -------------------------------------------------------------
    # TEST 2: MULTI-REGION X-RAY AI (Real Radiograph Fracture Detection)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Multi-Region X-Ray AI via Central Gateway...")
    xray_path = ROOT_DIR / "frontend" / "assets" / "images" / "sample_wrist.png"
    assert xray_path.exists(), f"X-Ray sample missing at {xray_path}"

    with open(xray_path, "rb") as f:
        t0 = time.time()
        xray_response = requests.post(
            f"{BASE_URL}/api/analysis/xray/analyze",
            files={"file": (xray_path.name, f, "image/png")},
            data={"patientId": test_patient_id, "patientName": test_patient_name},
            timeout=120
        )
        elapsed = time.time() - t0

    print(f"         HTTP Status: {xray_response.status_code} (took {elapsed:.2f}s)")
    assert xray_response.status_code == 200, f"X-Ray analysis failed: {xray_response.text}"

    xray_json = xray_response.json()
    xray_data = xray_json.get("data", {})
    xray_analysis_id = xray_data.get("analysisId")
    region = xray_data.get("anatomicalRegion")
    is_abnormal = xray_data.get("isAbnormal")
    affected_bone = xray_data.get("affectedBone")
    bbox = xray_data.get("boundingBoxPixels")

    print(f"         Analysis ID:     {xray_analysis_id}")
    print(f"         Detected Region: {region} ({xray_data.get('regionConfidence', 0)*100:.1f}%)")
    print(f"         Abnormal Defect: {is_abnormal} ({xray_data.get('confidence', 0)*100:.1f}%)")
    print(f"         Affected Bone:   {affected_bone}")
    print(f"         Damage BBox:     {bbox}")
    print(f"         Specimen URL:    {xray_data.get('specimenUrl')}")

    # Real predictions verification
    assert region.lower() == "wrist", f"Expected 'Wrist' region, got '{region}'"
    assert is_abnormal is True, "Expected abnormality/fracture to be detected"
    assert affected_bone == "distal_radius", f"Expected 'distal_radius', got '{affected_bone}'"
    assert len(bbox) == 4, f"Expected 4 bounding box coordinates, got {bbox}"

    # Verify MongoDB persistence
    print("         Verifying MongoDB Persistence...")
    db_xray_analysis = db["analysisresults"].find_one({"analysisId": xray_analysis_id})
    assert db_xray_analysis is not None, "X-Ray analysis not found in 'analysisresults' collection!"
    assert db_xray_analysis["patientId"] == test_patient_id, f"PatientId mismatch in DB: {db_xray_analysis['patientId']}"
    print(f"         SUCCESS: X-Ray analysis record saved with patientId '{test_patient_id}' and retrieved from MongoDB.")

    # -------------------------------------------------------------
    # TEST 3: CT-SCAN CLINICAL VISION (Real CT Slice Nodule Analysis)
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing CT-Scan Clinical Vision via Central Gateway...")
    ct_path = ROOT_DIR / "frontend" / "assets" / "images" / "sample_ct.jpg"
    assert ct_path.exists(), f"CT sample missing at {ct_path}"

    with open(ct_path, "rb") as f:
        t0 = time.time()
        ct_response = requests.post(
            f"{BASE_URL}/api/analysis/ct/analyze",
            files={"file": (ct_path.name, f, "image/jpeg")},
            data={"patientId": test_patient_id, "patientName": test_patient_name},
            timeout=120
        )
        elapsed = time.time() - t0

    print(f"         HTTP Status: {ct_response.status_code} (took {elapsed:.2f}s)")
    assert ct_response.status_code == 200, f"CT scan analysis failed: {ct_response.text}"

    ct_json = ct_response.json()
    ct_data = ct_json.get("data", {})
    ct_analysis_id = ct_data.get("analysisId")
    observations = ct_data.get("visualObservations", [])
    findings = ct_data.get("potentialFindings", [])

    print(f"         Analysis ID:     {ct_analysis_id}")
    print(f"         Report Title:    {ct_data.get('reportTitle')}")
    print(f"         Modality:        {ct_data.get('detectedModality')}")
    print(f"         Observations ({len(observations)}): {[o.get('density_or_structure') for o in observations[:3]]}")
    print(f"         Findings ({len(findings)}):     {[f.get('finding_or_condition') for f in findings[:2]]}")

    # Real predictions verification
    assert len(observations) > 0, "Expected at least 1 visual observation in CT slice"
    assert len(findings) > 0, "Expected at least 1 potential differential finding"

    # Verify MongoDB persistence
    print("         Verifying MongoDB Persistence...")
    db_ct_analysis = db["analysisresults"].find_one({"analysisId": ct_analysis_id})
    assert db_ct_analysis is not None, "CT scan analysis not found in 'analysisresults' collection!"
    assert db_ct_analysis["patientId"] == test_patient_id, f"PatientId mismatch in DB: {db_ct_analysis['patientId']}"
    print(f"         SUCCESS: CT scan analysis saved with patientId '{test_patient_id}' and retrieved from MongoDB.")

    # -------------------------------------------------------------
    # TEST 4: UNIFIED PATIENT TIMELINE CONSOLIDATION
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Unified Longitudinal Patient Timeline Retrieval...")
    timeline_res = requests.get(f"{BASE_URL}/api/patients/{test_patient_id}/timeline")
    assert timeline_res.status_code == 200, f"Timeline retrieval failed: {timeline_res.text}"

    t_data = timeline_res.json().get("data", {})
    analyses = t_data.get("analyses", [])
    prescriptions = t_data.get("prescriptions", [])

    print(f"         Total Analyses for {test_patient_id}:     {len(analyses)}")
    print(f"         Total Prescriptions for {test_patient_id}: {len(prescriptions)}")

    modalities_found = {a.get("modality") for a in analyses}
    print(f"         Modalities Linked to Patient: {modalities_found}")

    assert "prescription" in modalities_found, "Prescription modality missing from patient timeline"
    assert "xray" in modalities_found, "X-Ray modality missing from patient timeline"
    assert "ct_scan" in modalities_found, "CT-Scan modality missing from patient timeline"
    print(f"         SUCCESS: All 3 diagnostic modalities are verified consolidated under Patient '{test_patient_id}'!")

    # -------------------------------------------------------------
    # TEST 5: STATIC WEB PAGES SERVING
    # -------------------------------------------------------------
    print("\n[TEST 5] Verifying Unified Frontend Web Pages on Port 3000...")
    pages = ["/", "/index.html", "/prescription.html", "/xray.html", "/ct-scan.html", "/dashboard.html"]
    for page in pages:
        p_res = requests.get(f"{BASE_URL}{page}")
        assert p_res.status_code == 200, f"Page {page} returned {p_res.status_code}"
        assert len(p_res.text) > 200, f"Page {page} empty"
    print("         SUCCESS: All 5 medical web pages served directly by Express Gateway.")

    print("\n" + "=" * 75)
    print("   ALL INTEGRATION & PERSISTENCE TESTS PASSED SUCCESSFULLY! (5/5)")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()

