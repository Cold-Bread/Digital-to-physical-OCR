"""
Test the fixed evaluation script with a single image
"""

import sys
import cv2
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent
model_training_dir = current_dir.parent
sys.path.insert(0, str(model_training_dir))
sys.path.insert(0, str(model_training_dir.parent))  # ocr_paddle_service
sys.path.insert(0, str(model_training_dir.parent.parent))  # backend

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("PaddleOCR not installed. Please install with: pip install paddleocr")
    sys.exit(1)

def test_single_image():
    """Test OCR on a single image to verify the data format"""
    
    # Set up paths
    current_dir = Path(__file__).parent
    dataset_dir = current_dir.parent / "test_dataset"
    val_images_dir = dataset_dir / "val_images"
    
    # Find the first available image
    sample_image = None
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        images = list(val_images_dir.glob(ext))
        if images:
            sample_image = images[0]
            break
    
    if not sample_image:
        print(f"No images found in: {val_images_dir}")
        return
    
    print(f"Testing OCR on: {sample_image}")
    
    # Initialize OCR
    print("Initializing PaddleOCR...")
    ocr = PaddleOCR(lang='en')
    
    # Load image
    image = cv2.imread(str(sample_image))
    if image is None:
        print("Could not load image")
        return
    
    print(f"Image shape: {image.shape}")
    
    # Run OCR using standard ocr() method
    print("Running OCR...")
    ocr_result = ocr.ocr(image, cls=True)
    
    print(f"OCR result type: {type(ocr_result)}")
    print(f"OCR result length: {len(ocr_result) if isinstance(ocr_result, list) else 'N/A'}")
    
    # Process results using the standard format
    if ocr_result and ocr_result[0]:
        detected_texts = []
        for line in ocr_result[0]:
            if len(line) >= 2:
                text_info = line[1]
                
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                    text = text_info[0] if text_info[0] else ""
                    confidence = text_info[1] if text_info[1] is not None else 0.0
                    
                    if text and len(text.strip()) > 0:
                        detected_texts.append(text)
                        print(f"Detected: '{text}' (confidence: {confidence:.3f})")
        
        # Combine all text
        full_text = ' '.join(detected_texts) if detected_texts else ""
        print(f"Combined text: '{full_text}'")
        
        # Expected text (from ground truth)
        expected = "ELIOT"
        print(f"Expected text: '{expected}'")
        print(f"Match: {full_text.upper().strip() == expected}")
        
    else:
        print("No valid OCR results")

if __name__ == "__main__":
    test_single_image()