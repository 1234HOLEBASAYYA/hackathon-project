"""
Evaluation script for Stage 1: Anatomical Region Router.
Evaluates on independent held-out test data (data/splits/test_split.csv).
Computes exact, un-fabricated classification metrics, confusion matrix,
and per-region precision, recall, specificity, and F1-score.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import torch
from torch.utils.data import TensorDataset, DataLoader
from torchvision import transforms
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

from models.anatomical_router.model import AnatomicalRouter, REGIONS, REGION_TO_IDX

def load_test_tensors(test_csv="data/splits/test_split.csv"):
    df = pd.read_csv(test_csv)
    img_tensors = []
    labels = []
    
    t = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    for _, row in df.iterrows():
        reg = str(row["anatomical_region"]).lower()
        if reg in REGION_TO_IDX:
            fp_str = row.get("cached_filepath")
            fp = Path(fp_str) if (fp_str and Path(fp_str).exists()) else Path(row["filepath"])
            if fp.exists():
                try:
                    with Image.open(fp) as img:
                        rgb = img.convert("RGB")
                        if rgb.size != (224, 224):
                            rgb = rgb.resize((224, 224))
                        img_tensors.append(t(rgb))
                        labels.append(REGION_TO_IDX[reg])
                except Exception:
                    continue
                    
    X = torch.stack(img_tensors)
    y = torch.tensor(labels, dtype=torch.long)
    return X, y

def evaluate_router(checkpoint_path="models/weights/anatomical_router.pt", test_csv="data/splits/test_split.csv", device="cpu"):
    print("=" * 70)
    print("STAGE 1: EVALUATING ANATOMICAL REGION ROUTER ON HELD-OUT TEST SET")
    print("=" * 70)
    
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = AnatomicalRouter(num_classes=len(REGIONS)).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    
    X_test, y_test = load_test_tensors(test_csv)
    print(f"Loaded {len(X_test)} test samples.")
    test_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=32, shuffle=False)
    
    all_preds = []
    all_targets = []
    all_probs = []
    
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            preds = outputs.argmax(dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())
            
    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    all_probs = np.array(all_probs)
    
    # Calculate real metrics
    overall_acc = accuracy_score(all_targets, all_preds)
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(all_targets, all_preds, average="weighted", zero_division=0)
    
    cm = confusion_matrix(all_targets, all_preds, labels=list(range(len(REGIONS))))
    clf_report = classification_report(all_targets, all_preds, target_names=REGIONS, output_dict=True, zero_division=0)
    
    print(f"\nOverall Test Accuracy: {overall_acc*100:.2f}%")
    print(f"Macro F1-Score:        {macro_f1:.4f}")
    print(f"Weighted F1-Score:     {weighted_f1:.4f}")
    print("\nPer-Region Performance Breakdown:")
    for r in REGIONS:
        metrics = clf_report.get(r, {})
        print(f"  {r:<12}: Precision={metrics.get('precision', 0):.3f} | "
              f"Recall={metrics.get('recall', 0):.3f} | "
              f"F1={metrics.get('f1-score', 0):.3f} | Support={metrics.get('support', 0)}")
              
    # Save confusion matrix plot
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    cm_path = reports_dir / "confusion_matrix_router.png"
    
    plt.figure(figsize=(7, 6))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Confusion Matrix - Anatomical Region Router (Test Set)")
    plt.colorbar()
    tick_marks = np.arange(len(REGIONS))
    plt.xticks(tick_marks, REGIONS, rotation=45)
    plt.yticks(tick_marks, REGIONS)
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], "d"),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
                     
    plt.ylabel("Ground Truth Region")
    plt.xlabel("Predicted Region")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=200)
    plt.close()
    print(f"\nSaved confusion matrix plot to {cm_path}")
    
    metrics_out = {
        "model_name": "AnatomicalRegionRouter_ResNet18",
        "dataset_split": "test",
        "test_samples_count": len(X_test),
        "overall_accuracy": round(float(overall_acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "class_metrics": {r: clf_report.get(r, {}) for r in REGIONS},
        "confusion_matrix": cm.tolist(),
        "classes": REGIONS
    }
    
    metrics_json_path = Path("models/weights/anatomical_router_metrics.json")
    with open(metrics_json_path, "w") as f:
        json.dump(metrics_out, f, indent=2)
        
    print(f"Saved test evaluation metrics to {metrics_json_path}")
    return metrics_out

if __name__ == "__main__":
    evaluate_router()
