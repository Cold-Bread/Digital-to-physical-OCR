"""
Custom Model Training Script for PaddleOCR
Following PaddleOCR's official secondary development workflow from:
https://www.paddleocr.ai/main/en/version3.x/module_usage/text_recognition.html#4-secondary-development

This script implements the complete training pipeline including:
1. Dataset preparation in PaddleOCR format
2. Pre-trained model download
3. Training using official PaddleOCR tools
4. Model evaluation and export
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import tarfile

# Add parent directories to path for imports
current_dir = Path(__file__).parent
model_training_dir = current_dir
sys.path.insert(0, str(model_training_dir))
sys.path.insert(0, str(model_training_dir.parent))  # ocr_paddle_service
sys.path.insert(0, str(model_training_dir.parent.parent))  # backend


class PaddleOCRTrainer:
    """
    Official PaddleOCR training workflow implementation.
    Follows the secondary development guidelines from PaddleOCR documentation.
    """
    
    def __init__(self, dataset_path: str, pretrained_model_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path)
        self.model_training_dir = Path(__file__).parent
        self.training_output_dir = self.model_training_dir / "training_output"
        self.training_output_dir.mkdir(exist_ok=True)
        
        # PaddleOCR repository setup
        self.paddleocr_repo_dir = self.model_training_dir / "PaddleOCR"
        
        # Pre-trained model path configuration
        if pretrained_model_path:
            self.pretrained_model_path = Path(pretrained_model_path)
        else:
            # Default path for PP-OCRv5_server_rec model
            self.pretrained_model_path = self.model_training_dir / "pretrained_models" / "PP-OCRv5_server_rec_pretrained.pdparams"
        
        # Training configuration
        self.model_config = "PP-OCRv5_server_rec"  # Default model for training
        self.config_file = f"configs/rec/PP-OCRv5/{self.model_config}.yml"
        
    def setup_paddleocr_environment(self) -> bool:
        """
        Set up the PaddleOCR training environment by cloning the repository
        and installing dependencies.
        """        
        # Clone PaddleOCR repository if not exists
        if not self.paddleocr_repo_dir.exists():
            print("Cloning PaddleOCR repository...")
            try:
                subprocess.run([
                    "git", "clone", 
                    "https://github.com/PaddlePaddle/PaddleOCR.git",
                    str(self.paddleocr_repo_dir)
                ], check=True)
                print("✅ PaddleOCR repository cloned successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to clone PaddleOCR repository: {e}")
                return False
        else:
            print("✅ PaddleOCR repository already exists")
        return True

    def analyze_evaluation_results(self) -> Dict:
        """
        Analyze existing evaluation results to determine training priorities.
        """
        print("Analyzing existing evaluation results...")
        
        results_dir = self.model_training_dir / "evaluation_results"
        evaluation_files = [
            "full_ground_truth_evaluation.json",
            "ground_truth_evaluation.json", 
            "parameter_test_results.json"
        ]
        
        analysis = {
            "detection_issues": 0,
            "recognition_issues": 0, 
            "total_samples": 0,
            "avg_character_accuracy": 0.0,
            "recommendations": []
        }
        
        # Try to load the most comprehensive evaluation
        for eval_file in evaluation_files:
            eval_path = results_dir / eval_file
            if eval_path.exists():
                try:
                    with open(eval_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if 'summary' in data:
                        summary = data['summary']
                        analysis["total_samples"] = summary.get('total_processed', 0)
                        analysis["avg_character_accuracy"] = summary.get('avg_character_accuracy', 0.0)
                        
                        # Analyze individual results if available
                        if 'results' in data and isinstance(data['results'], list):
                            self._analyze_individual_results(data['results'], analysis)
                            
                    elif 'configurations' in data:  # Parameter test results
                        configs = data['configurations']
                        if configs:
                            best_config = max(configs, key=lambda x: x.get('avg_character_accuracy', 0))
                            analysis["avg_character_accuracy"] = best_config.get('avg_character_accuracy', 0.0)
                    
                    print(f"Loaded evaluation data from: {eval_file}")
                    break
                    
                except Exception as e:
                    print(f"Error loading {eval_file}: {e}")
                    continue
        
        # Generate recommendations based on analysis
        self._generate_training_recommendations(analysis)
        
        return analysis
    
    def _analyze_individual_results(self, results: List[Dict], analysis: Dict):
        """
        Analyze individual image results to identify specific issues.
        """
        detection_issues = 0
        recognition_issues = 0
        
        for result in results[:1000]:  # Analyze first 1000 samples
            predicted = result.get('predicted_text', '').strip()
            expected = result.get('expected_text', '').strip()
            num_segments = result.get('num_segments', 0)
            
            # Check for detection issues (no text detected)
            if not predicted or num_segments == 0:
                detection_issues += 1
            # Check for recognition issues (text detected but wrong)
            elif predicted != expected:
                recognition_issues += 1
        
        analysis["detection_issues"] = detection_issues
        analysis["recognition_issues"] = recognition_issues
    
    def _generate_training_recommendations(self, analysis: Dict):
        """
        Generate specific training recommendations based on analysis.
        """
        recommendations = []
        
        char_acc = analysis["avg_character_accuracy"]
        detection_issues = analysis["detection_issues"]
        recognition_issues = analysis["recognition_issues"]
        total_samples = analysis["total_samples"]
        
        if char_acc < 0.5:
            recommendations.append("CRITICAL: Custom training is essential - baseline accuracy too low")
        elif char_acc < 0.8:
            recommendations.append("RECOMMENDED: Custom training will significantly improve performance")
        else:
            recommendations.append("OPTIONAL: Fine-tuning may provide marginal improvements")
        
        if detection_issues > total_samples * 0.1:
            recommendations.append("FOCUS: Text Detection Module training needed")
        
        if recognition_issues > total_samples * 0.2:
            recommendations.append("FOCUS: Text Recognition Module training needed")
        
        # Specific training approach recommendations
        if char_acc < 0.3:
            recommendations.append("APPROACH: Full pipeline training with data augmentation")
        elif char_acc < 0.7:
            recommendations.append("APPROACH: Focus on recognition module with fine-tuning")
        else:
            recommendations.append("APPROACH: Parameter optimization may be sufficient")
        
        analysis["recommendations"] = recommendations

    def prepare_training_data(self, format_type: str = "paddleocr") -> bool:
        """
        Prepare training data in the official PaddleOCR format.
        This follows the dataset structure expected by PaddleOCR training tools.
        """
        print(f"Preparing training data in {format_type} format...")
        
        # Check if our converted dataset exists
        converted_dataset = self.model_training_dir / "training_dataset"
        if not converted_dataset.exists():
            print(f"Error: Converted dataset not found at {converted_dataset}")
            print("Please ensure you have run the dataset conversion first.")
            return False
        
        # Create training data directory structure following PaddleOCR conventions
        training_data_dir = self.training_output_dir / "formatted_data"
        training_data_dir.mkdir(exist_ok=True)
        
        if format_type == "paddleocr":
            return self._prepare_paddleocr_format(converted_dataset, training_data_dir)
        else:
            print(f"Format {format_type} not yet implemented")
            return False
    
    def _prepare_paddleocr_format(self, source_dir: Path, output_dir: Path) -> bool:
        """
        Prepare data in PaddleOCR's expected format for training.
        This creates the proper directory structure and label files.
        """
        try:
            # Create directory structure following PaddleOCR conventions
            train_dir = output_dir / "train_data"
            val_dir = output_dir / "val_data" 
            train_dir.mkdir(exist_ok=True)
            val_dir.mkdir(exist_ok=True)
            
            # Process validation data first
            source_val_images = source_dir / "val_images"
            source_val_labels = source_dir / "val_label.txt"
            
            if source_val_images.exists() and source_val_labels.exists():
                # Copy validation images
                val_images_dir = val_dir / "images"
                if val_images_dir.exists():
                    shutil.rmtree(val_images_dir)
                shutil.copytree(source_val_images, val_images_dir)
                
                # Create validation label file in PaddleOCR format
                self._convert_label_file(source_val_labels, val_dir / "Label.txt", "images")
                
                print(f"Validation data prepared: {len(list(val_images_dir.glob('*.jpg')))} images")
            
            # Process training data
            source_train_images = source_dir / "train_images" 
            source_train_labels = source_dir / "train_label.txt"
            
            if source_train_images.exists() and source_train_labels.exists():
                # Copy training images
                train_images_dir = train_dir / "images"
                if train_images_dir.exists():
                    shutil.rmtree(train_images_dir)
                shutil.copytree(source_train_images, train_images_dir)
                
                # Create training label file in PaddleOCR format
                self._convert_label_file(source_train_labels, train_dir / "Label.txt", "images")
                
                print(f"Training data prepared: {len(list(train_images_dir.glob('*.jpg')))} images")
            else:
                print("Warning: No training data found - will split validation data")
                self._split_validation_data(val_dir, train_dir)
            
            # Create or update the training configuration file
            self._create_training_config(output_dir)
            
            return True
            
        except Exception as e:
            print(f"Error preparing PaddleOCR format: {e}")
            return False
    
    def _convert_label_file(self, source_label_file: Path, target_label_file: Path, images_prefix: str):
        """
        Convert label file to PaddleOCR format.
        PaddleOCR expects: relative_image_path<tab>ground_truth_text
        """
        with open(source_label_file, 'r', encoding='utf-8') as source:
            with open(target_label_file, 'w', encoding='utf-8') as target:
                for line in source:
                    line = line.strip()
                    if line and '\t' in line:
                        image_path, text = line.split('\t', 1)
                        image_name = os.path.basename(image_path)
                        # Write in PaddleOCR format
                        target.write(f"{images_prefix}/{image_name}\t{text}\n")
    
    def _split_validation_data(self, val_dir: Path, train_dir: Path, split_ratio: float = 0.8):
        """
        Split validation data into training and validation sets.
        """
        print(f"Splitting validation data with {split_ratio:.1%} for training...")
        
        val_images_dir = val_dir / "images"
        val_label_file = val_dir / "Label.txt"
        
        if not val_images_dir.exists() or not val_label_file.exists():
            print("Error: Validation data not found for splitting")
            return
        
        # Read all labels
        with open(val_label_file, 'r', encoding='utf-8') as f:
            all_labels = [line.strip() for line in f if line.strip()]
        
        # Calculate split point
        split_point = int(len(all_labels) * split_ratio)
        train_labels = all_labels[:split_point]
        val_labels = all_labels[split_point:]
        
        # Create train images directory
        train_images_dir = train_dir / "images"
        train_images_dir.mkdir(exist_ok=True)
        
        # Process training data
        train_label_file = train_dir / "Label.txt"
        with open(train_label_file, 'w', encoding='utf-8') as f:
            for label_line in train_labels:
                parts = label_line.split('\t')
                if len(parts) == 2:
                    image_path, text = parts
                    image_name = os.path.basename(image_path.replace('images/', ''))
                    
                    # Move image to train directory
                    source_image = val_images_dir / image_name
                    target_image = train_images_dir / image_name
                    
                    if source_image.exists():
                        shutil.move(str(source_image), str(target_image))
                        f.write(f"images/{image_name}\t{text}\n")
        
        # Update validation label file
        with open(val_label_file, 'w', encoding='utf-8') as f:
            for label_line in val_labels:
                parts = label_line.split('\t')
                if len(parts) == 2:
                    image_path, text = parts
                    image_name = os.path.basename(image_path.replace('images/', ''))
                    f.write(f"images/{image_name}\t{text}\n")
        
        print(f"Data split complete:")
        print(f"  Training samples: {len(train_labels)}")
        print(f"  Validation samples: {len(val_labels)}")
    
    def _create_training_config(self, output_dir: Path):
        """
        Create or update the PaddleOCR training configuration file.
        This uses the official PP-OCRv5_server_rec configuration as base.
        """
        config_dir = output_dir / "configs"
        config_dir.mkdir(exist_ok=True)
        
        # Create a custom configuration based on PP-OCRv5_server_rec
        config_file = config_dir / "custom_rec_config.yml"
        
        config = {
            "Global": {
                "debug": False,
                "use_gpu": True,
                "epoch_num": 100,
                "log_smooth_window": 20,
                "print_batch_step": 10,
                "save_model_dir": str(self.training_output_dir / "rec_models"),
                "save_epoch_step": 10,
                "eval_batch_step": [0, 500],
                "cal_metric_during_train": True,
                "pretrained_model": str(self.pretrained_model_path.resolve()),
                "checkpoints": None,
                "save_inference_dir": None,
                "use_visualdl": False,
                "infer_img": None,
                "character_dict_path": str(self.paddleocr_repo_dir / "ppocr" / "utils" / "dict" / "ppocrv5_dict.txt"),
                "max_text_length": 25,
                "infer_mode": False,
                "use_space_char": True,
                "distributed": False,
                "save_res_path": str(config_dir / "predicts_rec.txt")
            },
            "Architecture": {
                "algorithm": "SVTR",
                "model_type": "rec",
                "Backbone": {
                    "name": "SVTRNet",
                    "img_size": [32, 128],
                    "out_char_num": 25,
                    "out_channels": 192,
                    "patch_merging": "Conv",
                    "embed_dim": [64, 128, 256],
                    "depth": [3, 6, 3],
                    "num_heads": [2, 4, 8],
                    "mixer": ["Local", "Local", "Local", "Local", "Local", "Local", 
                             "Global", "Global", "Global", "Global", "Global", "Global"],
                    "local_mixer": [[7, 11], [7, 11], [7, 11]],
                    "last_stage": True,
                    "prenorm": False
                },
                "Head": {
                    "name": "CTCHead",
                    "fc_decay": 0.00001
                },
                "Neck": {
                    "name": "SequenceEncoder",
                    "encoder_type": "svtr",
                    "dims": 192,
                    "depth": 2,
                    "hidden_dims": 120,
                    "use_guide": True
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
            "Train": {
                "dataset": {
                    "name": "SimpleDataSet",
                    "data_dir": str(output_dir / "train_data"),
                    "label_file_list": [str(output_dir / "train_data" / "Label.txt")],
                    "transforms": [
                        {"DecodeImage": {"img_mode": "BGR", "channel_first": False}},
                        {"CTCLabelEncode": {}},
                        {"RecAug": {}},
                        {"RecResizeImg": {"image_shape": [3, 32, 128]}},
                        {"KeepKeys": {"keep_keys": ["image", "label", "length"]}}
                    ]
                },
                "loader": {
                    "shuffle": True,
                    "batch_size_per_card": 256,
                    "drop_last": True,
                    "num_workers": 4
                }
            },
            "Eval": {
                "dataset": {
                    "name": "SimpleDataSet", 
                    "data_dir": str(output_dir / "val_data"),
                    "label_file_list": [str(output_dir / "val_data" / "Label.txt")],
                    "transforms": [
                        {"DecodeImage": {"img_mode": "BGR", "channel_first": False}},
                        {"CTCLabelEncode": {}},
                        {"RecResizeImg": {"image_shape": [3, 32, 128]}},
                        {"KeepKeys": {"keep_keys": ["image", "label", "length"]}}
                    ]
                },
                "loader": {
                    "shuffle": False,
                    "drop_last": False,
                    "batch_size_per_card": 256,
                    "num_workers": 4
                }
            }
        }
        
        # Save configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"Training configuration saved to: {config_file}")
        return config_file

    def execute_training(self, config_path: Optional[str] = None) -> bool:
        """
        Execute the training process using PaddleOCR's official training tools.
        This follows the secondary development workflow from the documentation.
        """
        print("Executing custom model training using PaddleOCR tools...")
        
        if not self.paddleocr_repo_dir.exists():
            print("❌ PaddleOCR repository not found. Please run setup first.")
            return False
        
        if not config_path:
            config_path = str(self.training_output_dir / "formatted_data" / "configs" / "custom_rec_config.yml")
        
        if not Path(config_path).exists():
            print(f"❌ Config file not found at {config_path}")
            print("Please run data preparation first: --action prepare")
            return False
        
        # Check for pre-trained model
        if not self.pretrained_model_path.exists():
            print(f"❌ Pre-trained model not found at: {self.pretrained_model_path}")
            print("Please ensure the pre-trained model file exists or specify a different path.")
            return False
        
        # Change to PaddleOCR directory for training
        original_cwd = os.getcwd()
        try:
            os.chdir(self.paddleocr_repo_dir)
            
            # Convert pretrained model path to absolute path to avoid issues when changing directories
            absolute_pretrained_path = str(self.pretrained_model_path.resolve())
            
            # Prepare training command following PaddleOCR documentation
            train_command = [
                sys.executable, "tools/train.py",
                "-c", str(config_path),
                "-o", f"Global.pretrained_model={absolute_pretrained_path}"
            ]
            
            print("Starting training with command:")
            print(" ".join(train_command))
            print("\n" + "="*60)
            print("TRAINING IN PROGRESS")
            print("="*60)
            print("This may take several hours depending on your dataset size and hardware.")
            print("Monitor the output for training progress and accuracy improvements.")
            print("="*60 + "\n")
            
            # Execute training
            result = subprocess.run(train_command, check=True)
            
            if result.returncode == 0:
                print("\n✅ Training completed successfully!")
                print(f"Models saved to: {self.training_output_dir / 'rec_models'}")
                return True
            else:
                print(f"\n❌ Training failed with return code: {result.returncode}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Training failed: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error during training: {e}")
            return False
        finally:
            # Return to original directory
            os.chdir(original_cwd)
    
    def evaluate_model(self, model_path: str) -> bool:
        """
        Evaluate the trained model using PaddleOCR's evaluation tools.
        """
        print(f"Evaluating trained model: {model_path}")
        
        if not self.paddleocr_repo_dir.exists():
            print("❌ PaddleOCR repository not found. Please run setup first.")
            return False
        
        config_path = str(self.training_output_dir / "formatted_data" / "configs" / "custom_rec_config.yml")
        if not Path(config_path).exists():
            print(f"❌ Config file not found at {config_path}")
            return False
        
        # Change to PaddleOCR directory for evaluation
        original_cwd = os.getcwd()
        try:
            os.chdir(self.paddleocr_repo_dir)
            
            # Prepare evaluation command
            eval_command = [
                sys.executable, "tools/eval.py",
                "-c", str(config_path),
                "-o", f"Global.pretrained_model={model_path}"
            ]
            
            print("Starting evaluation with command:")
            print(" ".join(eval_command))
            
            # Execute evaluation
            result = subprocess.run(eval_command, check=True)
            
            if result.returncode == 0:
                print("✅ Evaluation completed successfully!")
                return True
            else:
                print(f"❌ Evaluation failed with return code: {result.returncode}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Evaluation failed: {e}")
            return False
        finally:
            os.chdir(original_cwd)
    
    def export_model(self, model_path: str, output_dir: Optional[str] = None) -> bool:
        """
        Export the trained model for inference using PaddleOCR's export tools.
        """
        print(f"Exporting trained model: {model_path}")
        
        if not self.paddleocr_repo_dir.exists():
            print("❌ PaddleOCR repository not found. Please run setup first.")
            return False
        
        if not output_dir:
            output_dir = str(self.training_output_dir / "exported_model")
        
        config_path = str(self.training_output_dir / "formatted_data" / "configs" / "custom_rec_config.yml")
        if not Path(config_path).exists():
            print(f"❌ Config file not found at {config_path}")
            return False
        
        # Change to PaddleOCR directory for export
        original_cwd = os.getcwd()
        try:
            os.chdir(self.paddleocr_repo_dir)
            
            # Prepare export command to create the correct .pdmodel format
            export_command = [
                sys.executable, "tools/export_model.py",
                "-c", str(config_path),
                "-o", f"Global.pretrained_model={model_path}",
                f"Global.save_inference_dir={output_dir}",
                "Architecture.model_type=rec"
            ]
            
            print("Starting model export with command:")
            print(" ".join(export_command))
            
            # Execute export
            result = subprocess.run(export_command, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Model exported successfully to: {output_dir}")
                
                # Verify the exported files - check for both .pdmodel and .json formats
                expected_files = ['inference.pdiparams']
                model_files = ['inference.pdmodel', 'inference.json']  # Check for either format
                config_files = ['inference.yml', 'inference.pdiparams.info']
                
                missing_files = []
                model_file_found = False
                
                # Check for required parameter file
                for file_name in expected_files:
                    file_path = Path(output_dir) / file_name
                    if not file_path.exists():
                        missing_files.append(file_name)
                
                # Check for model file (either .pdmodel or .json)
                for file_name in model_files:
                    file_path = Path(output_dir) / file_name
                    if file_path.exists():
                        model_file_found = True
                        print(f"✅ Found model file: {file_name}")
                        break
                
                if not model_file_found:
                    missing_files.extend(model_files)
                
                # Check for configuration files (optional but helpful)
                for file_name in config_files:
                    file_path = Path(output_dir) / file_name
                    if file_path.exists():
                        print(f"✅ Found config file: {file_name}")
                
                if missing_files:
                    print(f"⚠️ Warning: Missing expected files: {missing_files}")
                else:
                    print("✅ Export verification complete - all essential files found.")
                
                print("The exported model can be integrated into PaddleOCR API.")
                return True
            else:
                print(f"❌ Export failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Export failed: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"Error details: {e.stderr}")
            return False
        finally:
            os.chdir(original_cwd)

    def create_training_plan(self) -> Dict:
        """
        Create a comprehensive training plan based on evaluation results.
        """
        print("Creating custom training plan...")
        
        analysis = self.analyze_evaluation_results()
        
        plan = {
            "analysis_summary": analysis,
            "training_approach": self._determine_training_approach(analysis),
            "training_steps": self._generate_training_steps(analysis),
            "expected_improvements": self._estimate_improvements(analysis),
            "resources_needed": self._estimate_resources(),
            "timeline": self._estimate_timeline(analysis)
        }
        
        # Save plan
        plan_file = self.training_output_dir / "training_plan.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        
        print(f"Training plan saved to: {plan_file}")
        return plan
    
    def _determine_training_approach(self, analysis: Dict) -> str:
        """
        Determine the best training approach based on analysis.
        """
        char_acc = analysis["avg_character_accuracy"]
        
        if char_acc < 0.3:
            return "full_pipeline_training"
        elif char_acc < 0.7:
            return "recognition_focused_training"
        else:
            return "parameter_optimization"
    
    def _generate_training_steps(self, analysis: Dict) -> List[Dict]:
        """
        Generate specific training steps following the PaddleOCR workflow.
        """
        char_acc = analysis["avg_character_accuracy"]
        
        if char_acc < 0.5:
            return [
                {
                    "step": 1,
                    "action": "setup_environment",
                    "description": "Set up PaddleOCR training environment",
                    "command": "python train_custom_model.py --action setup"
                },
                {
                    "step": 2,
                    "action": "prepare_data",
                    "description": "Prepare training data in PaddleOCR format",
                    "command": "python train_custom_model.py --action prepare --dataset_format paddleocr"
                },
                {
                    "step": 3,
                    "action": "train_model",
                    "description": "Train text recognition model (specify --pretrained_model_path if not using default)",
                    "command": "python train_custom_model.py --action train --pretrained_model_path /path/to/pretrained/model.pdparams"
                },
                {
                    "step": 4,
                    "action": "evaluate_model",
                    "description": "Evaluate trained model",
                    "command": "python train_custom_model.py --action evaluate --model_path training_output/rec_models/best_accuracy.pdparams"
                },
                {
                    "step": 5,
                    "action": "export_model",
                    "description": "Export model for inference",
                    "command": "python train_custom_model.py --action export --model_path training_output/rec_models/best_accuracy.pdparams"
                }
            ]
        else:
            return [
                {
                    "step": 1,
                    "action": "optimize_parameters",
                    "description": "Fine-tune OCR parameters based on parameter test results",
                    "command": "python OCR_Evaluation/parameter_test.py --optimize True"
                }
            ]
    
    def _estimate_improvements(self, analysis: Dict) -> Dict:
        """
        Estimate expected improvements from training.
        """
        current_acc = analysis["avg_character_accuracy"]
        
        if current_acc < 0.3:
            expected_improvement = 0.4  # 40% improvement
        elif current_acc < 0.7:
            expected_improvement = 0.2  # 20% improvement
        else:
            expected_improvement = 0.05  # 5% improvement
        
        return {
            "current_accuracy": current_acc,
            "expected_accuracy": min(0.95, current_acc + expected_improvement),
            "improvement_estimate": expected_improvement,
            "confidence": "medium" if current_acc < 0.5 else "high"
        }
    
    def _estimate_resources(self) -> Dict:
        """
        Estimate computational resources needed.
        """
        return {
            "gpu_memory": "8GB+ recommended",
            "training_time": "2-8 hours",
            "disk_space": "5GB+ for models and data",
            "python_packages": ["paddlepaddle-gpu", "paddleocr", "pyyaml"]
        }
    
    def _estimate_timeline(self, analysis: Dict) -> Dict:
        """
        Estimate training timeline.
        """
        char_acc = analysis["avg_character_accuracy"]
        
        if char_acc < 0.5:
            return {
                "preparation": "1-2 hours",
                "training": "4-8 hours", 
                "evaluation": "1 hour",
                "total": "6-11 hours"
            }
        else:
            return {
                "preparation": "30 minutes",
                "parameter_tuning": "1-2 hours",
                "evaluation": "30 minutes", 
                "total": "2-3 hours"
            }


def main():
    parser = argparse.ArgumentParser(description="Custom model training for PaddleOCR following official secondary development workflow")
    parser.add_argument("--dataset_path", default="training_dataset",
                       help="Path to the converted dataset")
    parser.add_argument("--action", required=True, 
                       choices=["setup", "analyze", "prepare", "config", "train", "evaluate", "export"],
                       help="Action to perform")
    parser.add_argument("--pretrained_model_path",
                       help="Path to the pre-trained model file (.pdparams)")
    parser.add_argument("--dataset_format", default="paddleocr",
                       choices=["paddleocr"],
                       help="Format to prepare data in")
    parser.add_argument("--config_path", 
                       help="Path to training configuration file")
    parser.add_argument("--model_path", 
                       help="Path to trained model for evaluation/export")
    parser.add_argument("--output_dir",
                       help="Output directory for exported model")
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute
    current_dir = Path(__file__).parent
    dataset_path = args.dataset_path
    if not os.path.isabs(dataset_path):
        dataset_path = str(current_dir / dataset_path)
    
    trainer = PaddleOCRTrainer(dataset_path, args.pretrained_model_path)
    
    if args.action == "setup":
        print("Setting up PaddleOCR training environment...")
        success = trainer.setup_paddleocr_environment()
        if success:
            print("✅ Environment setup completed successfully!")
        else:
            print("❌ Environment setup failed!")
    
    elif args.action == "analyze":
        print("Analyzing evaluation results...")
        analysis = trainer.analyze_evaluation_results()
        
        print("\n" + "="*60)
        print("TRAINING ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total samples analyzed: {analysis['total_samples']}")
        print(f"Average character accuracy: {analysis['avg_character_accuracy']:.3f}")
        print(f"Detection issues: {analysis['detection_issues']}")
        print(f"Recognition issues: {analysis['recognition_issues']}")
        print("\nRecommendations:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")
        
    elif args.action == "prepare":
        print("Preparing training data...")
        success = trainer.prepare_training_data(args.dataset_format)
        if success:
            print("✅ Data preparation completed successfully!")
            print("Next step: python train_custom_model.py --action train")
        else:
            print("❌ Data preparation failed!")
    
    elif args.action == "config":
        print("Creating training configuration and plan...")
        plan = trainer.create_training_plan()
        
        print("\n" + "="*60)
        print("TRAINING PLAN CREATED")
        print("="*60)
        print(f"Recommended approach: {plan['training_approach']}")
        print(f"Expected improvement: {plan['expected_improvements']['improvement_estimate']:.1%}")
        print(f"Estimated timeline: {plan['timeline']['total']}")
        print("\nNext steps:")
        for step in plan['training_steps']:
            print(f"  {step['step']}. {step['description']}")
            print(f"     Command: {step['command']}")
    
    elif args.action == "train":
        print("Executing training...")
        success = trainer.execute_training(args.config_path)
        if success:
            print("✅ Training completed successfully!")
            print("Next step: Evaluate your model with --action evaluate")
        else:
            print("❌ Training failed!")
    
    elif args.action == "evaluate":
        print("Evaluating trained model...")
        if not args.model_path:
            print("Error: --model_path required for evaluation")
            return
        success = trainer.evaluate_model(args.model_path)
        if success:
            print("✅ Evaluation completed successfully!")
        else:
            print("❌ Evaluation failed!")
    
    elif args.action == "export":
        print("Exporting trained model...")
        if not args.model_path:
            print("Error: --model_path required for export")
            return
        success = trainer.export_model(args.model_path, args.output_dir)
        if success:
            print("✅ Model export completed successfully!")
            print("The exported model can now be integrated into your PaddleOCR API.")
        else:
            print("❌ Model export failed!")
    
    print("\n" + "="*60)
    print("PADDLEOCR TRAINING SCRIPT EXECUTION COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()