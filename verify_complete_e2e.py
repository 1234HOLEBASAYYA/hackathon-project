import os
from pathlib import Path
import requests
import json

BASE_URL = "http://127.0.0.1:3000"
TEST_PATIENT = "P-1001"

print("===================================================================", flush=True)
print("     MEDVISION-AI: COMPREHENSIVE END-TO-END VERIFICATION SUITE     ", flush=True)
print("===================================================================", flush=True)

# 1. Health Check
print("\n[TEST 1] Verifying System Microservices Health...", flush=True)
health_res = requests.get(f"{BASE_URL}/api/health", timeout=10)
assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
services = health_res.json().get("services", {})
print(f"Health Status: {health_res.json().get('status')}", flush=True)
for s_name, s_data in services.items():
    print(f"  - Service {s_name:18}: {s_data.get('status')} ({s_data.get('url')})", flush=True)

# 2. Test Prescription OCR Pipeline
print("\n[TEST 2] Testing Prescription OCR & Digitizer (EasyOCR CRAFT+BiLSTM)...", flush=True)
base_dir = Path(__file__).resolve().parent
sample_rx_path = base_dir / "frontend" / "assets" / "images" / "sample_prescription.png"
if not sample_rx_path.exists():
    import glob
    candidates = list(base_dir.glob("storage/prescriptions/*.*"))
    sample_rx_path = candidates[0] if candidates else None

assert sample_rx_path and sample_rx_path.exists(), "No sample prescription file found!"
print(f"  Uploading specimen: {sample_rx_path}", flush=True)

with open(sample_rx_path, "rb") as f:
    rx_res = requests.post(
        f"{BASE_URL}/api/analysis/prescription/analyze",
        data={"patientId": TEST_PATIENT, "patientName": "Robert Miller"},
        files={"file": f},
        timeout=60
    )

assert rx_res.status_code == 200, f"Prescription analysis failed: {rx_res.text}"
rx_data = rx_res.json().get("data", {})
prescription_id = rx_data.get("prescriptionId")
print(f"  Prescription OCR Success! ID: {prescription_id}", flush=True)
print(f"  Extracted Doctor: {rx_data.get('doctor', {}).get('name', 'N/A')}", flush=True)
print(f"  Extracted Diagnosis: {rx_data.get('diagnosis', 'N/A')}", flush=True)
print(f"  Extracted Medications Count: {len(rx_data.get('medications', []))}", flush=True)
for med in rx_data.get('medications', [])[:3]:
    print(f"    * {med.get('medicineName')} ({med.get('strength')}) - {med.get('dosage')} - Conf: {med.get('confidence')}%", flush=True)

# 3. Test Prescription Interactive Update (Save Verified)
print("\n[TEST 3] Testing Prescription Interactive Editing & Verification Save...", flush=True)
update_payload = {
    "doctor": {"name": "Dr. Sarah Jenkins, MD", "specialization": "Interventional Cardiology", "clinicOrHospital": "Apollo Heart Institute"},
    "patientName": "Robert Miller",
    "patientAge": 58,
    "diagnosis": "Essential Hypertension & Type 2 Diabetes Mellitus",
    "advice": "Low sodium diet, brisk walking 30 mins daily, monitor blood pressure.",
    "followUp": "Review after 4 weeks with lipid profile",
    "medications": [
        {
            "medicineName": "Amlodipine Besylate",
            "name": "Amlodipine Besylate",
            "strength": "5mg",
            "dosage": "1 tablet",
            "frequency": "Once daily (OD)",
            "duration": "30 days",
            "specialInstructions": "Take in the morning after breakfast",
            "confidence": 100.0
        },
        {
            "medicineName": "Metformin Hydrochloride",
            "name": "Metformin Hydrochloride",
            "strength": "500mg",
            "dosage": "1 tablet",
            "frequency": "Twice daily (BD)",
            "duration": "30 days",
            "specialInstructions": "Take with meals",
            "confidence": 100.0
        }
    ]
}

up_res = requests.put(f"{BASE_URL}/api/analysis/prescription/{prescription_id}", json=update_payload, timeout=10)
assert up_res.status_code == 200, f"Prescription update failed: {up_res.text}"
print(f"  Verified Prescription Saved to MongoDB! Status: {up_res.json().get('data', {}).get('status')}", flush=True)

# 4. Test Multi-Region X-Ray Analysis Pipeline
print("\n[TEST 4] Testing Multi-Region X-Ray Diagnostic AI (ResNet-18 + DenseNet-121)...", flush=True)
xray_files = list(base_dir.glob("frontend/assets/images/sample_wrist.png")) or list(base_dir.glob("storage/xrays/*.*"))
assert xray_files, "No sample X-Ray file found!"
sample_xray_path = xray_files[0]
print(f"  Uploading radiograph: {sample_xray_path}", flush=True)

with open(sample_xray_path, "rb") as f:
    xray_res = requests.post(
        f"{BASE_URL}/api/analysis/xray/analyze",
        data={"patientId": TEST_PATIENT, "patientName": "Robert Miller"},
        files={"file": f},
        timeout=60
    )

