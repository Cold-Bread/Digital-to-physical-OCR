from fastapi import APIRouter, UploadFile, File, HTTPException
import requests

router = APIRouter()

# Update these if your services use different ports
PADDLE_OCR_URL = "http://localhost:8001/ocr"
TROCR_URL = "http://localhost:8002/ocr"


@router.post("/ocr/{engine}")
async def run_ocr(engine: str, file: UploadFile = File(...)):
    if engine not in ["paddle", "trocr"]:
        raise HTTPException(status_code=400, detail="Engine must be 'paddle' or 'trocr'.")

    try:
        service_url = PADDLE_OCR_URL if engine == "paddle" else TROCR_URL
        response = requests.post(
            service_url,
            files={"file": (file.filename, await file.read(), file.content_type)}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

