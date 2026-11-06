"""AI Prescription Reader - Master CLI & Server Entry Point.

Usage:
  python main.py               # Starts the FastAPI backend & serves the React UI
  python main.py <image_path>  # Analyzes a prescription image/PDF and prints extraction
  python main.py --test        # Runs the automated test suite
"""

import sys
import os
import warnings
warnings.filterwarnings("ignore")
import argparse
from pathlib import Path
import uvicorn


def run_cli_analysis(file_path: Path):
    from PIL import Image
    from ai.preprocessor import enhance_for_ocr
    from ai.ocr_engine import run_ai_ocr
    from ai.extractor import parse_prescription
    from ai.pdf_processor import convert_pdf_to_images

    print(f"\n========================================================")
    print(f" AI PRESCRIPTION READER - CLINICAL EXTRACTION")
    print(f" File: {file_path.name}")
    print(f"========================================================\n")

    if file_path.suffix.lower() == ".pdf":
        print("[*] Rasterizing PDF page at 300 DPI...")
        images = convert_pdf_to_images(file_path)
        if not images:
            print("[!] Failed to render PDF.")
            return
        image = images[0]
    else:
        print("[*] Preprocessing image (CLAHE, scaling, quality gate)...")
        pil_img = Image.open(file_path)
        prep = enhance_for_ocr(pil_img, apply_clahe=True, apply_deskew=False)
        image = prep["processed_image"]

    print("[*] Running AI Deep Learning OCR (EasyOCR / PyTorch GPU)...")
    ocr_result = run_ai_ocr(image, prefer_gpu=True)
    print(f"[*] Detected {len(ocr_result['bounding_boxes'])} text regions (Mean Conf: {ocr_result['confidence']}%).")

    print("[*] Extracting structured clinical data...")
    extraction = parse_prescription(ocr_result["raw_text"], ocr_result["bounding_boxes"])

    print("\n--- INSTITUTION ---")
    print(f"Clinic / Hospital: {extraction['clinic_header']}")

    print("\n--- DOCTOR DETAILS ---")
    doc = extraction["doctor"]
    print(f"Name:             {doc['name']}")
    print(f"Qualification:    {doc['qualification']}")
    print(f"Specialization:   {doc['specialization']}")
    print(f"Reg / Lic #:      {doc['registration_number']}")
    print(f"Clinic/Hospital:  {doc['clinic_or_hospital']}")
    print(f"Contact Number:   {doc['contact_number']}")

    print("\n--- PATIENT DETAILS ---")
    pat = extraction["patient"]
    print(f"Name:             {pat['name']}")
    print(f"Age:              {pat['age']}")
    print(f"Gender:           {pat['gender']}")
    print(f"Address:          {pat['address']}")
    print(f"Prescription Date:{pat['date']}")
    print(f"Patient ID:       {pat['patient_id']}")

    print("\n--- CLINICAL FINDINGS ---")
    print(f"Diagnosis:        {extraction['diagnosis']}")
    print(f"Medical Advice:   {extraction['advice']}")
    print(f"Follow-up:        {extraction['follow_up']}")

    print(f"\n--- PRESCRIBED MEDICINES ({len(extraction['medicines'])} detected) ---")
    for idx, med in enumerate(extraction["medicines"], 1):
        print(f"\n[{idx}] {med['medicine_name']}")
        print(f"    Strength:     {med['strength']}")
        print(f"    Dosage:       {med['dosage']}")
        print(f"    Route:        {med['route']}")
        print(f"    Frequency:    {med['frequency']}")
        print(f"    Duration:     {med['duration']}")
        print(f"    Food Timing:  {med['food_instructions']}")
        print(f"    Special:      {med['special_instructions']}")
        print(f"    Confidence:   {med['confidence']}%")

    print("\n" + "=" * 56 + "\n")


def main():
    parser = argparse.ArgumentParser(description="AI Prescription Reader")
    parser.add_argument("file", nargs="?", help="Path to prescription image/PDF to analyze")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")
    args = parser.parse_args()

    if args.test:
        import pytest
        sys.exit(pytest.main(["tests/test_prescription_reader.py", "-v"]))

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[!] File not found: {file_path}")
            sys.exit(1)
        run_cli_analysis(file_path)
    else:
        print(f"\n Starting AI Prescription Reader Backend on http://{args.host}:{args.port}")
        print(f" Frontend UI available at http://{args.host}:{args.port}/ and http://{args.host}:5173/\n")
        uvicorn.run("backend.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
