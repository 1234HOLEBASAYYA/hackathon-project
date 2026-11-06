"""Comprehensive Test Suite for AI Prescription Reader.

Verifies:
1. Health endpoint and hardware discovery.
2. Upload & analysis of printed prescription with multiple medicines.
3. Upload & analysis of handwritten style prescription.
4. Upload & analysis of PDF prescription document.
5. Quality check and blur detection on blurry prescription.
6. Graceful handling of unreadable / noisy scans.
7. Rejection of invalid file formats.
8. Rejection of empty (0-byte) files.
9. Result retrieval by ID.
10. Human correction / editing of medicines and marking as verified.
11. Clean PDF export with verification badge.
12. Clean CSV export with medicine details.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_health_check():
    """Verify backend health status and OCR device."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "EasyOCR" in data["ocr_engine"]
    assert data["device"] in ("cuda", "cpu")


def test_invalid_file_format_rejected():
    """Verify rejection of unsupported extensions."""
    file_path = FIXTURES_DIR / "invalid_file.txt"
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/prescription/upload",
            files={"file": ("invalid_file.txt", f, "text/plain")},
        )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_empty_file_rejected():
    """Verify rejection of 0-byte uploads."""
    file_path = FIXTURES_DIR / "empty_file.png"
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/prescription/upload",
            files={"file": ("empty_file.png", f, "image/png")},
        )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_printed_multi_medicine_prescription():
    """Verify end-to-end OCR and extraction for printed multi-medicine prescription."""
    file_path = FIXTURES_DIR / "printed_multimed.png"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("printed_multimed.png", f, "image/png")},
        )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    rx_id = upload_data["id"]

    # Analyze
    analyze_resp = client.post("/api/prescription/analyze", json={"id": rx_id, "use_gpu": True})
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()

    assert res["id"] == rx_id
    assert res["is_verified"] is False
    assert len(res["raw_text"]) > 20
    assert len(res["bounding_boxes"]) > 0

    # Check Patient & Doctor extraction
    assert res["patient"]["name"] is not None
    assert "Robert" in res["patient"]["name"] or "Miller" in res["patient"]["name"]
    assert res["doctor"]["name"] is not None
    assert "Jenkins" in res["doctor"]["name"] or "Sarah" in res["doctor"]["name"]

    # Check multiple medicines
    assert len(res["medicines"]) >= 2
    med_names = [m["medicine_name"] for m in res["medicines"]]
    # Atorvastatin / Metformin / Pantoprazole
    assert any("Atorvastatin" in name or "Metformin" in name or "Pantoprazole" in name for name in med_names)


def test_handwritten_prescription():
    """Verify processing of simulated handwritten prescription."""
    file_path = FIXTURES_DIR / "handwritten.png"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("handwritten.png", f, "image/png")},
        )
    assert upload_resp.status_code == 200
    rx_id = upload_resp.json()["id"]

    analyze_resp = client.post("/api/prescription/analyze", json={"id": rx_id, "use_gpu": True})
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    assert len(res["medicines"]) >= 1


def test_pdf_prescription():
    """Verify scanned PDF prescription rendering, OCR, and extraction."""
    file_path = FIXTURES_DIR / "sample_prescription.pdf"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("sample_prescription.pdf", f, "application/pdf")},
        )
    assert upload_resp.status_code == 200
    rx_id = upload_resp.json()["id"]

    analyze_resp = client.post("/api/prescription/analyze", json={"id": rx_id, "use_gpu": True})
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    assert len(res["medicines"]) >= 1
    med_names = [m["medicine_name"] for m in res["medicines"]]
    assert any("Azithromycin" in name or "Paracetamol" in name for name in med_names)


def test_blurry_prescription_quality_detection():
    """Verify that a blurry prescription is flagged by computer vision quality checks."""
    file_path = FIXTURES_DIR / "blurry.png"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("blurry.png", f, "image/png")},
        )
    assert upload_resp.status_code == 200
    rx_id = upload_resp.json()["id"]

    analyze_resp = client.post("/api/prescription/analyze", json={"id": rx_id, "use_gpu": True})
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    assert res["quality"] is not None
    assert res["quality"]["is_blurry"] is True


def test_unreadable_prescription_handling():
    """Verify that an unreadable noisy scan is handled safely without crashing."""
    file_path = FIXTURES_DIR / "unreadable.png"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("unreadable.png", f, "image/png")},
        )
    assert upload_resp.status_code == 200
    rx_id = upload_resp.json()["id"]

    analyze_resp = client.post("/api/prescription/analyze", json={"id": rx_id, "use_gpu": True})
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    # Should safely return 0 or empty medicines without throwing 500 error
    assert isinstance(res["medicines"], list)


