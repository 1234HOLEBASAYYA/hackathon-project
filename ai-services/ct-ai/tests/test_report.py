"""
Unit Tests for ReportLab PDF Medical Report Generation Service
"""

import os
import unittest
from pathlib import Path
from services.report_service import generate_pdf_report, get_scaled_report_image

TEST_TMP_DIR = Path("tests/tmp")


class TestReportGeneration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.sample_img_path = Path("dataset/chest_xray/test/PNEUMONIA/person1_virus_6.jpeg")

    def test_pdf_report_creation(self):
        """Verifies PDF report is successfully created and has valid PDF magic header."""
        test_report_data = {
            "report_title": "AI-Assisted CT Image Analysis Report",
            "filename": "person1_virus_6.jpeg",
            "image_information": {
                "image_type": "Axial CT Thoracic Slice",
                "image_dimensions": "512 x 512 px",
                "image_quality": "High diagnostic contrast",
                "limitations": ["Single axial slice"]
            },
            "visual_observations": [
                {
                    "observation": "Airspace Opacity",
                    "location": "Right lower zone",
                    "description": "Dense consolidation with visible air bronchograms.",
                    "certainty": "observed"
                },
                {
                    "observation": "Pleural Interface",
                    "location": "Bilateral costophrenic sulci",
                    "description": "Sharp costophrenic angles preserved without effusion.",
                    "certainty": "observed"
                }
            ],
            "potential_findings": [
                {
                    "finding": "Possible Lobar Consolidation",
                    "location": "Right lower lobe",
                    "description": "Visual density patterns compatible with acute infectious infiltrate.",
                    "certainty": "uncertain",
                    "supporting_visual_observation": "Airspace Opacity"
                }
            ],
            "summary": "Focal airspace opacification identified in right lower lung zone. Clinical review recommended.",
            "recommendations_for_review": [
                "Correlation with patient temperature, WBC count, and auscultation.",
                "Formal radiologist reading required."
            ],
            "limitations": [
                "Evaluation restricted to single uploaded image slice.",
                "Volumetric CT data unavailable."
            ],
            "medical_disclaimer": "This report is AI-generated for decision support and is not a definitive diagnosis.",
            "generated_at": "2026-11-05 20:30:00 UTC",
            "model_used": "Gemini 3.8 Flash"
        }

        image_path_str = str(self.sample_img_path) if self.sample_img_path.exists() else None
        pdf_path = generate_pdf_report(
            report_data=test_report_data,
            image_path=image_path_str,
            output_dir=str(TEST_TMP_DIR)
        )

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)

        # Check %PDF- magic bytes
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_scaled_image_dimensions(self):
        """Verifies image scaling calculates dimensions within bounds."""
        if self.sample_img_path.exists():
            rl_img = get_scaled_report_image(str(self.sample_img_path), max_width=200, max_height=200)
            self.assertIsNotNone(rl_img)
            self.assertLessEqual(rl_img.drawWidth, 200.01)
            self.assertLessEqual(rl_img.drawHeight, 200.01)


if __name__ == "__main__":
    unittest.main()
