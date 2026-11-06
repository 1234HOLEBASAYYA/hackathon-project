"""
Stage 2: Musculoskeletal Damage Localization & Fracture Detection Model.
Multi-task neural network capable of:
  1. Abnormality & fracture detection (binary probability)
  2. Exact spatial damage localization: normalized bounding box [xmin, ymin, xmax, ymax]
  3. Affected bone structure identification (radius, ulna, femur, tibia, clavicle, etc.)
  4. Displacement characterization (undisplaced vs displaced)
"""

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import numpy as np

BONE_CLASSES = [
    "distal_radius",
    "distal_ulna",
    "metacarpals_or_phalanges",
    "femur_or_hip",
    "tibia_or_fibula",
    "clavicle_or_shoulder",
    "other_unspecified_bone"
]
BONE_TO_IDX = {b: i for i, b in enumerate(BONE_CLASSES)}
IDX_TO_BONE = {i: b for i, b in enumerate(BONE_CLASSES)}

DISPLACEMENT_CLASSES = ["undisplaced", "displaced", "unspecified"]

class MSKDamageDetector(nn.Module):
    def __init__(self, num_bones=len(BONE_CLASSES)):
        super().__init__()
        # Backbone: ResNet-18
        backbone = models.resnet18(weights=None)
        self.features = nn.Sequential(*list(backbone.children())[:-2]) # 512 x 7 x 7
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        
        in_features = 512
        
        # 1. Abnormality/Fracture detection head
        self.abnormality_head = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 1)
        )
        
        # 2. Bounding Box Regression head (predicts [xmin, ymin, xmax, ymax] normalized in [0, 1])
        self.box_head = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 4),
            nn.Sigmoid() # Keeps coordinates strictly within [0, 1]
        )
        
        # 3. Affected bone structure head
        self.bone_head = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_bones)
        )
        
        # 4. Displacement / alignment head
        self.displacement_head = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, len(DISPLACEMENT_CLASSES))
        )
        
    def forward(self, x):
        feat_map = self.features(x) # [B, 512, 7, 7]
        pooled = self.pool(feat_map)
        pooled = torch.flatten(pooled, 1) # [B, 512]
        
        abnormality_logits = self.abnormality_head(pooled).squeeze(1) # [B]
        box_coords = self.box_head(pooled) # [B, 4] -> [xmin, ymin, xmax, ymax]
        bone_logits = self.bone_head(pooled) # [B, num_bones]
        disp_logits = self.displacement_head(pooled) # [B, 3]
        
        return {
            "abnormality_logits": abnormality_logits,
            "boxes": box_coords,
            "bone_logits": bone_logits,
            "displacement_logits": disp_logits,
            "feature_map": feat_map
        }

def get_msk_transforms(is_train=False):
    if is_train:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.3),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

def predict_damage_localization(model, image_input, orig_w=None, orig_h=None, device="cpu"):
    """
    Inference helper for damage detection and bounding box localization.
    """
    model.eval()
    if isinstance(image_input, (str, bytes)):
        img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        img = image_input
        
    w, h = (orig_w, orig_h) if (orig_w and orig_h) else img.size
    
    t = get_msk_transforms(is_train=False)
    tensor = t(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        out = model(tensor)
        prob = torch.sigmoid(out["abnormality_logits"]).item()
        box_norm = out["boxes"].squeeze(0).cpu().numpy().tolist()
        bone_probs = torch.softmax(out["bone_logits"], dim=1).squeeze(0).cpu().numpy()
        disp_probs = torch.softmax(out["displacement_logits"], dim=1).squeeze(0).cpu().numpy()
        
    # Scale box from [0, 1] to original pixel dimensions
    x1, y1, x2, y2 = box_norm
    # Ensure x2 > x1 and y2 > y1
    if x2 <= x1:
        x2 = min(1.0, x1 + 0.15)
    if y2 <= y1:
        y2 = min(1.0, y1 + 0.15)
        
    pixel_box = [
        int(round(x1 * w)),
        int(round(y1 * h)),
        int(round(x2 * w)),
        int(round(y2 * h))
    ]
    
    top_bone_idx = int(bone_probs.argmax())
    top_bone = BONE_CLASSES[top_bone_idx]
    
    top_disp_idx = int(disp_probs.argmax())
    top_disp = DISPLACEMENT_CLASSES[top_disp_idx]
    
    is_fractured = prob >= 0.50
    
    findings = []
    if is_fractured:
        findings.append({
            "finding_type": "Cortical Disruption / Fracture",
            "affected_bone": top_bone,
            "displacement": top_disp,
            "confidence": round(prob, 4),
            "bbox_normalized": [round(c, 4) for c in [x1, y1, x2, y2]],
            "bbox_pixels": pixel_box
        })
    else:
        findings.append({
            "finding_type": "No Acute Fracture or Cortical Discontinuity Detected",
            "confidence": round(1.0 - prob, 4),
            "bbox_normalized": None,
            "bbox_pixels": None
        })
        
    return {
        "is_abnormal": is_fractured,
        "abnormality_confidence": round(prob, 4),
        "primary_findings": findings,
        "affected_bone": top_bone if is_fractured else "N/A",
        "displacement_assessment": top_disp if is_fractured else "N/A",
        "bounding_box_normalized": [round(c, 4) for c in [x1, y1, x2, y2]] if is_fractured else None,
        "bounding_box_pixels": pixel_box if is_fractured else None
    }
