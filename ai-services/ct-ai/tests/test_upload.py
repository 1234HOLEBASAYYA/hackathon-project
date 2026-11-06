"""
Unit Tests for Image Upload and Preprocessing
Tests valid image decoding, corrupt image rejection, aspect-ratio-preserving resizing,
and format validation.
"""

import os
import unittest
import numpy as np
from PIL import Image
from pathlib import Path

from services.image_preprocessing import preprocess_ct_image, validate_image_file, ImageValidationError, IncompatibleImageModalityError

TEST_TMP_DIR = Path("tests/tmp")


class TestImageUploadAndPreprocessing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
        # Create a sample synthetic CT slice (grayscale 512x512)
        cls.valid_png_path = str(TEST_TMP_DIR / "synthetic_ct.png")
        img_arr = np.random.randint(40, 220, (512, 512), dtype=np.uint8)
        Image.fromarray(img_arr).save(cls.valid_png_path)

        # Create an oversized image (3000x1500) to test aspect ratio preservation (grayscale scan)
        cls.oversized_path = str(TEST_TMP_DIR / "oversized_scan.jpg")
        oversized_gray = np.random.randint(20, 180, (1500, 3000), dtype=np.uint8)
        Image.fromarray(oversized_gray).save(cls.oversized_path)

        # Create a fake corrupted file
        cls.corrupted_path = str(TEST_TMP_DIR / "corrupt.jpg")
        with open(cls.corrupted_path, "wb") as f:
            f.write(b"NOT_A_VALID_JPEG_HEADER_123456789")

        # Create an unsupported text file renamed as .png
        cls.fake_ext_path = str(TEST_TMP_DIR / "fake.txt")
        with open(cls.fake_ext_path, "w") as f:
            f.write("Plain text file")

    def test_valid_image_preprocessing(self):
        """Verify normal CT image validates, decodes and preserves dimensions."""
        res = preprocess_ct_image(self.valid_png_path, output_dir=str(TEST_TMP_DIR))
        self.assertEqual(res["status"], "valid")
        self.assertEqual(res["original_dimensions"]["width"], 512)
        self.assertEqual(res["original_dimensions"]["height"], 512)
        self.assertFalse(res["processed_dimensions"]["resized"])
        self.assertTrue(os.path.exists(res["processed_path"]))

    def test_oversized_image_resizing(self):
        """Verify oversized image is safely downscaled while preserving aspect ratio."""
        res = preprocess_ct_image(self.oversized_path, output_dir=str(TEST_TMP_DIR), max_dimension=2048)
        self.assertTrue(res["processed_dimensions"]["resized"])
        self.assertEqual(res["processed_dimensions"]["width"], 2048)
        expected_height = int(1500 * (2048 / 3000))
        self.assertEqual(res["processed_dimensions"]["height"], expected_height)

    def test_corrupted_image_rejection(self):
        """Verify corrupted binary raises ImageValidationError."""
        with self.assertRaises(ImageValidationError):
            preprocess_ct_image(self.corrupted_path)

    def test_unsupported_file_extension(self):
        """Verify non-image extensions are rejected immediately."""
        with self.assertRaises(ImageValidationError):
            validate_image_file(self.fake_ext_path)

    def test_prescription_document_rejection(self):
        """Verify prescription documents are rejected with IncompatibleImageModalityError."""
        # Create a synthetic white document with high brightness
        doc_path = str(TEST_TMP_DIR / "test_prescription.png")
        doc_arr = np.full((500, 400), 230, dtype=np.uint8)
        # Add black text lines
        doc_arr[100:105, 50:350] = 10
        doc_arr[150:155, 50:350] = 10
        Image.fromarray(doc_arr).save(doc_path)
        with self.assertRaises(IncompatibleImageModalityError):
            preprocess_ct_image(doc_path)


if __name__ == "__main__":
    unittest.main()
