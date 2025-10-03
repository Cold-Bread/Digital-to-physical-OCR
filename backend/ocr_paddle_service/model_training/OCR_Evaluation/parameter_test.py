"""
Parameter Test with Image Size Handling

Tests various OCR parameter configurations on a sample dataset to identify optimal settings,
with a focus on handling large images properly to preserve text quality.
"""

import sys
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

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

from evaluate_with_ground_truth import (
    load_ground_truth_labels, 
    calculate_similarity_metrics
)


def preprocess_large_image(image_path, max_dimension=8000):
    """
    Preprocess large images to reasonable sizes while preserving text quality.
    
    Args:
        image_path: Path to the image
        max_dimension: Maximum width or height in pixels
    
    Returns:
        Preprocessed image or None if failed
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        height, width = image.shape[:2]
        original_size = max(height, width)
        
        # If image is too large, resize it intelligently
        if original_size > max_dimension:
            # Calculate scale factor
            scale = max_dimension / original_size
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Use high-quality interpolation for text
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"    Resized from {width}x{height} to {new_width}x{new_height}")
        else:
            print(f"    Image size OK: {width}x{height}")
        
        return image
        
    except Exception as e:
        print(f"    Error preprocessing image: {e}")
        return None


def test_config_with_preprocessing(config_name, ocr_params, images_sample, ground_truth, num_test=10):
    """Test OCR configuration with proper image preprocessing"""
    
    print(f"\nTesting {config_name}...")
    print(f"Key parameters: {dict(list(ocr_params.items())[:5])}...")
    
    # Initialize OCR with specific parameters
    try:
        ocr = PaddleOCR(**ocr_params)
    except Exception as e:
        print(f"  Error initializing OCR: {e}")
        return None
    
    # Test on sample images
    results = []
    total_char_acc = 0
    total_word_acc = 0
    total_conf = 0
    exact_matches = 0
    successful_tests = 0
    
    for i, (image_path, filename) in enumerate(images_sample[:num_test]):
        expected_text = ground_truth[filename]
        
        try:
            # Preprocess the image
            image = preprocess_large_image(image_path, max_dimension=8000)
            if image is None:
                print(f"    Failed to load {filename}")
                continue
            
            # Initialize lists for this image
            detected_texts = []
            confidences = []
            
            # Run OCR using the predict method (preferred) or fallback to ocr()
            try:
                result = ocr.predict(image)
                
                # Handle the predict() return format
                if result and len(result) > 0:
                    ocr_result = result[0]  # First result
                    
                    # Try to extract text and confidence
                    if hasattr(ocr_result, 'rec_texts') and hasattr(ocr_result, 'rec_scores'):
                        texts = ocr_result.rec_texts
                        scores = ocr_result.rec_scores
                        
                        if isinstance(texts, list) and isinstance(scores, list):
                            for text, score in zip(texts, scores):
                                if text and len(str(text).strip()) > 0 and score > 0.1:
                                    detected_texts.append(str(text))
                                    confidences.append(float(score))
                    
                    # Fallback: try dict-like access
                    elif hasattr(ocr_result, '__getitem__'):
                        try:
                            texts = ocr_result['rec_texts']
                            scores = ocr_result['rec_scores']
                            for text, score in zip(texts, scores):
                                if text and len(str(text).strip()) > 0 and score > 0.1:
                                    detected_texts.append(str(text))
                                    confidences.append(float(score))
                        except (KeyError, TypeError):
                            pass
            except Exception:
                print(f"    Both predict() and ocr() failed for {filename}")
                continue
            
            predicted_text = ' '.join(detected_texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            # Calculate metrics
            metrics = calculate_similarity_metrics(predicted_text, expected_text)
            
            total_char_acc += metrics['character_accuracy']
            total_word_acc += metrics['word_accuracy']
            total_conf += avg_confidence
            
            if metrics['exact_match']:
                exact_matches += 1
            
            successful_tests += 1
            
            results.append({
                'filename': filename,
                'expected': expected_text,
                'predicted': predicted_text,
                'char_acc': metrics['character_accuracy'],
                'word_acc': metrics['word_accuracy'],
                'confidence': avg_confidence
            })
            
            if successful_tests <= 3:  # Show first few results
                print(f"    {filename}: '{expected_text}' -> '{predicted_text}' (acc: {100*metrics['character_accuracy']:.1f}%)")
            
        except Exception as e:
            print(f"    Error processing {filename}: {e}")
            continue
    
    # Calculate averages
    if successful_tests > 0:
        avg_char_acc = total_char_acc / successful_tests
        avg_word_acc = total_word_acc / successful_tests
        avg_conf = total_conf / successful_tests
        exact_match_rate = exact_matches / successful_tests
    else:
        avg_char_acc = avg_word_acc = avg_conf = exact_match_rate = 0
    
    print(f"  Results on {successful_tests} images:")
    print(f"  Character accuracy: {100*avg_char_acc:.1f}%")
    print(f"  Word accuracy: {100*avg_word_acc:.1f}%")
    print(f"  Exact matches: {exact_matches}/{successful_tests} ({100*exact_match_rate:.1f}%)")
    print(f"  Average confidence: {100*avg_conf:.1f}%")
    
    return {
        'config_name': config_name,
        'num_tested': successful_tests,
        'avg_character_accuracy': avg_char_acc,
        'avg_word_accuracy': avg_word_acc,
        'avg_confidence': avg_conf,
        'exact_match_rate': exact_match_rate,
        'exact_matches': exact_matches,
        'detailed_results': results
    }


def parameter_test():    
    print("🔬 OCR Parameter Test")
    print("="*60)
    
    # Check dataset
    dataset_dir = current_dir.parent / "test_dataset"
    label_file = dataset_dir / "val_label.txt"
    
    if not dataset_dir.exists() or not label_file.exists():
        print("❌ Dataset not found. Please ensure test_dataset exists.")
        return
    
    # Load ground truth
    print("Loading ground truth labels...")
    ground_truth = load_ground_truth_labels(str(label_file))
    
    # Get sample images
    val_images_dir = dataset_dir / "val_images"
    available_images = []
    for filename in list(ground_truth.keys())[:15]:  # Test on first 15 images
        image_path = val_images_dir / filename
        if image_path.exists():
            available_images.append((str(image_path), filename))
    
    if len(available_images) < 5:
        print("❌ Not enough test images found")
        return
    
    print(f"Testing on {len(available_images)} images...")
    
    # Define configurations with appropriate size limits to handle large images
    configs = [
        {
            'name': 'Baseline with Large Images',
            'params': {
                'lang': 'en',
                'text_det_box_thresh': 0.6,
                'text_det_unclip_ratio': 1.5,
                'text_det_limit_side_len': 8000,  # Much higher limit
                'use_textline_orientation': False,
                'text_recognition_batch_size': 6
            }
        },
        {
            'name': 'Sensitive Detection',
            'params': {
                'lang': 'en',
                'text_det_box_thresh': 0.4,  # More sensitive
                'text_det_unclip_ratio': 1.8,  # Better boundaries
                'text_det_limit_side_len': 10000,  # Very high limit
                'use_textline_orientation': True,  # Handle rotation
                'text_recognition_batch_size': 1  # Single processing
            }
        },
        {
            'name': 'High Quality Processing',
            'params': {
                'lang': 'en',
                'text_det_box_thresh': 0.35,
                'text_det_unclip_ratio': 2.0,
                'text_det_limit_side_len': 12000,  # Maximum detail
                'use_textline_orientation': True,
                'text_recognition_batch_size': 1,
                'text_det_thresh': 0.3
            }
        },
        {
            'name': 'Maximum Detail',
            'params': {
                'lang': 'en',
                'text_det_box_thresh': 0.3,  # Very sensitive
                'text_det_unclip_ratio': 2.2,
                'text_det_limit_side_len': 15000,  # Maximum detail
                'use_textline_orientation': True,
                'text_recognition_batch_size': 1,
                'text_det_thresh': 0.25
            }
        }
    ]
    
    # Test each configuration
    all_results = []
    
    for config in configs:
        try:
            result = test_config_with_preprocessing(
                config['name'], 
                config['params'], 
                available_images, 
                ground_truth,
                num_test=10  # Test on 10 images per config
            )
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"❌ Error testing {config['name']}: {e}")
            continue
    
    if not all_results:
        print("❌ No configurations completed successfully")
        return
    
    # Compare results
    print("\n" + "="*80)
    print("COMPARISON RESULTS - IMAGE HANDLING")
    print("="*80)
    
    print(f"{'Configuration':<25} {'Char Acc':<10} {'Word Acc':<10} {'Exact':<8} {'Confidence':<12}")
    print("-" * 80)
    
    baseline_char_acc = None
    best_config = None
    best_char_acc = 0
    
    for result in all_results:
        char_acc = 100 * result['avg_character_accuracy']
        word_acc = 100 * result['avg_word_accuracy']
        exact_rate = 100 * result['exact_match_rate']
        confidence = 100 * result['avg_confidence']
        
        print(f"{result['config_name']:<25} {char_acc:<10.1f} {word_acc:<10.1f} "
              f"{exact_rate:<8.1f} {confidence:<12.1f}")
        
        # Track baseline and best
        if 'Baseline' in result['config_name']:
            baseline_char_acc = result['avg_character_accuracy']
        
        if result['avg_character_accuracy'] > best_char_acc:
            best_char_acc = result['avg_character_accuracy']
            best_config = result
    
    # Show analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    if best_config:
        print(f"🏆 Best configuration: {best_config['config_name']}")
        print(f"🎯 Best character accuracy: {100*best_config['avg_character_accuracy']:.1f}%")
        print(f"📝 Best word accuracy: {100*best_config['avg_word_accuracy']:.1f}%")
        print(f"✅ Exact matches: {best_config['exact_matches']}/{best_config['num_tested']}")
        
        if baseline_char_acc and baseline_char_acc > 0:
            improvement = (best_config['avg_character_accuracy'] - baseline_char_acc) * 100
            print(f"📈 Improvement over baseline: +{improvement:.1f}%")
            
            if improvement > 10:
                print("✅ Significant improvement detected!")
                print("💡 Strong recommendation: Use these optimized parameters")
            elif improvement > 5:
                print("🟡 Good improvement detected")
                print("💡 Recommendation: Consider using optimized parameters")
            elif improvement > 2:
                print("🟠 Moderate improvement detected")
                print("💡 Recommendation: Test with larger sample")
            else:
                print("🔴 Limited improvement")
                print("💡 Recommendation: Focus on image preprocessing or custom training")
    
    # Show the best parameters
    if best_config:
        print("\n" + "="*60)
        print("RECOMMENDED PARAMETERS")
        print("="*60)
        
        # Find the config params for the best result
        best_config_params = None
        for config in configs:
            if config['name'] == best_config['config_name']:
                best_config_params = config['params']
                break
        
        if best_config_params:
            print("Apply these parameters to your main application:")
            print()
            for param, value in best_config_params.items():
                print(f"  {param}: {value}")
            
            print(f"\nExpected performance:")
            print(f"  Character accuracy: {100*best_config['avg_character_accuracy']:.1f}%")
            print(f"  Word accuracy: {100*best_config['avg_word_accuracy']:.1f}%")
            print(f"  Confidence: {100*best_config['avg_confidence']:.1f}%")
    
    # Save results
    output_file = current_dir / "parameter_test_results.json"
    results_data = {
        'test_date': datetime.now().isoformat(),
        'tested_images': len(available_images),
        'configurations': all_results,
        'best_config': best_config['config_name'] if best_config else None,
        'image_preprocessing': 'Applied intelligent resizing with max_dimension=8000'
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        print(f"\n📊 Results saved to: {output_file}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    # Show sample results from best config
    if best_config and best_config['detailed_results']:
        print(f"\n" + "="*60)
        print(f"SAMPLE RESULTS - {best_config['config_name']}")
        print("="*60)
        
        sorted_results = sorted(best_config['detailed_results'], 
                              key=lambda x: x['char_acc'], reverse=True)
        
        print("🎯 Best performing:")
        for i, result in enumerate(sorted_results[:3], 1):
            print(f"{i}. {result['filename']} (accuracy: {100*result['char_acc']:.1f}%)")
            print(f"   Expected: '{result['expected']}'")
            print(f"   Predicted: '{result['predicted']}'")
        
        print("\n⚠️  Most challenging:")
        for i, result in enumerate(sorted_results[-2:], 1):
            print(f"{i}. {result['filename']} (accuracy: {100*result['char_acc']:.1f}%)")
            print(f"   Expected: '{result['expected']}'")
            print(f"   Predicted: '{result['predicted']}'")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    if best_config and best_config['avg_character_accuracy'] > 0.6:
        print("1. ✅ Apply the optimized parameters to your main application")
        print("2. 🔧 Update text_det_limit_side_len to handle large images")
        print("3. 🔄 Restart your OCR service and test")
        print("4. 📊 Run full evaluation to confirm improvements")
    elif best_config and best_config['avg_character_accuracy'] > 0.4:
        print("1. 🟡 Consider applying optimized parameters for moderate improvement")
        print("2. 🔍 Investigate image quality and preprocessing")
        print("3. � Consider custom model training for your specific images")
    else:
        print("1. � Parameter optimization shows limited benefit")
        print("2. 🎯 Focus on custom model training for your dataset")
        print("3. 🔍 Analyze image quality issues (resolution, contrast, etc.)")
        print("4. � Consider data augmentation and specialized preprocessing")
    
    return all_results


def main():
    parameter_test()

if __name__ == "__main__":
    main()