"""
Dialog windows for the RecToDo application.
"""

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QPushButton,
)
from config import STAGE_OPTIONS


class AddCandidateDialog(QDialog):
    """
    Dialog for adding a new candidate or updating an existing one.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Update Candidate")
        self.resize(400, 300)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.client_edit = QLineEdit()
        self.role_edit = QLineEdit()

        self.stage_combo = QComboBox()
        self.stage_combo.addItems(STAGE_OPTIONS)
        self.next_action_edit = QLineEdit()
        self.notes_edit = QTextEdit()

        layout.addRow("Candidate name *", self.name_edit)
        layout.addRow("Email", self.email_edit)
        layout.addRow("Phone", self.phone_edit)
        layout.addRow("Client", self.client_edit)
        layout.addRow("Role", self.role_edit)
        layout.addRow("Stage", self.stage_combo)
        layout.addRow("Next action", self.next_action_edit)
        layout.addRow("Notes", self.notes_edit)

        btn_row = QHBoxLayout()
        self.btn_ok = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addRow(btn_row)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def get_data(self) -> dict:
        """
        Get the data entered in the dialog.
        
        Returns:
            Dictionary containing all form field values
        """
        return {
            "candidate_name": self.name_edit.text().strip(),
            "candidate_email": self.email_edit.text().strip(),
            "candidate_phone": self.phone_edit.text().strip(),
            "client": self.client_edit.text().strip(),
            "role": self.role_edit.text().strip(),
            "stage": self.stage_combo.currentText(),
            "next_action": self.next_action_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
        }
