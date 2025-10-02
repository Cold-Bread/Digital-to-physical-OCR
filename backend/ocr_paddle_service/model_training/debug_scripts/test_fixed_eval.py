"""
Test the fixed evaluation script with a single image
"""

import os
import sys
import cv2
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("PaddleOCR not installed. Please install with: pip install paddleocr")
    sys.exit(1)

def test_single_image():
    """Test OCR on a single image to verify the data format"""
    
    # Set up paths
    current_dir = Path(__file__).parent
    dataset_dir = current_dir / "converted_test_dataset"
    image_path = dataset_dir / "val_images" / "val_000000.jpg"
    
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return
    
    print(f"Testing OCR on: {image_path}")
    
    # Initialize OCR
    print("Initializing PaddleOCR...")
    ocr = PaddleOCR(lang='en')
    
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print("Could not load image")
        return
    
    print(f"Image shape: {image.shape}")
    
    # Run OCR
    print("Running OCR...")
    ocr_result = ocr.predict(image)
    
    print(f"OCR result type: {type(ocr_result)}")
    print(f"OCR result length: {len(ocr_result) if isinstance(ocr_result, list) else 'N/A'}")
    
    # Process results using the fixed format
    if ocr_result and isinstance(ocr_result, list) and len(ocr_result) > 0:
        result_dict = ocr_result[0]
        print(f"\nResult dict keys: {list(result_dict.keys())}")
        
        if 'rec_texts' in result_dict:
            rec_texts = result_dict['rec_texts']
            rec_scores = result_dict.get('rec_scores', [])
            
            print(f"\nRecognized texts: {rec_texts}")
            print(f"Confidence scores: {rec_scores}")
            
            # Combine all text
            full_text = ' '.join(rec_texts) if rec_texts else ""
            print(f"Combined text: '{full_text}'")
            
            # Expected text (from ground truth)
            expected = "ELIOT"
            print(f"Expected text: '{expected}'")
            print(f"Match: {full_text.upper().strip() == expected}")
            
        else:
            print("\nNo 'rec_texts' found in result")
    else:
        print("No valid OCR results")

if __name__ == "__main__":
    test_single_image()