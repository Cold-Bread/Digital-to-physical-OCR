import sqlite3

"""
This is only to be used if entering data into the excel sheet
"""

DATABASE_NAME = "patients.db"


def get_connection():
    print(f"          Connecting to database: {DATABASE_NAME}")
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def create_table():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            last_visit TEXT NOT NULL,
            taken_from TEXT NOT NULL,
            placed_in TEXT NOT NULL,
            to_shred BOOLEAN NOT NULL,
            date_shredded TEXT
        )
    """)
    conn.commit()
    conn.close()
