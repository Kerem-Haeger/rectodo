"""
Data loading and filtering functions for pipeline items.
"""

from typing import List
from domain import PipelineItem, filter_active, pipeline_item_from_sheet
from sheets_repo import get_pipeline_rows


def load_items_for_owner(owner: str) -> List[PipelineItem]:
    """
    Load all active pipeline items for a specific owner from Google Sheets.

    Args:
        owner: The owner name to filter by

    Returns:
        List of active PipelineItems belonging to the owner
    """
    rows = get_pipeline_rows()
    items = [pipeline_item_from_sheet(r) for r in rows]
    # Only this owner's candidates, non-archived
    return [i for i in filter_active(items) if i.owner == owner]


def kpi_counts(items: List[PipelineItem]) -> tuple[int, int, int, int]:
    """
    Calculate KPI counts for a list of pipeline items.

    Args:
        items: List of pipeline items to count

    Returns:
        Tuple of (green_count, yellow_count, red_count, total_count)
    """
    green = yellow = red = 0
    for i in items:
        if i.priority == "green":
            green += 1
        elif i.priority == "yellow":
            yellow += 1
        elif i.priority == "red":
            red += 1
    total = len(items)
    return green, yellow, red, total
