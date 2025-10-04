"""
Model configuration for PaddleOCR models.
This file defines available models and their configurations.
"""

from typing import Dict, Optional
from pathlib import Path

MODELS_DIR = Path(__file__).parent

class ModelConfig:
    """Configuration class for PaddleOCR models"""
    
    def __init__(self, 
                 name: str,
                 model_path: Optional[str] = None,
                 text_recognition_model_dir: Optional[str] = None,
                 text_recognition_model_name: Optional[str] = None,
                 description: str = "",
                 **paddle_params):
        self.name = name
        self.model_path = model_path
        self.text_recognition_model_dir = text_recognition_model_dir
        self.text_recognition_model_name = text_recognition_model_name
        self.description = description
        self.paddle_params = paddle_params
    
    def get_paddle_params(self) -> dict:
        """Get parameters for PaddleOCR initialization"""
        params = self.paddle_params.copy()
        if self.text_recognition_model_dir:
            params['text_recognition_model_dir'] = str(self.text_recognition_model_dir)
        # Note: text_recognition_model_name is only for registered models, not custom ones
        return params

AVAILABLE_MODELS = {
    "default_handwritten": ModelConfig(
        name="Default Handwritten",
        description="Default PaddleOCR model optimized for handwritten text",
        lang='en',
        det_db_box_thresh=0.3,
        det_db_unclip_ratio=2.0,
        det_limit_side_len=2048,
        det_limit_type='max',
        use_angle_cls=True,
        rec_batch_num=6
    ),
    
    "default_printed": ModelConfig(
        name="Default Printed",
        description="Default PaddleOCR model optimized for printed text",
        lang='en',
        det_db_box_thresh=0.6,
        det_db_unclip_ratio=1.5,
        det_limit_side_len=1280,
        det_limit_type='max'
    ),
    
    "custom_trained_v3": ModelConfig(
        name="Custom Trained v3", 
        description="Custom SVTR model with 70%+ accuracy (using en_PP-OCRv5_mobile_rec slot)",
        text_recognition_model_name="en_PP-OCRv5_mobile_rec",  # Use registered model slot
        lang='en',
        det_db_box_thresh=0.4,
        det_db_unclip_ratio=1.8,
        det_limit_side_len=1600,
        det_limit_type='max',
        use_angle_cls=True,
        rec_batch_num=6
    ),
}

def get_model_config(model_name: str) -> ModelConfig:
    """Get configuration for a specific model"""
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"Model '{model_name}' not found. Available models: {list(AVAILABLE_MODELS.keys())}")
    return AVAILABLE_MODELS[model_name]

def list_available_models() -> Dict[str, str]:
    """List all available models with their descriptions"""
    return {name: config.description for name, config in AVAILABLE_MODELS.items()}