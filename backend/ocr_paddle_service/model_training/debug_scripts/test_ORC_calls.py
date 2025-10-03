"""
Simple test to check PaddleOCR method calls
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

def test_ocr_methods():
    # Load a single image
    from pathlib import Path
    current_dir = Path(__file__).parent
    dataset_dir = current_dir.parent / "test_dataset"
    val_images_dir = dataset_dir / "val_images"
    
    # Find the first available image
    sample_image = None
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        images = list(val_images_dir.glob(ext))
        if images:
            sample_image = str(images[0])
            break
    
    if not sample_image:
        print(f"No images found in {val_images_dir}")
        return
    
    image = cv2.imread(sample_image)
    print(f"Testing with image: {sample_image}")
    print(f"Image loaded: {image.shape}")
    
    # Initialize OCR (this will take time the first time)
    print("Initializing OCR...")
    ocr = PaddleOCR(lang='en')
    print("OCR initialized!")
    
    # Test method 1: .ocr() (standard method - RECOMMENDED)
    print("\n=== Testing ocr.ocr() method (RECOMMENDED) ===")
    try:
        result1 = ocr.ocr(image, cls=True)
        print(f"✅ ocr.ocr() worked!")
        print(f"Result type: {type(result1)}")
        if result1 and result1[0]:
            print(f"Number of detected lines: {len(result1[0])}")
            for i, line in enumerate(result1[0][:3]):  # Show first 3 lines
                if len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                        text, confidence = text_info[0], text_info[1]
                        print(f"  Line {i+1}: '{text}' (conf: {confidence:.3f})")
        else:
            print("No text detected")
    except Exception as e:
        print(f"❌ ocr.ocr() failed: {e}")
    
    # Test method 2: .predict() (check if it exists)
    print("\n=== Testing ocr.predict() method (IF AVAILABLE) ===")
    try:
        if hasattr(ocr, 'predict'):
            result2 = ocr.predict(image)
            print(f"✅ ocr.predict() worked!")
            print(f"Result type: {type(result2)}")
            print(f"Result structure: {result2}")
        else:
            print("ℹ️ ocr.predict() method not available in this PaddleOCR version")
    except Exception as e:
        print(f"❌ ocr.predict() failed: {e}")

if __name__ == "__main__":
    test_ocr_methods()