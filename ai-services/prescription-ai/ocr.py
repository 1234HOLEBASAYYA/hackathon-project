"""
ocr.py
======
Enhanced Optical Character Recognition (OCR) module for the Doctor Prescription OCR project.

This module uses Tesseract OCR engine (via pytesseract) to extract text from
preprocessed images with confidence scores. It handles:
- Text extraction with confidence reporting
- Detailed OCR results (per word/line confidence)
- Text validation and saving
- Results display with confidence metrics

Tesseract is a powerful open-source OCR engine that works best with:
- Clear, preprocessed images
- Binary (black and white) images
- Good contrast between text and background
"""

import pytesseract
import os
from datetime import datetime
import json

from src.tesseract_config import configure_tesseract

configure_tesseract()


def extract_text_from_image(preprocessed_image):
    """
    Extract text from a preprocessed image using Tesseract OCR.
    
    Tesseract recognizes characters and words in the image and returns
    the extracted text as a string.
    
    Args:
        preprocessed_image (numpy.ndarray): Preprocessed binary image
        
    Returns:
        str: Extracted text from the image
        
    Raises:
        Exception: If Tesseract is not installed or fails to process
    """
    try:
        print("\n" + "="*60)
        print("OCR EXTRACTION STARTED")
        print("="*60)
        print("Sending image to Tesseract OCR engine...")
        
        # Extract text using Tesseract
        # --psm 6: Assume a single uniform block of text
        # This is a good default for prescription images
        extracted_text = pytesseract.image_to_string(
            preprocessed_image,
            config='--psm 6'  # PSM 6 works well for document text
        )
        
        print("✓ Text extraction completed successfully!")
        print(f"  Total characters extracted: {len(extracted_text)}")
        print(f"  Total lines extracted: {len(extracted_text.splitlines())}")
        print("="*60 + "\n")
        
        return extracted_text
        
    except pytesseract.TesseractNotFoundError:
        error_msg = (
            "Tesseract OCR engine is not installed!\n"
            "Please install it from: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "On Windows: Download the installer and add to PATH"
        )
        print(f"\n✗ Error: {error_msg}")
        raise
    except Exception as e:
        print(f"\n✗ OCR Error: {str(e)}")
        raise


def extract_text_with_confidence(preprocessed_image):
    """
    Extract text from image with detailed confidence scores.
    
    This function extracts not only the text but also returns confidence
    metrics for each word recognized. This helps assess the reliability
    of the OCR results.
    
    Args:
        preprocessed_image (numpy.ndarray): Preprocessed binary image
        
    Returns:
        dict: Dictionary containing:
            - 'text': Complete extracted text
            - 'confidence': Average confidence (0-100)
            - 'data': Detailed per-word data with coordinates and confidence
    """
    try:
        print("Extracting detailed OCR data with confidence scores...")
        
        # Get detailed data from Tesseract (includes coordinates and confidence)
        # output_type=pytesseract.Output.DICT returns a dictionary with detailed info
        data = pytesseract.image_to_data(
            preprocessed_image,
            config='--psm 6',
            output_type=pytesseract.Output.DICT
        )
        
        # Extract words and confidence scores
        words = []
        confidences = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = int(data['conf'][i])
            
            # Only include words with valid confidence (not -1)
            if text and confidence != -1:
                words.append({
                    'text': text,
                    'confidence': confidence
                })
                confidences.append(confidence)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Reconstruct full text
        full_text = '\n'.join(line for line in data['text'] if line.strip())
        
        result = {
            'text': full_text,
            'confidence': avg_confidence,
            'data': words,
            'words_recognized': len(words)
        }
        
        print(f"✓ Average confidence: {avg_confidence:.1f}%")
        print(f"✓ Words recognized: {len(words)}")
        
        return result
        
    except Exception as e:
        print(f"Note: Could not extract detailed confidence data: {str(e)}")
        print("Falling back to basic text extraction...")
        # If detailed extraction fails, fall back to basic text
        text = extract_text_from_image(preprocessed_image)
        return {
            'text': text,
            'confidence': 0,
            'data': [],
            'words_recognized': 0
        }


def calculate_confidence_statistics(ocr_result):
    """
    Calculate and display confidence statistics from OCR results.
    
    Args:
        ocr_result (dict): Result dictionary from extract_text_with_confidence()
        
    Returns:
        dict: Statistics dictionary containing:
            - 'average': Average confidence
            - 'min': Minimum confidence
            - 'max': Maximum confidence
            - 'quality': Quality assessment (Good/Fair/Poor)
    """
    if not ocr_result['data']:
        return {
            'average': 0,
            'min': 0,
            'max': 0,
            'quality': 'Unknown'
        }
    
    confidences = [word['confidence'] for word in ocr_result['data']]
    
    stats = {
        'average': sum(confidences) / len(confidences),
        'min': min(confidences),
        'max': max(confidences),
    }
    
    # Assign quality level based on average confidence
    if stats['average'] >= 85:
        stats['quality'] = 'Excellent'
    elif stats['average'] >= 75:
        stats['quality'] = 'Good'
    elif stats['average'] >= 60:
        stats['quality'] = 'Fair'
    else:
        stats['quality'] = 'Poor'
    
    return stats



