from models import StaffUser, Patient, VisitNote
from services import AuthService, PatientService, VisitService
from ai_service import AICategorizationService
from exceptions import UnauthorizedAccessError

class PRSController:
    """
    Application Controller Layer (Finding 3).
    Coordinates authorization, AI resolution, and business transactions away from the UI.
    """
    def __init__(self):
        self.ai_service = AICategorizationService()

    def authenticate_staff(self, username: str, password: str) -> StaffUser:
        return AuthService.login(username, password)

    def register_new_patient(self, user: StaffUser, fname: str, lname: str, dob: str, contact: str, addr: str) -> Patient:
        if not user.has_permission(["Receptionist", "Manager"]):
            raise UnauthorizedAccessError("Access Denied: Only receptionists or managers may register new patients.")
        return PatientService.register_patient(fname, lname, dob, contact, addr)

    def find_patient_by_id(self, patient_id: str) -> Patient:
        return PatientService.get_by_id(patient_id)

    def find_patients_by_criteria(self, last_name: str, dob: str) -> list:
        return PatientService.search_by_name_and_dob(last_name, dob)

    def update_patient_demographics(self, user: StaffUser, patient: Patient, fname: str, lname: str, contact: str, addr: str) -> bool:
        if not user.has_permission(["Receptionist", "Manager"]):
            raise UnauthorizedAccessError("Access Denied: Only receptionists or managers may update demographic details.")
        patient.update_permitted_info(
            contact_number=contact if contact else None,
            address=addr if addr else None,
            first_name=fname if fname else None,
            last_name=lname if lname else None
        )
        return PatientService.update_patient(patient)

    def request_ai_suggestion(self, note_text: str) -> dict:
        return self.ai_service.categorize_note(note_text)

    def record_visit_note(self, user: StaffUser, patient_id: str, note_text: str, category: str) -> VisitNote:
        if not user.has_permission(["Nurse", "Manager"]):
            raise UnauthorizedAccessError("Access Denied: Only clinical nurses or managers may save visit notes.")
        return VisitService.add_visit_note(patient_id, note_text, category, user.full_name)

    def load_visit_history(self, patient_id: str) -> list:
        return VisitService.get_visit_history(patient_id)