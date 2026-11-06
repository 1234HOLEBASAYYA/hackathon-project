"""
main.py
=======
Enhanced Doctor Prescription OCR - Main Entry Point

This is the main script that orchestrates the complete workflow:
1. Load and preprocess the prescription image (with resizing, sharpening, adaptive thresholding)
2. Extract text using enhanced OCR with confidence scores
3. Display and save the results with confidence metrics
4. Generate comparison images (original vs processed)

Project Structure:
- images/           : Folder containing prescription images to process
- output/           : Folder where extracted text results and comparisons are saved
- preprocess.py     : Enhanced image preprocessing module
- ocr.py            : Enhanced OCR text extraction module with confidence reporting
- requirements.txt  : Python package dependencies

Usage:
    python main_enhanced.py          # Will process images from images/ folder
    
New Features:
    - Image resizing for consistent OCR
    - Image sharpening for better text definition
    - Adaptive thresholding for varying lighting
    - Confidence score reporting from Tesseract
    - Before/after image comparisons
"""

import os
import sys
from preprocess import preprocess_image, create_comparison_image
from ocr import process_prescription_image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def find_image_files(images_folder="images"):
    """
    Find all image files in the images folder.
    
    Supports common image formats: .jpg, .jpeg, .png, .bmp, .tiff
    
    Args:
        images_folder (str): Path to folder containing images
        
    Returns:
        list: List of paths to image files found
        
    Notes:
        Creates the images folder if it does not exist.
    """
    if not os.path.exists(images_folder):
        os.makedirs(images_folder, exist_ok=True)
        print(f"Created missing images folder: {images_folder}")
        print(f"Please add prescription images to the '{images_folder}' folder and try again.")
        return []
    
    # Supported image extensions
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    
    image_files = []
    for file in os.listdir(images_folder):
        if file.lower().endswith(supported_formats):
            image_path = os.path.join(images_folder, file)
            image_files.append(image_path)
    
    return image_files


def process_prescription(image_path, output_folder="output", generate_comparison=True):
    """
    Process a single prescription image through the complete pipeline.
    
    Enhanced pipeline steps:
    1. Preprocess image (resize, grayscale, sharpen, blur, adaptive threshold, morphology)
    2. Extract text using Tesseract OCR with confidence scores
    3. Validate and clean text
    4. Generate comparison image (original vs processed)
    5. Save and display results with confidence metrics
    
    Args:
        image_path (str): Path to the prescription image
        output_folder (str): Path to output folder for results
        generate_comparison (bool): Whether to generate before/after comparison images
        
    Returns:
        dict: Processing results containing text, file path, and confidence metrics
        
    Raises:
        Exception: If any step in the pipeline fails
    """
    print(f"\nProcessing: {image_path}")
    print("-" * 60)
    
    try:
        # Step 1: Preprocess the image with new enhanced features
        print("\n[1/3] PREPROCESSING IMAGE (Enhanced)...")
        print("      - Resizing to standard width (1200px)")
        print("      - Sharpening for text clarity")
        print("      - Applying adaptive thresholding")
        preprocess_result = preprocess_image(image_path, use_adaptive=True, debug=False)
        preprocessed_image = preprocess_result['image']
        original_gray = preprocess_result['original_gray']
        
        # Step 2: Extract text with confidence scores
        print("\n[2/3] EXTRACTING TEXT WITH CONFIDENCE SCORES...")
        result = process_prescription_image(preprocessed_image, output_folder, show_confidence=True)
        
        # Step 3: Generate comparison image if requested
        if generate_comparison:
            print("\n[3/3] GENERATING COMPARISON IMAGE...")
            comparison_path = create_comparison_image(original_gray, preprocessed_image, output_folder)
            result['comparison_image'] = comparison_path
        
        # Display confidence summary
        print("\n" + "="*60)
        print("CONFIDENCE SUMMARY")
        print("="*60)
        print(f"Average Confidence: {result['confidence']:.1f}%")
        print(f"Words Recognized: {result['words_recognized']}")
        print("="*60)
        
        print("\n✓ Processing completed successfully!\n")
        return result
        
    except FileNotFoundError as e:
        print(f"\n✗ File Error: {str(e)}")
        return None
    except Exception as e:
        print(f"\n✗ Processing Error: {str(e)}")
        return None


def main():
    """
    Main function - Entry point for the Enhanced Doctor Prescription OCR application.
    
    Enhanced Workflow:
    1. Display welcome message with new features
    2. Find all images in images/ folder
    3. Process each image through the enhanced pipeline
    4. Generate comparisons and confidence reports
    5. Display summary with metrics
    """
    print("\n" + "="*60)
    print("ENHANCED DOCTOR PRESCRIPTION OCR")
    print("Automatic Text Extraction with Confidence Reporting")
    print("="*60)
    print("\nNew Features:")
    print("  • Image resizing for optimal OCR")
    print("  • Adaptive thresholding for varying lighting")
    print("  • Image sharpening for text clarity")
    print("  • Confidence score reporting")
    print("  • Before/after image comparisons")
    print()
    
    images_folder = "images"
    output_folder = "output"
    
    try:
        # Find all image files
        print(f"Searching for images in '{images_folder}' folder...")
        image_files = find_image_files(images_folder)
        
        if not image_files:
            print(f"✗ No image files found in '{images_folder}' folder")
            print(f"  Supported formats: .jpg, .jpeg, .png, .bmp, .tiff")
            print(f"\nPlease add prescription images to the '{images_folder}' folder and try again.")
            return
        
        print(f"✓ Found {len(image_files)} image(s) to process\n")
        
        # Process each image
        results = []
        for i, image_path in enumerate(image_files, 1):
            print(f"\n{'='*60}")
            print(f"IMAGE {i}/{len(image_files)}")
            print(f"{'='*60}")
            
            result = process_prescription(image_path, output_folder, generate_comparison=True)
            if result:
                results.append(result)
        
        # Display comprehensive summary
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Total images processed: {len(results)}/{len(image_files)}")
        print(f"Output folder: {output_folder}/")
        
        # Calculate average confidence across all images
        if results:
            avg_confidence_all = sum(r['confidence'] for r in results) / len(results)
            total_words = sum(r['words_recognized'] for r in results)
            print(f"\nOverall Statistics:")
            print(f"  Average confidence: {avg_confidence_all:.1f}%")
            print(f"  Total words recognized: {total_words}")
            print(f"\nGenerated Files:")
            print(f"  Text extractions: {len(results)} .txt files")
            print(f"  Comparison images: {len([r for r in results if 'comparison_image' in r])} .png files")
        
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n✗ Processing interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
