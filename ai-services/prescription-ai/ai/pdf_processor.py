"""PDF Processing module using PyMuPDF (fitz) for prescription documents."""

from __future__ import annotations

import logging
from pathlib import Path
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def convert_pdf_to_images(
    pdf_input: str | Path | bytes,
    dpi: int = 300,
    max_pages: int = 5,
) -> list[np.ndarray]:
    """Convert a PDF document into a list of OpenCV-compatible numpy image arrays (RGB).

    Args:
        pdf_input: File path or raw bytes of the PDF.
        dpi: Target resolution DPI (default: 300 DPI for high OCR accuracy).
        max_pages: Maximum pages to convert (default: 5).

    Returns:
        List of numpy arrays in RGB format.
    """
    images: list[np.ndarray] = []
    
    if isinstance(pdf_input, (str, Path)):
        doc = fitz.open(str(pdf_input))
    else:
        doc = fitz.open(stream=pdf_input, filetype="pdf")

    try:
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        page_count = min(len(doc), max_pages)
        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            # Convert PyMuPDF pixmap to numpy array (H, W, C)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
            if pix.n == 4:
                # RGBA to RGB
                img = img[:, :, :3]
            images.append(img)
            
        logger.info("Successfully converted %d PDF page(s) at %d DPI", len(images), dpi)
        return images
    finally:
        doc.close()


def save_first_page_preview(
    pdf_input: str | Path | bytes,
    output_path: str | Path,
    dpi: int = 150,
) -> Path:
    """Save the first page of a PDF as a preview PNG image.

    Args:
        pdf_input: File path or raw bytes of the PDF.
        output_path: Target path to save the preview PNG.
        dpi: Resolution for preview image.

    Returns:
        Path of the saved preview image.
    """
    images = convert_pdf_to_images(pdf_input, dpi=dpi, max_pages=1)
    if not images:
        raise ValueError("PDF contains no renderable pages")

    preview_img = Image.fromarray(images[0])
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    preview_img.save(str(out), format="PNG")
    return out

