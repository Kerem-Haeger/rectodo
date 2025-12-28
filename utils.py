"""
Utility helpers for RecToDo.
"""

from datetime import date
from typing import List, Optional

from domain import PipelineItem


def merge_csv_field(existing: str, new_value: str) -> str:
    """Merge a value into a comma-separated string without duplicates."""
    existing = (existing or "").strip()
    new_value = (new_value or "").strip()
    if not new_value:
        return existing
    if not existing:
        return new_value

    parts = [p.strip() for p in existing.split(",") if p.strip()]
    if new_value not in parts:
        parts.append(new_value)
    return ", ".join(parts)


def find_candidate_by_name(
    items: List[PipelineItem], owner: str, name: str
) -> Optional[PipelineItem]:
    """Return candidate matching owner and case-insensitive name."""
    name = name.strip().lower()
    for item in items:
        if item.owner == owner and item.candidate_name.strip().lower() == name:
            return item
    return None


def format_date_uk(value: Optional[date]) -> str:
    """Return dd.mm.yyyy for a date, empty string if missing."""
    if not value:
        return ""
    return value.strftime("%d.%m.%Y")
