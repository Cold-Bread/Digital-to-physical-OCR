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

def evaluate_current_model(test_images_dir: str, output_file: str = "baseline_evaluation.json", max_images: Optional[int] = None):
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
            
            # Run OCR using predict() method for proper format
            ocr_result = ocr.predict(image)
            
            # Process results - predict() returns list containing OCRResult objects
            detected_text = []
            
            # Check if ocr_result is a list with at least one element
            if ocr_result and isinstance(ocr_result, list) and len(ocr_result) > 0:
                # Extract the first OCRResult object from the result
                result_obj = ocr_result[0]
                
                # OCRResult objects behave like dictionaries - use dictionary-style access
                if 'rec_texts' in result_obj and 'rec_scores' in result_obj:
                    rec_texts = result_obj['rec_texts']
                    rec_scores = result_obj['rec_scores']
                    
                    # Ensure both lists have the same length
                    if isinstance(rec_texts, list) and isinstance(rec_scores, list) and len(rec_texts) == len(rec_scores):
                        for text, confidence in zip(rec_texts, rec_scores):
                            # Only add if we have actual text
                            if text and len(str(text).strip()) > 0:
                                detected_text.append({
                                    'text': str(text),
                                    'confidence': float(confidence),
                                    'bbox': None  # predict() doesn't provide bbox info
                                })
                                
                                all_confidences.append(float(confidence))
                                results['summary']['total_text_segments'] += 1
            
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
    
    # Ensure evaluation_results directory exists and save results
    current_dir = Path(__file__).parent
    model_training_dir = current_dir.parent
    eval_results_dir = model_training_dir / "evaluation_results"
    eval_results_dir.mkdir(exist_ok=True)
    
    # If output_file is just a filename, put it in evaluation_results
    if not os.path.isabs(output_file) and os.path.dirname(output_file) == "":
        output_file = str(eval_results_dir / output_file)
    
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
    parser.add_argument("--output", default="baseline_evaluation.json", help="Output file for results")
    parser.add_argument("--max_images", type=int, default=None, help="Maximum number of images to process (default: all)")
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute paths
    current_dir = Path(__file__).parent
    model_training_dir = current_dir.parent
    
    test_dir = args.test_dir
    if not os.path.isabs(test_dir):
        test_dir = str(model_training_dir / test_dir)
    
    if not os.path.exists(test_dir):
        print(f"Error: Test directory {test_dir} does not exist")
        return
    
    # Handle output file path
    output_file = args.output
    if not os.path.isabs(output_file):
        output_file = str(model_training_dir / output_file)
    
    print("Starting evaluation of current PaddleOCR model...")
    print(f"Test directory: {test_dir}")
    print(f"Output file: {output_file}")
    if args.max_images:
        print(f"Max images to process: {args.max_images}")
    print()
    
    evaluate_current_model(test_dir, output_file, args.max_images)

    print("\nEvaluation complete!")
    print("Next steps:")
    print("1. Review the results in the JSON file")
    print("2. If performance is poor, proceed with custom training")
    print("3. Use create_evaluation_dataset.py to prepare your training data")
    print("4. Use train_custom_model.py to train your custom model")

if __name__ == "__main__":
    main()