"""Pydantic schemas for prescription REST API."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response returned upon uploading a prescription file."""

    id: str
    filename: str
    file_type: str
    size_bytes: int
    preview_url: str
    message: str = "File uploaded successfully"


class AnalyzeRequest(BaseModel):
    """Request payload to trigger OCR analysis."""

    id: str
    use_gpu: bool = True
    apply_clahe: bool = True
    apply_deskew: bool = True


class MedicineSchema(BaseModel):
    """Structured medicine record."""

    medicine_name: str
    strength: str = "Not detected"
    dosage: str = "Not detected"
    frequency: str = "Not detected"
    duration: str = "Not detected"
    route: str = "Not detected"
    food_instructions: str = "Not detected"
    special_instructions: str = "Not detected"
    confidence: float = 100.0
    is_unclear: bool = False


class DoctorSchema(BaseModel):
    """Extracted doctor details."""

    name: str = "Not detected"
    qualification: str = "Not detected"
    specialization: str = "Not detected"
    registration_number: str = "Not detected"
    clinic_or_hospital: str = "Not detected"
    contact_number: str = "Not detected"


class PatientSchema(BaseModel):
    """Extracted patient details."""

    name: str = "Not detected"
    age: str = "Not detected"
    gender: str = "Not detected"
    address: str = "Not detected"
    date: str = "Not detected"
    patient_id: str = "Not detected"


class BoundingBoxSchema(BaseModel):
    """Detected word bounding box."""

    x: int
    y: int
    width: int
    height: int
    polygon: list[list[int]] = Field(default_factory=list)
    text: str
    confidence: float


class ImageQualitySchema(BaseModel):
    """Image quality assessment."""

    blur_variance: float
    is_blurry: bool
    contrast_score: float
    is_low_contrast: bool
    brightness_score: float
    width: int
    height: int
    quality_score: float


class PrescriptionResultSchema(BaseModel):
    """Complete prescription extraction result."""

    id: str
    filename: str
    preview_url: str
    clinic_header: str = "Not detected"
    doctor: DoctorSchema
    patient: PatientSchema
    diagnosis: str = "Not detected"
    advice: str = "Not detected"
    follow_up: str = "Not detected"
    medicines: list[MedicineSchema]
    raw_text: str
    quality: ImageQualitySchema | None = None
    bounding_boxes: list[BoundingBoxSchema] = Field(default_factory=list)
    is_verified: bool = False
    notes: list[str] = Field(default_factory=list)
    engine_used: str = "EasyOCR (GPU Accelerated)"
    created_at: str
    updated_at: str


class UpdateResultRequest(BaseModel):
    """Payload to update extracted prescription fields and verification state."""

    clinic_header: str | None = None
    doctor: DoctorSchema | None = None
    patient: PatientSchema | None = None
    diagnosis: str | None = None
    advice: str | None = None
    follow_up: str | None = None
    medicines: list[MedicineSchema] | None = None
    raw_text: str | None = None
    is_verified: bool | None = None
    notes: list[str] | None = None


class HealthResponse(BaseModel):
    """System health check response."""

    status: str = "ok"
    version: str = "1.0.0"
    device: str
    gpu_name: str | None = None
    ocr_engine: str
    supported_formats: list[str] = ["jpg", "jpeg", "png", "pdf"]
