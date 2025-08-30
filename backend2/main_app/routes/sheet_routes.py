from fastapi import APIRouter, HTTPException
from typing import List
from ..config.sheets_config import read_sheet_range, update_sheet_range
from ..models import Patient

router = APIRouter()

@router.post("/box/{box_number}")
async def get_box_patients(box_number: str):
    """Get patients from Google Sheets based on box number"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Adjust the range based on your sheet structure - querying up to row 5000 to be safe
    range_name = "2025 Review!A2:G5000"  # Increased range to capture more rows
    logger.info(f"Attempting to read from range: {range_name}")
    
    values = read_sheet_range(range_name)
    
    if values is None:
        logger.error("Failed to read from Google Sheets - values is None")
        raise HTTPException(status_code=500, detail="Failed to read from Google Sheets")
    
    logger.info(f"Retrieved {len(values)} rows from Google Sheets")
    
    # Filter rows by box number and convert to Patient objects
    patients = []
    
    for i, row in enumerate(values):
        if not row:  # Skip empty rows
            continue
            
        sheet_box = str(row[0]).strip() if row[0] else ""
        if sheet_box.upper() == box_number.upper():
            try:
                # Pad the row with None values if it's not long enough
                padded_row = row + [None] * (7 - len(row)) if len(row) < 7 else row
                
                patient = Patient(
                    box_number=padded_row[0],     # Column A: Box Number
                    name=padded_row[1] or "",     # Column B: Name
                    dob=padded_row[2] or "",      # Column C: DOB
                    year_joined=int(padded_row[3] or 0),  # Column D: Year Joined
                    last_dos=int(padded_row[4] or 0),     # Column E: Last DOS
                    shred_year=int(padded_row[5] or 0),   # Column F: Shred Year
                    is_child_when_joined=bool(padded_row[6]) if padded_row[6] is not None else False  # Column G
                )
                patients.append(patient)
            except Exception as e:
                logger.error(f"Error processing row {i+2}: {e}")
                continue
    
    if not patients:
        raise HTTPException(status_code=404, detail="No patients found for this box number")
    
    return patients

@router.post("/update-records")
async def update_records(patients: List[Patient]):
    """Update Google Sheets with patient information"""
    # Convert patients to rows - order matches sheet columns
    values = [[
        p.box_number,     # Column A: Box Number
        p.name,          # Column B: Name
        p.dob,           # Column C: DOB
        p.year_joined,   # Column D: Year Joined
        p.last_dos,      # Column E: Last DOS
        p.shred_year,    # Column F: Shred Year
        True if p.is_child_when_joined else None  # Column G: Is Child When Joined (boolean or null)
    ] for p in patients]
    
    # Adjust the range based on your sheet structure
    range_name = f"2025 Review!A2:G{len(values) + 1}"
    success = update_sheet_range(range_name, values)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update records")
    
    return {"message": "Records updated successfully"}
