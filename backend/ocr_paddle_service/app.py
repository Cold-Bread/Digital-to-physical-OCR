from fastapi import FastAPI, File, UploadFile, Query
from paddleocr import PaddleOCR
import numpy as np
import cv2
import logging
from shared_utils.types import TextType
from shared_utils.image_processing import enhance_image_cv2, classify_text
from models.model_config import get_model_config, list_available_models
from typing import Optional

# Configure logging to both file and console
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

# File handler
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'paddle_ocr.log'),
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# Add both handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

app = FastAPI()

# Initialize OCR models with configurable model support
def create_ocr_models(model_name: Optional[str] = None):
    """Create OCR models with optional custom model specification"""
    if model_name and model_name != "default":
        # Use specified custom model for both text types
        try:
            config = get_model_config(model_name)
            params = config.get_paddle_params()
            logger.info(f"Initializing custom model '{config.name}' with params: {params}")
            custom_ocr = PaddleOCR(**params)
            logger.info(f"Successfully initialized custom OCR model: {config.name}")
            return {
                TextType.HANDWRITTEN: custom_ocr,
                TextType.PRINTED: custom_ocr
            }
        except Exception as e:
            logger.error(f"Failed to load custom model '{model_name}': {e}")
            logger.info("Falling back to default models")
    
    # Use default models
    handwritten_config = get_model_config("default_handwritten")
    printed_config = get_model_config("default_printed")
    
    logger.info("Using default PaddleOCR models")
    return {
        TextType.HANDWRITTEN: PaddleOCR(**handwritten_config.get_paddle_params()),
        TextType.PRINTED: PaddleOCR(**printed_config.get_paddle_params())
    }

# Global OCR models - can be switched at runtime
ocr_models = create_ocr_models()
current_model_name = "default"

@app.get("/models")
async def get_available_models():
    """Get list of available OCR models"""
    return {
        "current_model": current_model_name,
        "available_models": list_available_models()
    }

@app.get("/switch_model")
async def switch_model(model_name: str = Query(..., description="Name of the model to switch to")):
    """Switch to a different OCR model"""
    global ocr_models, current_model_name
    
    try:
        if model_name == "default":
            ocr_models = create_ocr_models()
            current_model_name = "default"
            return {"status": "success", "message": f"Switched to default models"}
        else:
            ocr_models = create_ocr_models(model_name)
            current_model_name = model_name
            return {"status": "success", "message": f"Switched to model: {model_name}"}
    except Exception as e:
        logger.error(f"Failed to switch to model '{model_name}': {e}")
        return {"status": "error", "message": f"Failed to switch model: {str(e)}"}

@app.post("/ocr")
async def run_paddleocr(
    file: UploadFile = File(...),
    text_type: TextType = Query(TextType.PRINTED, description="Type of text to recognize"),
    model_name: Optional[str] = Query(None, description="Optional: Use specific model for this request")
):
    try:
        logger.info(f"Starting OCR process with text_type: {text_type}")
        logger.info(f"Processing file: {file.filename}")
        
        # Use specified model for this request or fall back to current global model
        if model_name and model_name != current_model_name:
            logger.info(f"Using temporary model: {model_name}")
            temp_models = create_ocr_models(model_name)
            ocr = temp_models[text_type]
        else:
            logger.info(f"Using current model: {current_model_name}")
            ocr = ocr_models[text_type]
        
        # Read the image file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("Failed to decode image")
            raise ValueError("Invalid image data")
        
        # Enhance image
        enhanced = enhance_image_cv2(image)
        
        # Log image properties for debugging
        logger.info(f"Image properties - Shape: {enhanced.shape}, Type: {enhanced.dtype}")
        
        # Attempt OCR
        logger.info("Starting OCR detection")
        result = ocr.ocr(enhanced)
        
        logger.info(f"Raw OCR result: {result}")
        
        # Process results from PaddleOCR
        # PaddleOCR returns: [{'rec_texts': [...], 'rec_scores': [...], ...}]
        text_results = []
        
        if result and result[0]:
            page_result = result[0]
            if isinstance(page_result, dict) and 'rec_texts' in page_result and 'rec_scores' in page_result:
                texts = page_result['rec_texts']
                scores = page_result['rec_scores']
                
                logger.info(f"Found {len(texts)} text segments in OCR result")
                
                # First pass: classify all texts
                classified_results = []
                for text, score in zip(texts, scores):
                    try:
                        # Skip very low confidence results
                        if score < 0.3:  # Lower minimum confidence threshold
                            continue
                            
                        if not text or not isinstance(text, str):
                            continue
                            
                        text = text.strip()
                        if len(text) <= 1 and not text.isdigit():
                            continue
                            
                        text = ' '.join(text.split())  # Normalize whitespace
                        classification_result = classify_text(text)
                        if classification_result:
                            classification_result['score'] = score  # Store confidence score
                            classified_results.append(classification_result)
                            logger.info(f"Detected text: {classification_result} (confidence: {score:.2f})")
                            
                    except Exception as e:
                        logger.error(f"Error processing text '{text}': {str(e)}")
                        continue
                
                # Second pass: combine stacked name/DOB pairs
                i = 0
                combined_results = []
                while i < len(classified_results):
                    current = classified_results[i]
                    next_result = classified_results[i + 1] if i + 1 < len(classified_results) else None
                    
                    # Check if current has name but no DOB and next has only DOB
                    if (next_result and
                        current.get('name') and not current.get('dob') and  # Current has name but no DOB
                        not next_result.get('name') and next_result.get('dob')):  # Next has DOB but no name
                        
                        # Combine them, preserving the higher score
                        current['dob'] = next_result['dob']
                        current['score'] = max(current.get('score', 0), next_result.get('score', 0))
                        combined_results.append(current)
                        i += 2  # Skip the DOB entry we just used
                        logger.info(f"Combined stacked entries: {current}")
                    else:
                        combined_results.append(current)
                        i += 1
                
                text_results.extend(combined_results)
            else:
                logger.warning(f"Unexpected PaddleOCR result format: {type(page_result)}")
        
        logger.info(f"Final results: {text_results}")
        return text_results
        
    except Exception as e:
        logger.error(f"Error in OCR process: {str(e)}")
        raise