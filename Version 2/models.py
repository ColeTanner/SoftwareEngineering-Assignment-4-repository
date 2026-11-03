import re
from datetime import datetime
from exceptions import ValidationError

class StaffUser:
    """Represents an authenticated clinic worker."""
    def __init__(self, username: str, full_name: str, role: str):
        self.username = username
        self.full_name = full_name
        self.role = role

    def has_permission(self, required_roles: list) -> bool:
        return self.role in required_roles


class Patient:
    """
    Patient domain model enforcing strict in-memory immutability (Finding 2)
    and robust input validation (Finding 1).
    """
    def __init__(self, patient_id: str, first_name: str, last_name: str, dob: str, contact_number: str, address: str):
        # Validate inputs before assignment
        Patient.validate_name(first_name, "First Name")
        Patient.validate_name(last_name, "Last Name")
        Patient.validate_phone(contact_number)
        Patient.validate_general_field(address, "Address")
        Patient.validate_general_field(dob, "Date of Birth")

        # Initialize internal state using super().__setattr__
        super().__setattr__("_patient_id", patient_id.strip())
        super().__setattr__("first_name", first_name.strip())
        super().__setattr__("last_name", last_name.strip())
        super().__setattr__("dob", dob.strip())
        super().__setattr__("contact_number", re.sub(r"[\s\-\(\)]", "", contact_number.strip()))
        super().__setattr__("address", address.strip())
        super().__setattr__("_initialized", True)

    @property
    def patient_id(self) -> str:
        """Read-only property getter."""
        return self._patient_id

    def __setattr__(self, name: str, value):
        """Prevents modifying immutable identity attributes in memory (Finding 2)."""
        if getattr(self, "_initialized", False) and name in ("_patient_id", "patient_id", "dob"):
            raise AttributeError(f"Field '{name}' is permanent and immutable.")
        super().__setattr__(name, value)

    def update_permitted_info(self, contact_number: str = None, address: str = None, first_name: str = None, last_name: str = None):
        """Validates and updates only permitted demographic fields (FR-04)."""
        if contact_number is not None:
            Patient.validate_phone(contact_number)
            self.contact_number = re.sub(r"[\s\-\(\)]", "", contact_number.strip())
        if address is not None:
            Patient.validate_general_field(address, "Address")
            self.address = address.strip()
        if first_name is not None:
            Patient.validate_name(first_name, "First Name")
            self.first_name = first_name.strip()
        if last_name is not None:
            Patient.validate_name(last_name, "Last Name")
            self.last_name = last_name.strip()

    @staticmethod
    def validate_name(val: str, field_name: str):
        if not val or not val.strip():
            raise ValidationError(f"{field_name} cannot be blank.")
        cleaned = val.strip()
        if len(cleaned) > 100:
            raise ValidationError(f"{field_name} exceeds maximum length of 100 characters.")
        if not re.match(r"^[A-Za-z\s\-']+$", cleaned):
            raise ValidationError(f"{field_name} must contain only alphabetic characters, spaces, or hyphens.")

    @staticmethod
    def validate_phone(val: str):
        if not val or not val.strip():
            raise ValidationError("Phone number cannot be blank.")
        cleaned = re.sub(r"[\s\-\(\)]", "", val.strip())
        if len(cleaned) != 10 or not cleaned.isdigit():
            raise ValidationError(f"Invalid phone number '{val}'. Must be exactly 10 numeric digits.")

    @staticmethod
    def validate_general_field(val: str, field_name: str):
        if not val or not val.strip():
            raise ValidationError(f"{field_name} cannot be blank.")
        if len(val.strip()) > 100:
            raise ValidationError(f"{field_name} exceeds maximum length of 100 characters.")


class VisitNote:
    """Represents a dated clinical visit note linked to a Patient."""
    def __init__(self, note_id: int, patient_id: str, note_text: str, category: str, author: str, timestamp: str = None):
        if not note_text or not note_text.strip():
            raise ValidationError("Clinical visit note text cannot be empty.")
        self.note_id = note_id
        self.patient_id = patient_id
        self.note_text = note_text.strip()
        self.category = category
        self.author = author
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")