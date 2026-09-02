"""Data-entry dialogs for purchases and stock outflows."""

from collections.abc import Callable

from PySide6.QtCore import QDate, QTime, Signal
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
                               QGroupBox, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QScrollArea,
                               QTimeEdit, QVBoxLayout, QWidget)

from .constants import TYPES


class RecordDialog(QDialog):
    error_reported = Signal(str)

    def __init__(self, title: str, fields: list[str], description_field: bool = False,
                 submit: Callable[[dict[str, str]], None] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.submit = submit
        self.widgets: dict[str, QLineEdit | QComboBox | QPlainTextEdit | QDateEdit] = {}
        form = QFormLayout(self)
        for field in fields:
            if field == 'Type':
                widget = QComboBox()
                widget.addItems(('Select a Type', *TYPES))
            elif field == 'Description' and description_field:
                widget = QPlainTextEdit()
                widget.setFixedHeight(90)
            elif field == 'Received Date':
                widget = QDateEdit(QDate.currentDate())
                widget.setCalendarPopup(True)
                widget.setDisplayFormat('yyyy-MM-dd')
            else:
                widget = QLineEdit()
            self.widgets[field] = widget
            form.addRow(f"{'*' if field in ('Name', 'Quantity') else ''}{field}", widget)
        self.error_message = QLabel()
        self.error_message.setWordWrap(True)
        self.error_message.setStyleSheet('color: #b42318; font-weight: bold;')
        self.error_message.hide()
        form.addRow(self.error_message)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict[str, str]:
        return {
            name: widget.currentText() if isinstance(widget, QComboBox)
            else widget.toPlainText() if isinstance(widget, QPlainTextEdit)
            else widget.date().toString('yyyy-MM-dd') if isinstance(widget, QDateEdit)
            else widget.text()
            for name, widget in self.widgets.items()
        }

    def _validate_and_accept(self) -> None:
        values = self.values()
        if not values['Name'].strip() or not values['Quantity'].strip():
            message = 'Name and quantity are required.'
            self.show_error(message)
            self.error_reported.emit(message)
            return
        if self.submit:
            try:
                self.submit(values)
            except Exception as error:
                message = str(error)
                self.show_error(message)
                self.error_reported.emit(message)
                return
        self.error_message.hide()
        self.accept()

    def show_error(self, message: str) -> None:
        self.error_message.setText(message)
        self.error_message.show()


class MaintenanceDialog(QDialog):
    error_reported = Signal(str)

    def __init__(self, submit: Callable[[dict[str, str], list[dict[str, str]]], None], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Record Maintenance')
        self.submit = submit
        self.part_rows: list[dict[str, QLineEdit | QComboBox]] = []
        layout = QVBoxLayout(self)

        maintenance = QGroupBox('Maintenance')
        maintenance_form = QFormLayout(maintenance)
        self.maintenance_widgets: dict[str, QLineEdit | QPlainTextEdit | QDateEdit | QTimeEdit] = {}
        for field in ('Equipment ID', 'Equipment Name', 'Technician Name', 'Job Description',
                      'Start Date', 'Start Time', 'Finish Date', 'Finish Time'):
            if field in ('Start Date', 'Finish Date'):
                widget = QDateEdit(QDate.currentDate())
                widget.setCalendarPopup(True)
                widget.setDisplayFormat('yyyy-MM-dd')
            elif field in ('Start Time', 'Finish Time'):
                widget = QTimeEdit(QTime.currentTime())
                widget.setDisplayFormat('HH:mm')
            else:
                widget = QPlainTextEdit() if field == 'Job Description' else QLineEdit()
            if isinstance(widget, QPlainTextEdit):
                widget.setFixedHeight(65)
            self.maintenance_widgets[field] = widget
            maintenance_form.addRow(field, widget)
        layout.addWidget(maintenance)

        parts = QGroupBox('Parts Used')
        parts_layout = QVBoxLayout(parts)
        self.parts_container = QWidget()
        self.parts_grid = QGridLayout(self.parts_container)
        for column, label in enumerate(('Part Name', 'Specification', 'Type', 'Quantity')):
            self.parts_grid.addWidget(QLabel(label), 0, column)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.parts_container)
        scroll.setMinimumHeight(145)
        parts_layout.addWidget(scroll)
        add_part = QPushButton('Add Part')
        add_part.clicked.connect(self.add_part)
        parts_layout.addWidget(add_part)
        layout.addWidget(parts)

        self.error_message = QLabel()
        self.error_message.setWordWrap(True)
        self.error_message.setStyleSheet('color: #b42318; font-weight: bold;')
        self.error_message.hide()
        layout.addWidget(self.error_message)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText('Save Maintenance')
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.add_part()

    def add_part(self) -> None:
        row = len(self.part_rows) + 1
        widgets: dict[str, QLineEdit | QComboBox] = {
            'Part Name': QLineEdit(), 'Specification': QLineEdit(),
            'Type': QComboBox(), 'Quantity': QLineEdit(),
        }
        widgets['Type'].addItems(('Select a Type', *TYPES))
        for column, field in enumerate(('Part Name', 'Specification', 'Type', 'Quantity')):
            self.parts_grid.addWidget(widgets[field], row, column)
        self.part_rows.append(widgets)

    def _values(self) -> tuple[dict[str, str], list[dict[str, str]]]:
        fields = {
            name: widget.toPlainText() if isinstance(widget, QPlainTextEdit)
            else widget.date().toString('yyyy-MM-dd') if isinstance(widget, QDateEdit)
            else widget.time().toString('HH:mm') if isinstance(widget, QTimeEdit)
            else widget.text()
            for name, widget in self.maintenance_widgets.items()
        }
        maintenance = {name: value for name, value in fields.items()
                       if name not in ('Start Date', 'Finish Date')}
        maintenance['Start Time'] = f"{fields['Start Date']} {fields['Start Time']}"
        maintenance['Finish Time'] = f"{fields['Finish Date']} {fields['Finish Time']}"
        parts = [{
            name: widget.currentText() if isinstance(widget, QComboBox) else widget.text()
            for name, widget in row.items()
        } for row in self.part_rows]
        return maintenance, parts

    def _save(self) -> None:
        maintenance, parts = self._values()
        required = ('Equipment ID', 'Equipment Name', 'Technician Name', 'Job Description',
                'Start Time', 'Finish Time')
        if any(not maintenance[field].strip() for field in required):
            self.show_error('Complete all maintenance fields.')
            return
        if not parts or any(not part['Part Name'].strip() or not part['Quantity'].strip() for part in parts):
            self.show_error('Add at least one part with a name and quantity.')
            return
        if any(part['Type'] == 'Select a Type' for part in parts):
            self.show_error('Select an item type for every part.')
            return
        try:
            self.submit(maintenance, parts)
        except Exception as error:
            self.show_error(str(error))
            self.error_reported.emit(str(error))
            return
        self.accept()

    def show_error(self, message: str) -> None:
        self.error_message.setText(message)
        self.error_message.show()
