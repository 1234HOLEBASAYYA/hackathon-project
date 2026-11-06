"""
Fast In-Memory Training Script for Stage 2: MSK Damage Localization & Fracture Detector.
Multi-task ResNet-18 optimization:
  - Binary fracture classification
  - Spatial damage localization (Smooth L1 Bounding Box regression)
  - Affected bone structure identification (6 bone classes)
Optimized for 8-core CPU execution with in-memory tensor buffering.
"""

import os
import sys
import json
import time
import ast
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from torchvision import transforms

from models.msk_pathway.detector_model import (
    MSKDamageDetector, BONE_CLASSES, BONE_TO_IDX, get_msk_transforms
)
from models.msk_pathway.evaluate_detector import evaluate_msk_detector

NUM_THREADS = os.cpu_count() or 4
torch.set_num_threads(NUM_THREADS)

def map_bone_to_idx(region: str, box_label: str = None) -> int:
    region = str(region).lower()
    lbl = str(box_label).lower() if box_label else ""
    if "radius" in lbl:
        return BONE_TO_IDX["distal_radius"]
    elif "ulna" in lbl:
        return BONE_TO_IDX["distal_ulna"]
    elif "femur" in lbl or "hip" in lbl or region == "hip":
        return BONE_TO_IDX["femur_or_hip"]
    elif "tibia" in lbl or "fibula" in lbl or region == "leg":
        return BONE_TO_IDX["tibia_or_fibula"]
    elif "clavicle" in lbl or "shoulder" in lbl or region == "shoulder":
        return BONE_TO_IDX["clavicle_or_shoulder"]
    elif region == "hand":
        return BONE_TO_IDX["metacarpals_or_phalanges"]
    elif region == "wrist":
        return BONE_TO_IDX["distal_radius"]
    return BONE_TO_IDX["other_unspecified_bone"]

def load_msk_tensors(split_csv: str):
    df = pd.read_csv(split_csv)
    img_list = []
    labels_list = []
    boxes_list = []
    has_boxes_list = []
    bones_list = []
    
    t = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    for _, row in df.iterrows():
        reg = str(row["anatomical_region"]).lower()
        if reg in ("wrist", "hand", "leg", "hip", "shoulder", "mixed"):
            fp_str = row.get("cached_filepath")
            fp = Path(fp_str) if (fp_str and Path(fp_str).exists()) else Path(row["filepath"])
            if not fp.exists():
                continue
                
            try:
                with Image.open(fp) as img:
                    rgb = img.convert("RGB")
                    if rgb.size != (224, 224):
                        rgb = rgb.resize((224, 224))
                    img_tensor = t(rgb)
            except Exception:
                continue
                
            is_frac = float(row.get("fracture_label", 0))
            
            # Parse bounding box
            boxes_val = row.get("bounding_boxes", "[]")
            if isinstance(boxes_val, str):
                try:
                    raw_boxes = ast.literal_eval(boxes_val)
                except Exception:
                    raw_boxes = []
            elif isinstance(boxes_val, list):
                raw_boxes = boxes_val
            else:
                raw_boxes = []
                
            first_box = [0.25, 0.25, 0.75, 0.75]
            has_b = 0.0
            box_lbl = ""
            
            if raw_boxes and len(raw_boxes) > 0:
                b_info = raw_boxes[0]
                box_lbl = b_info.get("label", "")
                coords = b_info.get("bbox", [])
                if len(coords) == 4:
                    has_b = 1.0
                    try:
                        raw_fp = Path(row["filepath"])
                        with Image.open(raw_fp) as tmp_img:
                            ow, oh = tmp_img.size
                        x1, y1, x2, y2 = coords
                        nx1 = np.clip(float(x1) / max(1, ow), 0.0, 1.0)
                        ny1 = np.clip(float(y1) / max(1, oh), 0.0, 1.0)
                        nx2 = np.clip(float(x2) / max(1, ow), 0.0, 1.0)
                        ny2 = np.clip(float(y2) / max(1, oh), 0.0, 1.0)
                        if nx2 > nx1 and ny2 > ny1:
                            first_box = [nx1, ny1, nx2, ny2]
                    except Exception:
                        pass
                        
            bone_idx = map_bone_to_idx(reg, box_lbl)
            
            img_list.append(img_tensor)
            labels_list.append(is_frac)
            boxes_list.append(first_box)
            has_boxes_list.append(has_b)
            bones_list.append(bone_idx)
            
    X = torch.stack(img_list)
    y_lbl = torch.tensor(labels_list, dtype=torch.float32)
    y_box = torch.tensor(boxes_list, dtype=torch.float32)
    y_has = torch.tensor(has_boxes_list, dtype=torch.float32)
    y_bone = torch.tensor(bones_list, dtype=torch.long)
    return X, y_lbl, y_box, y_has, y_bone

