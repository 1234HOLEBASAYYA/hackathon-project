"""
Unit & Integration Tests for Gemini Medical Image Analysis Service
"""

import os
import unittest
from pathlib import Path
from services.gemini_service import (
    validate_and_normalize_report,
    analyze_ct_scan_image,
    get_gemini_client,
    GeminiConfigurationError,
    clean_json_response
)


class TestGeminiAnalysis(unittest.TestCase):

    def test_clean_json_response(self):
        """Verifies markdown code fences are stripped correctly."""
        raw_markdown = "```json\n{\"report_title\": \"AI-Assisted Report\"}\n```"
        cleaned = clean_json_response(raw_markdown)
        self.assertEqual(cleaned, '{"report_title": "AI-Assisted Report"}')

    def test_schema_normalization_and_disclaimer(self):
        """Verifies missing fields are normalized and uncertainty is enforced."""
        incomplete_data = {
            "report_title": "CT Report",
            "visual_observations": [
                {"observation": "Hyperdensity", "location": "Right lung base"}
            ],
            "potential_findings": [
                {"finding": "Pneumonia", "certainty": "confirmed"} # Should be forced to uncertain
            ]
        }
        normalized = validate_and_normalize_report(incomplete_data, "test_slice.jpg", "512 x 512 px")

        # Check required fields
        self.assertIn("image_information", normalized)
        self.assertEqual(normalized["potential_findings"][0]["certainty"], "uncertain")
        self.assertIn("medical_disclaimer", normalized)
        self.assertIn("recommendations_for_review", normalized)
        self.assertIn("limitations", normalized)

    def test_missing_api_key_handling(self):
        """Verifies error raised when API key is missing."""
        orig_key = os.environ.get("GEMINI_API_KEY")
        try:
            os.environ["GEMINI_API_KEY"] = ""
            with self.assertRaises(GeminiConfigurationError):
                get_gemini_client()
        finally:
            if orig_key is not None:
                os.environ["GEMINI_API_KEY"] = orig_key

    def test_real_gemini_vision_connectivity(self):
        """Verifies live Gemini API call on test medical image."""
        sample_path = Path("dataset/chest_xray/test/PNEUMONIA/person1_virus_6.jpeg")
        if not sample_path.exists():
            self.skipTest("Sample test image not found.")

        result = analyze_ct_scan_image(
            str(sample_path),
            filename="person1_virus_6.jpeg",
            dimensions_str="512 x 512 px"
        )
        self.assertIn("report_title", result)
        self.assertIn("visual_observations", result)
        self.assertIn("potential_findings", result)
        self.assertIn("medical_disclaimer", result)
        self.assertTrue(len(result["visual_observations"]) > 0)


if __name__ == "__main__":
    unittest.main()
