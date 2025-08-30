from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from enum import Enum
import requests
import asyncio
from main_app.models import OCRResponse

router = APIRouter()

# Update these if your services use different ports
PADDLE_OCR_URL = "http://localhost:8001/ocr"
TROCR_URL = "http://localhost:8002/ocr"
# TESSERACT_URL = "http://localhost:8003/ocr"  # Temporarily disabled until service is set up

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
    """Process image through all OCR engines and return combined results"""
    try:
        contents = await file.read()
        
        # Process image through available OCR engines concurrently
        tasks = [
            process_ocr(PADDLE_OCR_URL, contents, file.filename, text_type),
            process_ocr(TROCR_URL, contents, file.filename, text_type),
            # process_ocr(TESSERACT_URL, contents, file.filename)  # Temporarily disabled
        ]
        
        ocr_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any errors from the results
        valid_results = [r for r in ocr_results if not isinstance(r, Exception)]
        
        if not valid_results:
            raise HTTPException(
                status_code=500, 
                detail="All OCR services failed to process the image"
            )
        
        # Process results to increase confidence
        final_result = process_ocr_results(valid_results)
        
        if not final_result:
            raise HTTPException(
                status_code=422, 
                detail="Could not extract valid text from the image"
            )
        
        # Transform raw results into OCRResult format
        formatted_results = []
        for result in valid_results:
            if isinstance(result, list) and result and isinstance(result[0], str):
                # For PaddleOCR - join characters into a single string
                formatted_results.append([{"name": "".join(result), "dob": None}])
            elif isinstance(result, str):
                # For TrOCR - wrap string in proper structure
                formatted_results.append([{"name": result, "dob": None}])
            else:
                # For any result already in correct format
                formatted_results.append(result if isinstance(result, list) else [])
        
        return OCRResponse(
            ocr1=formatted_results[0] if len(formatted_results) > 0 else [],
            ocr2=formatted_results[1] if len(formatted_results) > 1 else [],
            ocr3=formatted_results[2] if len(formatted_results) > 2 else [],
            finalResult=final_result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the image: {str(e)}"
        )

def process_ocr_results(results):
    """
    Process OCR results to increase confidence in the final result
    This is where you would implement your logic to compare and validate results
    """
    print(f"Processing OCR results: {results}")  # Debug log
    
    # Create a default OCR result structure
    default_result = {"name": "", "dob": None}
    
    # Find the first non-empty result
    for result in results:
        if result and len(result) > 0:
            if isinstance(result, list) and isinstance(result[0], str):
                # For PaddleOCR results - join characters
                return {"name": "".join(result), "dob": None}
            elif isinstance(result, str):
                # For TrOCR results - use string directly
                return {"name": result, "dob": None}
            
    return default_result

