import pandas as pd
from typing import List
from main_app.models import Patient

EXCEL_PATH = "path/to/your/excel/file.xlsx"  # Update this with your Excel file path

def get_patients_by_box(box_number: str) -> List[Patient]:
    """
    Retrieve patient records from Excel sheet based on box number
    """
    try:
        # Read Excel file
        df = pd.read_excel(EXCEL_PATH)
        
        # Filter by box number (case insensitive)
        box_df = df[df['box_number'].str.upper() == box_number.upper()]
        
        # Convert DataFrame rows to Patient objects
        patients = []
        for _, row in box_df.iterrows():
            patient = Patient(
                name=row['Patient Name'],
                dob=row['DOB'],
                year_joined=row['Year Joined'],
                last_dos=row['Last DOS'],
                shred_year=row['Shred Year'],
                is_child_when_joined=row['IsChildWhenJoined'],
                box_number=row['box_number']
            )
            patients.append(patient)
        
        return patients
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def update_excel_records(patients: List[Patient]) -> bool:
    """
    Update Excel records with new patient information
    """
    try:
        df = pd.read_excel(EXCEL_PATH)
        
        for patient in patients:
            # Find matching record
            mask = (df['Patient Name'] == patient.name) & (df['box_number'].str.upper() == patient.box_number.upper())
            
            if mask.any():
                # Update existing record
                df.loc[mask, 'DOB'] = patient.dob
                df.loc[mask, 'Year Joined'] = patient.year_joined
                df.loc[mask, 'Last DOS'] = patient.last_dos
                df.loc[mask, 'Shred Year'] = patient.shred_year
                df.loc[mask, 'IsChildWhenJoined'] = patient.is_child_when_joined
        
        # Save changes back to Excel
        df.to_excel(EXCEL_PATH, index=False)
        return True
    except Exception as e:
        print(f"Error updating Excel file: {e}")
        return False
