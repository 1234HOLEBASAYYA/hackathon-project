"""Tests for prescription field extraction."""

from __future__ import annotations

from typing import Any

import pytest

from src.extractor import extract_prescription_fields


@pytest.fixture()
def mock_ocr_outputs() -> list[str]:
    """Create mock OCR outputs.

    Returns:
        Ten representative OCR text samples.
    """
    return [
        """
        Patient: John Doe
        Age: 45
        Date: 12/05/2026
        Dr. Alice Smith
        Diagnosis: Hypertension
        Rx Tab Amlodipine 5mg OD for 30 days
        Notes: Review after one month
        """,
        """
        Name - Maria Gomez
        Aged 32 years
        Dt: 2026-06-01
        Doctor: Brian Clark
        Dx: Acute bronchitis
        1. Cap Amoxicillin 500mg TDS 7 days
        Advice: Take after food
        """,
        """
        Pt: Rakesh Kumar
        Age 60 y/o
        Date 01-06-2026
        Physician: Dr Nina Patel
        Assessment: Diabetes mellitus
        Tab Metformin 500mg BD for 90 days
        Remarks: Monitor fasting sugar
        """,
        """
        Patient Name: Emily Stone
        Age: 8
        Date: 6.2.2026
        Dr Robert Hall
        Diagnosis: Fever
        Syp Paracetamol 120ml TID 5 days
        Notes: Plenty of fluids
        """,
        """
        Patient: Omar Khan
        Age: 54 yrs
        Date: 15/06/26
        Dr. Sara Lee
        Diagnosis: Gastritis
        Rx Pantoprazole 40mg OD 14 days
        Rx Domperidone 10mg BD 5 days
        Advice: Avoid spicy food
        """,
        """
        Pt: A. K. Sharma
        Age: 29
        Dt: 10/06/2026
        Dr. J. P. Taylor
        Rx Tab Paracetamol 650mg SOS for 5 days
        """,
        """
        Age: 35
        Date: 12-06-2026
        Rx Tab Ibuprofen 400mg BD for 10 days
        Notes: Take after meal
        """,
        """
        Patient: Sarah Connor
        Age: 44
        Date: 2026-06-15
        Dr. Silberman
        1. Cap Fluoxetine 20mg OD for 30 days
        - Tab Diazepam 5mg PRN 7 days
        * Tab Melatonin 3mg QHS 15 days
        """,
        """
        Patient: Bruce Wayne
        Age: 38
        Date: 17/06/2026
        Dr. Leslie Thompkins
        • Tab Multivitamin 1 tab OD 90 days
        • Cap Vitamin D3 60k weekly 4 weeks
        """,
        """
        Diagnosis: Generalized Anxiety Disorder
        """,
    ]


def test_extract_patient_name_from_mock_outputs(mock_ocr_outputs: list[str]) -> None:
    """Test patient-name regex extraction across sample OCR text."""
    expected = ["John Doe", "Maria Gomez", "Rakesh Kumar", "Emily Stone", "Omar Khan"]
    for text, name in zip(mock_ocr_outputs[:5], expected):
        assert extract_prescription_fields(text)["patient_name"] == name


def test_extract_age_from_mock_outputs(mock_ocr_outputs: list[str]) -> None:
    """Test age regex extraction across sample OCR text."""
    expected = ["45", "32", "60", "8", "54"]
    for text, age in zip(mock_ocr_outputs[:5], expected):
        assert extract_prescription_fields(text)["patient_age"] == age


def test_extract_date_from_mock_outputs(mock_ocr_outputs: list[str]) -> None:
    """Test date regex extraction across sample OCR text."""
    expected = ["12/05/2026", "2026-06-01", "01-06-2026", "6.2.2026", "15/06/26"]
    for text, date in zip(mock_ocr_outputs[:5], expected):
        assert extract_prescription_fields(text)["date"] == date


def test_extract_diagnosis_and_notes(mock_ocr_outputs: list[str]) -> None:
    """Test diagnosis and notes extraction."""
    first = extract_prescription_fields(mock_ocr_outputs[0])
    assert first["diagnosis"] == "Hypertension"
    assert first["notes"] == "Review after one month"