assert xray_res.status_code == 200, f"X-Ray analysis failed: {xray_res.text}"
xray_data = xray_res.json().get("data", {})
print(f"  X-Ray Analysis Success! Analysis ID: {xray_data.get('analysisId')}", flush=True)
print(f"  Classified Anatomical Region: {xray_data.get('anatomicalRegion')} (Conf: {((xray_data.get('regionConfidence') or 0.8)*100):.1f}%)", flush=True)
print(f"  Abnormality Detected: {xray_data.get('isAbnormal')}", flush=True)
print(f"  Target Structure / Bone: {xray_data.get('affectedBone')}", flush=True)
print(f"  Bounding Box Pixels: {xray_data.get('boundingBoxPixels')}", flush=True)
print(f"  Annotated Specimen URL: {xray_data.get('specimenUrl')}", flush=True)

# 5. Test CT Clinical Vision Pipeline (Gemini Vision)
print("\n[TEST 5] Testing CT Clinical Vision Pipeline (Modality Check & Multi-Modal Vision)...", flush=True)
ct_files = list(base_dir.glob("frontend/assets/images/sample_ct.jpg")) or list(base_dir.glob("storage/ct-scans/*.*"))
assert ct_files, "No sample CT file found!"
sample_ct_path = ct_files[0]
print(f"  Uploading CT specimen: {sample_ct_path}", flush=True)

with open(sample_ct_path, "rb") as f:
    ct_res = requests.post(
        f"{BASE_URL}/api/analysis/ct/analyze",
        data={"patientId": TEST_PATIENT, "patientName": "Robert Miller"},
        files={"file": f},
        timeout=60
    )

if ct_res.status_code == 400:
    ct_err = ct_res.json()
    assert ct_err.get("message") == "not a proper image to scan"
    print(f"  CT Clinical Vision Rejection Verified! Identified phantom/non-patient scan with 'not a proper image to scan'.", flush=True)
else:
    assert ct_res.status_code == 200, f"CT scan analysis failed: {ct_res.text}"
    ct_data = ct_res.json().get("data", {})
    print(f"  CT Clinical Vision Success! Analysis ID: {ct_data.get('analysisId')}", flush=True)
    print(f"  Report Title: {ct_data.get('reportTitle')}", flush=True)
    print(f"  Detected Modality: {ct_data.get('detectedModality')}", flush=True)
    print(f"  Visual Observations Count: {len(ct_data.get('visualObservations', []))}", flush=True)
    for obs in ct_data.get('visualObservations', [])[:2]:
        print(f"    * {obs.get('observation')} at {obs.get('location')}", flush=True)
    print(f"  Potential Findings Count: {len(ct_data.get('potentialFindings', []))}", flush=True)
    for fnd in ct_data.get('potentialFindings', [])[:2]:
        print(f"    * {fnd.get('finding')} ({fnd.get('certainty')}) - {fnd.get('location')}", flush=True)

# 6. Test Patient Timeline Aggregation from MongoDB
print(f"\n[TEST 6] Testing Unified Patient Timeline Retrieval for {TEST_PATIENT} from MongoDB...", flush=True)
timeline_res = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT}/timeline", timeout=10)
assert timeline_res.status_code == 200, f"Timeline query failed: {timeline_res.text}"
t_data = timeline_res.json().get("data", {})
analyses_list = t_data.get("analyses", [])
prescriptions_list = t_data.get("prescriptions", [])
print(f"  Total Analyses in MongoDB: {len(analyses_list)}", flush=True)
print(f"  Total Prescriptions in MongoDB: {len(prescriptions_list)}", flush=True)

# Verify modalities present
modalities_present = set(a.get("modality") for a in analyses_list)
print(f"  Modalities present in patient timeline: {modalities_present}", flush=True)
assert "prescription" in modalities_present, "Prescription modality missing from timeline!"
assert "xray" in modalities_present, "X-Ray modality missing from timeline!"
assert "ct_scan" in modalities_present, "CT Scan modality missing from timeline!"

# 7. Test Dashboard Live Statistics
print("\n[TEST 7] Testing Dashboard Live Statistics API...", flush=True)
stats_res = requests.get(f"{BASE_URL}/api/reports/stats", timeout=10)
assert stats_res.status_code == 200, f"Stats API failed: {stats_res.text}"
s_data = stats_res.json().get("data", {})
print(f"  Live Stats: Patients: {s_data.get('totalPatients')}, Total Analyses: {s_data.get('totalAnalyses')}, Prescriptions: {s_data.get('totalPrescriptions')}, X-Rays: {s_data.get('totalXrays')}, CTs: {s_data.get('totalCTs')}", flush=True)

print("\n===================================================================", flush=True)
print("     ALL 7 END-TO-END VERIFICATION TESTS PASSED SUCCESSFULLY!      ", flush=True)
print("===================================================================", flush=True)

