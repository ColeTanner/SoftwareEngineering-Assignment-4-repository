from datetime import datetime

class StaffUser:
    """Represents an authenticated clinic worker."""
    def __init__(self, username: str, full_name: str, role: str):
        self.username = username
        self.full_name = full_name
        self.role = role

    def has_permission(self, required_roles: list) -> bool:
        return self.role in required_roles


class Patient:
    """Represents a Patient entity with an immutable patient_id."""
    def __init__(self, patient_id: str, first_name: str, last_name: str, dob: str, contact_number: str, address: str):
        self._patient_id = patient_id  # Encapsulated state
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob  # Format: YYYY-MM-DD
        self.contact_number = contact_number
        self.address = address

    @property
    def patient_id(self) -> str:
        """Read-only property enforcing immutability."""
        return self._patient_id

    def update_permitted_info(self, contact_number: str, address: str, first_name: str = None, last_name: str = None):
        """Allows updating editable fields per FR-04 while keeping ID locked."""
        if contact_number:
            self.contact_number = contact_number
        if address:
            self.address = address
        if first_name:
            self.first_name = first_name
        if last_name:
            self.last_name = last_name


class VisitNote:
    """Represents a dated clinical visit note linked to a Patient."""
    def __init__(self, note_id: int, patient_id: str, note_text: str, category: str, author: str, timestamp: str = None):
        self.note_id = note_id
        self.patient_id = patient_id
        self.note_text = note_text
        self.category = category
        self.author = author
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")