def test_extract_medicines_from_mock_outputs(mock_ocr_outputs: list[str]) -> None:
    """Test medicine extraction from all mock OCR outputs."""
    extracted = [extract_prescription_fields(text) for text in mock_ocr_outputs[:5]]
    assert extracted[0]["medicines"][0]["name"] == "Amlodipine"
    assert extracted[1]["medicines"][0]["dosage"] == "500mg"
    assert extracted[2]["medicines"][0]["frequency"].lower() == "twice daily"
    assert extracted[3]["medicines"][0]["duration"] == "5 days"
    assert len(extracted[4]["medicines"]) == 2


def test_extractor_confidence_and_nulls(mock_ocr_outputs: list[str]) -> None:
    """Test that confidence scores are between 0.0 and 1.0, and missing fields are None."""
    for text in mock_ocr_outputs:
        result = extract_prescription_fields(text)

        # Check top-level confidences
        assert "confidences" in result
        for field, score in result["confidences"].items():
            assert 0.0 <= score <= 1.0, f"Confidence for {field} is {score}, out of bounds!"

        # Check medicine-level confidences
        for med in result["medicines"]:
            assert 0.0 <= med["confidence"] <= 1.0
            assert "confidences" in med
            for f, s in med["confidences"].items():
                assert 0.0 <= s <= 1.0

    # Test sample 7 (index 6): patient_name and doctor_name should be None (null)
    missing_fields_res = extract_prescription_fields(mock_ocr_outputs[6])
    assert missing_fields_res["patient_name"] is None
    assert missing_fields_res["doctor_name"] is None

    # Check frequency mapping in sample 6 (index 5): SOS -> As needed
    sos_res = extract_prescription_fields(mock_ocr_outputs[5])
    assert sos_res["medicines"][0]["frequency"] == "As needed"

    # Check multi-drug list in sample 8 (index 7)
    multi_res = extract_prescription_fields(mock_ocr_outputs[7])
    assert len(multi_res["medicines"]) == 3
    assert multi_res["medicines"][0]["name"] == "Fluoxetine"
    assert multi_res["medicines"][1]["frequency"] == "As needed"  # PRN -> As needed


def test_extract_prescription_fields_uses_openai_when_configured(
    monkeypatch: pytest.MonkeyPatch,
    mock_ocr_outputs: list[str],
) -> None:
    """Test OpenAI-backed extraction without calling the real API."""

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": """
                            {
                              "patient_name": "OpenAI Patient",
                              "patient_age": "45",
                              "date": "12/05/2026",
                              "doctor_name": "Dr. Alice Smith",
                              "diagnosis": "Hypertension",
                              "notes": "Review after one month",
                              "medicines": [
                                {
                                  "name": "Amlodipine",
                                  "dosage": "5mg",
                                  "frequency": "Once daily",
                                  "duration": "30 days",
                                  "confidence": 0.95,
                                  "confidences": {
                                    "name": 0.95,
                                    "dosage": 0.95,
                                    "frequency": 0.95,
                                    "duration": 0.95
                                  }
                                }
                              ],
                              "confidences": {
                                "patient_name": 0.95,
                                "patient_age": 0.95,
                                "date": 0.95,
                                "doctor_name": 0.95,
                                "diagnosis": 0.95,
                                "notes": 0.95,
                                "medicines": 0.95
                              }
                            }
                            """
                        }
                    }
                ]
            }

    def fake_post(*args: Any, **kwargs: Any) -> FakeResponse:
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert kwargs["json"]["model"] == "gpt-4.1-mini"
        return FakeResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("src.llm.httpx.post", fake_post)

    result = extract_prescription_fields(
        mock_ocr_outputs[0],
        {"llm": {"provider": "openai", "model": "gpt-4.1-mini"}},
    )

    assert result["patient_name"] == "OpenAI Patient"
    assert result["medicines"][0]["frequency"] == "Once daily"
