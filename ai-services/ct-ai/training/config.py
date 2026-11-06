import os
import torch
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
TRAINING_DIR = BASE_DIR / "training"
BACKEND_DIR = BASE_DIR / "backend"
MODEL_DIR = BACKEND_DIR / "model"
RESULTS_DIR = TRAINING_DIR / "training_results"

# Locate dataset directory
DATASET_DIR = BASE_DIR / "dataset" / "chest_xray"
if not DATASET_DIR.exists():
    fallback_dataset = BASE_DIR / "chest_xray"
    if fallback_dataset.exists():
        DATASET_DIR = fallback_dataset

TRAIN_DIR = DATASET_DIR / "train"
VAL_DIR = DATASET_DIR / "val"
TEST_DIR = DATASET_DIR / "test"

# Hardware Device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model & Hyperparameters
MODEL_NAME = "resnet18"
NUM_CLASSES = 2
CLASS_NAMES = ["NORMAL", "PNEUMONIA"]
CLASS_TO_IDX = {"NORMAL": 0, "PNEUMONIA": 1}
IDX_TO_CLASS = {0: "NORMAL", 1: "PNEUMONIA"}

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
NUM_WORKERS = 0  # 0 for Windows multiprocessing safety
NUM_EPOCHS = 5
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

# Normalization constants (ImageNet standards)
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]

# Output artifact paths
MODEL_SAVE_PATH = MODEL_DIR / "chest_xray_model.pth"
CLASS_MAPPING_PATH = MODEL_DIR / "class_mapping.json"
MODEL_CONFIG_PATH = MODEL_DIR / "model_config.json"

METRICS_JSON_PATH = RESULTS_DIR / "metrics.json"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "confusion_matrix.png"
TRAINING_CURVES_PATH = RESULTS_DIR / "training_curves.png"

# Ensure output directories exist
MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
