import os
import sys
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import torchvision.models as models
import matplotlib.pyplot as plt

try:
    from training.config import (
        DEVICE, MODEL_NAME, NUM_CLASSES, CLASS_NAMES, CLASS_TO_IDX, IDX_TO_CLASS,
        IMAGE_SIZE, BATCH_SIZE, NUM_EPOCHS, LEARNING_RATE, WEIGHT_DECAY,
        NORM_MEAN, NORM_STD, MODEL_SAVE_PATH, CLASS_MAPPING_PATH, MODEL_CONFIG_PATH,
        TRAINING_CURVES_PATH, MODEL_DIR, RESULTS_DIR
    )
    from training.dataset_loader import get_dataloaders
    from training.evaluate import evaluate_model
except ImportError:
    from config import (
        DEVICE, MODEL_NAME, NUM_CLASSES, CLASS_NAMES, CLASS_TO_IDX, IDX_TO_CLASS,
        IMAGE_SIZE, BATCH_SIZE, NUM_EPOCHS, LEARNING_RATE, WEIGHT_DECAY,
        NORM_MEAN, NORM_STD, MODEL_SAVE_PATH, CLASS_MAPPING_PATH, MODEL_CONFIG_PATH,
        TRAINING_CURVES_PATH, MODEL_DIR, RESULTS_DIR
    )
    from dataset_loader import get_dataloaders
    from evaluate import evaluate_model


def build_model(num_classes=NUM_CLASSES, freeze_early_layers=True):
    """
    Initializes pretrained ResNet18 with transfer learning.
    Replaces the final fully connected layer for binary classification.
    Optionally freezes early convolutional layers (layer1, layer2) to prevent
    feature disruption and accelerate training.
    """
    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)

    if freeze_early_layers:
        # Freeze initial conv and early residual blocks
        for param in model.conv1.parameters():
            param.requires_grad = False
        for param in model.bn1.parameters():
            param.requires_grad = False
        for param in model.layer1.parameters():
            param.requires_grad = False
        for param in model.layer2.parameters():
            param.requires_grad = False

    # Replace final classification head
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, num_classes)
    )

    return model


