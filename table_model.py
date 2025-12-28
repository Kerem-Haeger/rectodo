"""
Qt table model for displaying pipeline items.
"""

from typing import List

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

from config import TABLE_COLUMNS
from domain import PipelineItem


class PipelineTableModel(QAbstractTableModel):
    """Table model backing the pipeline QTableView."""

    COLUMNS = TABLE_COLUMNS

    def __init__(self, items: List[PipelineItem]):
        super().__init__()
        self.items = items

    def rowCount(self, parent=QModelIndex()):
        return len(self.items)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return str(section + 1)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        item = self.items[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return item.candidate_name
            if col == 1:
                return item.client
            if col == 2:
                return item.role
            if col == 3:
                return item.stage
            if col == 4:
                return item.last_action_label
            if col == 5:
                if item.next_check_at:
                    return item.next_check_at.isoformat()
                return ""
            if col == 6:
                days = item.days_until_next_check
                return "" if days is None else str(days)
            if col == 7:
                return item.priority_label

        if role == Qt.ForegroundRole:
            if col == 7:
                if item.priority == "green":
                    return QColor("#22863a")
                if item.priority == "yellow":
                    return QColor("#b08800")
                if item.priority == "red":
                    return QColor("#d73a49")
            return QColor("#000000")

        if role == Qt.BackgroundRole:
            return QColor(item.priority_color)

        return None
