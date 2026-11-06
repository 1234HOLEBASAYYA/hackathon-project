"""OCR engine abstraction with Tesseract and EasyOCR fallback."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, TypedDict

import cv2
import numpy as np
import pytesseract

from src.tesseract_config import configure_tesseract

configure_tesseract()
from pathlib import Path

logger = logging.getLogger(__name__)


class WordBox(TypedDict):
    """Detected OCR word and its bounding box."""

    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int


class OCRResult(TypedDict):
    """Normalized OCR response."""

    raw_text: str
    confidence: float
    engine_used: str
    word_boxes: list[WordBox]


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load YAML configuration.

    Args:
        config_path: Optional path to config file.

    Returns:
        Parsed configuration dictionary.
    """
    path = config_path or Path.cwd() / "config.yaml"
    if not path.exists():
        logger.warning("Config file not found at %s; using defaults.", path)
        return {}
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML is not installed; using default configuration.")
        return {}
    with path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    return loaded if isinstance(loaded, dict) else {}


class OCREngine(ABC):
    """Abstract OCR engine interface."""

    @abstractmethod
    def recognize(self, image: np.ndarray, dpi: float | None = None) -> OCRResult:
        """Recognize text from an image.

        Args:
            image: Preprocessed image array.
            dpi: Optional resolution DPI.

        Returns:
            Normalized OCR result.
        """


class TesseractEngine(OCREngine):
    """Tesseract OCR engine."""

    def __init__(self, language: str = "eng", default_psm: int = 6) -> None:
        """Initialize Tesseract engine.

        Args:
            language: Tesseract language code.
            default_psm: Default page segmentation mode.
        """
        self.language = language
        self.default_psm = default_psm

    def select_psm(self, image: np.ndarray) -> int:
        """Select Tesseract PSM from page layout heuristics.

        Args:
            image: Preprocessed image array.

        Returns:
            Tesseract page segmentation mode.
        """
        height, width = image.shape[:2]
        aspect_ratio = width / max(height, 1)
        foreground_ratio = float(np.mean(image < 128)) if image.ndim == 2 else 0.0
        if aspect_ratio > 4.0:
            return 7
        if foreground_ratio < 0.015:
            return 11
        if height > width * 1.2:
            return 4
        return self.default_psm

    def recognize(self, image: np.ndarray, dpi: float | None = None) -> OCRResult:
        """Recognize text with Tesseract.

        Args:
            image: Preprocessed image.
            dpi: Optional resolution DPI.

        Returns:
            Normalized OCR result.
        """
        psm = self.select_psm(image)
        config = f"--oem 3 --psm {psm}"
        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config=config,
            output_type=pytesseract.Output.DICT,
        )

        word_boxes: list[WordBox] = []
        confidences: list[float] = []
        for index, text in enumerate(data.get("text", [])):
            cleaned = str(text).strip()
            confidence = _safe_float(data.get("conf", ["-1"])[index])
            if cleaned and confidence >= 0:
                word_boxes.append(
                    {
                        "text": cleaned,
                        "confidence": confidence,
                        "x": int(data["left"][index]),
                        "y": int(data["top"][index]),
                        "width": int(data["width"][index]),
                        "height": int(data["height"][index]),
                    }
                )
                confidences.append(confidence)

        raw_text = pytesseract.image_to_string(image, lang=self.language, config=config).strip()
        if not raw_text:
            raw_text = " ".join(box["text"] for box in word_boxes)
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return {
            "raw_text": raw_text,
            "confidence": round(average_confidence, 2),
            "engine_used": "tesseract",
            "word_boxes": word_boxes,
        }


class EasyOCREngine(OCREngine):
    """EasyOCR fallback engine."""

    def __init__(self, languages: list[str] | None = None) -> None:
        """Initialize EasyOCR lazily.

        Args:
            languages: EasyOCR language codes.
        """
        self.languages = languages or ["en"]
        self._reader: Any | None = None

    def _get_reader(self) -> Any:
        """Create or return the EasyOCR reader.

        Returns:
            EasyOCR reader instance.
        """
        if self._reader is None:
            import easyocr

            self._reader = easyocr.Reader(self.languages, gpu=False)
        return self._reader

    def recognize(self, image: np.ndarray, dpi: float | None = None) -> OCRResult:
        """Recognize text with EasyOCR.

        Args:
            image: Preprocessed image.
            dpi: Optional resolution DPI.

        Returns:
            Normalized OCR result.
        """
        reader = self._get_reader()
        readable_image = image
        if image.ndim == 2:
            readable_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        detections = reader.readtext(readable_image)
        word_boxes: list[WordBox] = []
        texts: list[str] = []
        confidences: list[float] = []
        for points, text, confidence in detections:
            x_values = [int(point[0]) for point in points]
            y_values = [int(point[1]) for point in points]
            scaled_confidence = float(confidence) * 100.0
            texts.append(str(text))
            confidences.append(scaled_confidence)
            word_boxes.append(
                {
                    "text": str(text),
                    "confidence": round(scaled_confidence, 2),
                    "x": min(x_values),
                    "y": min(y_values),
                    "width": max(x_values) - min(x_values),
                    "height": max(y_values) - min(y_values),
                }
            )
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return {
            "raw_text": "\n".join(texts),
            "confidence": round(average_confidence, 2),
            "engine_used": "easyocr",
            "word_boxes": word_boxes,
        }


