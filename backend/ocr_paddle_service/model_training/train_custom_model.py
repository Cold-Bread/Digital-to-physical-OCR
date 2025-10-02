"""
Custom PaddleOCR Training Script for Medical Documents

This script helps you:
1. Evaluate the current model on your test dataset
2. Prepare data for training
3. Train a custom recognition model
4. Compare performance

Before running this script:
1. Install PaddlePaddle: pip install paddlepaddle-gpu (or paddlepaddle for CPU)
2. Install PaddleOCR training dependencies: pip install "paddleocr[train]"
3. Clone PaddleOCR repository for training tools
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
import argparse
from datetime import datetime

class CustomOCRTrainer:
    def __init__(self, dataset_path: str, output_dir: str = "training_output"):
        """
        Initialize the trainer with dataset path and output directory
        
        Args:
            dataset_path: Path to your downloaded dataset
            output_dir: Directory to save training outputs
        """
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'training.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def evaluate_current_model(self, test_images_dir: str, ground_truth_file: Optional[str] = None) -> Dict:
        """
        Evaluate the current PaddleOCR model on your test dataset
        Uses the dedicated evaluate_baseline.py for actual evaluation
        
        Args:
            test_images_dir: Directory containing test images
            ground_truth_file: Optional JSON file with ground truth labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        self.logger.info("Running evaluation using evaluate_baseline.py...")
        
        import subprocess
        import sys
        
        # Run the dedicated evaluation script
        eval_script = Path(__file__).parent / "evaluate_baseline.py"
        output_file = self.output_dir / "current_model_evaluation.json"
        
        cmd = [sys.executable, str(eval_script), "--test_dir", test_images_dir, "--output", str(output_file)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Evaluation completed successfully")
            
            # Load and return results
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Evaluation failed: {e.stderr}")
            raise RuntimeError(f"Evaluation failed: {e.stderr}")
    
    def prepare_training_data(self, dataset_dir: str, dataset_format: str = "txt"):
        """
        Prepare your dataset for PaddleOCR training using dataset_converter.py
        
        Args:
            dataset_dir: Directory containing your dataset
            dataset_format: Format of the dataset ("txt", "csv", "json", "folder")
        """
        self.logger.info("Preparing training data using dataset_converter...")
        
        import subprocess
        import sys
        
        converter_script = Path(__file__).parent / "dataset_converter.py"
        output_dir = self.output_dir / "train_data"
        
        cmd = [
            sys.executable, str(converter_script),
            "--input_dir", dataset_dir,
            "--format", dataset_format,
            "--output_dir", str(output_dir),
            "--train_ratio", "0.8"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Dataset conversion completed successfully")
            self.logger.info(result.stdout)
            return output_dir
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Dataset conversion failed: {e.stderr}")
            raise RuntimeError(f"Dataset conversion failed: {e.stderr}")
    
    def create_training_config(self, model_type: str = "rec") -> str:
        """
        Create PaddleOCR training configuration
        
        Args:
            model_type: Type of model to train ("det" for detection, "rec" for recognition)
            
        Returns:
            Path to the configuration file
        """
        if model_type == "rec":
            config = {
                "Global": {
                    "use_gpu": True,
                    "epoch_num": 100,
                    "log_smooth_window": 20,
                    "print_batch_step": 10,
                    "save_model_dir": str(self.output_dir / "rec_model"),
                    "save_epoch_step": 10,
                    "eval_batch_step": 500,
                    "cal_metric_during_train": True,
                    "pretrained_model": "",  # Path to pretrained model if any
                    "checkpoints": "",
                    "save_inference_dir": str(self.output_dir / "rec_inference"),
                    "use_visualdl": False,
                    "infer_img": str(self.output_dir / "train_data/val_images"),
                    "character_dict_path": "ppocr/utils/ppocr_keys_v1.txt",
                    "character_type": "en",
                    "max_text_length": 25,
                    "infer_mode": False,
                    "use_space_char": True,
                    "distributed": False
                },
                "Optimizer": {
                    "name": "Adam",
                    "beta1": 0.9,
                    "beta2": 0.999,
                    "lr": {
                        "name": "Cosine",
                        "learning_rate": 0.001,
                        "warmup_epoch": 5
                    },
                    "regularizer": {
                        "name": "L2",
                        "factor": 1e-4
                    }
                },
                "Architecture": {
                    "model_type": "rec",
                    "algorithm": "SVTR_LCNet",
                    "Transform": None,
                    "Backbone": {
                        "name": "SVTRNet",
                        "img_size": [32, 320],
                        "out_char_num": 25,
                        "out_channels": 192,
                        "patch_merging": "Conv",
                        "arch": "base",
                        "last_stage": True
                    },
                    "Neck": {
                        "name": "SequenceEncoder",
                        "encoder_type": "svtr",
                        "dims": 64,
                        "depth": 2,
                        "hidden_dims": 120,
                        "use_guide": True
                    },
                    "Head": {
                        "name": "CTCHead",
                        "fc_decay": 1e-4
                    }
                },
                "Loss": {
                    "name": "CTCLoss"
                },
                "PostProcess": {
                    "name": "CTCLabelDecode"
                },
                "Metric": {
                    "name": "RecMetric",
                    "main_indicator": "acc"
                },
                "Train": {
                    "dataset": {
                        "name": "SimpleDataSet",
                        "data_dir": str(self.output_dir / "train_data"),
                        "label_file_list": [str(self.output_dir / "train_data/train_label.txt")],
                        "transforms": [
                            {"DecodeImage": {"img_mode": "BGR", "channel_first": False}},
                            {"RecAug": {}},
                            {"CTCLabelEncode": {}},
                            {"RecResizeImg": {"image_shape": [3, 32, 320]}},
                            {"KeepKeys": {"keep_keys": ["image", "label", "length"]}}
                        ]
                    },
                    "loader": {
                        "shuffle": True,
                        "batch_size_per_card": 128,
                        "drop_last": True,
                        "num_workers": 4
                    }
                },
                "Eval": {
                    "dataset": {
                        "name": "SimpleDataSet",
                        "data_dir": str(self.output_dir / "train_data"),
                        "label_file_list": [str(self.output_dir / "train_data/val_label.txt")],
                        "transforms": [
                            {"DecodeImage": {"img_mode": "BGR", "channel_first": False}},
                            {"CTCLabelEncode": {}},
                            {"RecResizeImg": {"image_shape": [3, 32, 320]}},
                            {"KeepKeys": {"keep_keys": ["image", "label", "length"]}}
                        ]
                    },
                    "loader": {
                        "shuffle": False,
                        "drop_last": False,
                        "batch_size_per_card": 128,
                        "num_workers": 4
                    }
                }
            }
        else:
            raise ValueError(f"Unsupported model type: {model_type}. Only 'rec' is currently supported.")
        
        config_file = self.output_dir / f"{model_type}_config.yml"
        
        # Convert to YAML format
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        self.logger.info(f"Training configuration saved to {config_file}")
        return str(config_file)
    


def main():
    parser = argparse.ArgumentParser(description="Custom PaddleOCR Training")
    parser.add_argument("--dataset_path", required=True, help="Path to your dataset")
    parser.add_argument("--test_images", help="Path to test images directory")
    parser.add_argument("--dataset_format", choices=["txt", "csv", "json", "folder"], 
                       default="txt", help="Format of the input dataset")
    parser.add_argument("--action", choices=["evaluate", "prepare", "config"], 
                       default="prepare", help="Action to perform")
    
    args = parser.parse_args()
    
    trainer = CustomOCRTrainer(args.dataset_path)
    
    if args.action == "evaluate" and args.test_images:
        results = trainer.evaluate_current_model(args.test_images)
        print(f"Evaluation complete. Check {trainer.output_dir / 'current_model_evaluation.json'}")
    
    elif args.action == "prepare":
        trainer.prepare_training_data(args.dataset_path, args.dataset_format)
        print(f"Training data prepared in {trainer.output_dir}")
        
    elif args.action == "config":
        trainer.create_training_config("rec")
        print(f"Training configuration created in {trainer.output_dir}")

if __name__ == "__main__":
    main()