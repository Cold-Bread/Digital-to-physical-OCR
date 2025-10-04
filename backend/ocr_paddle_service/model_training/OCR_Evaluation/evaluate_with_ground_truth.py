"""
Comprehensive evaluation script that compares OCR predictions against ground truth labels
from the converted dataset. This provides proper accuracy metrics for the baseline PaddleOCR model.
"""

import os
import sys
import cv2
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional, Dict
import difflib
import re

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


def load_ground_truth_labels(label_file: str) -> Dict[str, str]:
    """
    Load ground truth labels from the converted dataset format.
    
    Args:
        label_file: Path to the label file (e.g., val_label.txt)
        
    Returns:
        Dictionary mapping image paths to expected text
    """
    labels = {}
    
    try:
        with open(label_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Split by tab (PaddleOCR format: image_path\ttext)
                parts = line.split('\t')
                if len(parts) != 2:
                    print(f"Warning: Invalid format in line {line_num}: {line}")
                    continue
                
                image_path, expected_text = parts
                
                # Extract just the filename for easier matching
                image_filename = os.path.basename(image_path)
                labels[image_filename] = expected_text.strip()
                
    except FileNotFoundError:
        print(f"Error: Label file {label_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading label file: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(labels)} ground truth labels from {label_file}")
    return labels


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing extra spaces and converting to uppercase.
    """
    if not text:
        return ""
    
    # Convert to uppercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.strip().upper())
    return normalized


def calculate_similarity_metrics(predicted: str, expected: str) -> Dict:
    """
    Calculate various similarity metrics between predicted and expected text.
    
    Returns:
        Dictionary with similarity scores
    """
    pred_norm = normalize_text(predicted)
    exp_norm = normalize_text(expected)
    
    # Exact match
    exact_match = 1.0 if pred_norm == exp_norm else 0.0
    
    # Character-level accuracy
    if not exp_norm:
        char_accuracy = 1.0 if not pred_norm else 0.0
    else:
        # Calculate edit distance (Levenshtein)
        edit_distance = difflib.SequenceMatcher(None, pred_norm, exp_norm).ratio()
        char_accuracy = edit_distance
    
    # Word-level accuracy
    pred_words = pred_norm.split()
    exp_words = exp_norm.split()
    
    if not exp_words:
        word_accuracy = 1.0 if not pred_words else 0.0
    else:
        # Count matching words
        matching_words = sum(1 for word in pred_words if word in exp_words)
        word_accuracy = matching_words / len(exp_words)
    
    return {
        'exact_match': exact_match,
        'character_accuracy': char_accuracy,
        'word_accuracy': word_accuracy,
        'predicted_normalized': pred_norm,
        'expected_normalized': exp_norm
    }


def evaluate_with_ground_truth(
    dataset_dir: str, 
    label_file: str, 
    output_file: str = "default_ground_truth_evaluation.json", 
    max_images: Optional[int] = None,
    ocr_config: Optional[str] = "baseline",
    use_custom_model: bool = False,
    custom_model_path: Optional[str] = None
):
    """
    Evaluate OCR model against ground truth labels.
    
    Args:
        dataset_dir: Directory containing the converted test dataset
        label_file: Path to the label file (e.g., val_label.txt)
        output_file: Output file for results
        max_images: Maximum number of images to process (None for all)
        ocr_config: OCR configuration to use ('baseline', 'sensitive', 'high_quality', 'maximum_detail')
        use_custom_model: Whether to use custom trained model instead of default PaddleOCR
        custom_model_path: Path to custom model directory (if use_custom_model=True)
    """
    print("Loading ground truth labels...")
    ground_truth = load_ground_truth_labels(label_file)
    
    print("Initializing OCR model...")
    
    # Initialize variables
    model_type = "Unknown"
    selected_config = {'name': 'Unknown', 'params': {}}
    ocr = None
    
    # Determine which model to use
    if use_custom_model:
        if not custom_model_path:
            # Default to the exported model path
            current_dir = Path(__file__).parent
            model_training_dir = current_dir.parent
            custom_model_path = str(model_training_dir / "training_output" / "exported_model")
        
        print(f"Using CUSTOM trained model from: {custom_model_path}")
        
        # Check if custom model exists
        if not os.path.exists(custom_model_path):
            print(f"Error: Custom model path {custom_model_path} does not exist")
            print("Please ensure the model has been exported successfully")
            return None
        
        # Initialize PaddleOCR with custom model
        try:
            # Use the correct parameter names as shown in the deprecation warnings
            ocr = PaddleOCR(
                use_textline_orientation=True,  # Updated from use_angle_cls
                text_recognition_model_dir=custom_model_path,  # Updated from rec_model_dir
                lang='en',
                text_detection_model_dir=None,  # Updated from det_model_dir (use default)
                textline_orientation_model_dir=None,  # Updated from cls_model_dir (use default)
            )
            model_type = f"Custom trained model from {custom_model_path}"
            print(f"✅ Successfully loaded custom model")
        except Exception as e:
            print(f"❌ Error initializing custom model: {e}")
            print("This might be due to:")
            print("1. Model format incompatibility")
            print("2. Missing model files in the directory")
            print("3. Model architecture mismatch with PaddleOCR expectations")
            print(f"Files found in {custom_model_path}:")
            if os.path.exists(custom_model_path):
                files = os.listdir(custom_model_path)
                for file in files:
                    print(f"  - {file}")
            else:
                print(f"  Directory {custom_model_path} does not exist!")
            exit(1)
    
    if not use_custom_model:
        print("Using DEFAULT PaddleOCR model")
        
        # Define OCR configurations based on your parameter testing results
        ocr_configs = {
            'baseline': {
                'name': 'Baseline with Large Images (Best Performance)',
                'params': {
                    'lang': 'en',
                    'text_det_box_thresh': 0.6,
                    'text_det_unclip_ratio': 1.5,
                    'text_det_limit_side_len': 8000,
                    'text_det_limit_type': 'max',
                    'use_textline_orientation': False,
                    'text_recognition_batch_size': 6
                }
            },
            'sensitive': {
                'name': 'Sensitive Detection',
                'params': {
                    'lang': 'en',
                    'text_det_box_thresh': 0.4,
                    'text_det_unclip_ratio': 1.8,
                    'text_det_limit_side_len': 10000,
                    'text_det_limit_type': 'max',
                    'use_textline_orientation': True,
                    'text_recognition_batch_size': 1
                }
            },
            'high_quality': {
                'name': 'High Quality Processing',
                'params': {
                    'lang': 'en',
                    'text_det_box_thresh': 0.35,
                    'text_det_unclip_ratio': 2.0,
                    'text_det_limit_side_len': 12000,
                    'text_det_limit_type': 'max',
                    'use_textline_orientation': True,
                    'text_recognition_batch_size': 1,
                    'text_det_thresh': 0.3
                }
            },
            'maximum_detail': {
                'name': 'Maximum Detail',
                'params': {
                    'lang': 'en',
                    'text_det_box_thresh': 0.3,
                    'text_det_unclip_ratio': 2.2,
                    'text_det_limit_side_len': 15000,
                    'text_det_limit_type': 'max',
                    'use_textline_orientation': True,
                    'text_recognition_batch_size': 1,
                    'text_det_thresh': 0.25
                }
            }
        }
        
        # Get the selected configuration
        if ocr_config not in ocr_configs:
            print(f"Warning: Unknown OCR config '{ocr_config}'. Using 'baseline' instead.")
            ocr_config = 'baseline'
        
        selected_config = ocr_configs[ocr_config]
        print(f"Using OCR configuration: {selected_config['name']}")
        print(f"Parameters: {selected_config['params']}")
        
        # Initialize with the selected configuration
        ocr = PaddleOCR(**selected_config['params'])
        model_type = f"PaddleOCR default English model - {selected_config['name']}"
    
    # Ensure OCR is properly initialized
    if ocr is None:
        print("❌ Failed to initialize OCR model")
        return None
    
    # Find validation images directory
    val_images_dir = Path(dataset_dir) / "val_images"
    if not val_images_dir.exists():
        print(f"Error: Validation images directory {val_images_dir} does not exist")
        return
    
    # Get list of images that have ground truth labels
    available_images = []
    for image_filename in ground_truth.keys():
        image_path = val_images_dir / image_filename
        if image_path.exists():
            available_images.append((str(image_path), image_filename))
        else:
            print(f"Warning: Image {image_filename} not found in {val_images_dir}")
    
    if not available_images:
        print("No images found with corresponding ground truth labels")
        return
    
    # Limit the number of images if specified
    if max_images is not None and max_images > 0:
        available_images = available_images[:max_images]
        print(f"Limited to processing {len(available_images)} images (max_images={max_images})")
    
    print(f"Found {len(available_images)} images with ground truth labels to process")
    
    results = {
        'model_info': {
            'model_type': model_type,
            'configuration_name': selected_config['name'] if not use_custom_model else 'Custom Model',
            'configuration_params': selected_config['params'] if not use_custom_model else {'custom_model_path': custom_model_path},
            'evaluation_date': datetime.now().isoformat(),
            'dataset_directory': str(dataset_dir),
            'label_file': str(label_file),
            'total_images': len(available_images)
        },
        'results': [],
        'summary': {
            'total_processed': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'exact_matches': 0,
            'avg_character_accuracy': 0.0,
            'avg_word_accuracy': 0.0,
            'avg_confidence': 0.0,
            'accuracy_distribution': {
                'perfect_match': 0,      # 100% accuracy
                'high_accuracy': 0,      # 80-99% accuracy
                'medium_accuracy': 0,    # 50-79% accuracy
                'low_accuracy': 0,       # 20-49% accuracy
                'very_low_accuracy': 0   # 0-19% accuracy
            }
        }
    }
    
    all_confidences = []
    all_char_accuracies = []
    all_word_accuracies = []
    
    for i, (image_path, image_filename) in enumerate(available_images, 1):
        print(f"Processing {i}/{len(available_images)}: {image_filename}")
        
        expected_text = ground_truth[image_filename]
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"  Warning: Could not load {image_path}")
                results['summary']['failed_predictions'] += 1
                continue
            
            # Run OCR using predict() method for proper dictionary format
            ocr_result = ocr.predict(image)
            
            # Process OCR results - predict() returns list containing OCRResult objects
            detected_texts = []
            
            # Check if ocr_result is a list with at least one element
            if ocr_result and isinstance(ocr_result, list) and len(ocr_result) > 0:
                # Extract the first OCRResult object from the result
                result_obj = ocr_result[0]
                
                # Debug: Print available attributes to understand the structure
                print(f"    OCRResult type: {type(result_obj)}")
                if hasattr(result_obj, '__dict__'):
                    available_attrs = [attr for attr in dir(result_obj) if not attr.startswith('_')]
                    print(f"    Available attributes: {available_attrs[:10]}...")  # Show first 10
                
                # Try multiple ways to access the text data
                rec_texts = None
                rec_scores = None
                
                # Method 1: Direct attribute access
                if hasattr(result_obj, 'rec_texts') and hasattr(result_obj, 'rec_scores'):
                    print("    Using direct attribute access")
                    rec_texts = result_obj.rec_texts
                    rec_scores = result_obj.rec_scores
                
                # Method 2: Dictionary-style access
                elif hasattr(result_obj, '__getitem__'):
                    try:
                        print("    Trying dictionary-style access")
                        rec_texts = result_obj['rec_texts']
                        rec_scores = result_obj['rec_scores']
                    except (KeyError, TypeError):
                        pass
                
                # Method 3: Check if it has a data or result attribute
                elif hasattr(result_obj, 'data'):
                    print("    Trying data attribute")
                    data = result_obj.data
                    if isinstance(data, dict):
                        rec_texts = data.get('rec_texts')
                        rec_scores = data.get('rec_scores')
                
                # Method 4: Check for text/texts attribute
                if rec_texts is None:
                    for attr_name in ['texts', 'text', 'recognized_texts', 'predictions']:
                        if hasattr(result_obj, attr_name):
                            print(f"    Found {attr_name} attribute")
                            texts_attr = getattr(result_obj, attr_name)
                            if isinstance(texts_attr, list):
                                rec_texts = texts_attr
                                # Try to find corresponding scores
                                score_attrs = ['scores', 'confidences', 'confidence']
                                for score_attr in score_attrs:
                                    if hasattr(result_obj, score_attr):
                                        rec_scores = getattr(result_obj, score_attr)
                                        break
                                if rec_scores is None:
                                    # Create dummy scores if not found
                                    rec_scores = [1.0] * len(rec_texts)
                                break
                
                # If we found text data, process it
                if rec_texts is not None and rec_scores is not None:
                    print(f"    Found {len(rec_texts)} texts and {len(rec_scores)} scores")
                    
                    # Ensure both lists have the same length
                    if isinstance(rec_texts, list) and isinstance(rec_scores, list) and len(rec_texts) == len(rec_scores):
                        for text, confidence in zip(rec_texts, rec_scores):
                            # Only add if we have actual text
                            if text and len(str(text).strip()) > 0:
                                detected_texts.append({
                                    'text': str(text),
                                    'confidence': float(confidence),
                                    'bbox': None  # predict() doesn't provide bbox info
                                })
                                all_confidences.append(float(confidence))
                        print(f"    Successfully extracted {len(detected_texts)} text segments")
                    else:
                        print(f"    Warning: rec_texts and rec_scores length mismatch")
                        print(f"    rec_texts: {type(rec_texts)} with {len(rec_texts) if isinstance(rec_texts, list) else 'N/A'} items")
                        print(f"    rec_scores: {type(rec_scores)} with {len(rec_scores) if isinstance(rec_scores, list) else 'N/A'} items")
                else:
                    print(f"    Warning: Could not find text data in OCRResult object")
                    print(f"    Available methods: {[m for m in dir(result_obj) if not m.startswith('_') and callable(getattr(result_obj, m))][:5]}...")
            
            # Combine all detected text
            full_predicted_text = ' '.join([item['text'] for item in detected_texts])
            
            # Calculate similarity metrics
            similarity_metrics = calculate_similarity_metrics(full_predicted_text, expected_text)
            
            # Store result
            image_result = {
                'image_path': image_path,
                'image_name': image_filename,
                'expected_text': expected_text,
                'predicted_text': full_predicted_text,
                'detected_segments': detected_texts,
                'num_segments': len(detected_texts),
                'avg_confidence': np.mean([item['confidence'] for item in detected_texts]) if detected_texts else 0.0,
                'similarity_metrics': similarity_metrics
            }
            
            results['results'].append(image_result)
            results['summary']['successful_predictions'] += 1
            
            # Update accuracy tracking
            char_acc = similarity_metrics['character_accuracy']
            word_acc = similarity_metrics['word_accuracy']
            
            all_char_accuracies.append(char_acc)
            all_word_accuracies.append(word_acc)
            
            if similarity_metrics['exact_match']:
                results['summary']['exact_matches'] += 1
            
            # Categorize accuracy
            if char_acc >= 1.0:
                results['summary']['accuracy_distribution']['perfect_match'] += 1
            elif char_acc >= 0.8:
                results['summary']['accuracy_distribution']['high_accuracy'] += 1
            elif char_acc >= 0.5:
                results['summary']['accuracy_distribution']['medium_accuracy'] += 1
            elif char_acc >= 0.2:
                results['summary']['accuracy_distribution']['low_accuracy'] += 1
            else:
                results['summary']['accuracy_distribution']['very_low_accuracy'] += 1
            
            print(f"  Expected: '{expected_text}'")
            print(f"  Predicted: '{full_predicted_text}'")
            print(f"  Character accuracy: {char_acc:.3f}")
            print(f"  Word accuracy: {word_acc:.3f}")
            print(f"  Exact match: {similarity_metrics['exact_match']}")
            print(f"  Avg confidence: {image_result['avg_confidence']:.3f}")
            
        except Exception as e:
            print(f"  Error processing {image_path}: {e}")
            results['summary']['failed_predictions'] += 1
            continue
    
    results['summary']['total_processed'] = len(available_images)
    
    # Calculate summary statistics
    if all_confidences:
        results['summary']['avg_confidence'] = float(np.mean(all_confidences))
    
    if all_char_accuracies:
        results['summary']['avg_character_accuracy'] = float(np.mean(all_char_accuracies))
    
    if all_word_accuracies:
        results['summary']['avg_word_accuracy'] = float(np.mean(all_word_accuracies))
    
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
    
    # Print comprehensive summary
    print("\n" + "="*80)
    print("GROUND TRUTH EVALUATION SUMMARY")
    print("="*80)
    
    summary = results['summary']
    print(f"Total images processed: {summary['total_processed']}")
    print(f"Successful predictions: {summary['successful_predictions']}")
    print(f"Failed predictions: {summary['failed_predictions']}")
    print()
    
    print("ACCURACY METRICS:")
    print(f"Exact matches: {summary['exact_matches']}/{summary['successful_predictions']} ({100*summary['exact_matches']/max(1,summary['successful_predictions']):.1f}%)")
    print(f"Average character accuracy: {summary['avg_character_accuracy']:.3f} ({100*summary['avg_character_accuracy']:.1f}%)")
    print(f"Average word accuracy: {summary['avg_word_accuracy']:.3f} ({100*summary['avg_word_accuracy']:.1f}%)")
    print(f"Average confidence: {summary['avg_confidence']:.3f}")
    print()
    
    print("ACCURACY DISTRIBUTION:")
    total_success = summary['successful_predictions']
    if total_success > 0:
        for category, count in summary['accuracy_distribution'].items():
            percentage = 100 * count / total_success
            print(f"  {category.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    print()
    
    print(f"Detailed results saved to: {output_file}")
    
    # Show sample results
    print("\nSAMPLE RESULTS:")
    print("-" * 60)
    sample_results = sorted(results['results'], 
                          key=lambda x: x['similarity_metrics']['character_accuracy'], 
                          reverse=True)[:5]
    
    for i, result in enumerate(sample_results, 1):
        metrics = result['similarity_metrics']
        print(f"{i}. {result['image_name']}")
        print(f"   Expected: '{result['expected_text']}'")
        print(f"   Predicted: '{result['predicted_text']}'")
        print(f"   Character accuracy: {metrics['character_accuracy']:.3f}")
        print(f"   Exact match: {'Yes' if metrics['exact_match'] else 'No'}")
        print()
    
    # Provide recommendations
    print("RECOMMENDATIONS:")
    print("-" * 60)
    
    char_acc = summary['avg_character_accuracy']
    exact_match_rate = summary['exact_matches'] / max(1, summary['successful_predictions'])
    
    if exact_match_rate >= 0.8 and char_acc >= 0.9:
        print("✅ EXCELLENT: The baseline model performs very well on your dataset!")
        print("   Consider using it as-is or with minor parameter tuning.")
    elif exact_match_rate >= 0.6 and char_acc >= 0.8:
        print("🟡 GOOD: The baseline model shows decent performance.")
        print("   You might benefit from custom training to improve accuracy.")
    elif exact_match_rate >= 0.3 and char_acc >= 0.6:
        print("🟠 MODERATE: The baseline model has significant room for improvement.")
        print("   Custom training is recommended to achieve better results.")
    else:
        print("🔴 POOR: The baseline model performs poorly on your dataset.")
        print("   Custom training is strongly recommended.")
        print("   Consider data augmentation and hyperparameter tuning.")
    
    print()
    print("Next steps:")
    if char_acc < 0.8:
        print("1. ❌ Proceed with custom model training using your dataset")
        print("2. 📊 Use train_custom_model.py with the converted dataset")
        print("3. 🔧 Consider data augmentation techniques")
        print("4. ⚙️  Experiment with different model architectures")
    else:
        print("1. ✅ Consider using the baseline model with parameter optimization")
        print("2. 🔄 Test with a larger sample to confirm results")
        print("3. 🎯 Fine-tune OCR parameters for your specific use case")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate OCR model against ground truth labels")
    parser.add_argument("--dataset_dir", required=True, 
                       help="Directory containing the converted test dataset (with val_images/ and val_label.txt)")
    parser.add_argument("--label_file", 
                       help="Path to label file (default: dataset_dir/val_label.txt)")
    parser.add_argument("--output", default="default_ground_truth_evaluation.json", 
                       help="Output file for results")
    parser.add_argument("--max_images", type=int, default=None, 
                       help="Maximum number of images to process (default: all)")
    parser.add_argument("--config", default="baseline", 
                       choices=["baseline", "sensitive", "high_quality", "maximum_detail"],
                       help="OCR configuration to use (default: baseline - best performing)")
    parser.add_argument("--use_custom_model", action="store_true",
                       help="Use custom trained model instead of default PaddleOCR")
    parser.add_argument("--custom_model_path", 
                       help="Path to custom model directory (default: training_output/exported_model)")
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute paths
    current_dir = Path(__file__).parent
    model_training_dir = current_dir.parent
    
    dataset_dir = args.dataset_dir
    if not os.path.isabs(dataset_dir):
        dataset_dir = str(model_training_dir / dataset_dir)
    
    if not os.path.exists(dataset_dir):
        print(f"Error: Dataset directory {dataset_dir} does not exist")
        return
    
    # Default label file path if not specified
    if not args.label_file:
        label_file = os.path.join(dataset_dir, "val_label.txt")
    else:
        label_file = args.label_file
        if not os.path.isabs(label_file):
            label_file = str(model_training_dir / label_file)
    
    if not os.path.exists(label_file):
        print(f"Error: Label file {label_file} does not exist")
        return
    
    # Handle output file path
    output_file = args.output
    if not os.path.isabs(output_file):
        output_file = str(model_training_dir / output_file)
    
    print("Starting ground truth evaluation of OCR model...")
    print(f"Dataset directory: {dataset_dir}")
    print(f"Label file: {label_file}")
    print(f"Output file: {output_file}")
    print(f"OCR configuration: {args.config}")
    print(f"Use custom model: {args.use_custom_model}")
    if args.use_custom_model and args.custom_model_path:
        print(f"Custom model path: {args.custom_model_path}")
    if args.max_images:
        print(f"Max images to process: {args.max_images}")
    print()
    
    results = evaluate_with_ground_truth(
        dataset_dir, 
        label_file, 
        output_file, 
        args.max_images,
        args.config,
        args.use_custom_model,
        args.custom_model_path
    )
    
    print("\nEvaluation complete!")


if __name__ == "__main__":
    main()