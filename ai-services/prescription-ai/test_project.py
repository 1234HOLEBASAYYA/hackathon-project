"""
test_project.py
===============
Test script to verify that the Doctor Prescription OCR project is properly set up.

This script checks:
1. All required packages are installed
2. Tesseract OCR is installed
3. Project folders exist
4. All modules can be imported
5. Basic functionality works

Run this to diagnose setup issues:
    python test_project.py
"""

import sys
import os

from src.tesseract_config import configure_tesseract

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

configure_tesseract()


def test_python_version():
    """Check Python version."""
    print("="*60)
    print("1. CHECKING PYTHON VERSION")
    print("="*60)
    
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("✗ Python 3.7+ required")
        return False
    
    print("✓ Python version OK\n")
    return True


def test_packages():
    """Check if required packages are installed."""
    print("="*60)
    print("2. CHECKING INSTALLED PACKAGES")
    print("="*60)
    
    packages = {
        'cv2': 'OpenCV',
        'pytesseract': 'Pytesseract',
        'PIL': 'Pillow'
    }
    
    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed - run: pip install {name.lower()}")
            all_ok = False
    
    print()
    return all_ok


def test_tesseract():
    """Check if OCR engine (GPU EasyOCR or Tesseract) is installed."""
    print("="*60)
    print("3. CHECKING OCR ENGINE (GPU EasyOCR / Tesseract)")
    print("="*60)
    
    try:
        import torch
        import easyocr
        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        print(f"✓ AI Deep Learning OCR available: EasyOCR ({gpu_name})")
        print()
        return True
    except Exception:
        pass

    try:
        import pytesseract
        import cv2
        
        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract found: {version}")
        print()
        return True
        
    except Exception as e:
        print(f"✗ Tesseract not found")
        print(f"  Error: {str(e)}")
        print(f"\n  Install Tesseract from:")
        print(f"  https://github.com/UB-Mannheim/tesseract/wiki")
        print()
        return False


def test_project_structure():
    """Check if project folders exist."""
    print("="*60)
    print("4. CHECKING PROJECT STRUCTURE")
    print("="*60)
    
    required_files = {
        'main.py': 'Main entry point',
        'preprocess.py': 'Image preprocessing module',
        'ocr.py': 'OCR extraction module',
        'requirements.txt': 'Package dependencies',
        'README.md': 'Documentation',
    }
    
    required_folders = {
        'images': 'Input images folder',
        'output': 'Output results folder',
    }
    
    all_ok = True
    
    # Check files
    for filename, description in required_files.items():
        if os.path.exists(filename):
            print(f"✓ {filename:20s} - {description}")
        else:
            print(f"✗ {filename:20s} - NOT FOUND")
            all_ok = False
    
    # Check folders
    for foldername, description in required_folders.items():
        if os.path.exists(foldername):
            print(f"✓ {foldername:20s} - {description}")
        else:
            print(f"✗ {foldername:20s} - NOT FOUND")
            all_ok = False
    
    print()
    return all_ok


def test_modules_import():
    """Test if project modules can be imported."""
    print("="*60)
    print("5. TESTING MODULE IMPORTS")
    print("="*60)
    
    all_ok = True
    
    try:
        import preprocess
        print("✓ preprocess module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import preprocess: {e}")
        all_ok = False
    
    try:
        import ocr
        print("✓ ocr module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import ocr: {e}")
        all_ok = False
    
    print()
    return all_ok


def test_sample_image():
    """Check if there's a sample image to test with."""
    print("="*60)
    print("6. CHECKING SAMPLE IMAGE")
    print("="*60)
    
    image_files = []
    if os.path.exists('images'):
        for file in os.listdir('images'):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                image_files.append(file)
    
    if image_files:
        print(f"✓ Found {len(image_files)} image(s) in images/:")
        for img in image_files:
            print(f"  - {img}")
    else:
        print("⚠ No images found in images/ folder")
        print(f"\n  Create a sample image by running:")
        print(f"  python create_sample_prescription.py")
    
    print()
    return True


def test_basic_functionality():
    """Test basic functionality if all setup is OK."""
    print("="*60)
    print("7. TESTING BASIC FUNCTIONALITY")
    print("="*60)
    
    try:
        import cv2
        import numpy as np
        
        # Test creating a simple image
        test_image = np.ones((100, 100), dtype=np.uint8) * 200
        print("✓ Can create NumPy arrays")
        
        # Test OpenCV function
        blurred = cv2.GaussianBlur(test_image, (5, 5), 0)
        print("✓ OpenCV image processing works")
        
        print("✓ Basic functionality verified")
        print()
        return True
        
    except Exception as e:
        print(f"✗ Error testing functionality: {e}")
        print()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("#"*60)
    print("# DOCTOR PRESCRIPTION OCR - SETUP VERIFICATION")
    print("#"*60)
    print("\n")
    
    results = []
    
    # Run all tests
    results.append(("Python Version", test_python_version()))
    results.append(("Packages", test_packages()))
    results.append(("Tesseract OCR", test_tesseract()))
    results.append(("Project Structure", test_project_structure()))
    results.append(("Module Imports", test_modules_import()))
    results.append(("Sample Image", test_sample_image()))
    results.append(("Basic Functionality", test_basic_functionality()))
    
    # Print summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    if passed == total:
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        print("\nYou're ready to use the project!")
        print("Run: python main.py")
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total})")
        print("\nFix the issues above and try again.")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
