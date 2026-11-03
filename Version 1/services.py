import uuid
from database import get_connection
from models import Patient, VisitNote, StaffUser
from ai_service import AICategorizationService

class AuthService:
    """Manages staff session validation and authorization."""
    @staticmethod
    def login(username, password) -> StaffUser:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, full_name, role FROM staff_users WHERE username=? AND password_hash=?", 
                       (username, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            return StaffUser(row["username"], row["full_name"], row["role"])
        return None


class PatientService:
    """Handles patient registration, lookups, and profile updates."""
    
    @staticmethod
    def generate_patient_id() -> str:
        """Generates a permanent unique 6-digit ID (FR-02, BRC-01)."""
        return f"PT-{str(uuid.uuid4().int)[:6]}"

    @classmethod
    def register_patient(cls, first_name: str, last_name: str, dob: str, contact: str, address: str) -> Patient:
        """Creates a new patient with an immutable ID (FR-01, FR-02)."""
        patient_id = cls.generate_patient_id()
        patient = Patient(patient_id, first_name.strip(), last_name.strip(), dob.strip(), contact.strip(), address.strip())
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients (patient_id, first_name, last_name, dob, contact_number, address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient.patient_id, patient.first_name, patient.last_name, patient.dob, patient.contact_number, patient.address))
        conn.commit()
        conn.close()
        return patient

    @staticmethod
    def get_by_id(patient_id: str) -> Patient:
        """Primary search by Patient ID (FR-03)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Patient(row["patient_id"], row["first_name"], row["last_name"], row["dob"], row["contact_number"], row["address"])
        return None

    @staticmethod
    def search_by_name_and_dob(last_name: str, dob: str) -> list:
        """Secondary search by Last Name and DOB (FR-03, Elicitation 1.3)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM patients 
            WHERE LOWER(last_name) LIKE LOWER(?) AND dob = ?
        """, (f"%{last_name.strip()}%", dob.strip()))
        rows = cursor.fetchall()
        conn.close()
        return [Patient(r["patient_id"], r["first_name"], r["last_name"], r["dob"], r["contact_number"], r["address"]) for r in rows]

    @staticmethod
    def update_patient(patient: Patient) -> bool:
        """Updates editable contact and demographic fields; patient_id is not modified (FR-04)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patients 
            SET first_name=?, last_name=?, contact_number=?, address=?
            WHERE patient_id=?
        """, (patient.first_name, patient.last_name, patient.contact_number, patient.address, patient.patient_id))
        conn.commit()
        conn.close()
        return True


class VisitService:
    """Handles visit note creation and retrieval (FR-05, FR-06)."""

    @staticmethod
    def add_visit_note(patient_id: str, note_text: str, category: str, author_name: str) -> VisitNote:
        """Validates patient existence and records a permanent visit note (BRC-02)."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify patient exists
        cursor.execute("SELECT patient_id FROM patients WHERE patient_id=?", (patient_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Cannot add visit note. Patient ID {patient_id} does not exist.")

        cursor.execute("""
            INSERT INTO visit_notes (patient_id, note_text, category, author)
            VALUES (?, ?, ?, ?)
        """, (patient_id, note_text, category, author_name))
        conn.commit()
        note_id = cursor.lastrowid
        conn.close()

        return VisitNote(note_id, patient_id, note_text, category, author_name)

    @staticmethod
    def get_visit_history(patient_id: str) -> list:
        """Retrieves chronological read-only visit history for a patient (FR-06)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM visit_notes WHERE patient_id=? ORDER BY timestamp DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [VisitNote(r["note_id"], r["patient_id"], r["note_text"], r["category"], r["author"], r["timestamp"]) for r in rows]