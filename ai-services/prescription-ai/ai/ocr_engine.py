"""AI OCR Inference Engine with EasyOCR (GPU/CPU) and handwriting-aware text normalization."""

from __future__ import annotations

import logging
import re
import threading
from typing import Any, TypedDict
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Global cache for EasyOCR Reader to avoid reloads
_easyocr_gpu_reader: Any = None
_easyocr_cpu_reader: Any = None
_easyocr_lock = threading.Lock()


class BoundingBox(TypedDict):
    """Bounding box coordinates and detection details."""

    x: int
    y: int
    width: int
    height: int
    polygon: list[list[int]]
    text: str
    confidence: float


class AIOCRResult(TypedDict):
    """Complete OCR extraction output."""

    raw_text: str
    confidence: float
    engine_used: str
    bounding_boxes: list[BoundingBox]
    line_count: int
    word_count: int


def get_easyocr_reader(use_gpu: bool = False) -> Any:
    """Get or initialize singleton EasyOCR reader with GPU and CPU caches."""
    global _easyocr_gpu_reader, _easyocr_cpu_reader
    with _easyocr_lock:
        import torch
        import easyocr

        if not use_gpu:
            if _easyocr_cpu_reader is None:
                logger.info("Initializing CPU EasyOCR reader...")
                _easyocr_cpu_reader = easyocr.Reader(["en"], gpu=False)
                logger.info("CPU EasyOCR reader initialized successfully.")
            return _easyocr_cpu_reader

        if _easyocr_gpu_reader is None:
            cuda_available = torch.cuda.is_available()
            logger.info("Initializing EasyOCR reader (CUDA=%s)...", cuda_available)
            try:
                _easyocr_gpu_reader = easyocr.Reader(["en"], gpu=cuda_available)
                logger.info("GPU EasyOCR reader initialized successfully.")
            except Exception as e:
                logger.warning("GPU EasyOCR init failed (%s). Falling back to CPU.", e)
                return get_easyocr_reader(use_gpu=False)
        return _easyocr_gpu_reader


def normalize_ocr_token(text: str) -> str:
    """Normalize common handwriting OCR split digits and character confusions."""
    s = text.strip()
    # Normalize split numbers before units: 6 50 mg -> 650 mg, 5 00 mg -> 500 mg
    s = re.sub(r"(\b\d)\s+(\d{1,3}\s*(?:mg|mcg|g|ml|iu|%)\b)", r"\1\2", s, flags=re.IGNORECASE)
    # Fix OCR typos on unit 'mg': 500 m&, 500 mq, 500 m9 -> 500 mg
    s = re.sub(r"(\b\d+(?:\.\d+)?)\s*m[&q9]\b", r"\1 mg", s, flags=re.IGNORECASE)
    # Fix OCR typos on liquid dosage: [0 ml, /0 ml, I0 ml, l0 ml -> 10 ml
    s = re.sub(r"(?:[\[\/I|l]0)\s*ml\b", "10 ml", s, flags=re.IGNORECASE)
    return s


def sort_detections_reading_order(
    detections: list[tuple[Any, str, float]],
    y_threshold: int = 22,
) -> list[tuple[Any, str, float]]:
    """Sort OCR detections into natural clinical reading order (top-to-bottom, left-to-right)."""
    if not detections:
        return []

    items = []
    for poly, text, conf in detections:
        poly_arr = np.array(poly, dtype=np.int32)
        min_x = int(np.min(poly_arr[:, 0]))
        min_y = int(np.min(poly_arr[:, 1]))
        max_y = int(np.max(poly_arr[:, 1]))
        center_y = (min_y + max_y) // 2
        items.append((min_y, min_x, center_y, poly_arr, text, conf))

    # Sort primarily by vertical coordinate
    items.sort(key=lambda item: item[0])

    # Group into lines with vertical overlap tolerance
    lines: list[list[Any]] = []
    for item in items:
        min_y, min_x, center_y, poly_arr, text, conf = item
        placed = False
        for line in lines:
            avg_y = sum(x[2] for x in line) / len(line)
            if abs(center_y - avg_y) <= y_threshold:
                line.append(item)
                placed = True
                break
        if not placed:
            lines.append([item])

    # Sort each line left-to-right by min_x
    sorted_detections = []
    for line in lines:
        line.sort(key=lambda x: x[1])
        for _, _, _, poly_arr, text, conf in line:
            sorted_detections.append((poly_arr.tolist(), text, conf))

    return sorted_detections


