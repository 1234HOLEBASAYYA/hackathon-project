"""
preprocess.py
=============
Enhanced image preprocessing module for the Doctor Prescription OCR project.

This module handles all image preprocessing steps including:
- Image resizing (for consistent OCR processing)
- Grayscale conversion
- Image sharpening (make text more defined)
- Noise reduction (Gaussian blur)
- Adaptive thresholding (handles varying lighting)
- Morphological operations (clean up image)

These preprocessing steps improve OCR accuracy by making the text clearer and darker.
"""

import cv2
import os
import numpy as np


def load_image(image_path):
    """
    Load an image from the specified path.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        numpy.ndarray: The loaded image
        
    Raises:
        FileNotFoundError: If the image file does not exist
        ValueError: If the image cannot be loaded
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Load the image in BGR color format (OpenCV default)
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")
    
    print(f"✓ Image loaded successfully from: {image_path}")
    print(f"  Image dimensions: {image.shape[1]} x {image.shape[0]} pixels")
    
    return image


def convert_to_grayscale(image):
    """
    Convert a color image to grayscale.
    
    Grayscale conversion removes color information and focuses on intensity,
    which helps Tesseract recognize text more effectively.
    
    Args:
        image (numpy.ndarray): Input image in BGR format
        
    Returns:
        numpy.ndarray: Grayscale image
    """
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print("✓ Image converted to grayscale")
    return gray_image


def apply_blur(image, kernel_size=5):
    """
    Apply Gaussian blur to reduce noise in the image.
    
    Blur helps remove small noise spots and smooths the image, which can
    improve text recognition quality.
    
    Args:
        image (numpy.ndarray): Input grayscale image
        kernel_size (int): Size of the blur kernel (must be odd number)
        
    Returns:
        numpy.ndarray: Blurred image
    """
    # Ensure kernel size is odd (OpenCV requirement)
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    blurred_image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    print(f"✓ Gaussian blur applied (kernel size: {kernel_size}x{kernel_size})")
    return blurred_image


def resize_image(image, width=1200):
    """
    Resize image to a standard width for consistent OCR processing.
    
    Resizing ensures that text size is consistent, which helps Tesseract
    recognize characters better. The height is adjusted proportionally
    to maintain the original aspect ratio.
    
    Args:
        image (numpy.ndarray): Input image
        width (int): Target width in pixels (default: 1200)
        
    Returns:
        numpy.ndarray: Resized image
    """
    # Get original dimensions
    original_height, original_width = image.shape[:2]
    
    # Calculate height while maintaining aspect ratio
    ratio = width / original_width
    new_height = int(original_height * ratio)
    
    # Resize the image (cv2.INTER_CUBIC is good quality for upscaling/downscaling)
    resized_image = cv2.resize(image, (width, new_height), interpolation=cv2.INTER_CUBIC)
    
    print(f"✓ Image resized to: {width} x {new_height} pixels")
    return resized_image


def apply_sharpening(image):
    """
    Apply image sharpening to make text more defined and clear.
    
    Sharpening enhances edges and increases contrast between text and
    background, making characters more distinct for OCR.
    
    Args:
        image (numpy.ndarray): Input grayscale image
        
    Returns:
        numpy.ndarray: Sharpened image
    """
    # Unsharp mask kernel (standard sharpening technique)
    # This kernel emphasizes high-frequency details (edges/text)
    kernel = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ]) / 1.0
    
    # Apply the sharpening kernel to the image
    sharpened_image = cv2.filter2D(image, -1, kernel)
    print("✓ Image sharpening applied")
    return sharpened_image


def apply_threshold(image, threshold_value=150):
    """
    Convert the image to binary (black and white only) using thresholding.
    
    Thresholding makes text (dark) stand out from background (white), which
    is exactly what Tesseract OCR prefers for accurate text extraction.
    
    Args:
        image (numpy.ndarray): Input grayscale image
        threshold_value (int): Threshold value (0-255). Pixels below this
                              become black, above become white.
        
    Returns:
        numpy.ndarray: Binary (black and white) image
    """
    # Using binary thresholding: pixel values < threshold_value → 0 (black)
    # pixel values >= threshold_value → 255 (white)
    _, binary_image = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)
    print(f"✓ Fixed thresholding applied (threshold value: {threshold_value})")
    return binary_image


def apply_adaptive_threshold(image, block_size=11):
    """
    Apply adaptive thresholding to handle varying lighting conditions.
    
    Adaptive thresholding calculates a threshold for each pixel based on
    nearby pixels. This works better than fixed thresholding when the image
    has uneven lighting, shadows, or varying contrast levels.
    
    Args:
        image (numpy.ndarray): Input grayscale image
        block_size (int): Size of the neighborhood area (must be odd number)
                         Larger = considers more surrounding pixels
        
    Returns:
        numpy.ndarray: Binary (black and white) image
    """
    # Ensure block size is odd (OpenCV requirement)
    if block_size % 2 == 0:
        block_size += 1
    
    # ADAPTIVE_THRESH_GAUSSIAN_C: calculates threshold as mean of block
    # This is more sophisticated than fixed thresholding
    adaptive_binary = cv2.adaptiveThreshold(
        image,
        255,  # Maximum value (white)
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # Method: weighted gaussian
        cv2.THRESH_BINARY,  # Apply binary thresholding
        block_size,  # Neighborhood size
        2  # Constant subtracted (fine-tunes sensitivity)
    )
    
    print(f"✓ Adaptive thresholding applied (block size: {block_size}x{block_size})")
    return adaptive_binary


def apply_morphological_operations(image):
    """
    Apply morphological operations to clean up the binary image.
    
    - Dilation: Makes dark areas (text) thicker
    - Erosion: Makes dark areas thinner
    These operations help remove small noise and fill small holes in text.
    
    Args:
        image (numpy.ndarray): Binary input image
        
    Returns:
        numpy.ndarray: Cleaned binary image
    """
    # Create a kernel for morphological operations (3x3 rectangular shape)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    
    # Apply morphological close operation (dilation followed by erosion)
    # This fills small holes in text and removes small noise
    cleaned_image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=2)
    print("✓ Morphological operations applied")
    return cleaned_image


def create_comparison_image(original, preprocessed, output_folder="output"):
    """
    Create a side-by-side comparison of original and preprocessed images.
    
    This helps visualize the effect of preprocessing on the image and
    is useful for understanding how image processing improves OCR accuracy.
    
    Args:
        original (numpy.ndarray): Original grayscale image
        preprocessed (numpy.ndarray): Preprocessed binary image
        output_folder (str): Path to save the comparison
        
    Returns:
        str: Path to the saved comparison image
    """
    from datetime import datetime
    
    # Resize images to same height for side-by-side comparison
    # (if they're different sizes)
    if original.shape != preprocessed.shape:
        # Use the smaller height to fit both
        target_height = min(original.shape[0], preprocessed.shape[0])
        original_resized = cv2.resize(original, (int(original.shape[1] * target_height / original.shape[0]), target_height))
        preprocessed_resized = cv2.resize(preprocessed, (int(preprocessed.shape[1] * target_height / preprocessed.shape[0]), target_height))
    else:
        original_resized = original
        preprocessed_resized = preprocessed
    
    # Convert grayscale to 3-channel so we can combine with color image
    original_bgr = cv2.cvtColor(original_resized, cv2.COLOR_GRAY2BGR)
    preprocessed_bgr = cv2.cvtColor(preprocessed_resized, cv2.COLOR_GRAY2BGR)
    
    # Create side-by-side comparison
    comparison = np.hstack([original_bgr, preprocessed_bgr])
    
    # Add labels on the image
    cv2.putText(comparison, "Original (Grayscale)", (30, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(comparison, "Preprocessed (Binary)", 
                (original_resized.shape[1] + 30, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Save comparison image with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comparison_{timestamp}.png"
    filepath = os.path.join(output_folder, filename)
    cv2.imwrite(filepath, comparison)
    
    print(f"✓ Comparison image saved to: {filepath}")
    return filepath


def preprocess_image(image_path, use_adaptive=True, debug=False):
    """
    Enhanced preprocessing pipeline for prescription images.
    
    This function chains all preprocessing steps together to prepare
    the image for OCR. It performs:
    1. Load image
    2. Resize image (for consistent processing)
    3. Convert to grayscale
    4. Apply image sharpening (make text clearer)
    5. Reduce noise with Gaussian blur
    6. Apply thresholding (adaptive or fixed)
    7. Apply morphological operations (cleanup)
    
    Args:
        image_path (str): Path to the input image
        use_adaptive (bool): If True, use adaptive thresholding (better for
                            varying lighting). If False, use fixed threshold.
        debug (bool): If True, save intermediate processed images to output/
        
    Returns:
        dict: Dictionary containing:
            - 'image': Preprocessed image ready for OCR
            - 'original_gray': Grayscale original (for comparisons)
    """
    print("\n" + "="*60)
    print("ENHANCED PREPROCESSING PIPELINE STARTED")
    print("="*60)
    
    try:
        # Step 1: Load the image
        original = load_image(image_path)
        
        # Step 2: Resize for consistent processing
        resized = resize_image(original, width=1200)
        
        # Step 3: Convert to grayscale
        gray = convert_to_grayscale(resized)
        
        # Step 4: Apply image sharpening
        sharpened = apply_sharpening(gray)
        
        # Step 5: Reduce noise with Gaussian blur
        blurred = apply_blur(sharpened, kernel_size=5)
        
        # Step 6: Apply thresholding (choose method)
        if use_adaptive:
            binary = apply_adaptive_threshold(blurred, block_size=11)
            print("  Method: Adaptive thresholding (handles varying lighting)")
        else:
            binary = apply_threshold(blurred, threshold_value=150)
            print("  Method: Fixed thresholding")
        
        # Step 7: Clean up with morphological operations
        cleaned = apply_morphological_operations(binary)
        
        print("\n✓ Preprocessing completed successfully!")
        print("="*60 + "\n")
        
        # Optional: Save intermediate images for debugging
        if debug:
            cv2.imwrite("output/01_grayscale.png", gray)
            cv2.imwrite("output/02_sharpened.png", sharpened)
            cv2.imwrite("output/03_blurred.png", blurred)
            cv2.imwrite("output/04_binary.png", binary)
            cv2.imwrite("output/05_cleaned.png", cleaned)
            print("Debug images saved to output/ folder\n")
        
        # Return both preprocessed image and original grayscale for comparison
        return {
            'image': cleaned,
            'original_gray': gray,
            'original_path': image_path
        }
        
    except Exception as e:
        print(f"\n✗ Error during preprocessing: {str(e)}")
        raise


if __name__ == "__main__":
    # This allows testing the preprocessing module independently
    print("Doctor Prescription OCR - Image Preprocessing Module")
    print("This module is designed to be imported and used by main.py")
    print("\nTo test preprocessing, run: python main.py")
