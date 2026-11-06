"""Helpers for locating the Tesseract OCR executable on Windows."""

from __future__ import annotations

from pathlib import Path

import pytesseract


COMMON_TESSERACT_PATHS = (
    Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
    Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
)


def configure_tesseract() -> str | None:
    """Configure pytesseract from common install locations when PATH is missing."""
    for path in COMMON_TESSERACT_PATHS:
        if path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(path)
            return str(path)
    return None
