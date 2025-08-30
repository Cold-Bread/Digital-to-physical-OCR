from fastapi import FastAPI, UploadFile, File, Query
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageEnhance, ImageOps
from enum import Enum
import io
import numpy as np

class TextType(str, Enum):
    HANDWRITTEN = "handwritten"
    PRINTED = "printed"

app = FastAPI()

# Initialize both models at startup
processors = {
    TextType.HANDWRITTEN: TrOCRProcessor.from_pretrained("microsoft/trocr-large-handwritten"),
    TextType.PRINTED: TrOCRProcessor.from_pretrained("microsoft/trocr-large-printed")
}

models = {
    TextType.HANDWRITTEN: VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-handwritten"),
    TextType.PRINTED: VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-printed")
}

def enhance_image(image):
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    enhanced = enhancer.enhance(2.0)
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(enhanced)
    enhanced = enhancer.enhance(1.5)
    
    # Enhance brightness
    enhancer = ImageEnhance.Brightness(enhanced)
    enhanced = enhancer.enhance(1.2)
    
    return enhanced

def extract_text_regions(image):
    # Convert to numpy array for processing (keeping RGB)
    img_array = np.array(image)
    
    # Calculate regions based on the image height
    regions = []
    height = img_array.shape[0]
    # Create overlapping regions to ensure we don't cut through text
    for i in range(0, height, height//6):  # Smaller steps for more overlap
        region_height = height//3
        start = max(0, i - region_height//4)  # Add overlap
        end = min(height, i + region_height)
        crop = image.crop((0, start, image.width, end))
        regions.append(crop)
    
    return regions

@app.post("/ocr")
async def run_trocr(
    file: UploadFile = File(...),
    text_type: TextType = Query(TextType.PRINTED, description="Type of text to recognize")
):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Get the appropriate model and processor
    processor = processors[text_type]
    model = models[text_type]
    
    try:
        # Enhance the image while keeping RGB format
        enhanced = enhance_image(image)
        
        # Extract potential text regions
        regions = extract_text_regions(enhanced)
        
        all_texts = []
        seen_texts = set()  # To avoid duplicates from overlapping regions
        
        for region in regions:
            try:
                # Ensure region is RGB
                if region.mode != "RGB":
                    region = region.convert("RGB")
                
                # Process region
                inputs = processor(images=region, return_tensors="pt")
                generated_ids = model.generate(inputs.pixel_values)
                text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                
                # Clean and deduplicate text
                text = text.strip()
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    if any(c in text for c in ['/', '-', '.']):
                        all_texts.append({"name": "", "dob": text})
                    else:
                        all_texts.append({"name": text, "dob": None})
            except Exception as e:
                print(f"Error processing region: {str(e)}")
                continue
        
        return {"text": all_texts}
    except Exception as e:
        print(f"Error in OCR process: {str(e)}")
        raise
