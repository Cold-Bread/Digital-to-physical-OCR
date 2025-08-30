from fastapi import APIRouter, UploadFile, File, HTTPException
import requests
import asyncio
from typing import List
from ..models import OCRResponse, Patient, BoxRequest
from ..database import get_patients_by_box, update_excel_records

router = APIRouter()

# Update these if your services use different ports
PADDLE_OCR_URL = "http://localhost:8001/ocr"
TROCR_URL = "http://localhost:8002/ocr"
TESSERACT_URL = "http://localhost:8003/ocr"  # Add third OCR service

async def process_ocr(url: str, image_data: bytes, filename: str):
    """Helper function to process OCR request"""
    try:
        response = requests.post(
            url,
            files={"file": (filename, image_data, "image/jpeg")}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error processing OCR at {url}: {e}")
        return []

@router.get("/box/{box_number}")
async def get_box_patients(box_number: str):
    """Get patients from Excel sheet based on box number"""
    patients = get_patients_by_box(box_number)
    if not patients:
        raise HTTPException(status_code=404, detail="No patients found for this box number")
    return patients

@router.get("/process-image")
async def process_image(file: UploadFile = File(...)):
    """Process image through all OCR engines and return combined results"""
    contents = await file.read()
    
    # Process image through all OCR engines concurrently
    tasks = [
        process_ocr(PADDLE_OCR_URL, contents, file.filename),
        process_ocr(TROCR_URL, contents, file.filename),
        process_ocr(TESSERACT_URL, contents, file.filename)
    ]
    
    ocr_results = await asyncio.gather(*tasks)
    
    # Process results to increase confidence
    final_result = process_ocr_results(ocr_results)
    
    return OCRResponse(
        ocr1=ocr_results[0],
        ocr2=ocr_results[1],
        ocr3=ocr_results[2],
        finalResult=final_result
    )

def process_ocr_results(results):
    """
    Process OCR results to increase confidence in the final result
    This is where you would implement your logic to compare and validate results
    """
    # TODO: Implement your confidence-increasing logic here
    # For now, we'll just return the first non-empty result
    for result in results:
        if result and len(result) > 0:
            return result[0]
    return None

