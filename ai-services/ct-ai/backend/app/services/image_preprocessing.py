import torch
from torchvision import transforms
import torchvision.transforms.functional as TF
from PIL import Image
from pathlib import Path
import numpy as np

# ImageNet normalization parameters (strictly identical to training)
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]
IMAGE_SIZE = (224, 224)


class EnsureRGB:
    """Ensure grayscale chest X-rays are converted to 3-channel RGB."""
    def __call__(self, img):
        if img.mode != "RGB":
            return img.convert("RGB")
        return img


class SquarePad:
    """
    Pad the shorter dimension to make the image square before resizing.
    Prevents squeezing and compressing natural bronchovascular markings.
    """
    def __call__(self, image):
        w, h = image.size
        max_wh = max(w, h)
        hp = int((max_wh - w) / 2)
        vp = int((max_wh - h) / 2)
        padding = (hp, vp, max_wh - w - hp, max_wh - h - vp)
        return TF.pad(image, padding, 0, 'constant')


def get_inference_transforms():
    """Deterministic preprocessing matching evaluation/training normalization."""
    return transforms.Compose([
        EnsureRGB(),
        SquarePad(),
        transforms.Resize(IMAGE_SIZE, antialias=True),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])


def preprocess_chest_xray(image_source):
    """
    Preprocess image source into a normalized 4D tensor ready for ResNet18.
    Accepts: file path (str, Path), PIL Image, or numpy array.
    Returns: torch.Tensor of shape (1, 3, 224, 224), PIL.Image original
    """
    if isinstance(image_source, (str, bytes, Path)) or hasattr(image_source, "read"):
        pil_img = Image.open(str(image_source)).convert("RGB")
    elif isinstance(image_source, Image.Image):
        pil_img = image_source.convert("RGB")
    elif isinstance(image_source, np.ndarray):
        pil_img = Image.fromarray(image_source).convert("RGB")
    else:
        raise ValueError(f"Unsupported image type: {type(image_source)}")

    transforms_pipeline = get_inference_transforms()
    tensor = transforms_pipeline(pil_img)
    return tensor.unsqueeze(0), pil_img
