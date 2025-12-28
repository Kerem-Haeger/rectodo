from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

from domain import PipelineItem


class Action(Enum):
    SPOKE = "SPOKE"
    EMAILED = "EMAILED"
    NA_CALL_TOMORROW = "NA_CALL_TOMORROW"
    PREPARED = "PREPARED"
    SNOOZE_2D = "SNOOZE_2D"
    SNOOZE_3D = "SNOOZE_3D"
    FINISHED = "FINISHED"


def apply_action(
    item: PipelineItem, action: Action, now: Optional[datetime] = None
) -> PipelineItem:
    """
    Update last_action, last_action_at, next_check_at, status
    based on which action button was clicked.
    """
    if now is None:
        now = datetime.utcnow()
    today = date.today()

    # ensure sent_at is set on first action
    if item.sent_at is None:
        item.sent_at = today

    item.last_action = action.value
    item.last_action_at = today
    item.updated_at = now

    if action == Action.SPOKE:
        item.status = "ACTIVE"
        item.next_check_at = today + timedelta(days=2)
    elif action == Action.EMAILED:
        item.status = "ACTIVE"
        item.next_check_at = today + timedelta(days=3)
    elif action == Action.NA_CALL_TOMORROW:
        item.status = "ACTIVE"
        item.next_check_at = today + timedelta(days=1)
    elif action == Action.PREPARED:
        item.status = "ACTIVE"
        item.next_check_at = today + timedelta(days=1)
    elif action == Action.SNOOZE_2D:
        item.status = "SNOOZED"
        item.next_check_at = today + timedelta(days=2)
    elif action == Action.SNOOZE_3D:
        item.status = "SNOOZED"
        item.next_check_at = today + timedelta(days=3)
    elif action == Action.FINISHED:
        item.status = "DONE"
        item.next_check_at = None

    return item


def append_note(
    item: PipelineItem, note_text: str, now: Optional[datetime] = None
) -> PipelineItem:
    """
    Append a timestamped note. No manual "on xx/xx/xxxx" needed.
    """
    if not note_text.strip():
        return item
    if now is None:
        now = datetime.utcnow()
    timestamp = now.replace(microsecond=0).isoformat()
    prefix = f"[{timestamp}] "
    if item.notes:
        item.notes = item.notes + "\n\n" + prefix + note_text.strip()
    else:
        item.notes = prefix + note_text.strip()
    item.updated_at = now
    return item
