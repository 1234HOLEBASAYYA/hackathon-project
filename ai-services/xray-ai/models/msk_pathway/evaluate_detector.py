"""
Evaluation script for Stage 2: Musculoskeletal Damage Localization & Fracture Detection Model.
Evaluates on independent held-out test split (data/splits/test_split.csv).
Computes:
  - Classification: Accuracy, Precision, Recall, F1, Sensitivity, Specificity, AUROC, Confusion Matrix
  - Localization: mIoU, mAP@50, mAP@75, Localization Precision/Recall
  - Bone Identification: Top-1 Accuracy
Saves metrics to models/weights/msk_damage_detector_metrics.json and confusion matrix plot.
"""

import os
import sys
import json
import ast
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import torch
from torch.utils.data import TensorDataset, DataLoader
from torchvision import transforms
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score, roc_auc_score
)

from models.msk_pathway.detector_model import MSKDamageDetector, BONE_CLASSES, BONE_TO_IDX

def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    
    inter = max(0.0, xB - xA) * max(0.0, yB - yA)
    areaA = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    areaB = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0.0

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

def load_test_msk(test_csv="data/splits/test_split.csv"):
    df = pd.read_csv(test_csv)
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

def evaluate_msk_detector(checkpoint_path="models/weights/msk_damage_detector.pt", test_csv="data/splits/test_split.csv", device="cpu"):
    print("=" * 70)
    print("STAGE 2: EVALUATING MSK DAMAGE DETECTOR ON HELD-OUT TEST SET")
    print("=" * 70)
    
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = MSKDamageDetector().to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    
    X_te, y_lbl_te, y_box_te, y_has_te, y_bone_te = load_test_msk(test_csv)
    print(f"Loaded {len(X_te)} MSK test samples.")
    test_loader = DataLoader(TensorDataset(X_te, y_lbl_te, y_box_te, y_has_te, y_bone_te), batch_size=32, shuffle=False)
    
    all_targets = []
    all_probs = []
    all_preds = []
    
    ious = []
    map50_hits = []
    map75_hits = []
    
    bone_targets = []
    bone_preds = []
    
    with torch.no_grad():
        for imgs, lbls, gt_boxes, has_boxes, bone_idx in test_loader:
            imgs = imgs.to(device)
            labels_np = lbls.numpy()
            gt_boxes_np = gt_boxes.numpy()
            has_boxes_np = has_boxes.numpy()
            bone_idx_np = bone_idx.numpy()
            
            out = model(imgs)
            probs = torch.sigmoid(out["abnormality_logits"]).cpu().numpy()
            pred_labels = (probs >= 0.5).astype(int)
            pred_boxes = out["boxes"].cpu().numpy()
            p_bones = out["bone_logits"].argmax(dim=1).cpu().numpy()
            
            all_targets.extend(labels_np)
            all_probs.extend(probs)
            all_preds.extend(pred_labels)
            bone_targets.extend(bone_idx_np)
            bone_preds.extend(p_bones)
            
            for i in range(len(has_boxes_np)):
                if has_boxes_np[i] == 1.0:
                    iou = compute_iou(pred_boxes[i], gt_boxes_np[i])
                    ious.append(iou)
                    map50_hits.append(1 if (iou >= 0.5 and pred_labels[i] == 1) else 0)
                    map75_hits.append(1 if (iou >= 0.75 and pred_labels[i] == 1) else 0)
                    
    all_targets = np.array(all_targets)
    all_probs = np.array(all_probs)
    all_preds = np.array(all_preds)
    
    acc = accuracy_score(all_targets, all_preds)
    prec = precision_score(all_targets, all_preds, zero_division=0)
    rec = recall_score(all_targets, all_preds, zero_division=0)
    f1 = f1_score(all_targets, all_preds, zero_division=0)
    
    try:
        auroc = roc_auc_score(all_targets, all_probs)
    except Exception:
        auroc = 0.5
        
    cm = confusion_matrix(all_targets, all_preds)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    miou = float(np.mean(ious)) if ious else 0.0
    map50 = float(np.mean(map50_hits)) if map50_hits else 0.0
    map75 = float(np.mean(map75_hits)) if map75_hits else 0.0
    bone_acc = accuracy_score(bone_targets, bone_preds)
    
    print("\n--- TEST EVALUATION RESULTS ---")
    print(f"Classification Metrics:")
    print(f"  Accuracy:    {acc*100:.2f}%")
    print(f"  Precision:   {prec:.4f}")
    print(f"  Recall:      {rec:.4f} (Sensitivity: {sensitivity*100:.2f}%)")
    print(f"  Specificity: {specificity*100:.2f}%")
    print(f"  F1-Score:    {f1:.4f}")
    print(f"  AUROC:       {auroc:.4f}")
    print(f"\nDamage Localization Metrics (IoU & Detection):")
    print(f"  Mean IoU:    {miou:.4f}")
    print(f"  mAP@50:      {map50*100:.2f}%")
    print(f"  mAP@75:      {map75*100:.2f}%")
    print(f"  Bone Accuracy: {bone_acc*100:.2f}%")
    
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    cm_path = reports_dir / "confusion_matrix_msk.png"
    
    plt.figure(figsize=(5, 4))
    plt.imshow(cm, cmap=plt.cm.Greens)
    plt.title("MSK Fracture Classification Confusion Matrix")
    plt.colorbar()
    plt.xticks([0, 1], ["Normal", "Fractured"])
    plt.yticks([0, 1], ["Normal", "Fractured"])
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max()/2 else "black")
    plt.ylabel("Ground Truth")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=200)
    plt.close()
    
    metrics = {
        "model_name": "MSKDamageDetector_MultiTask_ResNet18",
        "dataset_split": "test",
        "test_samples_count": len(X_te),
        "classification": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "sensitivity": round(float(sensitivity), 4),
            "specificity": round(float(specificity), 4),
            "f1_score": round(float(f1), 4),
            "auroc": round(float(auroc), 4),
            "confusion_matrix": cm.tolist()
        },
        "localization": {
            "mean_iou": round(float(miou), 4),
            "mAP_50": round(float(map50), 4),
            "mAP_75": round(float(map75), 4),
            "annotated_boxes_evaluated": len(ious)
        },
        "bone_identification": {
            "top1_accuracy": round(float(bone_acc), 4)
        }
    }
    
    metrics_path = Path("models/weights/msk_damage_detector_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"Saved evaluation metrics to {metrics_path} and plot to {cm_path}")
    return metrics

if __name__ == "__main__":
    evaluate_msk_detector()
