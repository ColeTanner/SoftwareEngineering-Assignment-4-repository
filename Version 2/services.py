import uuid
import sqlite3
from database import get_connection
from models import Patient, VisitNote, StaffUser
from exceptions import (
    PatientNotFoundError,
    DuplicateRecordError,
    DatabaseOperationError
)

class AuthService:
    """Handles staff authentication against SQLite."""
    @staticmethod
    def login(username, password) -> StaffUser:
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT username, full_name, role FROM staff_users WHERE username=? AND password_hash=?",
                    (username.strip(), password.strip())
                )
                row = cursor.fetchone()
                if row:
                    return StaffUser(row["username"], row["full_name"], row["role"])
                return None
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Database error during authentication: {e}")


class PatientService:
    """Manages patient creation, key generation, queries, and updates."""

    @classmethod
    def generate_patient_id(cls) -> str:
        """Generates an 8-character hex ID backed by an active collision check loop (Finding 5)."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                while True:
                    candidate_id = f"PT-{uuid.uuid4().hex[:8].upper()}"
                    cursor.execute("SELECT 1 FROM patients WHERE patient_id = ?", (candidate_id,))
                    if not cursor.fetchone():
                        return candidate_id
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Database error during ID generation: {e}")

    @classmethod
    def register_patient(cls, first_name: str, last_name: str, dob: str, contact: str, address: str) -> Patient:
        """Constructs and persists a new patient record with an immutable ID."""
        patient_id = cls.generate_patient_id()
        # Instantiate domain model (validates format, length, and phone rules)
        patient = Patient(patient_id, first_name, last_name, dob, contact, address)

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO patients (patient_id, first_name, last_name, dob, contact_number, address)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (patient.patient_id, patient.first_name, patient.last_name, patient.dob, patient.contact_number, patient.address))
            return patient
        except sqlite3.IntegrityError as e:
            raise DuplicateRecordError(f"Integrity violation during patient registration: {e}")
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to persist patient record: {e}")

    @staticmethod
    def get_by_id(patient_id: str) -> Patient:
        """Primary search by Patient ID."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id.strip(),))
                row = cursor.fetchone()
                if row:
                    return Patient(
                        row["patient_id"], row["first_name"], row["last_name"],
                        row["dob"], row["contact_number"], row["address"]
                    )
                return None
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Database error during primary ID lookup: {e}")

    @staticmethod
    def search_by_name_and_dob(last_name: str, dob: str) -> list:
        """Secondary search leveraging the idx_patients_name_dob composite index."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM patients 
                    WHERE LOWER(last_name) LIKE LOWER(?) AND dob = ?
                """, (f"%{last_name.strip()}%", dob.strip()))
                rows = cursor.fetchall()
                return [
                    Patient(r["patient_id"], r["first_name"], r["last_name"], r["dob"], r["contact_number"], r["address"])
                    for r in rows
                ]
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Database error during secondary search: {e}")

    @staticmethod
    def update_patient(patient: Patient) -> bool:
        """Persists updated demographic fields to SQLite while keeping patient_id untouched."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE patients 
                    SET first_name=?, last_name=?, contact_number=?, address=?
                    WHERE patient_id=?
                """, (patient.first_name, patient.last_name, patient.contact_number, patient.address, patient.patient_id))
            return True
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Failed to update patient record: {e}")


class VisitService:
    """Manages dated visit notes and enforces referential integrity."""

    @staticmethod
    def add_visit_note(patient_id: str, note_text: str, category: str, author_name: str) -> VisitNote:
        """Validates patient presence and persists a permanent clinical visit note."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT patient_id FROM patients WHERE patient_id=?", (patient_id.strip(),))
                if not cursor.fetchone():
                    raise PatientNotFoundError(f"Cannot save visit note. Patient ID '{patient_id}' does not exist.")

                cursor.execute("""
                    INSERT INTO visit_notes (patient_id, note_text, category, author)
                    VALUES (?, ?, ?, ?)
                """, (patient_id.strip(), note_text.strip(), category, author_name))
                note_id = cursor.lastrowid
                return VisitNote(note_id, patient_id.strip(), note_text.strip(), category, author_name)
        except sqlite3.IntegrityError as e:
            raise DatabaseOperationError(f"Integrity violation adding visit note: {e}")
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Database failure while recording visit note: {e}")

    @staticmethod
    def get_visit_history(patient_id: str) -> list:
        """Retrieves read-only chronological history for a patient."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM visit_notes WHERE patient_id=? ORDER BY timestamp DESC
                """, (patient_id.strip(),))
                rows = cursor.fetchall()
                return [
                    VisitNote(r["note_id"], r["patient_id"], r["note_text"], r["category"], r["author"], r["timestamp"])
                    for r in rows
                ]
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Database error retrieving visit history: {e}")