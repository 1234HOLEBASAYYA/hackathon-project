from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    relative_x: Optional[float] = None
    relative_y: Optional[float] = None
    relative_width: Optional[float] = None
    relative_height: Optional[float] = None


class GradCAMData(BaseModel):
    overlay_b64: str
    heatmap_b64: str
    rois: List[BoundingBox] = []
    opacity_score: float = 0.0


class ImageAnalysisResponse(BaseModel):
    prediction: str = Field(..., description="NORMAL or PNEUMONIA")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    probabilities: Dict[str, float]
    is_abnormal: bool
    severity: str
    clinical_finding: str
    doctor_recommendation: str
    patient_explanation: str
    gradcam: Optional[GradCAMData] = None
    filename: Optional[str] = None
    timestamp: Optional[str] = None
    analysis_id: Optional[str] = None
    patient_id: Optional[str] = "guest_patient_001"
    report_title: Optional[str] = "Chest Radiograph Abnormality Report"
    modality: Optional[str] = "chest_xray"
    status: Optional[str] = "success"


class ImageAnalysisRequest(BaseModel):
    generate_gradcam: bool = True
    alpha: float = 0.45
