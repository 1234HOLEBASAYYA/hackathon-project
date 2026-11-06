import torch
from torchvision import transforms
import torchvision.transforms.functional as TF
from PIL import Image
from pathlib import Path
import numpy as np

try:
    from training.config import IMAGE_SIZE, NORM_MEAN, NORM_STD
except ImportError:
    from config import IMAGE_SIZE, NORM_MEAN, NORM_STD


class EnsureRGB:
    """Ensure the input image is 3-channel RGB (Chest X-Rays are often 1-channel grayscale)."""
    def __call__(self, img):
        if img.mode != "RGB":
            return img.convert("RGB")
        return img


class SquarePad:
    """
    Pad the shorter dimension to make the image square before resizing.
    This prevents severe aspect-ratio compression of chest radiographs that can
    falsely cluster normal bronchovascular markings into looking like consolidation.
    """
    def __call__(self, image):
        w, h = image.size
        max_wh = max(w, h)
        hp = int((max_wh - w) / 2)
        vp = int((max_wh - h) / 2)
        padding = (hp, vp, max_wh - w - hp, max_wh - h - vp)
        return TF.pad(image, padding, 0, 'constant')


def get_train_transforms():
    """
    Data augmentation and normalization for training.
    Carefully tuned for medical chest radiographs:
    - SquarePad preserves lung anatomy aspect ratio
    - Gentle rotation (patient positioning variation)
    - Gentle horizontal flip (anatomical symmetry)
    - Gentle contrast & brightness jitter (X-ray tube exposure variation)
    """
    return transforms.Compose([
        EnsureRGB(),
        SquarePad(),
        transforms.Resize(IMAGE_SIZE, antialias=True),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=7),
        transforms.ColorJitter(brightness=0.08, contrast=0.08),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])


def get_eval_transforms():
    """Deterministic preprocessing for validation, test, and inference."""
    return transforms.Compose([
        EnsureRGB(),
        SquarePad(),
        transforms.Resize(IMAGE_SIZE, antialias=True),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])


def preprocess_image(image_source):
    """
    Preprocess a single image for inference.
    Accepts: file path (str, bytes, Path), PIL.Image, or numpy.ndarray.
    Returns: torch.Tensor with shape (1, 3, 224, 224)
    """
    if isinstance(image_source, (str, bytes, Path)) or hasattr(image_source, "read"):
        pil_img = Image.open(str(image_source)).convert("RGB")
    elif isinstance(image_source, Image.Image):
        pil_img = image_source.convert("RGB")
    elif isinstance(image_source, np.ndarray):
        pil_img = Image.fromarray(image_source).convert("RGB")
    else:
        raise ValueError(f"Unsupported image source type: {type(image_source)}")

    transform = get_eval_transforms()
    tensor = transform(pil_img)
    return tensor.unsqueeze(0)
