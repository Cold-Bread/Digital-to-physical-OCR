from paddleocr import PaddleOCR
from pathlib import Path

ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Load model

image_path = r"C:\Users\Jacob\Downloads\imagetest.jpg"

# Check file exists
if not Path(image_path).exists():
    print(f"❌ Image not found: {image_path}")
else:
    print("Running OCR...")
    result = ocr.ocr(image_path, cls=True)

    # Print the recognized text
    for line in result[0]:
        text = line[1][0]
        print(f"✅ Recognized: {text}")