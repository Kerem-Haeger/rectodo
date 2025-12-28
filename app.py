import sys
import uuid
from datetime import date, datetime
from typing import List, Optional

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QFrame,
    QSizePolicy,
    QLineEdit,
    QDialog,
    QFormLayout,
    QComboBox,
    QMessageBox,
    QSlider,
    QInputDialog,
)

from sheets_repo import get_pipeline_rows, append_pipeline_row, update_pipeline_row
from domain import (
    PipelineItem,
    pipeline_item_from_sheet,
    pipeline_item_to_sheet,
    filter_active,
)
from theme import apply_theme, ThemeMode
from actions import Action, apply_action, append_note


# ---- CONFIG: set this per recruiter ----
CURRENT_OWNER = "Kerem"  # change this to your own name when you run it


# ------- Helpers to load data from Google Sheets -------


def load_items_for_owner(owner: str) -> List[PipelineItem]:
    rows = get_pipeline_rows()
    items = [pipeline_item_from_sheet(r) for r in rows]
    # Only this owner's candidates, non-archived / non-done
    return [i for i in filter_active(items) if i.owner == owner]


def kpi_counts(items: List[PipelineItem]) -> tuple[int, int, int, int]:
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


def merge_csv_field(existing: str, new_value: str) -> str:
    """Merge a new value into a comma-separated string, avoiding duplicates."""
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
    name = name.strip().lower()
    for item in items:
        if item.owner == owner and item.candidate_name.strip().lower() == name:
            return item
    return None


# ------- Table model -------


class PipelineTableModel(QAbstractTableModel):
    COLUMNS = [
        "Candidate",
        "Client",
        "Role",
        "Stage",
        "Last action",
        "Next check",
        "Due in (days)",
        "Priority",
    ]

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
                return item.last_action_label
            elif col == 5:
                return item.next_check_at.isoformat() if item.next_check_at else ""
            elif col == 6:
                d = item.days_until_next_check
                return "" if d is None else str(d)
            elif col == 7:
                return item.priority_label

        if role == Qt.ForegroundRole:
            # Priority label uses traffic light colours
            if col == 7:
                if item.priority == "green":
                    return QColor("#22863a")
                elif item.priority == "yellow":
                    return QColor("#b08800")
                elif item.priority == "red":
                    return QColor("#d73a49")
            # All other cells: dark text for readability on pastel backgrounds
            return QColor("#000000")


        if role == Qt.BackgroundRole:
            # Full-row gradient background
            return QColor(item.priority_color)

        return None


# ------- Add Candidate Dialog -------


class AddCandidateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Update Candidate")
        self.resize(350, 200)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.client_edit = QLineEdit()
        self.role_edit = QLineEdit()

        self.stage_combo = QComboBox()
        self.stage_combo.addItems(
            [
                "sent",
                "feedback requested",
                "interview",
                "offer",
                "rejected",
                "on hold",
            ]
        )

        layout.addRow("Candidate name *", self.name_edit)
        layout.addRow("Client", self.client_edit)
        layout.addRow("Role", self.role_edit)
        layout.addRow("Stage", self.stage_combo)

        btn_row = QHBoxLayout()
        self.btn_ok = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addRow(btn_row)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def get_data(self) -> dict:
        return {
            "candidate_name": self.name_edit.text().strip(),
            "client": self.client_edit.text().strip(),
            "role": self.role_edit.text().strip(),
            "stage": self.stage_combo.currentText(),
        }


# ------- Candidate Action Dialog -------


