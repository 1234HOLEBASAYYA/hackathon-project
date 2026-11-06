"""
Fast In-Memory Training Script for Stage 1: Anatomical Region Router.
Optimized for 8-core CPU execution:
  - Pre-buffers 224x224 cached images into RAM (zero disk I/O in epoch loops)
  - Utilizes all 8 logical CPU cores (torch.set_num_threads(8))
  - Employs transfer learning by fine-tuning deep feature representations (layers 3 & 4 + classifier)
  - Evaluates on held-out test split and saves metrics + confusion matrix
"""

import os
import sys
import json
import time
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from torchvision import transforms

from models.anatomical_router.model import AnatomicalRouter, REGIONS, REGION_TO_IDX
from models.anatomical_router.evaluate import evaluate_router

# Set CPU threads to maximum available
NUM_THREADS = os.cpu_count() or 4
torch.set_num_threads(NUM_THREADS)

def load_split_to_tensors(split_csv: str):
    df = pd.read_csv(split_csv)
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
                    
    if not img_tensors:
        raise ValueError(f"No valid images loaded from {split_csv}")
        
    X = torch.stack(img_tensors)
    y = torch.tensor(labels, dtype=torch.long)
    return X, y

def train_router_fast(epochs=4, batch_size=32, lr=5e-4):
    print("=" * 70, flush=True)
    print(f"STAGE 1 ROUTER FAST IN-MEMORY TRAINING ({NUM_THREADS} CPU Threads)", flush=True)
    print("=" * 70, flush=True)
    
    t0 = time.time()
    print("Buffering train and validation sets into memory...", flush=True)
    X_train, y_train = load_split_to_tensors("data/splits/train_split.csv")
    X_val, y_val = load_split_to_tensors("data/splits/val_split.csv")
    print(f"RAM buffered: {len(X_train)} train, {len(X_val)} val samples ({time.time()-t0:.1f}s)", flush=True)
    
    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=batch_size, shuffle=False)
    
    # Class weights to handle class imbalance
    counts = np.bincount(y_train.numpy(), minlength=len(REGIONS))
    counts = np.maximum(counts, 1.0)
    weights = len(y_train) / (len(REGIONS) * counts)
    weights = torch.tensor(np.clip(weights, 0.2, 5.0), dtype=torch.float32)
    print(f"Class weights: {[round(w, 2) for w in weights.tolist()]}", flush=True)
    
    model = AnatomicalRouter(num_classes=len(REGIONS))
    
    # Freeze early layers (conv1, bn1, layer1, layer2) to save ~60% FLOPs
    for name, param in model.features.named_parameters():
        if any(prefix in name for prefix in ["0.", "1.", "4.", "5."]):
            param.requires_grad = False
            
    criterion = nn.CrossEntropyLoss(weight=weights)
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_val_acc = 0.0
    best_state = None
    history = []
    
    weights_dir = Path("models/weights")
    weights_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = weights_dir / "anatomical_router.pt"
    
    for epoch in range(1, epochs + 1):
        st = time.time()
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for imgs, lbls in train_loader:
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, lbls)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * imgs.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == lbls).sum().item()
            total += lbls.size(0)
            
        scheduler.step()
        train_loss = running_loss / total
        train_acc = correct / total
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for imgs, lbls in val_loader:
                outputs = model(imgs)
                loss = criterion(outputs, lbls)
                val_loss += loss.item() * imgs.size(0)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == lbls).sum().item()
                val_total += lbls.size(0)
                
        val_loss = val_loss / val_total
        val_acc = val_correct / val_total
        dur = time.time() - st
        
        print(f"Epoch {epoch}/{epochs} ({dur:.1f}s) | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc*100:.2f}% | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc*100:.2f}%", flush=True)
              
        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "duration_s": dur
        })
        
        if val_acc > best_val_acc or best_state is None:
            best_val_acc = val_acc
            best_state = model.state_dict().copy()
            # Save intermediate best checkpoint immediately
            torch.save({
                "model_state_dict": best_state,
                "classes": REGIONS,
                "best_val_acc": best_val_acc,
                "history": history,
                "trained_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }, checkpoint_path)
            
    print(f"\nTraining Complete! Best Val Acc: {best_val_acc*100:.2f}%. Saved to {checkpoint_path}", flush=True)
    
    with open(weights_dir / "anatomical_router_history.json", "w") as f:
        json.dump(history, f, indent=2)
        
    # Evaluate on held-out test split
    print("\nRunning Evaluation on Test Split...", flush=True)
    evaluate_router()
    return checkpoint_path

if __name__ == "__main__":
    train_router_fast(epochs=4, batch_size=32, lr=5e-4)