def test_editing_and_verification():
    """Verify human reviewer editing and marking as verified."""
    file_path = FIXTURES_DIR / "printed_multimed.png"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("printed_multimed.png", f, "image/png")},
        )
    rx_id = upload_resp.json()["id"]
    client.post("/api/prescription/analyze", json={"id": rx_id})

    # Retrieve
    get_resp = client.get(f"/api/prescription/result/{rx_id}")
    assert get_resp.status_code == 200
    original = get_resp.json()
    assert original["is_verified"] is False

    # Edit fields and mark verified
    update_payload = {
        "doctor": {"name": "Dr. Sarah Jenkins, MD", "specialization": "Cardiology"},
        "patient": {"name": "Robert Miller", "age": "58", "gender": "Male", "date": "12/04/2026"},
        "medicines": [
            {
                "medicine_name": "Atorvastatin",
                "strength": "20mg",
                "dosage": "1 tablet",
                "frequency": "Once daily (Night)",
                "duration": "30 days",
                "route": "Oral (Tablet)",
                "food_instructions": "After dinner",
                "special_instructions": "Take at bedtime",
                "confidence": 100.0,
                "is_unclear": False,
            }
        ],
        "is_verified": True,
    }
    update_resp = client.put(f"/api/prescription/result/{rx_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["is_verified"] is True
    assert updated["medicines"][0]["medicine_name"] == "Atorvastatin"


def test_export_pdf_and_csv():
    """Verify export to PDF and CSV formats."""
    file_path = FIXTURES_DIR / "printed_multimed.png"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("printed_multimed.png", f, "image/png")},
        )
    rx_id = upload_resp.json()["id"]
    client.post("/api/prescription/analyze", json={"id": rx_id})

    # Export PDF
    pdf_resp = client.get(f"/api/prescription/export/{rx_id}?format=pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000  # Valid non-empty PDF bytes

    # Export CSV
    csv_resp = client.get(f"/api/prescription/export/{rx_id}?format=csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    csv_text = csv_resp.text
    assert "PRESCRIPTION EXTRACTION" in csv_text
    assert "Medicine Name" in csv_text


def test_indian_clinic_handwritten_prescription():
    """Verify extraction of actual user prescription (City Care Clinic).
    
    Checks:
    - Clinic header: City Care Clinic
    - Doctor: Dr. S. Kumar, MBBS, MD, Reg # 123456, Contact 080-12345678
    - Patient: Ramesh K, Bengaluru, Date 04/11/2025
    - Diagnosis: URTI, Fever
    - Advice: Rest, plenty of fluids
    - Paracetamol: 650 mg (not 50 mg), 5 days, After food
    - Azithromycin: 500 mg, 3 days, After food
    - Cetirizine: 10 mg, 5 days, at bedtime
    - Pantoprazole: 40 mg, 5 days, Before food
    - Ascoril LS: 10 ml (not 0 ml or 1 tablet), Oral (Syrup), 5 days
    """
    file_path = FIXTURES_DIR / "actual_handwritten_prescription.png"
    with open(file_path, "rb") as f:
        upload_resp = client.post(
            "/api/prescription/upload",
            files={"file": ("actual_handwritten_prescription.png", f, "image/png")},
        )
    assert upload_resp.status_code == 200
    rx_id = upload_resp.json()["id"]

    analyze_resp = client.post(
        "/api/prescription/analyze",
        json={"id": rx_id, "apply_clahe": True, "apply_deskew": False, "use_gpu": True},
    )
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()

    # Clinic Header
    assert res.get("clinic_header") is not None
    assert "City Care Clinic" in res["clinic_header"]

    # Doctor Details
    doc = res["doctor"]
    assert "Kumar" in doc["name"]
    assert "MBBS" in doc["qualification"] or "MD" in doc["qualification"]
    assert "123456" in doc["registration_number"]
    assert "080-12345678" in doc["contact_number"]

    # Patient Details
    pat = res["patient"]
    assert "Ramesh" in pat["name"]
    assert "Bengaluru" in pat["address"]
    assert "2025" in pat["date"] and "04" in pat["date"]

    # Clinical Findings
    assert "URTI" in res["diagnosis"] or "Fever" in res["diagnosis"]
    assert "fluids" in res["advice"].lower() or "rest" in res["advice"].lower()

    # Medicines Verification
    meds = res["medicines"]
    assert len(meds) >= 5

    # 1. Paracetamol 650 mg
    pcm = next((m for m in meds if "Paracetamol" in m["medicine_name"]), None)
    assert pcm is not None, "Paracetamol not found"
    assert "650" in pcm["strength"], f"Expected 650 mg but got {pcm['strength']}"
    assert "50 mg" != pcm["strength"].strip()
    assert "5 days" in pcm["duration"]
    assert "After food" in pcm["food_instructions"]
    assert "Tablet" in pcm["route"]

    # 2. Azithromycin 500 mg
    az = next((m for m in meds if "Azithromycin" in m["medicine_name"]), None)
    assert az is not None, "Azithromycin not found"
    assert "500" in az["strength"]
    assert "3 days" in az["duration"]
    assert "After food" in az["food_instructions"]

    # 3. Cetirizine 10 mg
    cet = next((m for m in meds if "Cetirizine" in m["medicine_name"]), None)
    assert cet is not None, "Cetirizine not found"
    assert "10" in cet["strength"]
    assert "5 days" in cet["duration"]

    # 4. Pantoprazole 40 mg
    panto = next((m for m in meds if "Pantoprazole" in m["medicine_name"]), None)
    assert panto is not None, "Pantoprazole not found"
    assert "40" in panto["strength"]
    assert "Before food" in panto["food_instructions"]

    # 5. Ascoril LS syrup - 10 ml, NOT 0 ml and NOT 1 tablet!
    ascoril = next((m for m in meds if "Ascoril" in m["medicine_name"]), None)
    assert ascoril is not None, "Ascoril LS not found"
    assert "10 ml" in ascoril["dosage"], f"Expected 10 ml dosage but got {ascoril['dosage']}"
    assert "0 ml" != ascoril["dosage"].strip()
    assert "tablet" not in ascoril["dosage"].lower()
    assert "Syrup" in ascoril["route"]
    assert "5 days" in ascoril["duration"]


