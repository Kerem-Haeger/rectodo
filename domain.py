from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Dict, Any, List


@dataclass
class PipelineItem:
    id: str
    owner: str
    candidate_name: str
    client: str
    role: str
    stage: str
    sent_at: Optional[date]
    last_action: Optional[str]
    last_action_at: Optional[date]
    next_check_at: Optional[date]
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime
    archived: bool

    # ---- Derived properties ----

    @property
    def days_until_next_check(self) -> Optional[int]:
        if not self.next_check_at:
            return None
        today = date.today()
        return (self.next_check_at - today).days

    @property
    def priority(self) -> str:
        """
        Coarse traffic light: green / yellow / red / none.
        Used for KPIs & filters.
        """
        if self.archived or self.status == "DONE":
            return "none"

        d = self.days_until_next_check
        if d is None:
            return "yellow"  # unknown = needs attention

        if d >= 1:
            return "green"
        elif d == 0:
            return "yellow"
        else:
            return "red"

    @property
    def priority_label(self) -> str:
        """
        Human label: Fresh / Upcoming / Due today / Overdue...
        Shown in the table.
        """
        if self.archived or self.status == "DONE":
            return "Done"

        d = self.days_until_next_check
        if d is None:
            return "Needs check"

        if d >= 2:
            return "Fresh"
        elif d == 1:
            return "Upcoming"
        elif d == 0:
            return "Due today"
        elif d >= -2:
            return "Overdue"
        else:
            return "Very overdue"

    @property
    def priority_color(self) -> str:
        """
        Hex colour for the FULL ROW background.
        Pastel / Excel-like, not aggressive.
        """
        if self.archived or self.status == "DONE":
            return "#f5f5f5"  # very light grey

        d = self.days_until_next_check
        if d is None:
            return "#e0e0e0"  # neutral grey (needs check)

        if d >= 2:
            return "#c8e6c9"  # fresh – soft green
        elif d == 1:
            return "#dcedc8"  # upcoming – lighter green
        elif d == 0:
            return "#fff9c4"  # due today – pale yellow
        elif d >= -2:
            return "#ffe0b2"  # slightly overdue – soft orange
        else:
            return "#ffcdd2"  # very overdue – soft red

    @property
    def is_active(self) -> bool:
        # "Active in system" (for KPIs / loading)
        return (not self.archived) and self.status in {"ACTIVE", "SNOOZED"}

    @property
    def is_visible_now(self) -> bool:
        """
        Should appear in the main list right now?
        ACTIVE => always visible
        SNOOZED => only when due or overdue
        """
        if not self.is_active:
            return False
        if self.status == "ACTIVE":
            return True
        # SNOOZED: only show when due
        d = self.days_until_next_check
        return d is None or d <= 0

    @property
    def last_action_label(self) -> str:
        """
        Human-readable version of last_action for the UI.
        """
        if not self.last_action:
            return ""

        mapping = {
            "SPOKE": "Spoke / update",
            "EMAILED": "Emailed",
            "NA_CALL_TOMORROW": "NA – call tomorrow",
            "PREPARED": "Prepared / briefed",
            "SNOOZE_2D": "Snoozed (2 days)",
            "SNOOZE_3D": "Snoozed (3 days)",
            "FINISHED": "Process finished",
        }
        return mapping.get(self.last_action, self.last_action)


# ---- Parsing helpers ----


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).strip().upper()
    return s in {"TRUE", "1", "YES", "Y"}


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    s = str(value).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ---- Converters to/from Sheets rows ----


def pipeline_item_from_sheet(row: Dict[str, Any]) -> PipelineItem:
    return PipelineItem(
        id=str(row.get("id") or ""),
        owner=str(row.get("owner") or ""),
        candidate_name=str(row.get("candidate_name") or ""),
        client=str(row.get("client") or ""),
        role=str(row.get("role") or ""),
        stage=str(row.get("stage") or ""),
        sent_at=_parse_date(row.get("sent_at")),
        last_action=str(row.get("last_action") or "") or None,
        last_action_at=_parse_date(row.get("last_action_at")),
        next_check_at=_parse_date(row.get("next_check_at")),
        status=str(row.get("status") or "ACTIVE"),
        notes=str(row.get("notes") or ""),
        created_at=_parse_datetime(row.get("created_at")) or datetime.utcnow(),
        updated_at=_parse_datetime(row.get("updated_at")) or datetime.utcnow(),
        archived=_parse_bool(row.get("archived")),
    )


def pipeline_item_to_sheet(item: PipelineItem) -> Dict[str, Any]:
    def _date_to_str(d: Optional[date]) -> str:
        return d.isoformat() if d else ""

    def _dt_to_str(dt: Optional[datetime]) -> str:
        return dt.replace(microsecond=0).isoformat() if dt else ""

    return {
        "id": item.id,
        "owner": item.owner,
        "candidate_name": item.candidate_name,
        "client": item.client,
        "role": item.role,
        "stage": item.stage,
        "sent_at": _date_to_str(item.sent_at),
        "last_action": item.last_action or "",
        "last_action_at": _date_to_str(item.last_action_at),
        "next_check_at": _date_to_str(item.next_check_at),
        "status": item.status,
        "notes": item.notes,
        "created_at": _dt_to_str(item.created_at),
        "updated_at": _dt_to_str(item.updated_at),
        "archived": "TRUE" if item.archived else "FALSE",
    }


def filter_active(items: List[PipelineItem]) -> List[PipelineItem]:
    return [i for i in items if i.is_active]


def filter_visible(items: List[PipelineItem]) -> List[PipelineItem]:
    return [i for i in items if i.is_visible_now]
