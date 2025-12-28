"""
Data loading and KPI calculations for RecToDo.
"""

from typing import List

from domain import PipelineItem, filter_active, pipeline_item_from_sheet
from sheets_repo import get_pipeline_rows


def load_items_for_owner(owner: str) -> List[PipelineItem]:
    """Load active items for a specific owner from Google Sheets."""
    rows = get_pipeline_rows()
    items = [pipeline_item_from_sheet(r) for r in rows]
    return [i for i in filter_active(items) if i.owner == owner]


def kpi_counts(items: List[PipelineItem]) -> tuple[int, int, int, int]:
    """Return counts for green/yellow/red/total items."""
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
