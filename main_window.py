"""
Main application window for the RecToDo application.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
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
    QMessageBox,
    QSlider,
)

from config import CURRENT_OWNER
from data_loader import load_items_for_owner, kpi_counts
from dialogs import AddCandidateDialog
from domain import PipelineItem, pipeline_item_to_sheet
from sheets_repo import append_pipeline_row, update_pipeline_row
from table_model import PipelineTableModel
from theme import apply_theme, ThemeMode
from utils import merge_csv_field, find_candidate_by_name


class MainWindow(QMainWindow):
    """
    Main application window for managing recruitment pipeline.
    """
    
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

        # Build sidebar
        sidebar = self._build_sidebar()
        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar)
        sidebar_frame.setFixedWidth(200)
        main_layout.addWidget(sidebar_frame)

        # Build main content area
        content = self._build_content_area()
        main_layout.addLayout(content)

        # Initial view
        self._refresh_view()

    def _build_sidebar(self) -> QVBoxLayout:
        """
        Build the sidebar with navigation and actions.
        
        Returns:
            QVBoxLayout containing sidebar widgets
        """
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

        self.btn_log_contact = QPushButton("Log contact (today)")
        sidebar.addWidget(self.btn_log_contact)

        # Theme slider: 0 = light, 1 = dark
        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme")
        theme_row.addWidget(theme_label)

        self.theme_slider = QSlider(Qt.Horizontal)
        self.theme_slider.setRange(0, 1)
        self.theme_slider.setValue(1)  # default: dark
        self.theme_slider.setFixedWidth(100)
        self.theme_slider.valueChanged.connect(self._on_theme_slider_changed)

        theme_row.addWidget(self.theme_slider)
        sidebar.addLayout(theme_row)

        sidebar.addStretch(1)

        # Connect signals
        self.btn_my.clicked.connect(self._set_view_my)
        self.btn_overdue.clicked.connect(self._set_view_overdue)
        self.btn_add.clicked.connect(self._add_candidate)
        self.btn_log_contact.clicked.connect(self._log_contact)

        return sidebar

    def _build_content_area(self) -> QVBoxLayout:
        """
        Build the main content area with KPIs, search, and table.
        
        Returns:
            QVBoxLayout containing content widgets
        """
        content = QVBoxLayout()

        # KPI row
        kpi_row = self._build_kpi_row()
        content.addLayout(kpi_row)

        # Search row
        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Candidate, client, role, next action..."
        )
        self.search_edit.textChanged.connect(self._refresh_view)
        search_row.addWidget(search_label)
        search_row.addWidget(self.search_edit)
        content.addLayout(search_row)

        # Table
        self.table = QTableView()
        self.table.setSortingEnabled(True)
        content.addWidget(self.table)

        return content

    def _build_kpi_row(self) -> QHBoxLayout:
        """
        Build the KPI display row.
        
        Returns:
            QHBoxLayout containing KPI labels
        """
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

        return kpi_row

    def _get_selected_item(self) -> Optional[PipelineItem]:
        """
        Get the currently selected pipeline item from the table.
        
        Returns:
            Selected PipelineItem or None if no selection
        """
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

    def _log_contact(self):
        """
        Log contact for the selected candidate (sets last_contact_at to today).
        """
        item = self._get_selected_item()
        if item is None:
            QMessageBox.information(
                self,
                "No candidate selected",
                "Please select a candidate in the table first.",
            )
            return

        now = datetime.utcnow()
        today = date.today()

        # Update domain object
        item.last_contact_at = today
        item.updated_at = now

        # Persist to Google Sheets
        row_dict = pipeline_item_to_sheet(item)
        update_pipeline_row(item.id, row_dict)

        # Reload all items from Sheets and refresh UI
        self.all_items = load_items_for_owner(CURRENT_OWNER)
        self._refresh_view()

    def _on_theme_slider_changed(self, value: int):
        """
        Handle theme slider value changes.
        
        Args:
            value: Slider value (0=light, 1=dark)
        """
        app = QApplication.instance()
        if not app:
            return
        mode = ThemeMode.DARK if value >= 1 else ThemeMode.LIGHT
        apply_theme(app, mode)

    def _filtered_items(self) -> List[PipelineItem]:
        """
        Get filtered items based on view mode and search query.
        
        Returns:
            List of filtered PipelineItems
        """
        items = list(self.all_items)

        # Filter by view mode
        if self.view_mode == "overdue":
            items = [i for i in items if i.priority == "red"]

        # Filter by search text
        query = self.search_edit.text().strip().lower()
        if query:

            def matches(i: PipelineItem) -> bool:
                haystack = " ".join(
                    [
                        i.candidate_name or "",
                        i.client or "",
                        i.role or "",
                        i.next_action or "",
                    ]
                ).lower()
                return query in haystack

            items = [i for i in items if matches(i)]

        return items

    def _refresh_view(self):
        """
        Refresh the table view and KPI displays.
        """
        items = self._filtered_items()
        model = PipelineTableModel(items)
        self.table.setModel(model)

        g, y, r, total = kpi_counts(self.all_items)
        self.kpi_green.setText(f"🟢 Fresh\n{g}")
        self.kpi_yellow.setText(f"🟡 Follow-up\n{y}")
        self.kpi_red.setText(f"🔴 Overdue\n{r}")
        self.kpi_total.setText(f"Total\n{total}")

    def _set_view_my(self):
        """
        Switch to 'my pipeline' view (all items).
        """
        self.view_mode = "my"
        self._refresh_view()

    def _set_view_overdue(self):
        """
        Switch to 'overdue only' view (red priority items).
        """
        self.view_mode = "overdue"
        self._refresh_view()

    def _add_candidate(self):
        """
        Show dialog to add a new candidate or update an existing one.
        """
        dlg = AddCandidateDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()
        name = data["candidate_name"]
        if not name:
            QMessageBox.warning(
                self, "Missing name", "Candidate name is required."
            )
            return

        # Reload items to avoid stale view
        self.all_items = load_items_for_owner(CURRENT_OWNER)

        existing = find_candidate_by_name(self.all_items, CURRENT_OWNER, name)

        now = datetime.utcnow()
        today = date.today()

        if existing is None:
            # Create new candidate
            new_item = PipelineItem(
                id=str(uuid.uuid4()),
                owner=CURRENT_OWNER,
                candidate_name=name,
                candidate_email=data["candidate_email"],
                candidate_phone=data["candidate_phone"],
                client=data["client"],
                role=data["role"],
                stage=data["stage"],
                sent_at=today,
                last_contact_at=None,
                next_action=data["next_action"],
                notes=data["notes"],
                created_at=now,
                updated_at=now,
                archived=False,
            )
            row_dict = pipeline_item_to_sheet(new_item)
            append_pipeline_row(row_dict)
            self.all_items.append(new_item)
        else:
            # Update existing candidate
            existing.client = merge_csv_field(existing.client, data["client"])
            existing.role = merge_csv_field(existing.role, data["role"])
            existing.stage = data["stage"] or existing.stage
            existing.next_action = data["next_action"] or existing.next_action
            if data["notes"]:
                # Append notes with timestamp
                timestamp = now.isoformat(timespec="seconds")
                existing.notes = (
                    existing.notes + "\n\n" if existing.notes else ""
                ) + f"[{timestamp}] {data['notes']}"
            existing.updated_at = now
            existing.sent_at = existing.sent_at or today

            row_dict = pipeline_item_to_sheet(existing)
            update_pipeline_row(existing.id, row_dict)

        self._refresh_view()