def validate_text(text):
    """
    Validate and clean the extracted text.
    
    This function performs basic validation and cleanup:
    - Removes extra whitespace
    - Checks if text is empty
    - Removes control characters
    
    Args:
        text (str): Raw extracted text from OCR
        
    Returns:
        str: Cleaned and validated text
    """
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple spaces with single space
    text = ' '.join(text.split())
    
    # Remove control characters (invisible characters)
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    
    # Check if text is empty
    if not text:
        print("⚠ Warning: No text extracted from image!")
        return ""
    
    print(f"✓ Text validation passed")
    return text


def save_text_to_file(text, output_folder="output", ocr_result=None):
    """
    Save extracted text to a .txt file with timestamp and optional confidence info.
    
    Creates a new file in the output folder with the current timestamp,
    ensuring each extraction result is saved separately. Optionally includes
    confidence metrics if provided.
    
    Args:
        text (str): Text to save
        output_folder (str): Path to output folder
        ocr_result (dict): Optional OCR result dictionary with confidence data
        
    Returns:
        str: Path to the saved file
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        # Ensure output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"✓ Created output folder: {output_folder}")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prescription_{timestamp}.txt"
        filepath = os.path.join(output_folder, filename)
        
        # Write text to file with confidence information if available
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write("="*60 + "\n")
            file.write("PRESCRIPTION OCR EXTRACTION RESULTS\n")
            file.write("="*60 + "\n\n")
            
            # Add confidence information if available
            if ocr_result:
                file.write(f"Extraction Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write(f"Average Confidence: {ocr_result['confidence']:.1f}%\n")
                file.write(f"Words Recognized: {ocr_result['words_recognized']}\n")
                file.write("\n" + "-"*60 + "\n\n")
            
            # Write the extracted text
            file.write("EXTRACTED TEXT:\n")
            file.write("-"*60 + "\n")
            file.write(text)
            file.write("\n" + "="*60 + "\n")
        
        print(f"\n✓ Results saved to: {filepath}")
        return filepath
        
    except IOError as e:
        print(f"\n✗ Error writing to file: {str(e)}")
        raise


def display_ocr_results(ocr_result):
    """
    Display OCR results with confidence metrics on terminal.
    
    Shows extracted text along with confidence scores and quality assessment.
    
    Args:
        ocr_result (dict): Result from extract_text_with_confidence()
    """
    print("\n" + "="*60)
    print("OCR RESULTS WITH CONFIDENCE METRICS")
    print("="*60)
    
    # Display confidence information
    print(f"\nAverage Confidence: {ocr_result['confidence']:.1f}%")
    print(f"Words Recognized: {ocr_result['words_recognized']}")
    
    # Calculate and show statistics
    if ocr_result['data']:
        stats = calculate_confidence_statistics(ocr_result)
        print(f"\nConfidence Statistics:")
        print(f"  Highest: {stats['max']}%")
        print(f"  Lowest:  {stats['min']}%")
        print(f"  Quality: {stats['quality']}")
    
    print("\n" + "-"*60)
    print("EXTRACTED TEXT:")
    print("-"*60 + "\n")
    
    if ocr_result['text'].strip():
        print(ocr_result['text'])
    else:
        print("[No text extracted]")
    
    print("\n" + "="*60 + "\n")


def display_text(text, title="EXTRACTED TEXT"):
    """
    Display extracted text in a formatted way on the terminal.
    
    Args:
        text (str): Text to display
        title (str): Title for the display section
    """
    print("\n" + "="*60)
    print(f"{title}")
    print("="*60)
    
    if text.strip():
        print(text)
    else:
        print("[No text extracted]")
    
    print("="*60 + "\n")


def process_prescription_image(preprocessed_image, output_folder="output", show_confidence=True):
    """
    Enhanced OCR processing pipeline for prescription images.
    
    This function chains the OCR steps together:
    1. Extract text using Tesseract with confidence scores
    2. Validate and clean the text
    3. Calculate confidence metrics
    4. Display results on terminal
    5. Save to file with confidence information
    
    Args:
        preprocessed_image (numpy.ndarray): Preprocessed binary image
        output_folder (str): Path to output folder for saving results
        show_confidence (bool): Whether to show detailed confidence info
        
    Returns:
        dict: Dictionary containing:
            - 'text': Extracted text
            - 'filepath': Path to saved file
            - 'confidence': Average confidence score (0-100)
            - 'words_recognized': Number of words recognized
    """
    try:
        print("\n" + "="*60)
        print("ENHANCED OCR PROCESSING STARTED")
        print("="*60)
        
        # Step 1: Extract text with confidence scores
        if show_confidence:
            ocr_result = extract_text_with_confidence(preprocessed_image)
            raw_text = ocr_result['text']
        else:
            raw_text = extract_text_from_image(preprocessed_image)
            ocr_result = None
        
        # Step 2: Validate and clean text
        cleaned_text = validate_text(raw_text)
        
        # Step 3: Display results with confidence if available
        if show_confidence and ocr_result:
            display_ocr_results(ocr_result)
        else:
            display_text(cleaned_text, "PRESCRIPTION TEXT")
        
        # Step 4: Save to file
        filepath = save_text_to_file(cleaned_text, output_folder, ocr_result)
        
        result = {
            'text': cleaned_text,
            'filepath': filepath,
            'confidence': ocr_result['confidence'] if ocr_result else 0,
            'words_recognized': ocr_result['words_recognized'] if ocr_result else 0
        }
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error during OCR processing: {str(e)}")
        raise


if __name__ == "__main__":
    # This allows testing the OCR module independently
    print("Doctor Prescription OCR - Text Extraction Module")
    print("This module is designed to be imported and used by main.py")
    print("\nTo test OCR extraction, run: python main.py")
