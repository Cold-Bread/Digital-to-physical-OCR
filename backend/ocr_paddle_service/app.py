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

def process_ocr_result(result, model_name: str) -> list:
    """Process OCR result from PaddleOCR and return classified text results"""
    text_results = []
    
    if result and result[0]:
        page_result = result[0]
        if isinstance(page_result, dict) and 'rec_texts' in page_result and 'rec_scores' in page_result:
            texts = page_result['rec_texts']
            scores = page_result['rec_scores']
            
            logger.info(f"Found {len(texts)} text segments in {model_name} OCR result")
            
            # First pass: classify all texts
            classified_results = []
            for text, score in zip(texts, scores):
                try:
                    # Skip very low confidence results - be more lenient with custom model
                    min_confidence = 0.25 if model_name == "custom_trained_v3" else 0.3
                    if score < min_confidence:
                        continue
                        
                    if not text or not isinstance(text, str):
                        continue
                        
                    text = text.strip()
                    if len(text) <= 1 and not text.isdigit():
                        continue
                        
                    text = ' '.join(text.split())  # Normalize whitespace
                    classification_result = classify_text(text)
                    if classification_result:
                        classification_result['score'] = score
                        classification_result['source_model'] = model_name
                        classified_results.append(classification_result)
                        logger.info(f"Detected text ({model_name}): {classification_result} (confidence: {score:.2f})")
                        
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
                    logger.info(f"Combined stacked entries ({model_name}): {current}")
                else:
                    combined_results.append(current)
                    i += 1
            
            text_results.extend(combined_results)
        else:
            logger.warning(f"Unexpected PaddleOCR result format from {model_name}: {type(page_result)}")
    
    return text_results

def should_use_fallback(custom_results: list, use_fallback_flag: bool) -> bool:
    """Determine if we should use fallback model based on custom model results quality"""
    if not use_fallback_flag:
        logger.info("Fallback disabled by user parameter")
        return False
    
    if not custom_results:
        logger.info("No results from custom model, using fallback")
        return True
    
    # Calculate quality metrics
    total_results = len(custom_results)
    complete_entries = sum(1 for r in custom_results if r.get('name') and r.get('dob'))
    high_confidence_results = sum(1 for r in custom_results if r.get('score', 0) > 0.6)
    very_low_confidence_results = sum(1 for r in custom_results if r.get('score', 0) < 0.3)
    avg_confidence = sum(r.get('score', 0) for r in custom_results) / total_results if total_results > 0 else 0
    
    logger.info(f"Custom model quality metrics: {total_results} total, {complete_entries} complete, {high_confidence_results} high confidence, {very_low_confidence_results} very low confidence, {avg_confidence:.2f} avg confidence")
    
    # More conservative thresholds - only use fallback if custom model is really struggling:
    # 1. Very few results (less than 1) - essentially no results
    # 2. Very low average confidence (less than 0.35)
    # 3. Most results are very low confidence (more than 60% under 0.3)
    # 4. No complete entries at all AND low average confidence
    should_fallback = (
        total_results == 0 or
        avg_confidence < 0.35 or
        (very_low_confidence_results / total_results) > 0.6 if total_results > 0 else True or
        (complete_entries == 0 and avg_confidence < 0.45)
    )
    
    logger.info(f"Should use fallback: {should_fallback}")
    return should_fallback

def merge_ocr_results(custom_results: list, fallback_results: list) -> list:
    """Intelligently merge results from custom and fallback models"""
    if not fallback_results:
        logger.info("No fallback results to merge, returning custom results")
        return custom_results
    
    if not custom_results:
        logger.info("No custom results, returning fallback results")
        return fallback_results
    
    logger.info(f"Merging {len(custom_results)} custom results with {len(fallback_results)} fallback results")
    
    # Strategy: Use custom results as base, fill gaps with fallback results
    merged = []
    
    # Add all custom results first
    for custom_result in custom_results:
        merged.append(custom_result)
    
    # Add fallback results that don't duplicate custom results
    for fallback_result in fallback_results:
        fallback_name = (fallback_result.get('name') or '').lower().strip()
        fallback_dob = (fallback_result.get('dob') or '').strip()
        
        # Check if this result is already covered by custom results
        is_duplicate = False
        for custom_result in custom_results:
            custom_name = (custom_result.get('name') or '').lower().strip()
            custom_dob = (custom_result.get('dob') or '').strip()
            
            # Consider it a duplicate if names are very similar or DOBs match
            if (
                (fallback_name and custom_name and are_names_similar(fallback_name, custom_name)) or
                (fallback_dob and custom_dob and fallback_dob == custom_dob)
            ):
                is_duplicate = True
                break
        
        if not is_duplicate:
            # Mark as coming from fallback model
            fallback_result['source_model'] = 'fallback'
            merged.append(fallback_result)
            logger.info(f"Added unique fallback result: {fallback_result}")
    
    logger.info(f"Final merged results count: {len(merged)}")
    return merged

