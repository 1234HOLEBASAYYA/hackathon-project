"""
Stage 2: Chest Radiograph Cardiopulmonary Analysis Pathway.
Integrates TorchXRayVision DenseNet-121 pretrained on NIH, CheXpert, MIMIC, PadChest.
Supports 18 cardiopulmonary pathologies:
  - Cardiomegaly, Pneumonia, Pneumothorax, Effusion, Atelectasis, Consolidation,
    Edema, Emphysema, Fibrosis, Infiltration, Mass, Nodule, Pleural Thickening,
    Hernia, Lung Lesion, Fracture, Lung Opacity, Enlarged Cardiomediastinum.
"""

import os
import sys
import torch
import numpy as np
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import torchxrayvision as xrv
from pathlib import Path

CHEST_WEIGHTS_PATH = Path("models/weights/densenet121-res224-all.pt")

class ChestAnalyzer:
    def __init__(self, weights_path=str(CHEST_WEIGHTS_PATH), device="cpu"):
        self.device = device
        print(f"Loading Chest Pathology DenseNet-121 model from {weights_path}...")
        self.model = xrv.models.DenseNet(weights="densenet121-res224-all")
        self.model.to(device)
        self.model.eval()
        self.pathologies = self.model.pathologies
        print(f"ChestAnalyzer loaded successfully with {len(self.pathologies)} supported pathologies.")
        
    def preprocess_image(self, img_input):
        if isinstance(img_input, (str, Path)):
            img = Image.open(img_input).convert("L")
        elif isinstance(img_input, Image.Image):
            img = img_input.convert("L")
        else:
            img = Image.fromarray(img_input).convert("L")
            
        arr = np.array(img)
        # TorchXRayVision expected input range: [-1024, 1024]
        # xrv.datasets.normalize scales [0, 255] to [-1024, 1024]
        norm_img = xrv.datasets.normalize(arr, 255)
        # Add channel and batch dims: [1, 1, H, W]
        tensor = torch.from_numpy(norm_img).unsqueeze(0).unsqueeze(0).float()
        # Resize to 224x224
        tensor = torch.nn.functional.interpolate(tensor, size=(224, 224), mode="bilinear", align_corners=False)
        return tensor.to(self.device), arr

    def analyze(self, img_input, threshold=0.35):
        """
        Runs chest radiograph inference.
        Returns:
          findings: list of detected pathologies with confidence scores
          all_probabilities: dict of all 18 pathologies
          top_finding: str
          top_confidence: float
          is_abnormal: bool
          model_name: str
        """
        tensor, raw_arr = self.preprocess_image(img_input)
        
        with torch.no_grad():
            preds = self.model(tensor)
            probs = torch.sigmoid(preds).squeeze(0).cpu().numpy()
            
        prob_dict = {self.pathologies[i]: round(float(probs[i]), 4) for i in range(len(self.pathologies))}
        
        # Sort findings by probability descending
        sorted_findings = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
        
        positive_findings = []
        for name, score in sorted_findings:
            if score >= threshold:
                positive_findings.append({
                    "pathology": name,
                    "confidence": score,
                    "severity_indicator": "High" if score >= 0.70 else "Moderate"
                })
                
        is_abnormal = len(positive_findings) > 0
        top_name, top_conf = sorted_findings[0]
        
        return {
            "is_abnormal": is_abnormal,
            "top_finding": top_name if is_abnormal else "No Cardiopulmonary Abnormality Detected",
            "top_confidence": top_conf,
            "detected_findings": positive_findings,
            "all_pathologies": prob_dict,
            "supported_pathologies_count": len(self.pathologies),
            "model_version": "TorchXRayVision DenseNet-121 (All-Datasets)",
            "limitations": "Model trained on adult chest radiographs. Non-diagnostic screening aid only."
        }
