"""Generate test fixtures for comprehensive prescription reader test suite."""

import os
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fitz

TEST_DIR = Path(__file__).resolve().parent / "fixtures"
TEST_DIR.mkdir(parents=True, exist_ok=True)


def create_printed_multimed_rx():
    """Create a printed multi-medicine prescription."""
    img = np.ones((900, 700, 3), dtype=np.uint8) * 250
    color = (20, 20, 20)
    
    cv2.putText(img, "APOLLO HOSPITALS CLINICAL OUTPATIENT", (80, 50), cv2.FONT_HERSHEY_DUPLEX, 0.7, (180, 0, 0), 2)
    cv2.putText(img, "Dr. Sarah Jenkins, MD, Cardiologist", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    cv2.putText(img, "Lic #: NY-892410", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    cv2.putText(img, "Date: 12/04/2026", (500, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    
    cv2.line(img, (50, 135), (650, 135), (100, 100, 100), 1)
    
    cv2.putText(img, "Patient Name: Robert Miller", (50, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    cv2.putText(img, "Age: 58 yrs | Gender: Male", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
    
    cv2.putText(img, "Rx (Medications)", (50, 250), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 160), 2)
    
    # Med 1: Atorvastatin
    cv2.putText(img, "1. Tab. Atorvastatin 20mg", (50, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    cv2.putText(img, "   1 tablet OD at bedtime", (70, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    cv2.putText(img, "   Duration: 30 days", (70, 345), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    
    # Med 2: Metformin
    cv2.putText(img, "2. Tab. Metformin 500mg", (50, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    cv2.putText(img, "   1 tablet Twice daily with meals", (70, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    cv2.putText(img, "   Duration: 60 days", (70, 445), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    
    # Med 3: Pantoprazole
    cv2.putText(img, "3. Cap. Pantoprazole 40mg", (50, 490), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    cv2.putText(img, "   Take 1 cap Once daily before breakfast", (70, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    cv2.putText(img, "   Duration: 14 days", (70, 545), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)
    
    cv2.putText(img, "Instructions: Do not crush or chew tablets. Drink plenty of water.", (50, 620), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    cv2.imwrite(str(TEST_DIR / "printed_multimed.png"), img)


def create_handwritten_style_rx():
    """Create a simulated handwritten prescription with cursive-like pen strokes."""
    img = np.ones((800, 600, 3), dtype=np.uint8) * 242
    color = (40, 20, 10)  # Dark brownish ink
    
    cv2.putText(img, "Dr. Emily Watson MBBS", (40, 70), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.1, color, 2)
    cv2.putText(img, "Reg: 54128-B", (40, 110), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.8, color, 2)
    cv2.putText(img, "Date: 15/06/2026", (380, 110), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.8, color, 2)
    
    cv2.putText(img, "Pt: Arthur Dent 38 y Male", (40, 170), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.95, color, 2)
    cv2.putText(img, "Rx", (40, 230), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.4, (120, 20, 20), 3)
    
    cv2.putText(img, "Paracetamol 650mg", (60, 280), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.0, color, 2)
    cv2.putText(img, "1 tab TDS after meals", (80, 320), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.85, color, 2)
    cv2.putText(img, "for 5 days", (80, 355), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.85, color, 2)
    
    cv2.putText(img, "Cetirizine 10mg", (60, 420), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.0, color, 2)
    cv2.putText(img, "1 tab OD at bedtime", (80, 460), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.85, color, 2)
    cv2.putText(img, "x 7 days", (80, 495), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 0.85, color, 2)
    
    cv2.imwrite(str(TEST_DIR / "handwritten.png"), img)


def create_blurry_rx():
    """Create a severely blurred prescription image."""
    base = cv2.imread(str(TEST_DIR / "printed_multimed.png"))
    if base is not None:
        blurred = cv2.GaussianBlur(base, (25, 25), 0)
        cv2.imwrite(str(TEST_DIR / "blurry.png"), blurred)


def create_unreadable_rx():
    """Create an unreadable noisy black image."""
    noisy = np.random.randint(0, 30, (400, 400, 3), dtype=np.uint8)
    cv2.imwrite(str(TEST_DIR / "unreadable.png"), noisy)


def create_pdf_rx():
    """Create a PDF prescription using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    
    # Insert text lines
    text = (
        "CITY GENERAL HOSPITAL - PRESCRIPTION\n"
        "Dr. David Miller, MD (General Medicine) | Reg No: MED-78901\n"
        "Date: 10/11/2026\n"
        "-------------------------------------------------------------------------\n"
        "Patient Name: Mary Higgins | Age: 29 | Gender: Female\n"
        "-------------------------------------------------------------------------\n"
        "Rx\n"
        "1. Azithromycin 500mg\n"
        "   Take 1 tablet Once daily before food\n"
        "   Duration: 3 days\n\n"
        "2. Paracetamol 500mg\n"
        "   Take 1 tablet Three times daily as needed for pain\n"
        "   Duration: 5 days\n\n"
        "Special Instructions: Complete the full course of antibiotics."
    )
    rect = fitz.Rect(50, 50, 545, 750)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv", color=(0, 0, 0))
    doc.save(str(TEST_DIR / "sample_prescription.pdf"))
    doc.close()


def create_invalid_and_empty_files():
    """Create invalid extension and empty files."""
    with open(TEST_DIR / "invalid_file.txt", "w") as f:
        f.write("This is a plain text file, not an image or PDF.")
    with open(TEST_DIR / "empty_file.png", "wb") as f:
        pass


if __name__ == "__main__":
    create_printed_multimed_rx()
    create_handwritten_style_rx()
    create_blurry_rx()
    create_unreadable_rx()
    create_pdf_rx()
    create_invalid_and_empty_files()
    print("All test fixtures generated successfully in tests/fixtures/")

