CREATE TABLE patientRecords (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    box_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    last_visit TEXT,
    delete_flag INTEGER DEFAULT 0 -- 0 = not flagged, 1 = flagged for deletion
);
