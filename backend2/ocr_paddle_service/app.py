from fastapi import FastAPI, File, UploadFile, Query
from paddleocr import PaddleOCR
import numpy as np
import cv2
from enum import Enum

class TextType(str, Enum):
    HANDWRITTEN = "handwritten"
    PRINTED = "printed"

app = FastAPI()

# Initialize both OCR models
ocr_models = {
    TextType.HANDWRITTEN: PaddleOCR(
        use_angle_cls=True,
        lang='en',
        det_limit_side_len=2560,
        det_db_thresh=0.3,  # Lower threshold for handwritten text
    ),
    TextType.PRINTED: PaddleOCR(
        use_angle_cls=True,
        lang='en',
        det_limit_side_len=2560,
        det_db_thresh=0.5,  # Higher threshold for printed text
    )
}

def enhance_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(gray)
    
    # Add thresholding for better text extraction
    _, thresh = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Convert back to BGR for PaddleOCR
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

@app.post("/ocr")
async def run_paddleocr(
    file: UploadFile = File(...),
    text_type: TextType = Query(TextType.PRINTED, description="Type of text to recognize")
):
    # Read the image file
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Enhance image
    enhanced = enhance_image(image)
    
    # Get the appropriate OCR model
    ocr = ocr_models[text_type]
    
    # Run OCR with appropriate confidence threshold
    result = ocr.ocr(enhanced)  # cls parameter is no longer needed, handled by use_angle_cls
    confidence_threshold = 0.5 if text_type == TextType.HANDWRITTEN else 0.65
    
    # Process results with confidence filtering
    text_results = []
    if result:
        for line in result:
            for item in line:
                # PaddleOCR returns [points, (text, confidence)] for each text box
                try:
                    text = item[1][0]  # Get text
                    confidence = item[1][1]  # Get confidence score
                    
                    if confidence > confidence_threshold:
                        # Check if text looks like a date
                        if any(c in text for c in ['/', '-', '.']):
                            text_results.append({"name": "", "dob": text})
                        else:
                            text_results.append({"name": text, "dob": None})
                except (IndexError, TypeError) as e:
                    print(f"Error processing item {item}: {str(e)}")
                    continue
    
    return {"text": text_results}
