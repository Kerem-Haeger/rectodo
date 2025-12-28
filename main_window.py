"""
Main application window for RecToDo.
"""

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from actions import apply_action, append_note
from config import CURRENT_OWNER
from data_loader import kpi_counts, load_items_for_owner
from dialogs import AddCandidateDialog, CandidateActionsDialog
from domain import PipelineItem, pipeline_item_to_sheet
from sheets_repo import (
    append_pipeline_row,
    delete_pipeline_row,
    update_pipeline_row,
)
from table_model import PipelineTableModel
from theme import apply_theme, ThemeMode
from utils import find_candidate_by_name, merge_csv_field


class MainWindow(QMainWindow):
    """Main application window with sidebar, KPIs, search, and table."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"RecToDo – {CURRENT_OWNER}'s Pipeline")
        self.resize(1200, 700)

        self.all_items: List[PipelineItem] = load_items_for_owner(
            CURRENT_OWNER
        )
        self.view_mode = "my"  # "my" or "overdue"

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)

        sidebar_frame = self._build_sidebar()
        main_layout.addWidget(sidebar_frame)

        content_layout = self._build_content()
        main_layout.addLayout(content_layout)

        self._refresh_view()

    # ---- UI builders ----

    def _build_sidebar(self) -> QFrame:
        sidebar = QVBoxLayout()
        sidebar.setSpacing(8)

        owner_label = QLabel(f"Owner: {CURRENT_OWNER}")
        sidebar.addWidget(owner_label)

        self.btn_my = QPushButton("My pipeline")
        self.btn_overdue = QPushButton("Overdue only")
        self.btn_add = QPushButton("Add candidate")

        self.btn_overdue.setCheckable(True)

        sidebar.addWidget(self.btn_my)
        sidebar.addWidget(self.btn_overdue)
        sidebar.addSpacing(20)
        sidebar.addWidget(self.btn_add)

        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme")
        theme_row.addWidget(theme_label)

        self.theme_slider = QSlider(Qt.Horizontal)
        self.theme_slider.setRange(0, 1)
        self.theme_slider.setValue(1)
        self.theme_slider.setFixedWidth(100)
        self.theme_slider.valueChanged.connect(self._on_theme_slider_changed)

        theme_row.addWidget(self.theme_slider)
        sidebar.addLayout(theme_row)

        sidebar.addStretch(1)

        self.btn_my.clicked.connect(self._set_view_my)
        self.btn_overdue.clicked.connect(self._toggle_overdue)
        self.btn_add.clicked.connect(self._add_candidate)

        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar)
        sidebar_frame.setFixedWidth(220)
        return sidebar_frame

    def _build_content(self) -> QVBoxLayout:
        content = QVBoxLayout()

        kpi_row = QHBoxLayout()
        self.kpi_green = QLabel()
        self.kpi_yellow = QLabel()
        self.kpi_red = QLabel()
        self.kpi_total = QLabel()

        kpi_widgets = (
            self.kpi_green,
            self.kpi_yellow,
            self.kpi_red,
            self.kpi_total,
        )
        for w in kpi_widgets:
            w.setFrameStyle(QFrame.Panel | QFrame.Raised)
            w.setMargin(10)
            w.setAlignment(Qt.AlignCenter)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            kpi_row.addWidget(w)

        content.addLayout(kpi_row)

        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Candidate, client, role...")
        self.search_edit.textChanged.connect(self._refresh_view)
        search_row.addWidget(search_label)
        search_row.addWidget(self.search_edit)
        content.addLayout(search_row)

        # Status / busy message
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #b08800;")
        content.addWidget(self.status_label)

        self.table = QTableView()
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(
            self._open_actions_for_selected_from_index
        )
        content.addWidget(self.table)

        return content

    def _set_busy(self, busy: bool, message: str = "") -> None:
        app = QApplication.instance()
        controls = [
            self.btn_my,
            self.btn_overdue,
            self.btn_add,
            self.theme_slider,
            self.search_edit,
            self.table,
        ]
        for c in controls:
            c.setEnabled(not busy)

        self.status_label.setText(message if busy else "")

        if not app:
            return
        if busy:
            app.setOverrideCursor(Qt.WaitCursor)
        else:
            app.restoreOverrideCursor()

    # ---- Theme ----

    def _on_theme_slider_changed(self, value: int):
        app = QApplication.instance()
        if not app:
            return
        mode = ThemeMode.DARK if value >= 1 else ThemeMode.LIGHT
        apply_theme(app, mode)

    # ---- View helpers ----

    def _filtered_items(self) -> List[PipelineItem]:
        items = [i for i in self.all_items if i.is_visible_now]
        if self.view_mode == "overdue":
            items = [i for i in items if i.priority == "red"]

        query = self.search_edit.text().strip().lower()
        if query:

            def matches(i: PipelineItem) -> bool:
                haystack = " ".join(
                    [i.candidate_name or "", i.client or "", i.role or ""]
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
        self.btn_overdue.setChecked(False)
        self._refresh_view()

    def _toggle_overdue(self):
        if self.view_mode == "overdue":
            self.view_mode = "my"
            self.btn_overdue.setChecked(False)
        else:
            self.view_mode = "overdue"
            self.btn_overdue.setChecked(True)
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

    # ---- Candidate actions ----

    def _open_actions_for_selected_from_index(self, index: QModelIndex):
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
            if dlg.note_text:
                self._set_busy(True, "Saving note...")
                append_note(item, dlg.note_text)
                row_dict = pipeline_item_to_sheet(item)
                update_pipeline_row(item.id, row_dict)
                self.all_items = load_items_for_owner(CURRENT_OWNER)
                self._refresh_view()
                self._set_busy(False)
            return

        if dlg.remove_requested:
            self._set_busy(True, "Removing candidate...")
            delete_pipeline_row(item.id)
            self.all_items = load_items_for_owner(CURRENT_OWNER)
            self._refresh_view()
            self._set_busy(False)
            return

        self._set_busy(True, "Updating candidate...")

        if dlg.selected_action is not None:
            apply_action(item, dlg.selected_action)

        if dlg.note_text:
            append_note(item, dlg.note_text)

        row_dict = pipeline_item_to_sheet(item)
        update_pipeline_row(item.id, row_dict)

        self.all_items = load_items_for_owner(CURRENT_OWNER)
        self._refresh_view()
        self._set_busy(False)

    # ---- Add / update candidate ----

    def _add_candidate(self):
        dlg = AddCandidateDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()
        name = data["candidate_name"]
        if not name:
            QMessageBox.warning(
                self,
                "Missing name",
                "Candidate name is required.",
            )
            return

        self._set_busy(True, "Saving candidate...")

        self.all_items = load_items_for_owner(CURRENT_OWNER)
        existing = find_candidate_by_name(self.all_items, CURRENT_OWNER, name)

        now = datetime.utcnow()
        today = date.today()

        if existing is None:
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
                next_check_at=today + timedelta(days=3),
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
            existing.client = merge_csv_field(existing.client, data["client"])
            existing.role = merge_csv_field(existing.role, data["role"])
            existing.stage = data["stage"] or existing.stage
            existing.updated_at = now

            row_dict = pipeline_item_to_sheet(existing)
            update_pipeline_row(existing.id, row_dict)

        self._refresh_view()
        self._set_busy(False)
