"""
Table model for displaying pipeline items in the UI.
"""

from typing import List
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor
from domain import PipelineItem
from config import TABLE_COLUMNS


class PipelineTableModel(QAbstractTableModel):
    """
    Table model for displaying pipeline items in a QTableView.
    """

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
            elif col == 1:
                return item.client
            elif col == 2:
                return item.role
            elif col == 3:
                return item.stage
            elif col == 4:
                return item.sent_at.isoformat() if item.sent_at else ""
            elif col == 5:
                if item.days_since_sent is None:
                    return ""
                return str(item.days_since_sent)
            elif col == 6:
                return item.priority_label
            elif col == 7:
                return item.next_action

        if role == Qt.ForegroundRole and col == 6:
            if item.priority == "green":
                return QColor("#22863a")
            elif item.priority == "yellow":
                return QColor("#b08800")
            elif item.priority == "red":
                return QColor("#d73a49")

        return None
