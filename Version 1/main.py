import sys
from database import init_db
from models import StaffUser
from services import AuthService, PatientService, VisitService
from ai_service import AICategorizationService

ai_engine = AICategorizationService()

def prompt_ai_categorization(note_text: str) -> str:
    """Manages AI suggestion, review, acceptance, or manual fallback (FR-07, AIR-01, AIR-02)."""
    print("\n--- Submitting Note to AI Categorization Service ---")
    result = ai_engine.categorize_note(note_text)
    status = result["status"]
    
    if status == "SUCCESS":
        suggested = result["suggested_category"]
        conf = result["confidence"]
        print(f"[AI Suggestion]: {suggested} (Confidence: {conf:.2f})")
        choice = input("Accept AI suggestion? (y/n): ").strip().lower()
        if choice == 'y':
            return suggested
        else:
            print("Staff rejected AI suggestion. Please select manually:")
    else:
        print(f"[Notice]: AI service returned status: '{status}'. Falling back to manual selection.")

    # Manual Selection Fallback
    categories = AICategorizationService.CATEGORIES
    for idx, cat in enumerate(categories, start=1):
        print(f" {idx}. {cat}")
    
    while True:
        sel = input("Select category number (1-4): ").strip()
        if sel in ["1", "2", "3", "4"]:
            return categories[int(sel) - 1]
        print("Invalid selection. Try again.")

def view_patient_profile(patient, current_user: StaffUser):
    """Displays patient details and full visit history (FR-03, FR-06)."""
    while True:
        print("\n" + "="*45)
        print(f"PATIENT PROFILE: {patient.first_name} {patient.last_name}")
        print("="*45)
        print(f"Patient ID:      {patient.patient_id} (IMMUTABLE)")
        print(f"Date of Birth:   {patient.dob}")
        print(f"Contact Number:  {patient.contact_number}")
        print(f"Home Address:    {patient.address}")
        print("-" * 45)
        
        # Display Visit History
        history = VisitService.get_visit_history(patient.patient_id)
        print(f"Visit History ({len(history)} entries):")
        if not history:
            print("  No previous visit notes on record.")
        else:
            for n in history:
                print(f"  [{n.timestamp}] Category: {n.category} | Author: {n.author}")
                print(f"    Note: {n.note_text}")
        print("-" * 45)
        
        print("Options: [1] Add Visit Note  [2] Edit Demographics  [3] Back to Main Menu")
        choice = input("Select an option: ").strip()

        if choice == '1':
            # Authorization: Nurses and Managers can log notes (UR-03)
            if not current_user.has_permission(["Nurse", "Manager"]):
                print("\n[Access Denied]: Only clinical nurses or managers may record visit notes.")
                continue
            
            note_text = input("\nEnter clinical visit note text:\n").strip()
            if not note_text:
                print("Note text cannot be empty.")
                continue

            category = prompt_ai_categorization(note_text)
            VisitService.add_visit_note(patient.patient_id, note_text, category, current_user.full_name)
            print("\n[Success]: Visit note saved successfully to database.")

        elif choice == '2':
            # Authorization: Receptionists and Managers can edit patient details (FR-04)
            if not current_user.has_permission(["Receptionist", "Manager"]):
                print("\n[Access Denied]: Only receptionists and managers can edit patient records.")
                continue

            print("\nLeave blank to keep existing value.")
            fname = input(f"New First Name [{patient.first_name}]: ").strip()
            lname = input(f"New Last Name [{patient.last_name}]: ").strip()
            contact = input(f"New Contact [{patient.contact_number}]: ").strip()
            address = input(f"New Address [{patient.address}]: ").strip()

            patient.update_permitted_info(contact or None, address or None, fname or None, lname or None)
            PatientService.update_patient(patient)
            print("[Success]: Patient record updated successfully.")

        elif choice == '3':
            break

def main():
    init_db()
    print("=" * 55)
    print("  PATIENT RECORD SYSTEM (PRS) - VERSION 1.0 (PROTOTYPE)")
    print("=" * 55)
    
    # 1. Staff Authentication
    current_user = None
    while not current_user:
        print("\nPlease Log In to Proceed (Defaults: recep1/pass123, nurse1/pass123, mgr1/pass123)")
        user = input("Username: ").strip()
        pwd = input("Password: ").strip()
        current_user = AuthService.login(user, pwd)
        if not current_user:
            print("Invalid credentials. Try again.")

    print(f"\nWelcome, {current_user.full_name} | Role: {current_user.role}")

    # 2. Main Navigation Loop
    while True:
        print("\n" + "-"*40)
        print("MAIN MENU")
        print("-" * 40)
        print("1. Register New Patient (FR-01, FR-02)")
        print("2. Search Patient by ID (FR-03 Primary)")
        print("3. Search Patient by Name & DOB (FR-03 Secondary)")
        print("4. Switch User / Logout")
        print("5. Exit System")
        choice = input("Select an option (1-5): ").strip()

        if choice == '1':
            if not current_user.has_permission(["Receptionist", "Manager"]):
                print("\n[Access Denied]: Only reception staff may register new patients.")
                continue

            print("\n--- Register New Patient ---")
            fname = input("First Name: ").strip()
            lname = input("Last Name: ").strip()
            dob = input("Date of Birth (YYYY-MM-DD): ").strip()
            contact = input("Contact Phone: ").strip()
            address = input("Street Address: ").strip()

            if not all([fname, lname, dob, contact, address]):
                print("[Error]: All fields are mandatory for registration.")
                continue

            new_patient = PatientService.register_patient(fname, lname, dob, contact, address)
            print(f"\n[Success]: Patient registered! Generated Immutable ID: {new_patient.patient_id}")
            view_patient_profile(new_patient, current_user)

        elif choice == '2':
            pid = input("\nEnter Patient ID (e.g., PT-123456): ").strip()
            patient = PatientService.get_by_id(pid)
            if patient:
                view_patient_profile(patient, current_user)
            else:
                print(f"\n[Search Notice]: No patient record found matching ID '{pid}'.")

        elif choice == '3':
            lname = input("\nEnter Patient Last Name (partial allowed): ").strip()
            dob = input("Enter Patient Date of Birth (YYYY-MM-DD): ").strip()
            results = PatientService.search_by_name_and_dob(lname, dob)
            if not results:
                print("\n[Search Notice]: No matching patient records found.")
            elif len(results) == 1:
                view_patient_profile(results[0], current_user)
            else:
                print(f"\nMultiple matches found ({len(results)}):")
                for i, p in enumerate(results, start=1):
                    print(f" {i}. {p.first_name} {p.last_name} | ID: {p.patient_id} | Addr: {p.address}")
                sel = input("Select patient index to view: ").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(results):
                    view_patient_profile(results[int(sel) - 1], current_user)
                else:
                    print("Invalid selection.")

        elif choice == '4':
            return main()

        elif choice == '5':
            print("Shutting down PRS application. Goodbye.")
            sys.exit(0)

if __name__ == "__main__":
    main()