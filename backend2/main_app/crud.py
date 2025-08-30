from main_app.database import get_connection
from main_app.models import Patient

def insert_patient(patient: Patient):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (name, dob, last_visit, taken_from, placed_in, to_shred, date_shredded) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            patient.name,
            patient.dob,
            patient.last_visit,
            patient.taken_from,
            patient.placed_in,
            patient.to_shred,
            patient.date_shredded
        )
    )
    conn.commit()
    user_id = cursor.lastrowid 
    conn.close()
    return {"id": user_id, "message": "Patient added successfully"}
