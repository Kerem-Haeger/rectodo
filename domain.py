from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Dict, Any, List


# --- Configurable thresholds (in days) ---

FRESH_MAX_DAYS = 3
FOLLOWUP_MAX_DAYS = 7


# --- Helper functions for date parsing/formatting ---

def _parse_date(value: str) -> Optional[date]:
    """
    Parse a YYYY-MM-DD string to date, or return None if empty/invalid.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_datetime(value: str) -> Optional[datetime]:
    """
    Parse ISO datetime string to datetime, or None if empty/invalid.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _format_date(value: Optional[date]) -> str:
    return value.isoformat() if value else ""


def _format_datetime(value: Optional[datetime]) -> str:
    return value.isoformat(timespec="seconds") if value else ""


# --- Core domain model ---

@dataclass
class PipelineItem:
    id: str
    owner: str
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    client: str
    role: str
    stage: str
    sent_at: Optional[date]
    last_contact_at: Optional[date]
    next_action: str
    notes: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    archived: bool = False

    # ---- Derived properties ----

    @property
    def days_since_sent(self) -> Optional[int]:
        if not self.sent_at:
            return None
        return (date.today() - self.sent_at).days

    @property
    def priority(self) -> str:
        """
        Returns 'green', 'yellow', 'red' or 'none' (if no sent_at).
        """
        d = self.days_since_sent
        if d is None:
            return "none"
        if d <= FRESH_MAX_DAYS:
            return "green"
        if d <= FOLLOWUP_MAX_DAYS:
            return "yellow"
        return "red"

    @property
    def priority_label(self) -> str:
        mapping = {
            "green": "🟢 Fresh",
            "yellow": "🟡 Needs follow-up",
            "red": "🔴 Overdue",
            "none": "No sent date",
        }
        return mapping[self.priority]


# --- Converters to/from Google Sheets rows ---


def pipeline_item_from_sheet(row: Dict[str, Any]) -> PipelineItem:
    """
    Convert a raw dict from Sheets (get_all_records) into a PipelineItem.
    Expects keys matching the header names in the 'pipeline' tab.
    """
    return PipelineItem(
        id=str(row.get("id", "")),
        owner=row.get("owner", ""),
        candidate_name=row.get("candidate_name", ""),
        candidate_email=row.get("candidate_email", ""),
        candidate_phone=row.get("candidate_phone", ""),
        client=row.get("client", ""),
        role=row.get("role", ""),
        stage=row.get("stage", ""),
        sent_at=_parse_date(row.get("sent_at", "")),
        last_contact_at=_parse_date(row.get("last_contact_at", "")),
        next_action=row.get("next_action", ""),
        notes=row.get("notes", ""),
        created_at=_parse_datetime(row.get("created_at", "")),
        updated_at=_parse_datetime(row.get("updated_at", "")),
        archived=str(row.get("archived", "")).strip().upper() == "TRUE",
    )


def pipeline_item_to_sheet(item: PipelineItem) -> Dict[str, str]:
    """
    Convert a PipelineItem back to a dict ready to be written to Sheets.
    Keys match the header row.
    """
    return {
        "id": item.id,
        "owner": item.owner,
        "candidate_name": item.candidate_name,
        "candidate_email": item.candidate_email,
        "candidate_phone": item.candidate_phone,
        "client": item.client,
        "role": item.role,
        "stage": item.stage,
        "sent_at": _format_date(item.sent_at),
        "last_contact_at": _format_date(item.last_contact_at),
        "next_action": item.next_action,
        "notes": item.notes,
        "created_at": _format_datetime(item.created_at),
        "updated_at": _format_datetime(item.updated_at),
        "archived": "TRUE" if item.archived else "FALSE",
    }


# --- Convenience filters for lists of items ---


def filter_by_owner(items: List[PipelineItem], owner: str) -> List[PipelineItem]:
    return [i for i in items if i.owner == owner]


def filter_overdue(items: List[PipelineItem]) -> List[PipelineItem]:
    """
    Items with priority 'red'.
    """
    return [i for i in items if i.priority == "red" and not i.archived]


def filter_active(items: List[PipelineItem]) -> List[PipelineItem]:
    """
    Non-archived items.
    """
    return [i for i in items if not i.archived]
