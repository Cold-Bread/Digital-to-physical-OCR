"""
Quick evaluation script to test current PaddleOCR model on your dataset
Run this first to see baseline performance before training
"""

import os
import sys
import cv2
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional

# Add parent directory to path to import paddleocr
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("PaddleOCR not installed. Please install with: pip install paddleocr")
    sys.exit(1)

from typing import Optional

def evaluate_current_model(test_images_dir: str, output_file: str = "evaluation_results.json", max_images: Optional[int] = None):
    """
    Quick evaluation of current PaddleOCR model on test images
    
    Args:
        test_images_dir: Directory containing test images
        output_file: Output file for results
        max_images: Maximum number of images to process (None for all images)
    """
    print("Initializing PaddleOCR model...")
    
    # Initialize with the same settings as your current app
    ocr = PaddleOCR(
        lang='en',
        text_det_box_thresh=0.3,
        text_det_unclip_ratio=2.0,
        text_det_limit_side_len=2048,
        text_det_limit_type='max',
        use_textline_orientation=True,
        text_recognition_batch_size=6
    )
    
    test_dir = Path(test_images_dir)
    if not test_dir.exists():
        print(f"Error: Test directory {test_dir} does not exist")
        return
    
    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(test_dir.glob(f'*{ext}'))
        image_files.extend(test_dir.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No image files found in {test_dir}")
        return
    
    # Limit the number of images if max_images is specified
    if max_images is not None and max_images > 0:
        image_files = image_files[:max_images]
        print(f"Limited to processing {len(image_files)} images (max_images={max_images})")
    
    print(f"Found {len(image_files)} images to process")
    
    results = {
        'model_info': {
            'model_type': 'PaddleOCR default English model',
            'evaluation_date': datetime.now().isoformat(),
            'test_directory': str(test_dir),
            'total_images': len(image_files)
        },
        'results': [],
        'summary': {
            'successful_predictions': 0,
            'failed_predictions': 0,
            'total_text_segments': 0,
            'avg_confidence': 0.0
        }
    }
    
    all_confidences = []
    
    for i, img_path in enumerate(image_files, 1):
        print(f"Processing {i}/{len(image_files)}: {img_path.name}")
        
        try:
            # Load image
            image = cv2.imread(str(img_path))
            if image is None:
                print(f"  Warning: Could not load {img_path}")
                results['summary']['failed_predictions'] += 1
                continue
            
            # Run OCR
            ocr_result = ocr.predict(image)
            
            # Debug: Print the structure of the first result to understand the format
            if i == 1:  # Only print for the first image to avoid spam
                print(f"  Debug - OCR result type: {type(ocr_result)}")
                print(f"  Debug - OCR result structure: {ocr_result}")
                if hasattr(ocr_result, 'prediction'):
                    print(f"  Debug - Has prediction attribute: {type(ocr_result.prediction)}")
                
            # Process results
            detected_text = []
            
            # Handle the new predict() method result format
            if ocr_result and hasattr(ocr_result, 'prediction') and ocr_result.prediction:
                # New format: result.prediction contains the OCR data
                ocr_data = ocr_result.prediction
            elif ocr_result and isinstance(ocr_result, list) and len(ocr_result) > 0:
                # Fallback: treat as list format
                ocr_data = ocr_result[0] if ocr_result[0] else []
            else:
                ocr_data = []
            
            if ocr_data:
                for line in ocr_data:
                    try:
                        if len(line) >= 2:
                            bbox = line[0]  # Bounding box coordinates
                            text_info = line[1]  # (text, confidence)
                            
                            # Handle different OCR result formats
                            if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                text = text_info[0] if text_info[0] else ""
                                confidence = text_info[1] if text_info[1] is not None else 0.0
                            else:
                                # Fallback if format is unexpected
                                text = str(text_info) if text_info else ""
                                confidence = 0.0
                            
                            # Only add if we have actual text
                            if text and len(text.strip()) > 0:
                                detected_text.append({
                                    'text': text,
                                    'confidence': float(confidence),
                                    'bbox': bbox
                                })
                                
                                all_confidences.append(confidence)
                                results['summary']['total_text_segments'] += 1
                    except (IndexError, TypeError, ValueError) as e:
                        print(f"    Warning: Error processing OCR line: {e}")
                        print(f"    Line structure: {line}")
                        continue
            
            # Store result
            image_result = {
                'image_path': str(img_path),
                'image_name': img_path.name,
                'detected_text': detected_text,
                'full_text': ' '.join([item['text'] for item in detected_text]),
                'num_text_segments': len(detected_text),
                'avg_confidence': np.mean([item['confidence'] for item in detected_text]) if detected_text else 0.0
            }
            
            results['results'].append(image_result)
            results['summary']['successful_predictions'] += 1
            
            print(f"  Detected {len(detected_text)} text segments")
            if detected_text:
                print(f"  Sample text: {detected_text[0]['text'][:50]}...")
                print(f"  Avg confidence: {image_result['avg_confidence']:.3f}")
            else:
                print(f"  No text detected in image")
            
        except Exception as e:
            print(f"  Error processing {img_path}: {e}")
            # Store failed result for tracking
            image_result = {
                'image_path': str(img_path),
                'image_name': img_path.name,
                'detected_text': [],
                'full_text': '',
                'num_text_segments': 0,
                'avg_confidence': 0.0,
                'error': str(e)
            }
            results['results'].append(image_result)
            results['summary']['failed_predictions'] += 1
    
    # Calculate summary statistics
    if all_confidences:
        results['summary']['avg_confidence'] = float(np.mean(all_confidences))
        results['summary']['min_confidence'] = float(np.min(all_confidences))
        results['summary']['max_confidence'] = float(np.max(all_confidences))
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Total images processed: {results['model_info']['total_images']}")
    print(f"Successful predictions: {results['summary']['successful_predictions']}")
    print(f"Failed predictions: {results['summary']['failed_predictions']}")
    print(f"Total text segments detected: {results['summary']['total_text_segments']}")
    
    if all_confidences:
        print(f"Average confidence: {results['summary']['avg_confidence']:.3f}")
        print(f"Confidence range: {results['summary']['min_confidence']:.3f} - {results['summary']['max_confidence']:.3f}")
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Show some sample results
    print("\nSample Results:")
    print("-" * 40)
    for i, result in enumerate(results['results'][:3]):  # Show first 3 results
        print(f"{i+1}. {result['image_name']}")
        print(f"   Text segments: {result['num_text_segments']}")
        if result['detected_text']:
            print(f"   Sample text: {result['detected_text'][0]['text']}")
            print(f"   Confidence: {result['detected_text'][0]['confidence']:.3f}")
        print()
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Evaluate current PaddleOCR model")
    parser.add_argument("--test_dir", required=True, help="Directory containing test images")
    parser.add_argument("--output", default="evaluation_results.json", help="Output file for results")
    parser.add_argument("--max_images", type=int, default=None, help="Maximum number of images to process (default: all)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.test_dir):
        print(f"Error: Test directory {args.test_dir} does not exist")
        return
    
    print("Starting evaluation of current PaddleOCR model...")
    print(f"Test directory: {args.test_dir}")
    print(f"Output file: {args.output}")
    if args.max_images:
        print(f"Max images to process: {args.max_images}")
    print()
    
    results = evaluate_current_model(args.test_dir, args.output, args.max_images)
    
    print("\nEvaluation complete!")
    print("Next steps:")
    print("1. Review the results in the JSON file")
    print("2. If performance is poor, proceed with custom training")
    print("3. Use dataset_converter.py to prepare your training data")
    print("4. Follow the training_instructions.md guide")

if __name__ == "__main__":
    main()