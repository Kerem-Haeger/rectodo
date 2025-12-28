"""
Dialog windows for RecToDo.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QLineEdit,
)

from actions import Action
from config import STAGE_OPTIONS
from domain import PipelineItem


class AddCandidateDialog(QDialog):
    """Dialog for adding or updating a candidate."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Update Candidate")
        self.resize(350, 200)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.client_edit = QLineEdit()
        self.role_edit = QLineEdit()

        self.stage_combo = QComboBox()
        self.stage_combo.addItems(STAGE_OPTIONS)

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


class CandidateActionsDialog(QDialog):
    """Dialog presenting action buttons for a candidate."""

    def __init__(self, item: PipelineItem, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update candidate")
        self.resize(400, 250)
        self.selected_action: Optional[Action] = None
        self.note_text: str = ""

        layout = QVBoxLayout(self)

        header = QLabel(f"{item.candidate_name}\n{item.client} – {item.role}")
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
            if self.note_text:
                self.note_text += "\n\n" + text.strip()
            else:
                self.note_text = text.strip()
