"""
Simple test to check PaddleOCR method calls
"""

import cv2
from paddleocr import PaddleOCR

def test_ocr_methods():
    # Load a single image
    image_path = "converted_test_dataset/val_images/val_000000.jpg"
    image = cv2.imread(image_path)
    
    print(f"Image loaded: {image.shape}")
    
    # Initialize OCR (this will take time the first time)
    print("Initializing OCR...")
    ocr = PaddleOCR(lang='en')
    print("OCR initialized!")
    
    # Test method 1: .ocr() (standard method)
    print("\n=== Testing ocr.ocr() method ===")
    try:
        result1 = ocr.ocr(image, cls=True)
        print(f"✅ ocr.ocr() worked!")
        print(f"Result type: {type(result1)}")
        print(f"Result: {result1}")
    except Exception as e:
        print(f"❌ ocr.ocr() failed: {e}")
    
    # Test method 2: .predict() (used in evaluation script)
    print("\n=== Testing ocr.predict() method ===")
    try:
        result2 = ocr.predict(image)
        print(f"✅ ocr.predict() worked!")
        print(f"Result type: {type(result2)}")
        print(f"Result: {result2}")
    except Exception as e:
        print(f"❌ ocr.predict() failed: {e}")

if __name__ == "__main__":
    test_ocr_methods()