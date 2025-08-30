from fastapi import APIRouter, HTTPException
from typing import List
from ..config.sheets_config import read_sheet_range, update_sheet_range
from ..models import Patient

router = APIRouter()

@router.get("/patients/{box_number}")
async def get_patients_by_box(box_number: str):
    """Get patients from Google Sheets based on box number"""
    # Adjust the range based on your sheet structure
    range_name = f"Sheet1!A2:G"  # Assuming headers are in row 1
    values = read_sheet_range(range_name)
    
    if values is None:
        raise HTTPException(status_code=500, detail="Failed to read from Google Sheets")
    
    # Filter rows by box number and convert to Patient objects
    patients = []
    for row in values:
        if len(row) >= 7 and row[6].upper() == box_number.upper():  # Assuming box_number is in column G
            patient = Patient(
                name=row[0],
                dob=row[1],
                year_joined=int(row[2]),
                last_dos=int(row[3]),
                shred_year=int(row[4]),
                is_child_when_joined=int(row[5]),
                box_number=row[6]
            )
            patients.append(patient)
    
    if not patients:
        raise HTTPException(status_code=404, detail="No patients found for this box number")
    
    return patients

@router.post("/update-records")
async def update_records(patients: List[Patient]):
    """Update Google Sheets with patient information"""
    # Convert patients to rows
    values = [[
        p.name,
        p.dob,
        p.year_joined,
        p.last_dos,
        p.shred_year,
        p.is_child_when_joined,
        p.box_number
    ] for p in patients]
    
    # Adjust the range based on your sheet structure
    range_name = f"Sheet1!A2:G{len(values) + 1}"
    success = update_sheet_range(range_name, values)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update records")
    
    return {"message": "Records updated successfully"}
