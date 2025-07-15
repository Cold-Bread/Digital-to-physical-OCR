from database import get_db

def insert_patient(patient):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO patients (name, dob, last_visit) VALUES (?, ?, ?)",
                   (patient.name, patient.dob, patient.last_visit))
    db.commit()
    return {"status": "Patient added"}
