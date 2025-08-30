import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from main_app.routes.ocr_routes import router as ocr_router
#from main_app.routes.main_routes import router as user_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    yield
    logger.info("Shutting down application...")

app = FastAPI(lifespan=lifespan)
app.include_router(ocr_router)

# Basic root endpoint/ health check
@app.get("/")
def read_root():
    return {"message": "OCR Service API"}
