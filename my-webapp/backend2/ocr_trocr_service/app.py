from fastapi import FastAPI, UploadFile, File
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import io

app = FastAPI()

# Load TrOCR model and processor once at startup
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

@app.post("/ocr")
async def run_trocr(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    pixel_values = processor(images=image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return {"text": text}
