import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from routes.main_routes import router as user_router
from routes.ocr_routes import router as ocr_router
from models import Patient
from crud import insert_patient
from database import create_table

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Update these if your services use different ports
PADDLE_OCR_URL = "http://localhost:8001/ocr"
TROCR_URL = "http://localhost:8002/ocr"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    create_table()  # Ensure db file exists at startup

    

    yield
    logger.info("Shutting down application...")

app = FastAPI(lifespan=lifespan)

app.include_router(ocr_router)
app.include_router(user_router)

# Basic root endpoint/ health check
@app.get("/get_patient")
def read_root():
    return {"message": "Welcome to the API"}

@app.post("/add_patient")
def add_patient(patient: Patient):
    return insert_patient(patient)
