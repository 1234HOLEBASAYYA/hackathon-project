"""
Image Preprocessing Service for MedVision-AI CT Scan Image Analyzer
Handles secure validation, decoding, dimension extraction, aspect-ratio-preserving
resizing, and format normalization without distorting clinical visual features.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageOps
import cv2
import numpy as np

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "dcm", "dicom"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
MAX_DIMENSION = 2048  # Maximum width or height for safe Gemini transmission


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation checks."""
    pass


class IncompatibleImageModalityError(ImageValidationError):
    """Raised when an incompatible image type (e.g., prescription, document, regular photo) is uploaded to the CT module."""
    def __init__(self, detected_modality: str, message: str):
        super().__init__(message)
        self.detected_modality = detected_modality
        self.message = message


def detect_image_modality(pil_image: Image.Image, filename: str = "") -> Dict[str, Any]:
    """
    Evaluates visual density, intensity distribution, color variance, and text edge signatures
    to categorize the image into:
    - 'ct_scan': Axial/Thoracic CT scan with dark peripheral background.
    - 'chest_xray': Radiograph with thoracic cavity and bone contrast.
    - 'prescription_doc': Paper document, prescription, or clinical note.
    - 'unsupported': Non-medical color photo or generic graphic.
    """
    fn_lower = filename.lower()
    if any(k in fn_lower for k in ["prescri", "priscrition", "prescription", "rx_", "_rx", "doctor_note"]):
        return {
            "modality": "prescription_doc",
            "is_compatible_ct": False,
            "confidence": 0.98,
            "reason": "Filename or metadata indicates a medical prescription or clinical note."
        }

    # Analyze PIL image metrics
    rgb_img = pil_image.convert("RGB")
    np_rgb = np.array(rgb_img)
    gray = np.array(rgb_img.convert("L"))
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    h, w = gray.shape

    # Color saturation / variance
    r, g, b = np_rgb[:, :, 0], np_rgb[:, :, 1], np_rgb[:, :, 2]
    color_var = float(np.mean(np.abs(r.astype(float) - g.astype(float))) +
                      np.mean(np.abs(g.astype(float) - b.astype(float))))

    corners = [
        gray[:max(1, int(h*0.12)), :max(1, int(w*0.12))],
        gray[:max(1, int(h*0.12)), max(1, int(w*0.88)):],
        gray[max(1, int(h*0.88)):, :max(1, int(w*0.12))],
        gray[max(1, int(h*0.88)):, max(1, int(w*0.88)):]
    ]
    corner_mean = float(np.mean([np.mean(c) for c in corners]))

    # 1. Document / Prescription detection: High mean brightness (white paper background)
    if mean_val > 170:
        grad_x = np.abs(np.diff(gray, axis=1))
        text_edge_density = float(np.mean(grad_x > 25))
        if text_edge_density > 0.02 or mean_val > 185:
            return {
                "modality": "prescription_doc",
                "is_compatible_ct": False,
                "confidence": 0.96,
                "reason": f"High-contrast document background (mean brightness {mean_val:.1f}) with text line structure."
            }

    # 2. Authentic CT scan / axial slices with dark peripheral margins:
    # Medical CT scans (including those with clinical false-color palettes, Doppler, PET-CT, or annotations)
    # have pitch-black peripheral margins (corner_mean < 35.0) and dark-to-moderate overall brightness.
    if corner_mean < 35.0 and mean_val < 140.0:
        return {
            "modality": "ct_scan",
            "is_compatible_ct": True,
            "confidence": 0.95,
            "reason": "Axial/cross-sectional radiological density with dark peripheral margins consistent with CT scan."
        }

    # 3. Chest Radiograph / Plain Film:
    if 25.0 <= mean_val <= 170.0 and color_var < 35.0:
        return {
            "modality": "chest_xray" if corner_mean >= 15 else "ct_scan",
            "is_compatible_ct": True,
            "confidence": 0.88,
            "reason": "Radiological density pattern compatible with clinical imaging."
        }

    # 4. Non-medical color photos (e.g. landscape photos, selfies, screenshots):
    if color_var > 35.0 or corner_mean > 45.0:
        return {
            "modality": "unsupported",
            "is_compatible_ct": False,
            "confidence": 0.93,
            "reason": f"High color variance ({color_var:.1f}) and non-radiological boundary distribution indicate a non-medical photographic image."
        }

    return {
        "modality": "ct_scan",
        "is_compatible_ct": True,
        "confidence": 0.80,
        "reason": "Default radiological processing."
    }


