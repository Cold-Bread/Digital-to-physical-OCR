"""
Simple script to create evaluation dataset from CSV
"""

import pandas as pd
import shutil
from pathlib import Path
from typing import Optional

def create_evaluation_dataset(csv_file: str, images_dir: str, output_dir: str, max_samples: Optional[int] = None):
    """
    Create evaluation dataset from CSV file
    
    Args:
        csv_file: Path to CSV file with FILENAME and IDENTITY columns
        images_dir: Directory containing the images
        output_dir: Output directory for evaluation dataset
        max_samples: Maximum number of samples to include
    """
    
    # Read CSV
    df = pd.read_csv(csv_file)
    print(f"Loaded CSV with {len(df)} entries")
    print(f"Columns: {list(df.columns)}")
    
    # Limit samples if specified
    if max_samples and max_samples < len(df):
        df = df.head(max_samples)
        print(f"Limited to {max_samples} samples")
    
    # Create output directories
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    images_output = output_path / "images"
    images_output.mkdir(exist_ok=True)
    
    # Create label file
    label_file = output_path / "labels.txt"
    
    created_count = 0
    missing_count = 0
    
    with open(label_file, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            filename = row['FILENAME']
            text = row['IDENTITY']
            
            # Source image path
            src_image = Path(images_dir) / filename
            
            if src_image.exists():
                # Copy image to output directory
                dst_image = images_output / filename
                shutil.copy2(src_image, dst_image)
                
                # Write label entry
                f.write(f"images/{filename}\t{text}\n")
                created_count += 1
            else:
                print(f"Warning: Image not found: {src_image}")
                missing_count += 1
    
    print(f"\nDataset creation complete!")
    print(f"Created: {created_count} samples")
    print(f"Missing: {missing_count} images")
    print(f"Output directory: {output_dir}")
    print(f"Label file: {label_file}")
    
    return str(label_file)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create dataset from CSV")
    parser.add_argument("--csv_file", required=True, help="Path to CSV file")
    parser.add_argument("--images_dir", required=True, help="Directory containing images")
    parser.add_argument("--output_dir", default="evaluation_dataset", help="Output directory")
    parser.add_argument("--max_samples", type=int, help="Maximum number of samples")
    
    args = parser.parse_args()
    
    label_file = create_evaluation_dataset(
        args.csv_file, 
        args.images_dir, 
        args.output_dir, 
        args.max_samples
    )
    
    print(f"\nYou can now run evaluation with:")
    print(f"python OCR_Evaluation/evaluate_with_ground_truth.py --dataset_dir {args.output_dir} --max_images {args.max_samples or 'all'}")