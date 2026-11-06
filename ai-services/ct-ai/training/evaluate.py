import os
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)

try:
    from training.config import (
        DEVICE, TEST_DIR, NUM_CLASSES, CLASS_NAMES, CLASS_TO_IDX,
        MODEL_SAVE_PATH, METRICS_JSON_PATH, CONFUSION_MATRIX_PATH
    )
    from training.dataset_loader import SafeImageFolder, DataLoader
    from training.preprocessing import get_eval_transforms
except ImportError:
    from config import (
        DEVICE, TEST_DIR, NUM_CLASSES, CLASS_NAMES, CLASS_TO_IDX,
        MODEL_SAVE_PATH, METRICS_JSON_PATH, CONFUSION_MATRIX_PATH
    )
    from dataset_loader import SafeImageFolder, DataLoader
    from preprocessing import get_eval_transforms


def load_model_for_eval(model_path=MODEL_SAVE_PATH):
    """Loads ResNet18 model initialized with saved weights."""
    import torchvision.models as models
    import torch.nn as nn

    model = models.resnet18(weights=None)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, NUM_CLASSES)
    )

    state_dict = torch.load(model_path, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model


def evaluate_model(model=None, test_loader=None, save_results=True, threshold=0.65):
    """
    Evaluates model on held-out test dataset and computes all required clinical metrics.
    Supports decision threshold calibration to balance Normal Specificity and Pneumonia Sensitivity.
    """
    if model is None:
        model = load_model_for_eval()

    if test_loader is None:
        test_dataset = SafeImageFolder(TEST_DIR, transform=get_eval_transforms())
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)

    model.eval()
    all_targets = []
    all_probs = []

    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs = inputs.to(DEVICE)
            outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1)

            all_targets.extend(targets.numpy().tolist())
            all_probs.extend(probs.cpu().numpy().tolist())

    y_true = np.array(all_targets)
    probs_np = np.array(all_probs)
    pneu_probs = probs_np[:, 1]

    # Predictions based on calibrated threshold
    y_pred = (pneu_probs >= threshold).astype(int)

    # Calculate metrics
    acc = float(accuracy_score(y_true, y_pred))
    prec_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    prec_weighted = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    rec_weighted = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    roc_auc = float(roc_auc_score(y_true, pneu_probs))

    cm = confusion_matrix(y_true, y_pred).tolist()
    # cm: [[TN, FP], [FN, TP]]
    tn, fp = cm[0][0], cm[0][1]
    fn, tp = cm[1][0], cm[1][1]

    sensitivity = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0  # Recall for Pneumonia
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0  # True normal clearance

    report = classification_report(y_true, y_pred, target_names=CLASS_NAMES, output_dict=True)

    metrics = {
        "dataset": "Chest X-Ray (Pneumonia)",
        "total_test_samples": len(y_true),
        "decision_threshold": threshold,
        "roc_auc": round(roc_auc, 4),
        "accuracy": round(acc, 4),
        "precision_macro": round(prec_macro, 4),
        "recall_macro": round(rec_macro, 4),
        "f1_macro": round(f1_macro, 4),
        "precision_weighted": round(prec_weighted, 4),
        "recall_weighted": round(rec_weighted, 4),
        "f1_weighted": round(f1_weighted, 4),
        "sensitivity_recall_pneumonia": round(sensitivity, 4),
        "specificity_normal": round(specificity, 4),
        "confusion_matrix": {
            "matrix": cm,
            "labels": CLASS_NAMES,
            "true_negatives_normal": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives_pneumonia": tp
        },
        "per_class_report": report
    }

    print("\n" + "=" * 55)
    print(f"   HELD-OUT TEST EVALUATION (Threshold = {threshold:.2f})")
    print("=" * 55)
    print(f"Total Test Images: {len(y_true)}")
    print(f"ROC-AUC:           {roc_auc * 100:.2f}%")
    print(f"Accuracy:          {acc * 100:.2f}%")
    print(f"Specificity (TN):  {specificity * 100:.2f}% ({tn}/{tn+fp} Normal cleared)")
    print(f"Sensitivity (TP):  {sensitivity * 100:.2f}% ({tp}/{tp+fn} Pneumonia detected)")
    print(f"Precision (Macro): {prec_macro * 100:.2f}%")
    print(f"F1-Score (Macro):  {f1_macro * 100:.2f}%")
    print("-" * 55)
    print(f"Confusion Matrix:")
    print(f"  [TN={tn:3d}, FP={fp:3d}] (Actual NORMAL)")
    print(f"  [FN={fn:3d}, TP={tp:3d}] (Actual PNEUMONIA)")
    print("=" * 55 + "\n")

    if save_results:
        # Save metrics JSON
        with open(METRICS_JSON_PATH, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"Saved metrics to: {METRICS_JSON_PATH}")

        # Plot Confusion Matrix
        plt.figure(figsize=(6, 5))
        plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        plt.title(f"Confusion Matrix (Threshold={threshold:.2f})", fontsize=12, pad=15)
        plt.colorbar()
        tick_marks = np.arange(len(CLASS_NAMES))
        plt.xticks(tick_marks, CLASS_NAMES, fontsize=10)
        plt.yticks(tick_marks, CLASS_NAMES, fontsize=10)

        thresh_val = np.array(cm).max() / 2.0
        for i in range(len(CLASS_NAMES)):
            for j in range(len(CLASS_NAMES)):
                plt.text(
                    j, i, format(cm[i][j], "d"),
                    horizontalalignment="center",
                    color="white" if cm[i][j] > thresh_val else "black",
                    fontsize=12, fontweight="bold"
                )

        plt.ylabel("True Label", fontsize=11)
        plt.xlabel("Predicted Label", fontsize=11)
        plt.tight_layout()
        plt.savefig(CONFUSION_MATRIX_PATH, dpi=200)
        plt.close()
        print(f"Saved confusion matrix plot to: {CONFUSION_MATRIX_PATH}")

    return metrics


if __name__ == "__main__":
    evaluate_model()
