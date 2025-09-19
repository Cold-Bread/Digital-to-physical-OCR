from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import requests
from shared_utils.types import TextType
from main_app.models import OCRResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Update if your service uses a different port
PADDLE_OCR_URL = "http://localhost:8001/ocr"

async def process_ocr(url: str, image_data: bytes, filename: str, text_type: TextType) -> list[str]:
    try:
        response = requests.post(
            url,
            files = {"file": (filename, image_data, "image/jpeg")},
            params = {"text_type": text_type}
        )
        response.raise_for_status()
        result = response.json()
        logger.error(f"OCR Response from {url}: {result}")
        return result.get('text', []) if isinstance(result, dict) else result
    except Exception as e:
        logger.error(f"Error processing OCR at {url}: {e}")
        return []


@router.post("/process-image")
async def process_image(
    file: UploadFile = File(...),
    text_type: TextType = Query(TextType.PRINTED, description = "Type of text to recognize")):
    try:
        contents = await file.read()
        
        paddle_ocr_result = await process_ocr(PADDLE_OCR_URL, contents, file.filename, text_type)
        
        if not paddle_ocr_result:
            raise HTTPException(
                status_code = 422, 
                detail = "Could not extract valid text from the image"
            )
        
        return OCRResponse(
            ocr1 = paddle_ocr_result
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"An error occurred while processing the image: {str(e)}"
        )
