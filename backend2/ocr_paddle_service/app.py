from fastapi import FastAPI, File, UploadFile, Query
from paddleocr import PaddleOCR
import numpy as np
import cv2
import logging
from shared_utils.types import TextType
from shared_utils.image_processing import enhance_image_cv2, classify_text, extract_text_regions

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

# Initialize OCR models with optimized parameters
ocr_models = {
    TextType.HANDWRITTEN: PaddleOCR(
        lang='en',
        det_db_box_thresh=0.55,  # Slightly lower to catch handwritten text
        det_db_unclip_ratio=2.0,  # Larger to connect handwritten strokes
        det_limit_side_len=1280,  # Larger size for better detail
        det_limit_type='max'
    ),
    TextType.PRINTED: PaddleOCR(
        lang='en',
        det_db_box_thresh=0.6,   # Higher for cleaner printed text detection
        det_db_unclip_ratio=1.5,  # Standard for printed text
        det_limit_side_len=1280,  # Larger size for better detail
        det_limit_type='max'
    )
}

@app.post("/ocr")
async def run_paddleocr(
    file: UploadFile = File(...),
    text_type: TextType = Query(TextType.PRINTED, description="Type of text to recognize")
):
    try:
        logger.info(f"Starting OCR process with text_type: {text_type}")
        logger.info(f"Processing file: {file.filename}")
        
        # Read the image file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("Failed to decode image")
            raise ValueError("Invalid image data")
        
        # Enhance image
        enhanced = enhance_image_cv2(image)
        
        # Save enhanced image for debugging
        debug_path = "debug_enhanced.png"
        cv2.imwrite(debug_path, enhanced)
        logger.info(f"Saved enhanced image to {debug_path}")
        
        # Split image into vertical slices
        regions = extract_text_regions(enhanced, method='vertical_slice')
        logger.info(f"Split image into {len(regions)} vertical regions")
        
        # Save regions for debugging
        for i, region in enumerate(regions):
            cv2.imwrite(f"debug_region_{i}.png", region)
        
        # Get the appropriate OCR model
        ocr = ocr_models[text_type]
        
        # Process each region
        all_results = []
        for i, region in enumerate(regions):
            logger.info(f"Processing region {i}")
            result = ocr.ocr(region)
            if result:
                all_results.extend(result)
        
        # Save original image for comparison
        cv2.imwrite("debug_original.png", image)
        logger.info("Saved original image for comparison")
        
        # Log image properties
        logger.info(f"Image properties - Shape: {enhanced.shape}, Type: {enhanced.dtype}, Min: {enhanced.min()}, Max: {enhanced.max()}")
        
        # Attempt OCR
        logger.info("Starting OCR detection")
        result = ocr.ocr(enhanced)
        logger.info(f"Raw OCR result: {result}")
        
        # Process results
        text_results = []
        
        if result and isinstance(result, list):
            # Get the first result (usually there's only one page)
            page_result = result[0]
            
            if isinstance(page_result, dict) and 'rec_texts' in page_result and 'rec_scores' in page_result:
                texts = page_result['rec_texts']
                scores = page_result['rec_scores']
                
                logger.info(f"Found {len(texts)} text segments")
                
                # First pass: classify all texts
                classified_results = []
                for text, score in zip(texts, scores):
                    try:
                        if not text or not isinstance(text, str):
                            continue
                            
                        text = text.strip()
                        if len(text) <= 1 and not text.isdigit():
                            continue
                            
                        text = ' '.join(text.split())  # Normalize whitespace
                        result = classify_text(text)
                        if result:
                            result['score'] = score  # Store confidence score
                            classified_results.append(result)
                            logger.info(f"Detected text: {result} (confidence: {score:.2f})")
                            
                    except Exception as e:
                        logger.error(f"Error processing text '{text}': {str(e)}")
                        continue
                
                # Second pass: combine stacked name/DOB pairs
                text_results = []
                i = 0
                while i < len(classified_results):
                    current = classified_results[i]
                    
                    # Look ahead for potential DOB to combine with name
                    if (i + 1 < len(classified_results) and
                        current['name'] and not current['dob'] and  # Current has name but no DOB
                        not classified_results[i + 1]['name'] and classified_results[i + 1]['dob']):  # Next has DOB but no name
                        
                        # Combine them
                        current['dob'] = classified_results[i + 1]['dob']
                        text_results.append(current)
                        i += 2  # Skip the DOB we just used
                        logger.info(f"Combined stacked entries: {current}")
                        
                    else:
                        text_results.append(current)
                        i += 1
        
        logger.info(f"Final results: {text_results}")
        return text_results
        
    except Exception as e:
        logger.error(f"Error in OCR process: {str(e)}")
        raise