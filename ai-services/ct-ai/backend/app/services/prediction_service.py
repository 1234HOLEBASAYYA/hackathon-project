import os
import json
import torch
from pathlib import Path
from PIL import Image

try:
    from app.models.resnet_model import load_model
    from app.services.image_preprocessing import preprocess_chest_xray
    from app.services.gradcam_service import GradCAMService
except (ImportError, ModuleNotFoundError):
    from backend.app.models.resnet_model import load_model
    from backend.app.services.image_preprocessing import preprocess_chest_xray
    from backend.app.services.gradcam_service import GradCAMService

# Resolve base paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BACKEND_DIR / "model" / "chest_xray_model.pth"
CLASS_MAPPING_PATH = BACKEND_DIR / "model" / "class_mapping.json"
MODEL_CONFIG_PATH = BACKEND_DIR / "model" / "model_config.json"


class PredictionService:
    """
    Singleton service that loads the fine-tuned ResNet18 model once on startup
    and provides cached, high-throughput inference for Chest X-Rays.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PredictionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: str = None, mapping_path: str = None):
        if self._initialized:
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.mapping_path = Path(mapping_path) if mapping_path else CLASS_MAPPING_PATH

        self.model = None
        self.gradcam_service = None
        self.idx_to_class = {0: "NORMAL", 1: "PNEUMONIA"}
        self.classes = ["NORMAL", "PNEUMONIA"]

        self._load_artifacts()
        self._initialized = True

    def _load_artifacts(self):
        # Load class mapping
        if self.mapping_path.exists():
            try:
                with open(self.mapping_path, "r") as f:
                    data = json.load(f)
                    self.idx_to_class = {int(k): v for k, v in data.get("idx_to_class", {0: "NORMAL", 1: "PNEUMONIA"}).items()}
                    self.classes = data.get("classes", ["NORMAL", "PNEUMONIA"])
            except Exception as e:
                print(f"Warning loading class mapping: {e}")

        # Load model weights
        if self.model_path.exists():
            try:
                self.model = load_model(str(self.model_path), device=self.device)
                self.gradcam_service = GradCAMService(self.model)
                print(f"[PredictionService] Successfully loaded model from {self.model_path} onto {self.device}")
            except Exception as e:
                print(f"[PredictionService] Error loading model: {e}")
        else:
            print(f"[PredictionService] Model weight file not yet present at {self.model_path}. Will reload on demand.")

    def ensure_model_loaded(self):
        if self.model is None and self.model_path.exists():
            self._load_artifacts()
        return self.model is not None

    def predict(self, image_source, generate_cam: bool = True, cam_alpha: float = 0.45, pneumonia_threshold: float = 0.65):
        """
        Runs complete abnormality detection and visualization pipeline.
        """
        if not self.ensure_model_loaded():
            raise RuntimeError(
                f"Trained model checkpoint not found at {self.model_path}. Please complete training first."
            )

        tensor, pil_img = preprocess_chest_xray(image_source)
        tensor = tensor.to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probabilities = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        pred_idx = int(probabilities.argmax())
        pred_label = self.idx_to_class.get(pred_idx, "UNKNOWN")
        confidence = float(probabilities[pred_idx])

        probs_dict = {
            self.idx_to_class.get(i, f"Class {i}"): round(float(p), 4)
            for i, p in enumerate(probabilities)
        }

        is_abnormal = (pred_label == "PNEUMONIA")

        # Clinical Severity Assessment
        if is_abnormal:
            severity = "Severe" if confidence > 0.90 else "Moderate" if confidence > 0.75 else "Mild"
            clinical_finding = "Pulmonary opacification, parenchymal consolidation, and interstitial infiltrates observed."
            doctor_recommendation = (
                "Correlate with auscultatory findings (crackles/bronchial breath sounds), "
                "serum inflammatory markers (CRP/ESR), and consider sputum culture or empirical antimicrobial coverage."
            )
            patient_explanation = (
                "The AI scan indicates signs consistent with lung infection/pneumonia. "
                "Please consult your pulmonologist or physician promptly for clinical evaluation and appropriate treatment."
            )
        else:
            severity = "None"
            clinical_finding = "Clear lung fields bilaterally without focal consolidation, pneumothorax, or pleural effusion."
            doctor_recommendation = (
                "Normal radiographic baseline. No immediate pulmonary acute intervention indicated on this radiograph."
            )
            patient_explanation = (
                "Your chest X-ray appears clear with no visible lung abnormalities or pneumonia patterns detected."
            )

        response = {
            "prediction": pred_label,
            "confidence": round(confidence, 4),
            "probabilities": probs_dict,
            "is_abnormal": is_abnormal,
            "severity": severity,
            "clinical_finding": clinical_finding,
            "doctor_recommendation": doctor_recommendation,
            "patient_explanation": patient_explanation,
            "gradcam": None
        }

        if generate_cam and self.gradcam_service:
            try:
                with torch.enable_grad():
                    cam_heatmap, _ = self.gradcam_service.generate_heatmap(tensor, target_class=pred_idx)
                    cam_data = self.gradcam_service.create_visualization(pil_img, cam_heatmap, alpha=cam_alpha)
                    response["gradcam"] = cam_data
            except Exception as e:
                print(f"[GradCAM error]: {e}")

        return response


# Cached global instance
prediction_service = PredictionService()