def train_msk_fast(epochs=4, batch_size=32, lr=4e-4):
    print("=" * 70, flush=True)
    print(f"STAGE 2: FAST IN-MEMORY MSK DAMAGE DETECTOR TRAINING ({NUM_THREADS} CPU Threads)", flush=True)
    print("=" * 70, flush=True)
    
    t0 = time.time()
    print("Buffering MSK train and val sets into memory...", flush=True)
    X_tr, y_lbl_tr, y_box_tr, y_has_tr, y_bone_tr = load_msk_tensors("data/splits/train_split.csv")
    X_va, y_lbl_va, y_box_va, y_has_va, y_bone_va = load_msk_tensors("data/splits/val_split.csv")
    print(f"RAM buffered: {len(X_tr)} train, {len(X_va)} val samples ({time.time()-t0:.1f}s)", flush=True)
    
    train_loader = DataLoader(TensorDataset(X_tr, y_lbl_tr, y_box_tr, y_has_tr, y_bone_tr), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_va, y_lbl_va, y_box_va, y_has_va, y_bone_va), batch_size=batch_size, shuffle=False)
    
    model = MSKDamageDetector()
    
    # Freeze early layers (conv1, bn1, layer1, layer2)
    for name, param in model.features.named_parameters():
        if any(prefix in name for prefix in ["0.", "1.", "4.", "5."]):
            param.requires_grad = False
            
    bce_loss = nn.BCEWithLogitsLoss()
    smooth_l1 = nn.SmoothL1Loss(reduction="none")
    ce_loss = nn.CrossEntropyLoss()
    
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_score = 0.0
    best_state = None
    history = []
    
    weights_dir = Path("models/weights")
    weights_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = weights_dir / "msk_damage_detector.pt"
    
    for epoch in range(1, epochs + 1):
        st = time.time()
        model.train()
        total_loss = 0.0
        n_samples = 0
        correct_frac = 0
        
        for imgs, lbls, gt_boxes, has_boxes, bone_indices in train_loader:
            optimizer.zero_grad()
            out = model(imgs)
            
            l_cls = bce_loss(out["abnormality_logits"], lbls)
            box_diff = smooth_l1(out["boxes"], gt_boxes).mean(dim=1)
            l_box = (box_diff * (lbls * 0.7 + has_boxes * 0.3)).mean()
            l_bone = ce_loss(out["bone_logits"], bone_indices)
            
            loss = l_cls + 2.5 * l_box + 0.4 * l_bone
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item() * imgs.size(0)
            preds = (torch.sigmoid(out["abnormality_logits"]) >= 0.5).float()
            correct_frac += (preds == lbls).sum().item()
            n_samples += imgs.size(0)
            
        scheduler.step()
        train_loss = total_loss / n_samples
        train_acc = correct_frac / n_samples
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_n = 0
        val_iou_sum = 0.0
        val_box_count = 0
        
        with torch.no_grad():
            for imgs, lbls, gt_boxes, has_boxes, bone_indices in val_loader:
                out = model(imgs)
                l_cls = bce_loss(out["abnormality_logits"], lbls)
                box_diff = smooth_l1(out["boxes"], gt_boxes).mean(dim=1)
                l_box = (box_diff * (lbls * 0.7 + has_boxes * 0.3)).mean()
                l_bone = ce_loss(out["bone_logits"], bone_indices)
                
                v_loss = l_cls + 2.5 * l_box + 0.4 * l_bone
                val_loss += v_loss.item() * imgs.size(0)
                
                preds = (torch.sigmoid(out["abnormality_logits"]) >= 0.5).float()
                val_correct += (preds == lbls).sum().item()
                val_n += imgs.size(0)
                
                pred_b = out["boxes"].cpu().numpy()
                gt_b = gt_boxes.cpu().numpy()
                has_b = has_boxes.cpu().numpy()
                for i in range(len(has_b)):
                    if has_b[i] == 1.0:
                        px1, py1, px2, py2 = pred_b[i]
                        gx1, gy1, gx2, gy2 = gt_b[i]
                        ix1 = max(px1, gx1)
                        iy1 = max(py1, gy1)
                        ix2 = min(px2, gx2)
                        iy2 = min(py2, gy2)
                        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                        union = (px2 - px1)*(py2 - py1) + (gx2 - gx1)*(gy2 - gy1) - inter
                        iou = inter / union if union > 0 else 0.0
                        val_iou_sum += iou
                        val_box_count += 1
                        
        val_loss = val_loss / val_n
        val_acc = val_correct / val_n
        val_miou = val_iou_sum / val_box_count if val_box_count > 0 else 0.0
        dur = time.time() - st
        
        print(f"Epoch {epoch}/{epochs} ({dur:.1f}s) | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc*100:.2f}% | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc*100:.2f}% | mIoU: {val_miou:.3f}", flush=True)
              
        score = float(val_acc) * 0.6 + float(val_miou) * 0.4
        history.append({
            "epoch": int(epoch),
            "train_loss": round(float(train_loss), 4),
            "train_acc": round(float(train_acc), 4),
            "val_loss": round(float(val_loss), 4),
            "val_acc": round(float(val_acc), 4),
            "val_miou": round(float(val_miou), 4),
            "duration_s": round(float(dur), 1)
        })
        
        if score > best_score or best_state is None:
            best_score = score
            best_state = model.state_dict().copy()
            torch.save({
                "model_state_dict": best_state,
                "classes": BONE_CLASSES,
                "history": history,
                "best_score": best_score,
                "trained_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }, checkpoint_path)
            
    print(f"\nMSK Damage Detector Training Complete! Saved best checkpoint to {checkpoint_path}", flush=True)
    with open(weights_dir / "msk_damage_detector_history.json", "w") as f:
        json.dump(history, f, indent=2)
        
    # Evaluate on held-out test split
    print("\nRunning Evaluation on Test Split...", flush=True)
    evaluate_msk_detector()
    return checkpoint_path

if __name__ == "__main__":
    train_msk_fast(epochs=4, batch_size=32, lr=4e-4)