def are_names_similar(name1: str, name2: str, threshold: float = 0.8) -> bool:
    """Check if two names are similar using simple string comparison"""
    if not name1 or not name2:
        return False
    
    # Ensure we have strings and handle None values
    name1 = str(name1) if name1 is not None else ""
    name2 = str(name2) if name2 is not None else ""
    
    if not name1.strip() or not name2.strip():
        return False
    
    # Simple similarity check - you could use more sophisticated algorithms
    name1_words = set(name1.lower().split())
    name2_words = set(name2.lower().split())
    
    if not name1_words or not name2_words:
        return False
    
    # Jaccard similarity
    intersection = len(name1_words.intersection(name2_words))
    union = len(name1_words.union(name2_words))
    
    similarity = intersection / union if union > 0 else 0
    return similarity >= threshold

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
    model_name: Optional[str] = Query(None, description="Optional: Use specific model for this request"),
    use_fallback: bool = Query(True, description="Use fallback to default model if custom model results are poor")
):
    try:
        logger.info(f"Starting OCR process with text_type: {text_type}")
        logger.info(f"Processing file: {file.filename}")
        
        # Read the image file once
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("Failed to decode image")
            raise ValueError("Invalid image data")
        
        # Enhance image
        enhanced = enhance_image_cv2(image)
        logger.info(f"Image properties - Shape: {enhanced.shape}, Type: {enhanced.dtype}")
        
        # Step 1: Try custom_trained_v3 model first
        custom_results = []
        fallback_results = []
        
        try:
            logger.info("Step 1: Trying custom_trained_v3 model")
            custom_models = create_ocr_models("custom_trained_v3")
            custom_ocr = custom_models[text_type]
            custom_result = custom_ocr.ocr(enhanced)
            logger.info(f"Custom model raw result: {custom_result}")
            custom_results = process_ocr_result(custom_result, "custom_trained_v3")
            logger.info(f"Custom model processed results: {custom_results}")
        except Exception as e:
            logger.error(f"Error with custom model: {e}")
            custom_results = []
        
        # Step 2: Evaluate custom model results quality
        needs_fallback = should_use_fallback(custom_results, use_fallback)
        
        if needs_fallback:
            logger.info("Step 2: Custom model results insufficient, trying default model")
            try:
                # Use specified model for this request or fall back to default
                if model_name and model_name not in ["custom_trained_v3", current_model_name]:
                    logger.info(f"Using specified fallback model: {model_name}")
                    temp_models = create_ocr_models(model_name)
                    fallback_ocr = temp_models[text_type]
                else:
                    logger.info("Using default model for fallback")
                    default_models = create_ocr_models("default")
                    fallback_ocr = default_models[text_type]
                
                fallback_result = fallback_ocr.ocr(enhanced)
                logger.info(f"Fallback model raw result: {fallback_result}")
                fallback_results = process_ocr_result(fallback_result, "default")
                logger.info(f"Fallback model processed results: {fallback_results}")
            except Exception as e:
                logger.error(f"Error with fallback model: {e}")
                fallback_results = []
        
        # Step 3: Merge results intelligently
        final_results = merge_ocr_results(custom_results, fallback_results)
        
        logger.info(f"Final merged results: {final_results}")
        return final_results
        
    except Exception as e:
        logger.error(f"Error in OCR process: {str(e)}")
        raise