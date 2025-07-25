from fastapi import APIRouter
from models import Patient

router = APIRouter()

#look at response_model field to ensure errors aren't thrown and the patient id is added correctly

# GET dummy route (for now)
@router.get("/patient/{patient_id}")
async def get_patient(patient_id: int):
    # Replace this with DB lookup
    return {"message": f"Fetching patient #{patient_id}"}

# POST route with validation using Patient model
@router.post("/patient/", response_model=Patient)
async def post_patient(patient: Patient):
    # This is where you'd send patient to be archived
    # You can now safely access patient.name, patient.dob, etc.
    return {"message": "Patient received", "patient": patient}

