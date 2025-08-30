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

from typing import Dict, Any

@router.post("/update-records")
async def update_records(patients: List[Patient]):
    """Update Google Sheets with patient information"""
    import logging
    logger = logging.getLogger(__name__)
    
    # First, read all existing records
    range_name = "2025 Review!A2:G5000"  # Read all possible rows
    existing_values = read_sheet_range(range_name)
    
    if existing_values is None:
        raise HTTPException(status_code=500, detail="Failed to read from Google Sheets")

    # Create a map of box numbers and relative positions to row indices
    box_positions: Dict[str, list] = {}  # Map box numbers to lists of rows
    box_to_rows: Dict[str, Dict[int, int]] = {}  # Map box numbers and positions to sheet rows
    
    for i, row in enumerate(existing_values):
        if row and len(row) > 0 and row[0]:  # If row has a box number
            box_num = str(row[0]).strip().upper()
            if box_num not in box_positions:
                box_positions[box_num] = []
                box_to_rows[box_num] = {}
            
            # Store the position within the box
            position = len(box_positions[box_num])
            box_positions[box_num].append(i + 2)  # +2 for 1-based index and header
            box_to_rows[box_num][position] = i + 2
            
    # Prepare updates for each patient
    updates = []
    for i, patient in enumerate(patients):
        row_data = [
            patient.box_number,     # Column A: Box Number
            patient.name,          # Column B: Name
            patient.dob,           # Column C: DOB
            patient.year_joined,   # Column D: Year Joined
            patient.last_dos,      # Column E: Last DOS
            patient.shred_year,    # Column F: Shred Year
            True if patient.is_child_when_joined else None  # Column G: Is Child When Joined
        ]
        
        box_num = patient.box_number.strip().upper()
        if box_num in box_to_rows and i < len(box_to_rows[box_num]):
            # Get the row number for this position in the box
            row_num = box_to_rows[box_num][i]
            
            # Update existing row
            range_name = f"2025 Review!A{row_num}:G{row_num}"
            logger.info(f"Updating row {row_num} for patient {patient.name} in box {patient.box_number} at position {i}")
            success = update_sheet_range(range_name, [row_data])
            if not success:
                logger.error(f"Failed to update row {row_num} for patient {patient.name} in box {patient.box_number}")
                raise HTTPException(status_code=500, detail=f"Failed to update patient {patient.name} in box {patient.box_number}")
            updates.append(f"Updated {patient.name} in box {patient.box_number}")
        else:
            logger.error(f"Could not find row for patient {patient.name} at position {i} in box {patient.box_number}")
            raise HTTPException(
                status_code=404, 
                detail=f"Position {i} in box {patient.box_number} not found in sheet"
            )
    
    return {"message": f"Records updated successfully: {', '.join(updates)}"}
    
    return {"message": f"Records updated successfully: {', '.join(updates)}"}
    
    return {"message": "Records updated successfully"}