class CandidateActionsDialog(QDialog):
    def __init__(self, item: PipelineItem, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update candidate")
        self.resize(400, 250)
        self.selected_action: Optional[Action] = None
        self.note_text: str = ""

        layout = QVBoxLayout(self)

        header = QLabel(
            f"{item.candidate_name}\n{item.client} – {item.role}"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # Action buttons
        row1 = QHBoxLayout()
        btn_spoke = QPushButton("✔ Spoke / update")
        btn_email = QPushButton("📩 Emailed")
        btn_na = QPushButton("📞 NA – call tomorrow")
        row1.addWidget(btn_spoke)
        row1.addWidget(btn_email)
        row1.addWidget(btn_na)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        btn_prepared = QPushButton("🧑‍🍳 Prepared / briefed")
        btn_snooze2 = QPushButton("⏭ Snooze 2 days")
        btn_snooze3 = QPushButton("⏭ Snooze 3 days")
        row2.addWidget(btn_prepared)
        row2.addWidget(btn_snooze2)
        row2.addWidget(btn_snooze3)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        btn_note = QPushButton("📝 Add note…")
        btn_done = QPushButton("🏁 Process finished")
        row3.addWidget(btn_note)
        row3.addWidget(btn_done)
        layout.addLayout(row3)

        # Cancel
        btn_cancel = QPushButton("Cancel")
        layout.addWidget(btn_cancel)

        # Wire up actions
        btn_spoke.clicked.connect(lambda: self._choose_action(Action.SPOKE))
        btn_email.clicked.connect(lambda: self._choose_action(Action.EMAILED))
        btn_na.clicked.connect(
            lambda: self._choose_action(Action.NA_CALL_TOMORROW)
        )
        btn_prepared.clicked.connect(
            lambda: self._choose_action(Action.PREPARED)
        )
        btn_snooze2.clicked.connect(
            lambda: self._choose_action(Action.SNOOZE_2D)
        )
        btn_snooze3.clicked.connect(
            lambda: self._choose_action(Action.SNOOZE_3D)
        )
        btn_done.clicked.connect(lambda: self._choose_action(Action.FINISHED))
        btn_cancel.clicked.connect(self.reject)
        btn_note.clicked.connect(self._add_note)

    def _choose_action(self, action: Action):
        self.selected_action = action
        self.accept()

    def _add_note(self):
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Add note",
            "Note:",
            "",
        )
        if ok and text.strip():
            # Store note, but keep dialog open so user can also choose an action
            if self.note_text:
                self.note_text += "\n\n" + text.strip()
            else:
                self.note_text = text.strip()


# ------- Main window -------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"RecToDo – {CURRENT_OWNER}'s Pipeline")
        self.resize(1200, 700)

        self.all_items: List[PipelineItem] = load_items_for_owner(CURRENT_OWNER)
        self.view_mode = "my"  # "my" or "overdue"

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setSpacing(8)

        owner_label = QLabel(f"Owner: {CURRENT_OWNER}")
        sidebar.addWidget(owner_label)

        self.btn_my = QPushButton("My pipeline")
        self.btn_overdue = QPushButton("Overdue only")
        self.btn_add = QPushButton("Add candidate")

        sidebar.addWidget(self.btn_my)
        sidebar.addWidget(self.btn_overdue)
        sidebar.addSpacing(20)
        sidebar.addWidget(self.btn_add)

        # Theme slider: 0 = light, 1 = dark
        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme")
        theme_row.addWidget(theme_label)

        self.theme_slider = QSlider(Qt.Horizontal)
        self.theme_slider.setRange(0, 1)
        self.theme_slider.setValue(1)  # default: dark, matches main()
        self.theme_slider.setFixedWidth(100)
        self.theme_slider.valueChanged.connect(self.on_theme_slider_changed)

        theme_row.addWidget(self.theme_slider)
        sidebar.addLayout(theme_row)

        sidebar.addStretch(1)

        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar)
        sidebar_frame.setFixedWidth(220)
        main_layout.addWidget(sidebar_frame)

        # Main content
        content = QVBoxLayout()
        main_layout.addLayout(content)

        # KPI row
        kpi_row = QHBoxLayout()
        self.kpi_green = QLabel()
        self.kpi_yellow = QLabel()
        self.kpi_red = QLabel()
        self.kpi_total = QLabel()

        for w in (self.kpi_green, self.kpi_yellow, self.kpi_red, self.kpi_total):
            w.setFrameStyle(QFrame.Panel | QFrame.Raised)
            w.setMargin(10)
            w.setAlignment(Qt.AlignCenter)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            kpi_row.addWidget(w)

        content.addLayout(kpi_row)

        # Search row
        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Candidate, client, role..."
        )
        search_row.addWidget(search_label)
        search_row.addWidget(self.search_edit)
        content.addLayout(search_row)

        # Table
        self.table = QTableView()
        self.table.setSortingEnabled(True)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

        content.addWidget(self.table)

        # Signals
        self.btn_my.clicked.connect(self._set_view_my)
        self.btn_overdue.clicked.connect(self._set_view_overdue)
        self.btn_add.clicked.connect(self._add_candidate)
        self.search_edit.textChanged.connect(self._refresh_view)
        self.table.doubleClicked.connect(
            self._open_actions_for_selected_from_index
        )

        # Initial view
        self._refresh_view()

    # Theme handler
    def on_theme_slider_changed(self, value: int):
        app = QApplication.instance()
        if not app:
            return
        mode = ThemeMode.DARK if value >= 1 else ThemeMode.LIGHT
        apply_theme(app, mode)

    # ---- View helpers ----

    def _filtered_items(self) -> List[PipelineItem]:
        items = list(self.all_items)

        # Only items that should be visible now (ACTIVE + due SNOOZED)
        items = [i for i in items if i.is_visible_now]

        # filter by view mode (my vs overdue – all are already owner-specific)
        if self.view_mode == "overdue":
            items = [i for i in items if i.priority == "red"]

        # filter by search text
        query = self.search_edit.text().strip().lower()
        if query:

            def matches(i: PipelineItem) -> bool:
                haystack = " ".join(
                    [
                        i.candidate_name or "",
                        i.client or "",
                        i.role or "",
                    ]
                ).lower()
                return query in haystack

            items = [i for i in items if matches(i)]

        return items

    def _refresh_view(self):
        items = self._filtered_items()
        model = PipelineTableModel(items)
        self.table.setModel(model)

        g, y, r, total = kpi_counts(self.all_items)
        self.kpi_green.setText(f"🟢 Fresh\n{g}")
        self.kpi_yellow.setText(f"🟡 Follow-up\n{y}")
        self.kpi_red.setText(f"🔴 Overdue\n{r}")
        self.kpi_total.setText(f"Total\n{total}")

    def _set_view_my(self):
        self.view_mode = "my"
        self._refresh_view()

    def _set_view_overdue(self):
        self.view_mode = "overdue"
        self._refresh_view()

    def _get_selected_item(self) -> Optional[PipelineItem]:
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        model = self.table.model()
        if not hasattr(model, "items"):
            return None
        row = index.row()
        if row < 0 or row >= len(model.items):
            return None
        return model.items[row]

    def _open_actions_for_selected_from_index(self, index: QModelIndex):
        # Double-click handler – we ignore the index itself and use current index
        self._open_actions_for_selected()

    def _open_actions_for_selected(self):
        item = self._get_selected_item()
        if item is None:
            QMessageBox.information(
                self,
                "No candidate selected",
                "Please select a candidate in the table first.",
            )
            return

        dlg = CandidateActionsDialog(item, self)
        if dlg.exec() != QDialog.Accepted:
            # Even if only note was added, we still want to persist it
            if dlg.note_text:
                append_note(item, dlg.note_text)
                row_dict = pipeline_item_to_sheet(item)
                update_pipeline_row(item.id, row_dict)
                self.all_items = load_items_for_owner(CURRENT_OWNER)
                self._refresh_view()
            return

        # Apply chosen action
        if dlg.selected_action is not None:
            apply_action(item, dlg.selected_action)

        # Append any notes
        if dlg.note_text:
            append_note(item, dlg.note_text)

        # Persist changes
        row_dict = pipeline_item_to_sheet(item)
        update_pipeline_row(item.id, row_dict)

        # Reload items to avoid stale data and refresh UI
        self.all_items = load_items_for_owner(CURRENT_OWNER)
        self._refresh_view()

    # ---- Add / update candidate ----

    def _add_candidate(self):
        dlg = AddCandidateDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()
        name = data["candidate_name"]
        if not name:
            QMessageBox.warning(self, "Missing name", "Candidate name is required.")
            return

        # Reload items to avoid stale view if someone else added rows
        self.all_items = load_items_for_owner(CURRENT_OWNER)

        existing = find_candidate_by_name(self.all_items, CURRENT_OWNER, name)

        now = datetime.utcnow()
        today = date.today()

        if existing is None:
            # New candidate row
            new_item = PipelineItem(
                id=str(uuid.uuid4()),
                owner=CURRENT_OWNER,
                candidate_name=name,
                client=data["client"],
                role=data["role"],
                stage=data["stage"],
                sent_at=today,
                last_action=None,
                last_action_at=None,
                next_check_at=None,
                status="ACTIVE",
                notes="",
                created_at=now,
                updated_at=now,
                archived=False,
            )
            row_dict = pipeline_item_to_sheet(new_item)
            append_pipeline_row(row_dict)
            self.all_items.append(new_item)
        else:
            # Update existing candidate basic info
            existing.client = merge_csv_field(existing.client, data["client"])
            existing.role = merge_csv_field(existing.role, data["role"])
            existing.stage = data["stage"] or existing.stage
            existing.updated_at = now

            row_dict = pipeline_item_to_sheet(existing)
            update_pipeline_row(existing.id, row_dict)

        self._refresh_view()


# ------- Entry point -------


def main():
    app = QApplication(sys.argv)

    # Default theme: dark
    apply_theme(app, ThemeMode.DARK)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
