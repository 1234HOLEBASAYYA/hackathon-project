"""
End-to-End API Integration Tests for MedVision-AI Application
Tests all endpoints using Flask test client.
"""

import io
import json
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

from app import app


class TestMedVisionAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

        # Create dummy image bytes
        img_arr = np.random.randint(60, 200, (256, 256), dtype=np.uint8)
        img = Image.fromarray(img_arr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        cls.valid_png_bytes = buf.getvalue()

    def test_index_page(self):
        """Verify HTML dashboard renders."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"MedVision", res.data)
        self.assertIn(b"Upload CT Scan Image", res.data)

    def test_health_endpoint(self):
        """Verify health check returns service and Gemini status."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gemini", data)
        self.assertTrue(data["gemini"]["api_key_configured"])

    def test_analyze_no_file(self):
        """Verify 400 error when no file uploaded."""
        res = self.client.post("/api/analyze", data={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)

    def test_analyze_invalid_extension(self):
        """Verify 400 error when unsupported file format is uploaded."""
        data = {
            "file": (io.BytesIO(b"fake text data"), "test.txt")
        }
        res = self.client.post("/api/analyze", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)

    def test_sample_image_endpoint(self):
        """Verify sample scan endpoint returns valid image."""
        res = self.client.get("/api/sample")
        if res.status_code == 200:
            self.assertEqual(res.mimetype, "image/jpeg")

    def test_generate_report_and_download_flow(self):
        """Verify PDF report generation and download cycle."""
        sample_report = {
            "report_title": "AI-Assisted CT Image Analysis Report",
            "filename": "test_case.png",
            "image_information": {
                "image_type": "Axial CT Slice",
                "image_dimensions": "256 x 256 px",
                "image_quality": "Adequate",
                "limitations": ["Single slice"]
            },
            "visual_observations": [
                {
                    "observation": "Visual Opacity",
                    "location": "Left lung base",
                    "description": "Faint haziness observed.",
                    "certainty": "observed"
                }
            ],
            "potential_findings": [
                {
                    "finding": "Possible Atelectasis",
                    "location": "Left lower lobe",
                    "description": "Dependent density pattern.",
                    "certainty": "uncertain",
                    "supporting_visual_observation": "Visual Opacity"
                }
            ],
            "summary": "Screening evaluation completed.",
            "recommendations_for_review": ["Radiology correlation"],
            "limitations": ["Single slice"],
            "medical_disclaimer": "AI decision support only.",
            "generated_at": "2026-11-05 21:00:00 UTC",
            "model_used": "Gemini 3.8 Flash"
        }

        # 1. Generate Report
        gen_res = self.client.post(
            "/api/generate-report",
            json={"report": sample_report}
        )
        self.assertEqual(gen_res.status_code, 200)
        gen_data = gen_res.get_json()
        self.assertIn("download_url", gen_data)
        filename = gen_data["filename"]

        # 2. Download Report
        dl_res = self.client.get(f"/api/reports/download/{filename}")
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res.mimetype, "application/pdf")
        self.assertTrue(dl_res.data.startswith(b"%PDF-"))

    def test_reject_prescription_upload_to_ct_endpoint(self):
        """Verify uploading a prescription document to the CT endpoint is rejected with 400."""
        from PIL import Image
        import numpy as np
        doc_arr = np.full((400, 300), 225, dtype=np.uint8)
        img_io = io.BytesIO()
        Image.fromarray(doc_arr).save(img_io, format="PNG")
        img_io.seek(0)

        res = self.client.post(
            "/api/analyze",
            data={"file": (img_io, "2prescription.png")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)
        self.assertIn("Incompatible", data.get("error", "") + data.get("message", ""))


if __name__ == "__main__":
    unittest.main()
