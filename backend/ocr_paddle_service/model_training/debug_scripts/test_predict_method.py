"""
Simple test script to verify that the predict() method fix works correctly.
This will help debug the data format issue and ensure proper text extraction.
"""

import os
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

def test_predict_method_fix():
    """
    Test the predict() method and verify proper data extraction
    """
    print("Testing PaddleOCR predict() method fix...")
    
    # Find test images
    dataset_dir = model_training_dir / "test_dataset"
    val_images_dir = dataset_dir / "val_images"
    
    if not val_images_dir.exists():
        print(f"Error: Validation images directory {val_images_dir} does not exist")
        print("Please run this script from the correct location or ensure dataset exists")
        return
    
    # Find the first available image
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    sample_image = None
    for ext in image_extensions:
        images = list(val_images_dir.glob(f'*{ext}'))
        images.extend(list(val_images_dir.glob(f'*{ext.upper()}')))
        if images:
            sample_image = str(images[0])
            break
    
    if not sample_image:
        print(f"No images found in {val_images_dir}")
        return
    
    # Load image
    image = cv2.imread(sample_image)
    if image is None:
        print(f"Error: Could not load image {sample_image}")
        return
    
    print(f"Testing with image: {sample_image}")
    print(f"Image shape: {image.shape}")
    
    # Initialize OCR
    print("Initializing PaddleOCR...")
    ocr = PaddleOCR(
        lang='en',
        text_det_box_thresh=0.3,
        text_det_unclip_ratio=2.0,
        text_det_limit_side_len=2048,
        text_det_limit_type='max',
        use_textline_orientation=True,
        text_recognition_batch_size=6
    )
    print("OCR initialized!")
    
    # Test predict() method with detailed output
    print("\n" + "="*60)
    print("TESTING predict() METHOD")
    print("="*60)
    
    try:
        ocr_result = ocr.predict(image)
        
        print(f"✅ predict() method executed successfully!")
        print(f"Result type: {type(ocr_result)}")
        print(f"Result length: {len(ocr_result) if isinstance(ocr_result, list) else 'not a list'}")
        
        if ocr_result:
            if isinstance(ocr_result, list) and len(ocr_result) > 0:
                print(f"First element type: {type(ocr_result[0])}")
                
                if isinstance(ocr_result[0], dict):
                    result_dict = ocr_result[0]
                    print(f"Dictionary keys: {list(result_dict.keys())}")
                    
                    # Check for expected keys
                    if 'rec_texts' in result_dict:
                        rec_texts = result_dict['rec_texts']
                        print(f"rec_texts type: {type(rec_texts)}")
                        print(f"rec_texts length: {len(rec_texts) if isinstance(rec_texts, list) else 'not a list'}")
                        if isinstance(rec_texts, list) and rec_texts:
                            print(f"First few rec_texts: {rec_texts[:3]}")
                    
                    if 'rec_scores' in result_dict:
                        rec_scores = result_dict['rec_scores']
                        print(f"rec_scores type: {type(rec_scores)}")
                        print(f"rec_scores length: {len(rec_scores) if isinstance(rec_scores, list) else 'not a list'}")
                        if isinstance(rec_scores, list) and rec_scores:
                            print(f"First few rec_scores: {rec_scores[:3]}")
                    
                    # Test the fixed extraction logic
                    print("\n" + "-"*40)
                    print("TESTING FIXED EXTRACTION LOGIC")
                    print("-"*40)
                    
                    detected_texts = []
                    
                    if 'rec_texts' in result_dict and 'rec_scores' in result_dict:
                        rec_texts = result_dict['rec_texts']
                        rec_scores = result_dict['rec_scores']
                        
                        if isinstance(rec_texts, list) and isinstance(rec_scores, list) and len(rec_texts) == len(rec_scores):
                            for i, (text, confidence) in enumerate(zip(rec_texts, rec_scores)):
                                if text and len(str(text).strip()) > 0:
                                    detected_texts.append({
                                        'text': str(text),
                                        'confidence': float(confidence)
                                    })
                                    print(f"Text {i+1}: '{text}' (confidence: {confidence:.3f})")
                            
                            # Combine all texts
                            full_text = ' '.join([item['text'] for item in detected_texts])
                            print(f"\n✅ FINAL EXTRACTED TEXT: '{full_text}'")
                            print(f"✅ Number of text segments: {len(detected_texts)}")
                            
                            if detected_texts:
                                avg_confidence = sum(item['confidence'] for item in detected_texts) / len(detected_texts)
                                print(f"✅ Average confidence: {avg_confidence:.3f}")
                            
                            # Check if this looks like the nonsensical output
                            if full_text and len(full_text.split()) > 5 and all(len(word) <= 2 for word in full_text.split()):
                                print("⚠️  WARNING: This output looks like the nonsensical repeated characters bug!")
                                print("   The fix may not be working correctly.")
                            else:
                                print("✅ Output looks normal - fix appears to be working!")
                        
                        else:
                            print("❌ ERROR: rec_texts and rec_scores length mismatch or invalid format")
                            print(f"   rec_texts: {type(rec_texts)} with length {len(rec_texts) if isinstance(rec_texts, list) else 'N/A'}")
                            print(f"   rec_scores: {type(rec_scores)} with length {len(rec_scores) if isinstance(rec_scores, list) else 'N/A'}")
                    
                    else:
                        print("❌ ERROR: Missing rec_texts or rec_scores keys")
                        print(f"   Available keys: {list(result_dict.keys())}")
                
                else:
                    print("❌ ERROR: First element is not a dictionary")
                    print(f"   First element: {ocr_result[0]}")
            
            else:
                print("❌ ERROR: Result is not a list or is empty")
                print(f"   Result: {ocr_result}")
        
        else:
            print("❌ ERROR: No OCR results returned")
    
    except Exception as e:
        print(f"❌ ERROR: predict() method failed: {e}")
        import traceback
        traceback.print_exc()
    
    # For comparison, also test the old ocr() method
    print("\n" + "="*60)
    print("TESTING ocr() METHOD (FOR COMPARISON)")
    print("="*60)
    
    try:
        ocr_result_old = ocr.ocr(image)
        print(f"✅ ocr() method executed successfully!")
        print(f"Result type: {type(ocr_result_old)}")
        
        if ocr_result_old and ocr_result_old[0]:
            print(f"Number of detected lines: {len(ocr_result_old[0])}")
            
            detected_texts_old = []
            for i, line in enumerate(ocr_result_old[0][:3]):  # Show first 3 lines
                if len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                        text, confidence = text_info[0], text_info[1]
                        detected_texts_old.append(text)
                        print(f"Line {i+1}: '{text}' (conf: {confidence:.3f})")
            
            full_text_old = ' '.join(detected_texts_old)
            print(f"✅ OLD METHOD EXTRACTED TEXT: '{full_text_old}'")
        else:
            print("No text detected with old method")
    
    except Exception as e:
        print(f"❌ ERROR: ocr() method failed: {e}")

if __name__ == "__main__":
    test_predict_method_fix()