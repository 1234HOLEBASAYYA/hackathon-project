"""Prescription image preprocessing and quality assessment pipeline using OpenCV."""

from __future__ import annotations

import logging
from typing import Any, TypedDict
import cv2
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


class ImageQuality(TypedDict):
    """Quality metrics for prescription image."""

    blur_variance: float
    is_blurry: bool
    contrast_score: float
    is_low_contrast: bool
    brightness_score: float
    width: int
    height: int
    quality_score: float  # Normalized 0.0 - 1.0


class PreprocessingResult(TypedDict):
    """Result of preprocessing pipeline."""

    processed_image: np.ndarray  # Enhanced image array for OCR
    preview_image: np.ndarray    # Enhanced color image for display
    quality: ImageQuality
    skew_angle: float


def assess_image_quality(image_bgr: np.ndarray) -> ImageQuality:
    """Assess sharpness, contrast, and brightness of the prescription image."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY) if len(image_bgr.shape) == 3 else image_bgr
    h, w = gray.shape[:2]

    # Laplacian variance for blur detection
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry = laplacian_var < 70.0

    # Contrast & Brightness
    contrast = float(gray.std())
    is_low_contrast = contrast < 20.0
    brightness = float(gray.mean())

    # Overall quality score (0.0 to 1.0)
    blur_norm = min(1.0, laplacian_var / 250.0)
    contrast_norm = min(1.0, contrast / 50.0)
    quality_score = round(float(0.6 * blur_norm + 0.4 * contrast_norm), 2)

    return ImageQuality(
        blur_variance=round(laplacian_var, 2),
        is_blurry=is_blurry,
        contrast_score=round(contrast, 2),
        is_low_contrast=is_low_contrast,
        brightness_score=round(brightness, 2),
        width=w,
        height=h,
        quality_score=quality_score,
    )


def correct_skew(gray: np.ndarray) -> tuple[np.ndarray, float]:
    """Detect skew angle and deskew image safely."""
    try:
        # Invert colors so text is white
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return gray, 0.0

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # If angle is negligible or too extreme, don't rotate
        if abs(angle) < 0.6 or abs(angle) > 25.0:
            return gray, 0.0

        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated, round(float(angle), 2)
    except Exception as exc:
        logger.warning("Deskew skipped: %s", exc)
        return gray, 0.0


def enhance_for_ocr(
    image_input: np.ndarray | Image.Image,
    target_width: int = 1800,
    apply_clahe: bool = True,
    apply_deskew: bool = True,
) -> PreprocessingResult:
    """Comprehensive image preparation for printed & handwritten prescription OCR.

    1. Normalizes color channels and handles PIL / numpy inputs.
    2. Resizes proportionally to standard OCR width (1800px for crisp stroke separation).
    3. Evaluates image quality (blur, contrast, brightness).
    4. Applies CLAHE (Contrast-Limited Adaptive Histogram Equalization) for faint ink strokes.
    5. Performs bilateral filtering (smoothes background paper grain while preserving sharp pen strokes).
    6. Performs deskewing to restore horizontal text alignment.
    """
    # Convert PIL Image to OpenCV BGR if necessary
    if isinstance(image_input, Image.Image):
        image_input = ImageOps.exif_transpose(image_input)
        img_np = np.array(image_input.convert("RGB"))
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    else:
        img_bgr = image_input.copy()
        if len(img_bgr.shape) == 2:
            img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_GRAY2BGR)

    # Proportional resize for optimal OCR stroke detection
    h, w = img_bgr.shape[:2]
    if w > 0 and w < target_width:
        scale = target_width / float(w)
        target_height = max(100, int(h * scale))
        img_bgr = cv2.resize(img_bgr, (target_width, target_height), interpolation=cv2.INTER_CUBIC)

    # Quality check
    quality = assess_image_quality(img_bgr)

    # Convert to grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Deskew if requested
    skew_angle = 0.0
    if apply_deskew:
        gray, skew_angle = correct_skew(gray)

    # Bilateral filter to reduce paper texture and noise while keeping ink edges crisp
    denoised = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)

    # CLAHE contrast enhancement for faint pencil/ballpoint handwriting
    if apply_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
    else:
        enhanced = denoised

    # Enhanced preview BGR
    preview_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    return PreprocessingResult(
        processed_image=enhanced,
        preview_image=preview_bgr,
        quality=quality,
        skew_angle=skew_angle,
    )
