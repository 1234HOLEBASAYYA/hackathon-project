"""Tests for preprocessing steps."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from src.preprocessor import (
    adaptive_threshold,
    apply_clahe,
    apply_morphology,
    deskew_image,
    preprocess_array,
    remove_noise,
    to_grayscale,
)


@pytest.fixture()
def color_image() -> np.ndarray:
    """Create a synthetic prescription-like color image.

    Returns:
        BGR image with text-like lines.
    """
    image = np.full((160, 300, 3), 245, dtype=np.uint8)
    cv2.putText(image, "Dr Smith", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    cv2.putText(image, "Tab ABC 500mg", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    return image


@pytest.fixture()
def grayscale_image(color_image: np.ndarray) -> np.ndarray:
    """Create a grayscale fixture.

    Args:
        color_image: Synthetic color fixture.

    Returns:
        Grayscale image.
    """
    return cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)


def test_to_grayscale_returns_2d_image(color_image: np.ndarray) -> None:
    """Test grayscale conversion in isolation."""
    gray = to_grayscale(color_image)
    assert gray.ndim == 2
    assert gray.shape == color_image.shape[:2]


def test_apply_clahe_preserves_shape(grayscale_image: np.ndarray) -> None:
    """Test CLAHE output shape and dtype."""
    enhanced = apply_clahe(grayscale_image, clip_limit=2.0, tile_grid_size=(8, 8))
    assert enhanced.shape == grayscale_image.shape
    assert enhanced.dtype == np.uint8


def test_remove_noise_preserves_shape(grayscale_image: np.ndarray) -> None:
    """Test denoising output shape."""
    noisy = grayscale_image.copy()
    noisy[::5, ::5] = 0
    denoised = remove_noise(noisy, enabled=True)
    assert denoised.shape == noisy.shape
    assert denoised.dtype == np.uint8


def test_deskew_image_returns_angle(grayscale_image: np.ndarray) -> None:
    """Test deskew step returns an image and numeric angle."""
    deskewed, angle = deskew_image(grayscale_image, enabled=True)
    assert deskewed.shape == grayscale_image.shape
    assert isinstance(angle, float)


def test_adaptive_threshold_returns_binary(grayscale_image: np.ndarray) -> None:
    """Test adaptive thresholding produces binary output."""
    binary = adaptive_threshold(grayscale_image, block_size=11, c_value=2)
    unique_values = set(np.unique(binary).tolist())
    assert binary.shape == grayscale_image.shape
    assert unique_values.issubset({0, 255})


def test_apply_morphology_preserves_shape(grayscale_image: np.ndarray) -> None:
    """Test morphology output shape."""
    binary = adaptive_threshold(grayscale_image, block_size=11, c_value=2)
    cleaned = apply_morphology(binary, kernel_size=(2, 2))
    assert cleaned.shape == binary.shape


def test_preprocess_array_returns_metadata(color_image: np.ndarray) -> None:
    """Test the full preprocessing pipeline result contract."""
    config = {
        "preprocessing": {
            "resize_width": 300,
            "clahe_clip_limit": 2.0,
            "clahe_tile_grid_size": [8, 8],
            "deskew": True,
            "denoise": True,
            "adaptive_block_size": 11,
            "adaptive_c": 2,
            "morphology_kernel_size": [2, 2],
        }
    }
    result = preprocess_array(color_image, config)
    assert result["image"].ndim == 2
    assert result["metadata"]["clahe_applied"] is True
    assert 0.0 <= result["metadata"]["confidence"] <= 1.0


def test_preprocess_array_returns_pipeline_report(color_image: np.ndarray) -> None:
    """Test that pipeline_report keys are present in preprocess_array result."""
    result = preprocess_array(color_image, None)
    assert "pipeline_report" in result
    report = result["pipeline_report"]
    assert "deskew_angle" in report
    assert "clahe_applied" in report
    assert "denoised" in report
    assert "final_resolution" in report
    assert isinstance(report["deskew_angle"], float)
    assert isinstance(report["clahe_applied"], bool)
    assert isinstance(report["denoised"], bool)
    assert isinstance(report["final_resolution"], list)
    assert len(report["final_resolution"]) == 2


def test_preprocess_black_image_raises_value_error() -> None:
    """Test that a completely black image raises a ValueError."""
    black_img = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="completely black"):
        preprocess_array(black_img, None)

