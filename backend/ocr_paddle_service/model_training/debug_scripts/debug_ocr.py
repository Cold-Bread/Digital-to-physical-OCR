"""
Debug script to understand what's happening with OCR processing
"""

import sys
import cv2
import numpy as np
import traceback
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

def debug_single_image(image_path, expected_text):
    print(f"🔍 Debugging image: {image_path}")
    print(f"📝 Expected text: '{expected_text}'")
    print("=" * 60)
    
    # Load image
    print("1. Loading image...")
    image = cv2.imread(image_path)
    if image is None:
        print("❌ ERROR: Could not load image!")
        return
    
    print(f"✅ Image loaded successfully: {image.shape}")
    print(f"   - Height: {image.shape[0]}")
    print(f"   - Width: {image.shape[1]}")
    print(f"   - Channels: {image.shape[2]}")
    print(f"   - Data type: {image.dtype}")
    print(f"   - Value range: {image.min()} - {image.max()}")
    
    # Initialize OCR
    print("\n2. Initializing PaddleOCR...")
    try:
        ocr = PaddleOCR(
            lang='en',
            use_textline_orientation=True
        )
        print("✅ PaddleOCR initialized successfully")
    except Exception as e:
        print(f"❌ ERROR initializing PaddleOCR: {e}")
        traceback.print_exc()
        return
    
    # Run OCR
    print("\n3. Running OCR...")
    try:
        result = ocr.ocr(image, cls=True)
        print(f"✅ OCR completed")
        print(f"   - Result type: {type(result)}")
        print(f"   - Result length: {len(result) if result else 0}")
        
        if result:
            print(f"   - First level type: {type(result[0])}")
            print(f"   - First level length: {len(result[0]) if result[0] else 0}")
            
            # Debug the raw result structure
            print("\n4. Raw OCR Result Structure:")
            print("-" * 40)
            
            if result and result[0]:
                for i, line in enumerate(result[0]):
                    print(f"Line {i}: {type(line)} - {line}")
                    if len(line) >= 2:
                        bbox = line[0]
                        text_info = line[1]
                        print(f"  Bbox: {type(bbox)} - {bbox}")
                        print(f"  Text info: {type(text_info)} - {text_info}")
                        
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            text = text_info[0]
                            confidence = text_info[1]
                            print(f"    Text: '{text}' (type: {type(text)})")
                            print(f"    Confidence: {confidence} (type: {type(confidence)})")
                        print()
            else:
                print("No text detected!")
        
        # Process results like the evaluation script does
        print("\n5. Processing results (like evaluation script)...")
        detected_texts = []
        
        if result and result[0]:
            for line in result[0]:
                try:
                    if len(line) >= 2:
                        bbox = line[0]
                        text_info = line[1]
                        
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            text = text_info[0] if text_info[0] else ""
                            confidence = text_info[1] if text_info[1] is not None else 0.0
                        else:
                            text = str(text_info) if text_info else ""
                            confidence = 0.0
                        
                        if text and len(text.strip()) > 0:
                            detected_texts.append({
                                'text': text,
                                'confidence': float(confidence),
                                'bbox': bbox
                            })
                            print(f"   ✅ Added: '{text}' (conf: {confidence:.3f})")
                        else:
                            print(f"   ⚠️ Skipped empty text: '{text}'")
                            
                except Exception as e:
                    print(f"   ❌ Error processing line: {e}")
                    print(f"      Line content: {line}")
        
        # Combine text
        full_text = ' '.join([item['text'] for item in detected_texts])
        avg_confidence = np.mean([item['confidence'] for item in detected_texts]) if detected_texts else 0.0
        
        print(f"\n6. Final Results:")
        print(f"   Expected: '{expected_text}'")
        print(f"   Predicted: '{full_text}'")
        print(f"   Segments found: {len(detected_texts)}")
        print(f"   Average confidence: {avg_confidence:.3f}")
        
        # Character-level comparison
        if expected_text and full_text:
            matching_chars = sum(1 for a, b in zip(expected_text.upper(), full_text.upper()) if a == b)
            char_accuracy = matching_chars / max(len(expected_text), len(full_text))
            print(f"   Character accuracy: {char_accuracy:.3f}")
        
    except Exception as e:
        print(f"❌ ERROR during OCR: {e}")
        traceback.print_exc()

def main():
    # Test with just one sample image
    current_dir = Path(__file__).parent
    # Look for sample image in the dataset
    dataset_dir = current_dir.parent / "test_dataset"
    val_images_dir = dataset_dir / "val_images"
    
    # Find the first available image
    sample_image = None
    expected_text = "ELIOT"  # Default expected text
    
    if val_images_dir.exists():
        # Look for any jpg/png file
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            images = list(val_images_dir.glob(ext))
            if images:
                sample_image = str(images[0])
                break
    
    if not sample_image:
        print("❌ No sample images found in dataset")
        print(f"Looking in: {val_images_dir}")
        return
    
    # Try to get expected text from label file
    label_file = dataset_dir / "val_label.txt"
    if label_file.exists():
        try:
            with open(label_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if '\t' in first_line:
                    _, expected_text = first_line.split('\t', 1)
        except Exception as e:
            print(f"Warning: Could not read label file: {e}")
    
    print(f"Using sample image: {sample_image}")
    print(f"Expected text: {expected_text}")
    
    debug_single_image(sample_image, expected_text)

if __name__ == "__main__":
    main()