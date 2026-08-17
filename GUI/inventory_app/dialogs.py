"""Data-entry dialogs for purchases and stock outflows."""

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox, QPlainTextEdit

from .constants import TYPES


class RecordDialog(QDialog):
    def __init__(self, title: str, fields: list[str], description_field: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.widgets: dict[str, QLineEdit | QComboBox | QPlainTextEdit] = {}
        form = QFormLayout(self)
        for field in fields:
            if field == 'Type':
                widget = QComboBox()
                widget.addItems(('Select a Type', *TYPES))
            elif field == 'Description' and description_field:
                widget = QPlainTextEdit()
                widget.setFixedHeight(90)
            else:
                widget = QLineEdit()
            self.widgets[field] = widget
            form.addRow(f"{'*' if field in ('Name', 'Quantity') else ''}{field}", widget)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict[str, str]:
        return {name: widget.currentText() if isinstance(widget, QComboBox) else widget.toPlainText() if isinstance(widget, QPlainTextEdit) else widget.text()
                for name, widget in self.widgets.items()}

    def _validate_and_accept(self) -> None:
        values = self.values()
        if not values['Name'].strip() or not values['Quantity'].strip():
            QMessageBox.warning(self, 'Missing values', 'Name and quantity are required.')
            return
        self.accept()
