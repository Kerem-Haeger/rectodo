"""
Utility functions for the RecToDo application.
"""

from typing import List, Optional
from domain import PipelineItem


def merge_csv_field(existing: str, new_value: str) -> str:
    """
    Merge a new value into a comma-separated string, avoiding duplicates.
    
    Args:
        existing: Existing comma-separated string
        new_value: New value to add
        
    Returns:
        Updated comma-separated string with new value if not already present
    """
    existing = existing.strip()
    new_value = new_value.strip()
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
    """
    Find a candidate by name for a specific owner (case-insensitive).
    
    Args:
        items: List of pipeline items to search
        owner: Owner name to filter by
        name: Candidate name to search for
        
    Returns:
        The matching PipelineItem if found, None otherwise
    """
    name = name.strip().lower()
    for item in items:
        if item.owner == owner and item.candidate_name.strip().lower() == name:
            return item
    return None