class OCRPipeline:
    """OCR pipeline with confidence-based fallback."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize OCR pipeline.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        ocr_config = self.config.get("ocr", {})
        self.confidence_threshold = float(ocr_config.get("confidence_threshold", 60))
        self.fallback_engine = str(ocr_config.get("fallback_engine", "easyocr")).lower()
        self.primary = TesseractEngine(
            language=str(ocr_config.get("language", "eng")),
            default_psm=int(ocr_config.get("tesseract_psm", 6)),
        )
        self.easyocr_languages = [str(language) for language in ocr_config.get("easyocr_languages", ["en"])]

        qc_config = self.config.get("quality_check", {})
        self.min_dpi = int(qc_config.get("min_dpi", 150))
        self.blur_threshold = int(qc_config.get("blur_threshold", 100))

    def recognize(self, image: np.ndarray, dpi: float | None = None) -> OCRResult:
        """Run OCR and fallback when confidence is low.

        Args:
            image: Preprocessed image.
            dpi: Optional resolution DPI.

        Returns:
            Best OCR result.
        """
        # Quality pre-checks
        # 1. DPI check
        if dpi is None:
            # Estimate DPI assuming standard letter/A4 sheet (8.5 inches wide)
            dpi = max(image.shape[1] / 8.5, image.shape[0] / 11.0)
            logger.info("DPI not provided; estimated resolution is %.1f DPI", dpi)

        if dpi < self.min_dpi:
            raise ValueError(
                f"Image resolution too low: {dpi:.1f} DPI (minimum required: {self.min_dpi} DPI)"
            )

        # 2. Blurriness warning
        try:
            gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            if variance < self.blur_threshold:
                logger.warning(
                    "Image is blurry (Laplacian variance: %.2f < %d). OCR quality may be reduced.",
                    variance, self.blur_threshold
                )
            else:
                logger.info("Image clarity check passed (Laplacian variance: %.2f)", variance)
        except Exception as e:
            logger.warning("Could not calculate image blurriness: %s", e)

        # Prefer high-accuracy GPU EasyOCR engine
        try:
            from ai.ocr_engine import run_ai_ocr
            ai_res = run_ai_ocr(image, prefer_gpu=True)
            word_boxes = [
                {
                    "text": b["text"],
                    "confidence": b["confidence"],
                    "x": b["x"],
                    "y": b["y"],
                    "width": b["width"],
                    "height": b["height"],
                }
                for b in ai_res["bounding_boxes"]
            ]
            return {
                "raw_text": ai_res["raw_text"],
                "confidence": ai_res["confidence"],
                "engine_used": ai_res["engine_used"],
                "word_boxes": word_boxes,
            }
        except Exception as exc:
            logger.warning("GPU EasyOCR attempt failed, falling back to legacy pipeline: %s", exc)

        try:
            result = self.primary.recognize(image, dpi)
            logger.info("Primary OCR engine (Tesseract) executed successfully.")
        except Exception as exc:
            logger.exception("Tesseract OCR failed: %s", exc)
            result = {"raw_text": "", "confidence": 0.0, "engine_used": "tesseract", "word_boxes": []}

        if result["confidence"] >= self.confidence_threshold:
            logger.info(
                "Using primary engine (Tesseract) because confidence (%.2f) is above threshold (%d).",
                result["confidence"], self.confidence_threshold
            )
            return result

        if self.fallback_engine != "easyocr":
            logger.info(
                "Tesseract confidence (%.2f) is below threshold (%d) but no fallback engine is configured.",
                result["confidence"], self.confidence_threshold
            )
            return result

        logger.info(
            "Tesseract confidence (%.2f) is below threshold (%d). Invoking EasyOCR fallback.",
            result["confidence"], self.confidence_threshold
        )
        try:
            fallback = EasyOCREngine(self.easyocr_languages).recognize(image, dpi)
        except Exception as exc:
            logger.exception("EasyOCR fallback failed: %s", exc)
            logger.info("Falling back to Tesseract results due to fallback failure.")
            return result

        if fallback["confidence"] > result["confidence"]:
            logger.info(
                "Using EasyOCR fallback engine because its confidence (%.2f) is higher than Tesseract (%.2f).",
                fallback["confidence"], result["confidence"]
            )
            return fallback

        logger.info(
            "Using Tesseract engine because its confidence (%.2f) is higher than or equal to EasyOCR (%.2f).",
            result["confidence"], fallback["confidence"]
        )
        return result


def _safe_float(value: Any) -> float:
    """Parse a float safely.

    Args:
        value: Value to parse.

    Returns:
        Parsed float, or -1.0.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1.0


def run_ocr(
    image: np.ndarray,
    config_path: Path | None = None,
    dpi: float | None = None,
) -> OCRResult:
    """Run the configured OCR pipeline.

    Args:
        image: Preprocessed image.
        config_path: Optional config path.
        dpi: Optional resolution DPI.

    Returns:
        Normalized OCR result.
    """
    return OCRPipeline(load_config(config_path)).recognize(image, dpi=dpi)
