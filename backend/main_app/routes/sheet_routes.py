
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from ..config.sheets_config import read_sheet_range, update_sheet_range, batch_update_sheet_ranges
from ..models import Patient
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()

# Constants
SHEET_RANGE = "2025 Review!A2:G5000"  # Adjust as needed

@router.api_route("/box/{box_number}", methods=["GET", "POST"])
async def get_box_patients(box_number: str) -> List[Patient]:
    """Get patients from Google Sheets based on box number"""
    logger.info(f"📦 Received request for box: {box_number}")
    logger.info(f"Attempting to read from range: {SHEET_RANGE}")
    values = read_sheet_range(SHEET_RANGE)
    if values is None:
        logger.error("Failed to read from Google Sheets - values is None")
        raise HTTPException(status_code=500, detail="Failed to read from Google Sheets")
    logger.info(f"Retrieved {len(values)} rows from Google Sheets")
    patients: List[Patient] = []
    for i, row in enumerate(values):
        if not row:
            continue
        sheet_box = str(row[0]).strip() if row[0] else ""
        if sheet_box.upper() == box_number.upper():
            try:
                padded_row = row + [None] * (7 - len(row)) if len(row) < 7 else row
                patient = Patient(
                    box_number = padded_row[0] or "",
                    name = padded_row[1] or "",
                    dob = padded_row[2] or "",
                    year_joined = int(padded_row[3] or 0),
                    last_dos = int(padded_row[4] or 0),
                    shred_year = int(padded_row[5] or 0),
                    is_child_when_joined = bool(padded_row[6]) if padded_row[6] is not None else False
                )
                patients.append(patient)
            except Exception as e:
                logger.error(f"Error processing row {i+2}: {e}")
                continue
    if not patients:
        logger.warning(f"No patients found for box number: {box_number}")
        raise HTTPException(status_code = 404, detail="No patients found for this box number")
    return patients


@router.post("/update-records")
async def update_records(patients: List[Patient]) -> dict:
    if not patients:
        logger.warning("No patients provided for update.")
        raise HTTPException(status_code = 400, detail="No patients provided for update.")
    
    existing_values = read_sheet_range(SHEET_RANGE)
    if existing_values is None:
        logger.error("Failed to read from Google Sheets")
        raise HTTPException(status_code = 500, detail="Failed to read from Google Sheets")
    
    # Map (box_number, position) to row index
    row_lookup: Dict[tuple, int] = {}
    box_counts: Dict[str, int] = {}
    for i, row in enumerate(existing_values):
        if row and row[0]:
            box_num = str(row[0]).strip().upper()
            pos = box_counts.get(box_num, 0)
            row_lookup[(box_num, pos)] = i + 2  # 1-based index, +1 for header
            box_counts[box_num] = pos + 1
    # OPTIMIZATION: Prepare batch update data instead of individual updates
    batch_data = []
    updates = []
    box_input_counts: Dict[str, int] = {}
    start_time = time.time()
    
    for patient in patients:
        box_num = patient.box_number.strip().upper()
        pos = box_input_counts.get(box_num, 0)
        key = (box_num, pos)
        row_num = row_lookup.get(key)
        
        if not row_num:
            logger.error(f"Could not find row for patient {patient.name} at position {pos} in box {patient.box_number}")
            raise HTTPException(
                status_code = 404,
                detail = f"Position {pos} in box {patient.box_number} not found in sheet"
            )
        
        row_data = [
            patient.box_number,
            patient.name,
            patient.dob,
            patient.year_joined,
            patient.last_dos,
            patient.shred_year,
            True if patient.is_child_when_joined else None
        ]
        
        # Add to batch instead of individual update
        batch_data.append({
            'range': f"2025 Review!A{row_num}:G{row_num}",
            'values': [row_data]
        })
        
        updates.append(f"Updated {patient.name} in box {patient.box_number}")
        box_input_counts[box_num] = pos + 1
    
    # OPTIMIZATION: Single batch update API call
    logger.info(f"Starting batch update for {len(batch_data)} records")
    batch_result = batch_update_sheet_ranges(batch_data)
    
    if not batch_result['success']:
        logger.error(f"Batch update failed: {batch_result.get('error', 'Unknown error')}")
        raise HTTPException(status_code = 500, detail=f"Failed to update records: {batch_result.get('error', 'Unknown error')}")
    
    total_time = time.time() - start_time
    logger.info(f"Batch update completed in {total_time:.2f}s")
    
    # OPTIMIZATION: Return updated patients to avoid frontend refresh
    return {
        "message": f"Records updated successfully: {', '.join(updates)}",
        "updated_patients": patients,
        "performance": {
            "total_time": f"{total_time:.2f}s",
            "rows_updated": batch_result.get('updated_rows', 0),
            "cells_updated": batch_result.get('updated_cells', 0)
        }
    }