"""
create_sample_prescription.py
=============================
Generate a sample prescription image for testing the OCR project.

This script creates a simple prescription image with text that you can use
to test the Doctor Prescription OCR system without needing a real prescription.

Run this ONCE to create a sample image:
    python create_sample_prescription.py

It will create: images/sample_prescription.png
"""

import cv2
import numpy as np
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def create_sample_prescription_image():
    """
    Create a sample prescription image for testing.
    
    The image contains:
    - Doctor information
    - Patient details
    - Medication information
    - Prescription notes
    
    Simulates a simple prescription document.
    """
    
    print("Creating sample prescription image...")
    
    # Create a white canvas (light gray background to simulate paper)
    height, width = 800, 600
    image = np.ones((height, width, 3), dtype=np.uint8) * 240  # Light gray
    
    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_size = 0.9
    color = (0, 0, 0)  # Black text
    thickness = 2
    line_spacing = 40
    
    # Starting position
    x = 50
    y = 80
    
    # Add header
    cv2.putText(image, "PRESCRIPTION", (150, y), cv2.FONT_HERSHEY_DUPLEX, 1.5, color, 2)
    y += line_spacing + 20
    
    # Add date
    today = datetime.now().strftime("%d/%m/%Y")
    cv2.putText(image, f"Date: {today}", (x, y), font, font_size, color, thickness)
    y += line_spacing
    
    # Add doctor info
    cv2.putText(image, "Dr. Michael Johnson", (x, y), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2)
    y += line_spacing
    cv2.putText(image, "General Practitioner", (x, y), font, font_size, color, thickness)
    y += line_spacing
    cv2.putText(image, "Lic. #: MD-45892", (x, y), font, font_size, color, thickness)
    y += line_spacing + 20
    
    # Add patient info
    cv2.putText(image, "Patient Name: James Smith", (x, y), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2)
    y += line_spacing
    cv2.putText(image, "Age: 42 | Gender: Male", (x, y), font, font_size, color, thickness)
    y += line_spacing + 20
    
    # Add medication
    cv2.putText(image, "MEDICATIONS:", (x, y), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2)
    y += line_spacing
    
    cv2.putText(image, "1. Amoxicillin 500mg", (x + 20, y), font, font_size, color, thickness)
    y += line_spacing
    cv2.putText(image, "   Take one tablet three times daily", (x + 20, y), font, 0.8, color, 1)
    y += line_spacing
    cv2.putText(image, "   Duration: 7 days", (x + 20, y), font, 0.8, color, 1)
    y += line_spacing + 15
    
    cv2.putText(image, "2. Ibuprofen 400mg", (x + 20, y), font, font_size, color, thickness)
    y += line_spacing
    cv2.putText(image, "   Take one tablet twice daily with food", (x + 20, y), font, 0.8, color, 1)
    y += line_spacing
    cv2.putText(image, "   As needed for pain", (x + 20, y), font, 0.8, color, 1)
    y += line_spacing + 20
    
    # Add notes
    cv2.putText(image, "NOTES:", (x, y), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2)
    y += line_spacing
    cv2.putText(image, "Complete the full course of antibiotics", (x + 20, y), font, 0.8, color, 1)
    y += line_spacing
    cv2.putText(image, "Do not exceed recommended dosage", (x + 20, y), font, 0.8, color, 1)
    y += line_spacing + 30
    
    # Add signature area
    cv2.line(image, (x, y), (x + 150, y), color, 2)
    cv2.putText(image, "Doctor Signature", (x, y + 30), font, 0.7, color, 1)
    
    # Create images folder if it doesn't exist
    import os
    if not os.path.exists('images'):
        os.makedirs('images')
        print("✓ Created 'images' folder")
    
    # Save the image
    output_path = 'images/sample_prescription.png'
    cv2.imwrite(output_path, image)
    
    print(f"✓ Sample prescription image created: {output_path}")
    print(f"  Image size: {width}x{height} pixels")
    print(f"\nYou can now run: python main.py")
    print("The OCR will extract text from this sample prescription.")


if __name__ == "__main__":
    try:
        create_sample_prescription_image()
        print("\n✓ Sample image ready for testing!")
    except Exception as e:
        print(f"✗ Error creating sample image: {e}")
        import traceback
        traceback.print_exc()
