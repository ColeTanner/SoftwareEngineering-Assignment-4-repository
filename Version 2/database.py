import sqlite3

DB_FILE = "prs_database.db"

def get_connection():
    """Returns a SQLite connection with foreign key enforcement and row mapping."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables, composite search indexes, and immutability triggers in dependency order."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Staff Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff_users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Receptionist', 'Nurse', 'Manager'))
        );
        """)

        # 2. Patients Table
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

        # 3. Composite Index for secondary search optimization (Finding 5, NFR-01)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_patients_name_dob 
        ON patients (last_name COLLATE NOCASE, dob);
        """)

        # 4. Database-level Immutability Trigger for Patients (Finding 2, BRC-01)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_prevent_patient_id_update
        BEFORE UPDATE OF patient_id ON patients
        BEGIN
            SELECT RAISE(ABORT, 'Patient ID is permanent and immutable.');
        END;
        """)

        # 5. Visit Notes Table (Must be created before triggers referencing it)
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

        # 6. Database-level Read-Only Trigger for Visit Notes (BRC-02)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_prevent_visit_note_update
        BEFORE UPDATE ON visit_notes
        BEGIN
            SELECT RAISE(ABORT, 'Clinical visit notes are permanent and cannot be modified.');
        END;
        """)

        # 7. Seed initial staff users if database is empty
        cursor.execute("SELECT COUNT(*) FROM staff_users;")
        if cursor.fetchone()[0] == 0:
            sample_staff = [
                ("recep1", "pass123", "Sarah Receptionist", "Receptionist"),
                ("nurse1", "pass123", "Gabe Nurse", "Nurse"),
                ("mgr1", "pass123", "Cole Manager", "Manager")
            ]
            cursor.executemany("INSERT INTO staff_users VALUES (?, ?, ?, ?);", sample_staff)