def run_ai_ocr(
    image: np.ndarray,
    prefer_gpu: bool = False,
    confidence_threshold: float = 0.20,
) -> AIOCRResult:
    """Run AI Deep Learning OCR on a prescription image with tuned handwriting parameters."""
    reader = get_easyocr_reader(use_gpu=prefer_gpu)

    # Use tuned detection parameters to capture faint cursive pen strokes and numbers
    try:
        raw_detections = reader.readtext(
            image,
            contrast_ths=0.1,
            adjust_contrast=0.5,
            text_threshold=0.5,
            low_text=0.3,
            link_threshold=0.4,
        )
    except Exception as exc:
        err_str = str(exc).lower()
        if "cuda" in err_str or "out of memory" in err_str:
            logger.warning("CUDA memory pressure/error encountered: %s. Falling back to CPU EasyOCR.", exc)
            import torch
            if torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
            cpu_reader = get_easyocr_reader(use_gpu=False)
            raw_detections = cpu_reader.readtext(
                image,
                contrast_ths=0.1,
                adjust_contrast=0.5,
                text_threshold=0.5,
                low_text=0.3,
                link_threshold=0.4,
            )
        else:
            raise exc

    # Sort into natural reading order
    ordered_detections = sort_detections_reading_order(raw_detections, y_threshold=22)

    bounding_boxes: list[BoundingBox] = []
    lines: list[str] = []
    current_line_parts: list[str] = []
    current_line_y: float | None = None
    total_conf = 0.0
    valid_count = 0

    for poly, text, conf in ordered_detections:
        clean_text = normalize_ocr_token(str(text))
        if not clean_text:
            continue

        conf_float = round(float(conf), 4)
        total_conf += conf_float
        valid_count += 1

        poly_arr = np.array(poly, dtype=np.int32)
        min_x = int(np.min(poly_arr[:, 0]))
        min_y = int(np.min(poly_arr[:, 1]))
        max_x = int(np.max(poly_arr[:, 0]))
        max_y = int(np.max(poly_arr[:, 1]))
        width = max(1, max_x - min_x)
        height = max(1, max_y - min_y)
        center_y = (min_y + max_y) / 2.0

        bounding_boxes.append(
            BoundingBox(
                x=min_x,
                y=min_y,
                width=width,
                height=height,
                polygon=poly,
                text=clean_text,
                confidence=round(conf_float * 100.0, 1),
            )
        )

        # Line accumulation with grouping
        if current_line_y is None or abs(center_y - current_line_y) < 22:
            current_line_parts.append(clean_text)
            current_line_y = center_y
        else:
            if current_line_parts:
                lines.append(" ".join(current_line_parts))
            current_line_parts = [clean_text]
            current_line_y = center_y

    if current_line_parts:
        lines.append(" ".join(current_line_parts))

    raw_text = "\n".join(lines).strip()
    avg_confidence = round((total_conf / valid_count * 100.0), 1) if valid_count > 0 else 0.0
    word_count = len(raw_text.split())

    return AIOCRResult(
        raw_text=raw_text,
        confidence=avg_confidence,
        engine_used="EasyOCR (Deep Learning CRAFT + BiLSTM, GPU Accelerated)",
        bounding_boxes=bounding_boxes,
        line_count=len(lines),
        word_count=word_count,
    )
