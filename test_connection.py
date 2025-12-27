from datetime import datetime
from sheets_repo import get_pipeline_rows, append_pipeline_row


def main():
    print("Reading existing rows...")
    rows = get_pipeline_rows()
    print(f"Found {len(rows)} rows")
    for r in rows[:5]:
        print(r)

    print("\nAppending a test row...")
    now = datetime.utcnow().isoformat(timespec="seconds")

    new_row = {
        "id": now,  # just to have something unique for the test
        "owner": "Kerem",
        "candidate_name": "Test Candidate",
        "candidate_email": "test@example.com",
        "candidate_phone": "+49 000 000000",
        "client": "Test Client",
        "role": "Test Role",
        "stage": "sent",
        "sent_at": now[:10],          # YYYY-MM-DD
        "last_contact_at": "",
        "next_action": "Follow up in a few days",
        "notes": "Created by test_connection.py",
        "created_at": now,
        "updated_at": now,
        "archived": "FALSE",
    }

    append_pipeline_row(new_row)
    print("Row appended. Check your Google Sheet!")


if __name__ == "__main__":
    main()
