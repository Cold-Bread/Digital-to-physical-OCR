import sqlite3
import time
# Connect to database
con = sqlite3.connect("patients.db")
cur = con.cursor()

# Create table if it doesn't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    box_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    last_visit TEXT,
    delete_flag INTEGER DEFAULT 0
)
""")
con.commit()

# Function to insert patient if not exists (by name and dob)
def insert_patient(name, dob, last_visit):
    # check if record needs to be flagged for deltion
    if last_visit< time.strftime("%Y-%m-%d"): # needs to check if person is a child or not
        print("Last visit is past deltion date for age range, flagging for deletion.")
        cur.execute("INSERT patients SET delete_flag = 1 WHERE name = ? AND dob = ?", (name, dob))
        con.commit()
    else:
        #if record exists, check if name and dob match any other previous records
        cur.execute("SELECT * FROM patients WHERE name = ?", (name,))
        matches = cur.fetchall()

        if not matches:
            # No existing name, safe to insert
            cur.execute("""
                INSERT INTO patients (name, dob, last_visit)
                VALUES (?, ?, ?)
            """, (name, dob, last_visit))
            con.commit()
            print("Inserted new patient.")
        else:
            # At least one patient with same name found
            for row in matches:
                if row[2] == dob:  # row[2] is DOB
                    print("Patient already exists with same name and DOB.")
                    return
            print("Potential duplicate: Same name, different DOB.")
            # Optional: insert with a "flag" column, log it, or notify for manual review

# Function to delete patient by name and dob
def delete_patient(name, dob):
    cur.execute("SELECT * FROM patients WHERE name = ? AND dob = ?", (name, dob))
    if not cur.fetchone():
        print("Patient not found.")
        return

    cur.execute("DELETE FROM patients WHERE name = ? AND dob = ?", (name, dob))
    con.commit()

# Function to get patients by partial name match and optional dob
def get_patient(name_partial, dob=None):
    if dob:
        cur.execute("SELECT * FROM patients WHERE name LIKE ? AND dob = ?", (f"%{name_partial}%", dob))
    else:
        cur.execute("SELECT * FROM patients WHERE name LIKE ?", (f"%{name_partial}%",))
    return cur.fetchall()


# Compare duplicate entries (if any) for a given name
def flag_record_delete(name):
    cur.execute("SELECT * FROM patients WHERE name = ?", (name,))
    rows = cur.fetchall()
    if len(rows) <= 1:
        print("No duplicates found.")
    else:
        print("Multiple entries found:")
        for row in rows:
            print(row)

con.close()
