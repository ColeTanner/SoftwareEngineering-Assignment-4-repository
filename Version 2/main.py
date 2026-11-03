import sys
from database import init_db
from controller import PRSController
from ai_service import AICategorizationService
from exceptions import PRSError

app_controller = PRSController()

def handle_ai_categorization_flow(note_text: str) -> str:
    """Coordinates presentation of AI suggestion and human approval/fallback."""
    print("\n--- Submitting Note to AI Categorization Service ---")
    result = app_controller.request_ai_suggestion(note_text)
    status = result["status"]

    if status == "SUCCESS":
        suggested = result["suggested_category"]
        conf = result["confidence"]
        print(f"[AI Suggestion]: {suggested} (Confidence: {conf:.2f})")
        choice = input("Accept AI recommendation? (y/n): ").strip().lower()
        if choice == 'y':
            return suggested
        print("Staff declined recommendation. Please select manually:")
    else:
        print(f"[Notice]: AI service returned status '{status}'. Falling back to manual selection.")

    categories = AICategorizationService.CATEGORIES
    for i, c in enumerate(categories, 1):
        print(f"  {i}. {c}")
    while True:
        sel = input("Select category number (1-4): ").strip()
        if sel in ["1", "2", "3", "4"]:
            return categories[int(sel) - 1]
        print("Invalid selection. Please enter a number between 1 and 4.")

def view_patient_screen(patient, current_user):
    """Displays patient profile and clinical visit notes."""
    while True:
        print("\n" + "="*52)
        print(f"PATIENT RECORD: {patient.first_name} {patient.last_name}")
        print("="*52)
        print(f"Patient ID:      {patient.patient_id} (IMMUTABLE)")
        print(f"Date of Birth:   {patient.dob}")
        print(f"Contact Phone:   {patient.contact_number}")
        print(f"Address:         {patient.address}")
        print("-" * 52)

        try:
            history = app_controller.load_visit_history(patient.patient_id)
            print(f"Clinical Visit History ({len(history)} entries):")
            if not history:
                print("  No prior visit notes on record.")
            else:
                for note in history:
                    print(f"  [{note.timestamp}] Category: {note.category} | Staff: {note.author}")
                    print(f"    Note: {note.note_text}")
        except PRSError as e:
            print(f"[Error loading history]: {e}")
        print("-" * 52)

        print("Actions: [1] Add Visit Note  [2] Update Demographics  [3] Return to Main Menu")
        cmd = input("Select an action: ").strip()

        if cmd == '1':
            note_text = input("\nEnter clinical visit note text:\n").strip()
            if not note_text:
                print("[Error]: Note text cannot be empty.")
                continue

            category = handle_ai_categorization_flow(note_text)
            try:
                app_controller.record_visit_note(current_user, patient.patient_id, note_text, category)
                print("\n[Success]: Clinical visit note recorded successfully.")
            except PRSError as e:
                print(f"\n[Operation Failed]: {e}")

        elif cmd == '2':
            print("\nEnter updated values (leave blank to retain current):")
            fname = input(f"New First Name [{patient.first_name}]: ").strip()
            lname = input(f"New Last Name [{patient.last_name}]: ").strip()
            contact = input(f"New 10-Digit Phone [{patient.contact_number}]: ").strip()
            addr = input(f"New Street Address [{patient.address}]: ").strip()

            try:
                app_controller.update_patient_demographics(
                    current_user, patient,
                    fname or "", lname or "", contact or "", addr or ""
                )
                print("[Success]: Demographics updated successfully.")
            except PRSError as e:
                print(f"\n[Validation/Update Error]: {e}")

        elif cmd == '3':
            break

def main():
    init_db()
    print("=" * 60)
    print("  PATIENT RECORD SYSTEM (PRS) - VERSION 2.0 (REFACTORED)")
    print("=" * 60)

    current_user = None
    while not current_user:
        print("\nPlease Log In to Proceed (Defaults: recep1/pass123, nurse1/pass123, mgr1/pass123)")
        u = input("Username: ").strip()
        p = input("Password: ").strip()
        try:
            current_user = app_controller.authenticate_staff(u, p)
            if not current_user:
                print("[Error]: Invalid username or password.")
        except PRSError as e:
            print(f"[System Error]: {e}")

    print(f"\nActive Session: {current_user.full_name} | Role: {current_user.role}")

    while True:
        print("\n" + "-"*40)
        print("PRS APPLICATION MENU")
        print("-" * 40)
        print("1. Register New Patient (FR-01, FR-02)")
        print("2. Search Patient by ID (FR-03 Primary)")
        print("3. Search by Name & Date of Birth (FR-03 Secondary)")
        print("4. Switch User / Logout")
        print("5. Exit System")
        choice = input("Select an option (1-5): ").strip()

        try:
            if choice == '1':
                print("\n--- New Patient Registration ---")
                fname = input("First Name: ").strip()
                lname = input("Last Name: ").strip()
                dob = input("Date of Birth (YYYY-MM-DD): ").strip()
                contact = input("Phone Number (10 digits): ").strip()
                addr = input("Street Address: ").strip()

                new_patient = app_controller.register_new_patient(current_user, fname, lname, dob, contact, addr)
                print(f"\n[Success]: Patient registered! Assigned Permanent ID: {new_patient.patient_id}")
                view_patient_screen(new_patient, current_user)

            elif choice == '2':
                pid = input("\nEnter Patient ID (e.g., PT-A1B2C3D4): ").strip()
                patient = app_controller.find_patient_by_id(pid)
                if patient:
                    view_patient_screen(patient, current_user)
                else:
                    print(f"\n[Search Notice]: No active record found matching ID '{pid}'.")

            elif choice == '3':
                lname = input("\nEnter Patient Last Name (partial search supported): ").strip()
                dob = input("Enter Patient Date of Birth (YYYY-MM-DD): ").strip()
                results = app_controller.find_patients_by_criteria(lname, dob)
                if not results:
                    print("\n[Search Notice]: No matching patient records located.")
                elif len(results) == 1:
                    view_patient_screen(results[0], current_user)
                else:
                    print(f"\nMultiple matches found ({len(results)}):")
                    for idx, p in enumerate(results, 1):
                        print(f" {idx}. {p.first_name} {p.last_name} | ID: {p.patient_id} | Phone: {p.contact_number}")
                    sel = input("Select patient index to inspect: ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(results):
                        view_patient_screen(results[int(sel) - 1], current_user)
                    else:
                        print("Invalid selection index.")

            elif choice == '4':
                return main()

            elif choice == '5':
                print("Shutting down PRS application. Goodbye.")
                sys.exit(0)

        except PRSError as e:
            print(f"\n[Operation Failed]: {e}")

if __name__ == "__main__":
    main()