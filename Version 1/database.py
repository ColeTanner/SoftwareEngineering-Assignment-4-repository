import sqlite3
import os

DB_FILE = "prs_database.db"

def get_connection():
    """Returns a SQLite connection with foreign key support enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema matching Assignment #2 and #3 specs."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Staff Users Table for Authentication & Authorization
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff_users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Receptionist', 'Nurse', 'Manager'))
    );
    """)

    # Patients Table: Enforces unique, immutable Patient ID
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        contact_number TEXT NOT NULL,
        address TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Visit Notes Table: Immutable once created, strict foreign key to Patient
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visit_notes (
        note_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        note_text TEXT NOT NULL,
        category TEXT NOT NULL CHECK(category IN ('Respiratory', 'Digestive', 'Musculoskeletal', 'General/Other')),
        author TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE RESTRICT
    );
    """)

    # Pre-populate sample clinic staff for testing
    cursor.execute("SELECT COUNT(*) FROM staff_users;")
    if cursor.fetchone()[0] == 0:
        sample_staff = [
            ("recep1", "pass123", "Sarah Receptionist", "Receptionist"),
            ("nurse1", "pass123", "Gabe Nurse", "Nurse"),
            ("mgr1", "pass123", "Cole Manager", "Manager")
        ]
        cursor.executemany("INSERT INTO staff_users VALUES (?, ?, ?, ?);", sample_staff)

    conn.commit()
    conn.close()