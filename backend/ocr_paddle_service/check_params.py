
from backend.shared_utils.logging_config import get_logger
from paddleocr import PaddleOCR


logger = get_logger(__name__)
ocr = PaddleOCR()

# Log all attributes
logger.info("PaddleOCR Attributes:")
logger.info("--------------------")
for attr in dir(ocr):
    if not attr.startswith('_'):  # Skip private attributes
        try:
            value = getattr(ocr, attr)
            if not callable(value):  # Skip methods, only show parameters
                logger.info(f"{attr}: {value}")
        except Exception:
            pass