def validate_image_file(file_path: str, max_size_bytes: int = MAX_FILE_SIZE) -> Dict[str, Any]:
    """
    Validates file existence, extension, and file size.
    Returns file metadata dict if valid, raises ImageValidationError otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        raise ImageValidationError(f"File not found: {path.name}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise ImageValidationError("Uploaded file is empty (0 bytes).")

    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise ImageValidationError(
            f"File size ({actual_mb:.1f} MB) exceeds maximum allowed limit ({max_mb:.0f} MB)."
        )

    ext = path.suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ImageValidationError(
            f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS)).upper()}."
        )

    return {
        "file_name": path.name,
        "file_size_bytes": file_size,
        "file_size_formatted": format_file_size(file_size),
        "extension": ext
    }


def format_file_size(size_bytes: int) -> str:
    """Formats bytes into human-readable size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def preprocess_ct_image(
    image_path: str,
    output_dir: Optional[str] = None,
    max_dimension: int = MAX_DIMENSION,
    enforce_ct_modality: bool = True
) -> Dict[str, Any]:
    """
    Validates, decodes, and prepares a CT scan or medical image for analysis.
    
    1. Validates file header and decodes with Pillow.
    2. Performs modality verification to reject prescriptions or unsupported documents.
    3. Corrects EXIF orientation if present.
    4. Detects original dimensions, mode, and aspect ratio.
    5. Converts grayscale or RGBA safely to RGB without loss of contrast.
    6. Performs safe aspect-ratio-preserving resizing ONLY if dimensions exceed max_dimension.
    7. Saves a normalized JPEG/PNG copy for API transmission while preserving the original.
    
    Returns a dictionary with image metadata, original and processed dimensions,
    modality detection details, and paths to both original and processed images.
    """
    # 1. Validation
    validation_info = validate_image_file(image_path)
    ext = validation_info["extension"].lower()

    if ext in ("dcm", "dicom"):
        try:
            import pydicom
            ds = pydicom.dcmread(image_path)
            pix = ds.pixel_array.astype(float)
            pix = (pix - np.min(pix)) / (np.max(pix) - np.min(pix) + 1e-6) * 255.0
            pil_img = Image.fromarray(pix.astype(np.uint8)).convert("RGB")
        except Exception as e:
            raise ImageValidationError(f"Failed to decode DICOM image: {str(e)}")
    else:
        try:
            # Open with PIL
            with Image.open(image_path) as raw_img:
                # Verify file integrity
                raw_img.verify()
        except Exception as e:
            raise ImageValidationError(f"Invalid image file or corrupted image data: {str(e)}")

        # Re-open after verify() (Pillow requirement)
        try:
            pil_img = Image.open(image_path)
            # Transpose according to EXIF if available
            pil_img = ImageOps.exif_transpose(pil_img)
        except Exception as e:
            raise ImageValidationError(f"Failed to decode image: {str(e)}")

    # 2. Modality Gatekeeper
    modality_info = detect_image_modality(pil_img, validation_info["file_name"])
    if enforce_ct_modality and not modality_info["is_compatible_ct"]:
        raise IncompatibleImageModalityError(
            detected_modality=modality_info["modality"],
            message="not a proper image to scan"
        )

    orig_width, orig_height = pil_img.size
    orig_mode = pil_img.mode
    aspect_ratio = round(orig_width / max(1, orig_height), 3)

    # Convert to RGB (CT scans are often 8-bit or 16-bit grayscale or palette)
    if pil_img.mode != "RGB":
        if pil_img.mode in ("I", "I;16"):
            # 16-bit grayscale to 8-bit normalization
            arr = np.array(pil_img)
            arr_norm = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            pil_img = Image.fromarray(arr_norm).convert("RGB")
        elif pil_img.mode == "RGBA":
            # White background composite
            bg = Image.new("RGB", pil_img.size, (255, 255, 255))
            bg.paste(pil_img, mask=pil_img.split()[3])
            pil_img = bg
        else:
            pil_img = pil_img.convert("RGB")

    # Determine if resizing is needed
    needs_resizing = orig_width > max_dimension or orig_height > max_dimension
    if needs_resizing:
        if orig_width > orig_height:
            new_width = max_dimension
            new_height = int(orig_height * (max_dimension / orig_width))
        else:
            new_height = max_dimension
            new_width = int(orig_width * (max_dimension / orig_height))
        # High quality Lanczos antialiasing preserves subtle densities
        processed_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    else:
        new_width, new_height = orig_width, orig_height
        processed_img = pil_img

    # Save processed image if output_dir specified
    processed_path = image_path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_name = Path(image_path).stem
        processed_file_name = f"proc_{base_name}.jpg"
        processed_path = str(Path(output_dir) / processed_file_name)
        processed_img.save(processed_path, format="JPEG", quality=92, optimize=True)

    return {
        "status": "valid",
        "file_name": validation_info["file_name"],
        "file_size_formatted": validation_info["file_size_formatted"],
        "modality_info": modality_info,
        "original_dimensions": {
            "width": orig_width,
            "height": orig_height,
            "formatted": f"{orig_width} x {orig_height} px",
            "aspect_ratio": aspect_ratio,
            "color_mode": orig_mode
        },
        "processed_dimensions": {
            "width": new_width,
            "height": new_height,
            "formatted": f"{new_width} x {new_height} px",
            "resized": needs_resizing
        },
        "original_path": str(Path(image_path).resolve()),
        "processed_path": str(Path(processed_path).resolve()),
        "pil_image": processed_img
    }
