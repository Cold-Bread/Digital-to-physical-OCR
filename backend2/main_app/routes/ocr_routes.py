from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from enum import Enum
import requests
from main_app.models import OCRResponse

router = APIRouter()

# Update if your service uses a different port
PADDLE_OCR_URL = "http://localhost:8001/ocr"

class TextType(str, Enum):
    HANDWRITTEN = "handwritten"
    PRINTED = "printed"

async def process_ocr(url: str, image_data: bytes, filename: str, text_type: TextType):
    """Helper function to process OCR request"""
    try:
        response = requests.post(
            url,
            files={"file": (filename, image_data, "image/jpeg")},
            params={"text_type": text_type}
        )
        response.raise_for_status()
        result = response.json()
        print(f"OCR Response from {url}: {result}")  # Debug log
        return result.get('text', []) if isinstance(result, dict) else result
    except Exception as e:
        print(f"Error processing OCR at {url}: {e}")
        return []

@router.post("/process-image")
async def process_image(
    file: UploadFile = File(...),
    text_type: TextType = Query(TextType.PRINTED, description="Type of text to recognize")
):
    """Process image through PaddleOCR and return results"""
    try:
        contents = await file.read()
        
        # Process image through PaddleOCR
        ocr_result = await process_ocr(PADDLE_OCR_URL, contents, file.filename, text_type)
        
        if not ocr_result:
            raise HTTPException(
                status_code=422, 
                detail="Could not extract valid text from the image"
            )
        
        # Return results directly from PaddleOCR
        return OCRResponse(
            ocr1=ocr_result  # PaddleOCR results
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the image: {str(e)}"
        )

