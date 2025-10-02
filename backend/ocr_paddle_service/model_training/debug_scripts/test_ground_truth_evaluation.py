"""
Quick test script to run the ground truth evaluation on a small sample
"""

from pathlib import Path

def main():
    # Set up paths
    current_dir = Path(__file__).parent
    dataset_dir = current_dir / "converted_test_dataset"
    
    print("🔍 Running Ground Truth Evaluation Test")
    print("=" * 50)
    
    # Check if dataset exists
    if not dataset_dir.exists():
        print(f"❌ Error: Dataset directory {dataset_dir} does not exist")
        return
    
    val_label_file = dataset_dir / "val_label.txt"
    if not val_label_file.exists():
        print(f"❌ Error: Label file {val_label_file} does not exist")
        return
    
    val_images_dir = dataset_dir / "val_images"
    if not val_images_dir.exists():
        print(f"❌ Error: Images directory {val_images_dir} does not exist")
        return
    
    print(f"✅ Found dataset at: {dataset_dir}")
    print(f"✅ Found labels at: {val_label_file}")
    print(f"✅ Found images at: {val_images_dir}")
    
    # Count available files
    try:
        with open(val_label_file, 'r', encoding='utf-8') as f:
            label_count = sum(1 for line in f if line.strip())
        
        image_files = list(val_images_dir.glob("*.jpg")) + list(val_images_dir.glob("*.jpeg")) + list(val_images_dir.glob("*.png"))
        
        print(f"📊 Found {label_count} labels and {len(image_files)} images")
        
    except Exception as e:
        print(f"❌ Error reading files: {e}")
        return
    
    # Import and run evaluation (with small sample for testing)
    try:
        from backend.ocr_paddle_service.model_training.OCR_Evaluation.evaluate_with_ground_truth import evaluate_with_ground_truth
        
        print("\n🚀 Starting evaluation with 10 sample images...")
        
        results = evaluate_with_ground_truth(
            dataset_dir=str(dataset_dir),
            label_file=str(val_label_file),
            output_file="sample_ground_truth_results.json",
            max_images=10  # Start with small sample
        )
        
        if results:
            print("\n✅ Evaluation completed successfully!")
            print("📁 Results saved to: sample_ground_truth_results.json")
            print("\n💡 To run full evaluation, use:")
            print("python evaluate_with_ground_truth.py --dataset_dir converted_test_dataset --max_images 100")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure PaddleOCR is installed:")
        print("pip install paddleocr")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()