def train_pipeline(num_epochs=NUM_EPOCHS, batch_size=BATCH_SIZE, lr=LEARNING_RATE):
    print("=" * 60)
    print("   CHEST X-RAY ABNORMALITY DETECTION MODEL TRAINING PIPELINE")
    print("=" * 60)
    print(f"Device Selected:     {DEVICE}")
    if DEVICE.type == "cuda":
        print(f"GPU Model:           {torch.cuda.get_device_name(0)}")
        print(f"Allocated VRAM:      {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("Note: Running on CPU. Efficient layer-selective transfer learning enabled.")
    
    print("\n[Step 1/5] Loading datasets and calculating class distribution...")
    train_loader, val_loader, test_loader, class_weights, train_ds, val_ds, test_ds = get_dataloaders(
        batch_size=batch_size
    )

    train_counts = train_ds.get_class_counts()
    val_counts = val_ds.get_class_counts()
    test_counts = test_ds.get_class_counts()

    print(f"Train Dataset: {len(train_ds)} samples -> NORMAL: {train_counts['NORMAL']}, PNEUMONIA: {train_counts['PNEUMONIA']}")
    print(f"Val Dataset:   {len(val_ds)} samples -> NORMAL: {val_counts['NORMAL']}, PNEUMONIA: {val_counts['PNEUMONIA']}")
    print(f"Test Dataset:  {len(test_ds)} samples -> NORMAL: {test_counts['NORMAL']}, PNEUMONIA: {test_counts['PNEUMONIA']}")
    print(f"Class Imbalance Weights for Loss: {class_weights.tolist()}")

    print("\n[Step 2/5] Initializing Pretrained ResNet18 Architecture...")
    model = build_model(num_classes=NUM_CLASSES, freeze_early_layers=True)
    model.to(DEVICE)

    criterion = nn.CrossEntropyLoss(weight=class_weights.to(DEVICE))
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.AdamW(trainable_params, lr=lr, weight_decay=WEIGHT_DECAY)
    scheduler = lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=1)

    print(f"Total Parameters:     {sum(p.numel() for p in model.parameters()):,}")
    print(f"Trainable Parameters: {sum(p.numel() for p in trainable_params):,}")

    history = {
        "train_loss": [], "train_acc": [],
        "val_loss": [], "val_acc": []
    }

    best_val_loss = float("inf")
    best_model_weights = None

    print("\n[Step 3/5] Starting Model Training & Validation Loop...")
    start_time = time.time()

    for epoch in range(1, num_epochs + 1):
        epoch_start = time.time()
        print(f"\n--- Epoch {epoch}/{num_epochs} ---")

        # Training phase
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for batch_idx, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            preds = outputs.argmax(dim=1)
            correct_train += (preds == labels).sum().item()
            total_train += labels.size(0)

            if (batch_idx + 1) % 40 == 0 or (batch_idx + 1) == len(train_loader):
                batch_acc = (preds == labels).float().mean().item() * 100
                print(f"  Batch {batch_idx + 1:3d}/{len(train_loader)}: Loss = {loss.item():.4f}, Acc = {batch_acc:.1f}%")

        epoch_train_loss = running_loss / total_train
        epoch_train_acc = correct_train / total_train

        # Validation phase
        model.eval()
        running_val_loss = 0.0
        correct_val = 0
        total_val = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                outputs = model(inputs)
                loss = criterion(outputs, labels)

                running_val_loss += loss.item() * inputs.size(0)
                preds = outputs.argmax(dim=1)
                correct_val += (preds == labels).sum().item()
                total_val += labels.size(0)

        epoch_val_loss = running_val_loss / max(1, total_val)
        epoch_val_acc = correct_val / max(1, total_val)

        scheduler.step(epoch_val_loss)

        history["train_loss"].append(round(epoch_train_loss, 4))
        history["train_acc"].append(round(epoch_train_acc, 4))
        history["val_loss"].append(round(epoch_val_loss, 4))
        history["val_acc"].append(round(epoch_val_acc, 4))

        epoch_duration = time.time() - epoch_start
        print(f"Epoch {epoch} Summary: Train Loss = {epoch_train_loss:.4f}, Train Acc = {epoch_train_acc*100:.2f}% | Val Loss = {epoch_val_loss:.4f}, Val Acc = {epoch_val_acc*100:.2f}% | Time: {epoch_duration:.1f}s")

        if epoch_val_loss < best_val_loss or best_model_weights is None:
            best_val_loss = epoch_val_loss
            best_model_weights = model.state_dict().copy()
            print(f"  (*) New best validation performance! Saving checkpoint...")

    total_training_time = time.time() - start_time
    print(f"\nTraining completed in {total_training_time:.1f} seconds ({total_training_time/60:.2f} mins).")

    print("\n[Step 4/5] Saving Model Artifacts and Preprocessing Config...")
    if best_model_weights is not None:
        model.load_state_dict(best_model_weights)

    # Save trained PyTorch model state dict
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"Saved trained model to: {MODEL_SAVE_PATH}")

    # Also save checkpoint to training results for archival
    torch.save(model.state_dict(), RESULTS_DIR / "chest_xray_model.pth")

    # Save class mapping
    class_mapping = {
        "class_to_idx": CLASS_TO_IDX,
        "idx_to_class": IDX_TO_CLASS,
        "classes": CLASS_NAMES
    }
    with open(CLASS_MAPPING_PATH, "w") as f:
        json.dump(class_mapping, f, indent=2)
    with open(RESULTS_DIR / "class_mapping.json", "w") as f:
        json.dump(class_mapping, f, indent=2)
    print(f"Saved class mapping to: {CLASS_MAPPING_PATH}")

    # Save model configuration & preprocessing params
    model_config = {
        "model_architecture": MODEL_NAME,
        "pretrained": True,
        "input_image_size": list(IMAGE_SIZE),
        "input_channels": 3,
        "normalization": {
            "mean": NORM_MEAN,
            "std": NORM_STD
        },
        "classes": CLASS_NAMES,
        "num_classes": NUM_CLASSES,
        "training_epochs": num_epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "weight_decay": WEIGHT_DECAY,
        "device_used": str(DEVICE),
        "total_training_time_sec": round(total_training_time, 2)
    }
    with open(MODEL_CONFIG_PATH, "w") as f:
        json.dump(model_config, f, indent=2)
    with open(RESULTS_DIR / "model_config.json", "w") as f:
        json.dump(model_config, f, indent=2)
    print(f"Saved model config to: {MODEL_CONFIG_PATH}")

    # Plot Training & Validation Curves
    plt.figure(figsize=(12, 5))
    epochs_range = range(1, num_epochs + 1)

    # Loss subplot
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, history["train_loss"], "b-o", label="Train Loss", linewidth=2)
    plt.plot(epochs_range, history["val_loss"], "r--s", label="Val Loss", linewidth=2)
    plt.title("Loss Curves (Training vs Validation)", fontsize=12)
    plt.xlabel("Epoch", fontsize=10)
    plt.ylabel("Cross-Entropy Loss", fontsize=10)
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)

    # Accuracy subplot
    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, [acc * 100 for acc in history["train_acc"]], "b-o", label="Train Accuracy", linewidth=2)
    plt.plot(epochs_range, [acc * 100 for acc in history["val_acc"]], "r--s", label="Val Accuracy", linewidth=2)
    plt.title("Accuracy Curves (Training vs Validation)", fontsize=12)
    plt.xlabel("Epoch", fontsize=10)
    plt.ylabel("Accuracy (%)", fontsize=10)
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(TRAINING_CURVES_PATH, dpi=200)
    plt.close()
    print(f"Saved training curves to: {TRAINING_CURVES_PATH}")

    print("\n[Step 5/5] Evaluating Best Model on Held-out Test Dataset...")
    eval_metrics = evaluate_model(model=model, test_loader=test_loader, save_results=True)

    print("\nPipeline execution completed successfully!")
    return model, history, eval_metrics


if __name__ == "__main__":
    epochs = 4
    if len(sys.argv) > 1:
        try:
            epochs = int(sys.argv[1])
        except ValueError:
            pass
    train_pipeline(num_epochs=epochs)
