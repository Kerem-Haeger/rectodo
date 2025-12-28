# test_domain.py
from datetime import date
from domain import PipelineItem

item = PipelineItem(
    id="1",
    owner="Kerem",
    candidate_name="Test Candidate",
    candidate_email="test@example.com",
    candidate_phone="",
    client="Test Client",
    role="Test Role",
    stage="sent",
    sent_at=date(2025, 12, 20),
    last_contact_at=None,
    next_action="Follow up",
    notes="",
    created_at=None,
    updated_at=None,
)

print("Days since sent:", item.days_since_sent)
print("Priority:", item.priority)
print("Label:", item.priority_label)
