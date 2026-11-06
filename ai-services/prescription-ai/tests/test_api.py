"""Tests for FastAPI endpoints."""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from PIL import Image

from src.api import app

client = TestClient(app)


def test_health() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_ocr_rejects_non_image() -> None:
    """Test that non-image formats are rejected by validation."""
    files = {"file": ("test.txt", b"some text content", "text/plain")}
    response = client.post("/ocr", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_ocr_black_image() -> None:
    """Test that a completely black image is rejected with an HTTP 400."""
    img = Image.new("RGB", (10, 10), color=0)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    files = {"file": ("black.png", img_bytes, "image/png")}
    response = client.post("/ocr", files=files)
    assert response.status_code == 400
    assert "black" in response.json()["detail"].lower()


@patch("src.api.process_image_array")
def test_ocr_batch(mock_process: patch) -> None:
    """Test batch OCR processing with multiple files."""
    mock_process.return_value = {
        "extracted_fields": {
            "patient_name": "Test Patient",
            "patient_age": "30",
            "date": "17/06/2026",
            "doctor_name": "Dr. House",
            "medicines": [],
            "diagnosis": "None",
            "notes": "None",
            "confidences": {}
        },
        "ocr": {"raw_text": "Mock text", "confidence": 0.95, "engine_used": "mock", "word_boxes": []},
        "preprocessing": {"confidence": 0.9},
        "medicine_validation": {"valid": True, "suggestions": [], "flagged": []},
        "confidence": {"ocr": 0.95, "preprocessing": 0.9}
    }

    # Generate a tiny valid image to pass decode_image check
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    files = [
        ("files", ("image1.png", img_bytes, "image/png")),
        ("files", ("image2.png", img_bytes, "image/png")),
        ("files", ("image3.png", img_bytes, "image/png")),
    ]
    response = client.post("/ocr/batch", files=files)
    assert response.status_code == 200
    res_json = response.json()
    assert isinstance(res_json, list)
    assert len(res_json) == 3

    for item in res_json:
        assert item["filename"] in ["image1.png", "image2.png", "image3.png"]
        assert item["status"] == "success"
        assert item["data"]["extracted_fields"]["patient_name"] == "Test Patient"
        assert "request_id" in item
        assert item["request_id"] != ""
        assert "X-Request-ID" in response.headers
