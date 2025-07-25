from fastapi import FastAPI, UploadFile, File
from paddleocr import PaddleOCR
import cv2
import numpy as np

app = FastAPI()

# Load PaddleOCR model once at startup
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # set lang='ch' if Chinese OCR needed

@app.post("/ocr")
async def run_paddleocr(file: UploadFile = File(...)):
    image_bytes = await file.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    result = ocr.ocr(image, cls=True)
    extracted_text = "\n".join([line[1][0] for line in result[0]])

    return {"text": extracted_text}
