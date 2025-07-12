from fastapi import APIRouter
from models import Patient
from webapp.backend.crud import insert_patient

router = APIRouter()

# GET dummy route (for now)
@app.get("/patient/{patient_id}")
async def get_patient(patient_id: int):
    # Replace this with DB lookup
    return {"message": f"Fetching patient #{patient_id}"}

# POST route with validation using Patient model
@app.post("/patient/")
async def post_patient(patient: Patient):
    # This is where you'd send patient to be archived
    # You can now safely access patient.name, patient.dob, etc.
    return {"message": "Patient received", "patient": patient}
