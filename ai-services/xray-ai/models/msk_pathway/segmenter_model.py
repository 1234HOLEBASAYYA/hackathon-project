"""
Stage 2: Musculoskeletal Fracture Segmentation Model (U-Net).
Provides pixel-level damage segmentation where ground-truth fracture masks
are available (FracAtlas COCO/VGG masks).
Evaluates using Dice score (F1 on pixels) and IoU (Jaccard index).
"""

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np

class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class UNetSegmenter(nn.Module):
    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()
        self.inc = DoubleConv(in_channels, 32)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(32, 64))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(64, 128))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(128, 256))
        
        self.up1 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.conv_up1 = DoubleConv(256, 128)
        
        self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.conv_up2 = DoubleConv(128, 64)
        
        self.up3 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.conv_up3 = DoubleConv(64, 32)
        
        self.outc = nn.Conv2d(32, out_channels, 1)
        
    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        
        x = self.up1(x4)
        x = torch.cat([x, x3], dim=1)
        x = self.conv_up1(x)
        
        x = self.up2(x)
        x = torch.cat([x, x2], dim=1)
        x = self.conv_up2(x)
        
        x = self.up3(x)
        x = torch.cat([x, x1], dim=1)
        x = self.conv_up3(x)
        
        logits = self.outc(x)
        return logits

def dice_coefficient(pred_mask, gt_mask, eps=1e-6):
    inter = (pred_mask * gt_mask).sum()
    union = pred_mask.sum() + gt_mask.sum()
    return (2.0 * inter + eps) / (union + eps)

def iou_score(pred_mask, gt_mask, eps=1e-6):
    inter = (pred_mask * gt_mask).sum()
    union = pred_mask.sum() + gt_mask.sum() - inter
    return (inter + eps) / (union + eps)

def predict_segmentation_mask(model, image_input, orig_w=None, orig_h=None, threshold=0.5, device="cpu"):
    """
    Inference helper for pixel-level fracture segmentation.
    Returns:
      mask_binary: 2D numpy array [H, W] of 0/1
      has_segmentation: bool
      coverage_pct: float
    """
    model.eval()
    if isinstance(image_input, (str, bytes)):
        img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        img = image_input
        
    w, h = (orig_w, orig_h) if (orig_w and orig_h) else img.size
    
    t = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    tensor = t(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits).squeeze(0).squeeze(0).cpu().numpy()
        
    mask_224 = (probs >= threshold).astype(np.uint8)
    # Resize back to original dimensions
    mask_img = Image.fromarray(mask_224 * 255).resize((w, h), resample=Image.NEAREST)
    mask_full = (np.array(mask_img) > 127).astype(np.uint8)
    
    coverage = float(mask_full.sum()) / float(w * h) * 100.0
    return {
        "mask_binary": mask_full,
        "has_damage_mask": bool(mask_full.sum() > 50),
        "damage_area_percentage": round(coverage, 2),
        "peak_pixel_probability": round(float(probs.max()), 4)
    }
