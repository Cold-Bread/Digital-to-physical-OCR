from .ocr_routes import router as ocr_router
from .main_routes import router as user_router
__all__ = ["ocr_router", "user_router"]