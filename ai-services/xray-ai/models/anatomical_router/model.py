"""
Stage 1: Anatomical Region Identification & Routing Model.
Classifies input radiographs into anatomical categories:
  - wrist
  - hand
  - leg
  - hip
  - shoulder
  - chest
Includes confidence gating to flag out-of-distribution or ambiguous inputs
as 'uncertain' / 'unsupported' rather than forcing a false positive classification.
"""

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
from PIL import Image

REGIONS = ["wrist", "hand", "leg", "hip", "shoulder", "chest"]
REGION_TO_IDX = {r: i for i, r in enumerate(REGIONS)}
IDX_TO_REGION = {i: r for i, r in enumerate(REGIONS)}

UNCERTAIN_THRESHOLD = 0.50

class AnatomicalRouter(nn.Module):
    def __init__(self, num_classes=len(REGIONS), dropout_p=0.3):
        super().__init__()
        self.num_classes = num_classes
        # Use ResNet-18 backbone
        backbone = models.resnet18(weights=None)
        
        # Modify first conv to accept single-channel (grayscale) or 3-channel
        # We use standard 3-channel input by repeating grayscale across channels
        self.features = nn.Sequential(*list(backbone.children())[:-1])
        in_features = backbone.fc.in_features
        
        self.classifier = nn.Sequential(
            nn.Dropout(p=dropout_p),
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_p),
            nn.Linear(256, num_classes)
        )
        
    def forward(self, x):
        feats = self.features(x)
        feats = torch.flatten(feats, 1)
        logits = self.classifier(feats)
        return logits

def get_router_transforms(is_train=False):
    if is_train:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
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

def predict_region(model, image_input, device="cpu"):
    """
    Inference helper with confidence gating.
    Returns:
      region: str ('wrist', 'hand', 'leg', 'hip', 'shoulder', 'chest', or 'unsupported')
      confidence: float (0.0 to 1.0)
      probabilities: dict {region: score}
      is_uncertain: bool
    """
    model.eval()
    if isinstance(image_input, (str, bytes)):
        img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        img = image_input
        
    t = get_router_transforms(is_train=False)
    tensor = t(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()
        
    top_idx = int(probs.argmax())
    top_score = float(probs[top_idx])
    prob_dict = {REGIONS[i]: float(probs[i]) for i in range(len(REGIONS))}
    
    is_uncertain = top_score < UNCERTAIN_THRESHOLD
    pred_region = REGIONS[top_idx] if not is_uncertain else "unsupported"
    
    return {
        "predicted_region": pred_region,
        "raw_top_region": REGIONS[top_idx],
        "confidence": top_score,
        "is_uncertain": is_uncertain,
        "probabilities": prob_dict,
        "supported": not is_uncertain
    }
