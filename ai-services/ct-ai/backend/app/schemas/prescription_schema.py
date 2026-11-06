from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class MedicationItem(BaseModel):
    name: str
    class_: str = Field(..., alias="class")
    indicated_for: str
    dosage: str
    frequency: str

    class Config:
        populate_by_name = True


class RespiratoryMarker(BaseModel):
    keyword: str
    significance: str


class PrescriptionAnalysisRequest(BaseModel):
    text: Optional[str] = None


class PrescriptionAnalysisResponse(BaseModel):
    summary: str
    detected_medications: List[Dict[str, Any]]
    medications: Optional[List[Dict[str, Any]]] = None
    respiratory_signs: List[Dict[str, str]]
    clinical_warnings: List[str]
    doctor_guidance: List[str]
    raw_text: Optional[str] = None
    report_title: Optional[str] = "Clinical Prescription Analysis Report"
    modality: Optional[str] = "prescription_doc"
    patient_id: Optional[str] = "guest_patient_001"
    prescription_id: Optional[str] = None
    analysis_id: Optional[str] = None
    status: Optional[str] = "success"
