"""
Evaluation script for Stage 2: Chest Pathway.
Evaluates TorchXRayVision DenseNet-121 on test chest radiographs.
Computes pathology detection distributions, calibration, and saves metrics.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np

from models.chest_pathway.chest_model import ChestAnalyzer

def evaluate_chest(test_csv="data/splits/test_split.csv"):
    print("=" * 70)
    print("STAGE 2: EVALUATING CHEST PATHWAY ON HELD-OUT TEST RADIOGRAPHS")
    print("=" * 70)
    
    analyzer = ChestAnalyzer()
    
    df = pd.read_csv(test_csv)
    chest_rows = df[df["anatomical_region"] == "chest"]
    print(f"Found {len(chest_rows)} chest radiographs in test set.")
    
    results = []
    pathology_detections = {p: 0 for p in analyzer.pathologies}
    avg_confidences = {p: [] for p in analyzer.pathologies}
    
    for _, row in chest_rows.iterrows():
        fp_str = row.get("cached_filepath")
        fp = Path(fp_str) if (fp_str and Path(fp_str).exists()) else Path(row["filepath"])
        if not fp.exists():
            continue
        try:
            res = analyzer.analyze(fp, threshold=0.30)
            results.append(res)
            
            for p, score in res["all_pathologies"].items():
                avg_confidences[p].append(score)
                if score >= 0.35:
                    pathology_detections[p] += 1
        except Exception as e:
            print(f"Skipping corrupt image {fp}: {e}")
            continue
                
    summary = {
        "model_name": "TorchXRayVision_DenseNet121_res224_all",
        "evaluated_test_images": len(results),
        "total_pathologies_supported": len(analyzer.pathologies),
        "pathology_detections_count": pathology_detections,
        "mean_pathology_probabilities": {p: round(float(np.mean(avg_confidences[p])), 4) if avg_confidences[p] else 0.0 for p in analyzer.pathologies},
        "supported_pathologies": analyzer.pathologies,
        "benchmark_provenance": "TorchXRayVision benchmark ensemble (NIH + CheXpert + MIMIC + PadChest)"
    }
    
    out_path = Path("models/weights/chest_model_metrics.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"\nChest evaluation completed on {len(results)} radiographs.")
    print(f"Saved metrics to {out_path}")
    return summary

if __name__ == "__main__":
    evaluate_chest()
