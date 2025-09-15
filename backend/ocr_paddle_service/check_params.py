from paddleocr import PaddleOCR
import pprint

# Create an instance
ocr = PaddleOCR()

# Print all attributes
print("PaddleOCR Attributes:")
print("--------------------")
for attr in dir(ocr):
    if not attr.startswith('_'):  # Skip private attributes
        try:
            value = getattr(ocr, attr)
            if not callable(value):  # Skip methods, only show parameters
                print(f"{attr}: {value}")
        except:
            pass
