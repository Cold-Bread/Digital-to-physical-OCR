"""
Dataset analysis script to understand the ground truth data characteristics
"""

import os
import sys
from pathlib import Path
from collections import Counter, defaultdict
import json
from datetime import datetime
import statistics

# Add parent directories to path for imports
current_dir = Path(__file__).parent
model_training_dir = current_dir.parent
sys.path.insert(0, str(model_training_dir))
sys.path.insert(0, str(model_training_dir.parent))  # ocr_paddle_service
sys.path.insert(0, str(model_training_dir.parent.parent))  # backend

def analyze_ground_truth_dataset(label_file: str, images_dir: str | None = None):
    """
    Analyze the ground truth dataset to understand characteristics of the names.
    """
    print("📊 Analyzing Ground Truth Dataset")
    print("=" * 50)
    
    if not os.path.exists(label_file):
        print(f"❌ Error: Label file {label_file} not found")
        return
    
    labels = []
    name_stats = {
        'total_names': 0,
        'unique_names': set(),
        'name_lengths': [],
        'character_distribution': Counter(),
        'name_patterns': defaultdict(int),
        'common_names': Counter(),
        'special_characters': Counter()
    }
    
    # Read all labels
    try:
        with open(label_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) != 2:
                    print(f"⚠️  Warning: Invalid format in line {line_num}: {line}")
                    continue
                
                image_path, name = parts
                name = name.strip().upper()
                
                labels.append((os.path.basename(image_path), name))
                
                # Update statistics
                name_stats['total_names'] += 1
                name_stats['unique_names'].add(name)
                name_stats['name_lengths'].append(len(name))
                name_stats['common_names'][name] += 1
                
                # Character distribution
                for char in name:
                    name_stats['character_distribution'][char] += 1
                    if not char.isalpha():
                        name_stats['special_characters'][char] += 1
                
                # Name patterns
                if '-' in name:
                    name_stats['name_patterns']['hyphenated'] += 1
                if any(char.isdigit() for char in name):
                    name_stats['name_patterns']['contains_numbers'] += 1
                if len(name.split()) > 1:
                    name_stats['name_patterns']['multi_word'] += 1
                if any(ord(char) > 127 for char in name):
                    name_stats['name_patterns']['non_ascii'] += 1
                
    except Exception as e:
        print(f"❌ Error reading label file: {e}")
        return
    
    # Check image availability if directory provided
    available_images = 0
    missing_images = []
    
    if images_dir and os.path.exists(images_dir):
        images_path = Path(images_dir)
        for image_name, _ in labels:
            image_file = images_path / image_name
            if image_file.exists():
                available_images += 1
            else:
                missing_images.append(image_name)
    
    # Print analysis results
    print(f"📁 Label file: {label_file}")
    if images_dir:
        print(f"🖼️  Images directory: {images_dir}")
    print()
    
    print("📈 DATASET STATISTICS:")
    print(f"   Total labels: {name_stats['total_names']:,}")
    print(f"   Unique names: {len(name_stats['unique_names']):,}")
    print(f"   Duplicate rate: {(name_stats['total_names'] - len(name_stats['unique_names'])) / max(1, name_stats['total_names']) * 100:.1f}%")
    
    if images_dir:
        print(f"   Available images: {available_images:,}")
        print(f"   Missing images: {len(missing_images):,}")
        if missing_images:
            print(f"   Missing rate: {len(missing_images) / len(labels) * 100:.1f}%")
    
    print()
    
    print("📏 NAME LENGTH STATISTICS:")
    if name_stats['name_lengths']:
        import statistics
        lengths = name_stats['name_lengths']
        print(f"   Average length: {statistics.mean(lengths):.1f} characters")
        print(f"   Median length: {statistics.median(lengths):.1f} characters")
        print(f"   Min length: {min(lengths)} characters")
        print(f"   Max length: {max(lengths)} characters")
        
        # Length distribution
        length_dist = Counter(lengths)
        print(f"   Most common lengths:")
        for length, count in length_dist.most_common(5):
            print(f"     {length} chars: {count:,} names ({count/len(lengths)*100:.1f}%)")
    
    print()
    
    print("🔤 CHARACTER ANALYSIS:")
    total_chars = sum(name_stats['character_distribution'].values())
    print(f"   Total characters: {total_chars:,}")
    print(f"   Unique characters: {len(name_stats['character_distribution'])}")
    
    print(f"   Most common characters:")
    for char, count in name_stats['character_distribution'].most_common(10):
        percentage = count / total_chars * 100
        char_display = repr(char) if not char.isprintable() else char
        print(f"     '{char_display}': {count:,} ({percentage:.1f}%)")
    
    if name_stats['special_characters']:
        print(f"   Special characters found:")
        for char, count in name_stats['special_characters'].most_common():
            char_display = repr(char) if not char.isprintable() else char
            print(f"     '{char_display}': {count:,}")
    
    print()
    
    print("📝 NAME PATTERNS:")
    total_names = name_stats['total_names']
    for pattern, count in name_stats['name_patterns'].items():
        percentage = count / total_names * 100
        print(f"   {pattern.replace('_', ' ').title()}: {count:,} ({percentage:.1f}%)")
    
    print()
    
    print("👑 MOST COMMON NAMES:")
    for name, count in name_stats['common_names'].most_common(15):
        percentage = count / total_names * 100
        print(f"   '{name}': {count:,} ({percentage:.1f}%)")
    
    print()
    
    # OCR Challenge Analysis
    print("🎯 OCR CHALLENGE ASSESSMENT:")
    
    # Names with potential OCR difficulties
    challenging_names = []
    for name, count in name_stats['common_names'].items():
        challenges = []
        
        if any(char in name for char in ['I', 'L', '1']):
            challenges.append("I/L/1 confusion")
        if any(char in name for char in ['O', '0']):
            challenges.append("O/0 confusion")
        if any(char in name for char in ['S', '5']):
            challenges.append("S/5 confusion")
        if '-' in name:
            challenges.append("hyphenation")
        if len(name) > 15:
            challenges.append("long name")
        if any(char in name for char in ['Q', 'Z', 'X']):
            challenges.append("uncommon letters")
        
        if challenges:
            challenging_names.append((name, count, challenges))
    
    if challenging_names:
        print(f"   Names with potential OCR challenges: {len(challenging_names):,}")
        print(f"   Sample challenging names:")
        for name, count, challenges in sorted(challenging_names, key=lambda x: x[1], reverse=True)[:10]:
            print(f"     '{name}' ({count:,}x): {', '.join(challenges)}")
    
    # Save detailed analysis
    analysis_results = {
        'dataset_info': {
            'label_file': label_file,
            'images_directory': images_dir,
            'analysis_date': str(datetime.now()),
            'total_labels': name_stats['total_names'],
            'unique_names': len(name_stats['unique_names']),
            'available_images': available_images
        },
        'statistics': {
            'name_lengths': {
                'mean': statistics.mean(name_stats['name_lengths']) if name_stats['name_lengths'] else 0,
                'median': statistics.median(name_stats['name_lengths']) if name_stats['name_lengths'] else 0,
                'min': min(name_stats['name_lengths']) if name_stats['name_lengths'] else 0,
                'max': max(name_stats['name_lengths']) if name_stats['name_lengths'] else 0,
                'distribution': dict(Counter(name_stats['name_lengths']))
            },
            'character_distribution': dict(name_stats['character_distribution']),
            'name_patterns': dict(name_stats['name_patterns']),
            'most_common_names': dict(name_stats['common_names'].most_common(50))
        },
        'ocr_challenges': {
            'challenging_names_count': len(challenging_names),
            'sample_challenging_names': [
                {'name': name, 'count': count, 'challenges': challenges} 
                for name, count, challenges in challenging_names[:20]
            ]
        }
    }
    
    analysis_file = "dataset_analysis.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"💾 Detailed analysis saved to: {analysis_file}")
    
    return analysis_results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze ground truth dataset")
    parser.add_argument("--label_file", required=True, help="Path to label file (e.g., val_label.txt)")
    parser.add_argument("--images_dir", help="Path to images directory (optional)")
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute paths
    current_dir = Path(__file__).parent
    model_training_dir = current_dir.parent
    
    # Handle relative paths from model_training directory
    label_file = args.label_file
    if not os.path.isabs(label_file):
        label_file = str(model_training_dir / label_file)
    
    images_dir = args.images_dir
    if images_dir and not os.path.isabs(images_dir):
        images_dir = str(model_training_dir / images_dir)
    
    analyze_ground_truth_dataset(label_file, images_dir)

if __name__ == "__main__":
    main()