"""Main PySide6 window coordinating UI actions with the repository."""

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget, QComboBox, QPlainTextEdit,
                               QDialog, QDialogButtonBox)

from .constants import TYPES
from .dashboard import Dashboard
from .dialogs import EquipmentDialog, MaintenanceDialog, RecordDialog, set_autocomplete
from .repository import InventoryRepository
from .table import RecordTable


class InventoryWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.repository = InventoryRepository()
        self.tables: dict[str, RecordTable] = {}
        self.setWindowTitle('ANMA Inventory Management System')
        self.resize(1600, 900)
        self._build_ui()
        self.refresh_tables()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addLayout(self._search_bar())
        content = QHBoxLayout()
        content.addWidget(self._actions(), 0)
        self.tabs = QTabWidget()
        self.dashboard = Dashboard(self.add_purchase, self.add_outflow, self.show_inventory)
        self.tabs.addTab(self.dashboard, 'Dashboard')
        self.tab_keys = []
        for key, title in (('inventory', 'Inventory'), ('equipment', 'Equipment List'), ('purchase', 'Purchase History'),
                   ('outflow', 'Outflow History'), ('maintenance', 'Maintenance')):
            table = RecordTable(key)
            table.edit_requested.connect(self.update_field)

            if key == 'maintenance':
                table.description_requested.connect(
                    self.show_job_description
                )
                table.reference_files_requested.connect(self.open_reference_files)

            self.tables[key] = table
            self.tab_keys.append(key)
            self.tabs.addTab(table, title)
        content.addWidget(self.tabs, 1)
        layout.addLayout(content, 1)
        self.status = QLabel('Ready')
        self.status.setFrameShape(QFrame.Shape.StyledPanel)
        layout.addWidget(self.status)
        self.setCentralWidget(root)

    def _search_bar(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        row = QHBoxLayout()
        self.search_text = QLineEdit()
        self.search_text.setPlaceholderText('Search Equipment ID, Equipment Name, or Maintenance ID')
        set_autocomplete(self.search_text, self.repository.autocomplete_values('Search'))
        self.search_text.returnPressed.connect(self.refresh_tables)
        row.addWidget(self.search_text, 1)
        self.stock = QComboBox()
        self.stock.addItems(('All', 'In Stock', 'Out of Stock'))
        row.addWidget(self.stock)
        self.item_type = QComboBox()
        self.item_type.addItems(('All spare part types', *TYPES))
        self.item_type.currentIndexChanged.connect(self.refresh_tables)
        row.addWidget(self.item_type)
        search = QPushButton('Search')
        search.clicked.connect(self.refresh_tables)
        clear = QPushButton('Clear')
        clear.clicked.connect(self.clear_search)
        row.addWidget(search)
        row.addWidget(clear)
        layout.addLayout(row)
        return layout

    def _actions(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title = QLabel('ANMA\nInventory Management')
        title.setStyleSheet('font-size: 22px; font-weight: bold;')
        layout.addWidget(title)
        for label, handler in (('Add Purchase', self.add_purchase), ('Record Maintenance', self.add_outflow), ('Add Equipment', self.add_equipment),
                       ('Export to Excel', self.export), ('Delete Entry', self.delete_selected)):
            button = QPushButton(label)
            button.clicked.connect(handler)
            layout.addWidget(button)
        layout.addStretch()
        return panel

    def current_type(self) -> str:
        return 'All' if self.item_type.currentIndex() == 0 else self.item_type.currentText()

    def refresh_tables(self) -> None:
        try:
            set_autocomplete(self.search_text, self.repository.autocomplete_values('Search'))
            self.dashboard.refresh(self.repository.dashboard_data())
            for key, table in self.tables.items():
                table.set_records(self.repository.records(key, self.search_text.text().strip(), self.current_type(), self.stock.currentText()))
            self.set_status('Records loaded.')
        except Exception as error:
            self.show_error(error)

    def show_inventory(self) -> None:
        self.tabs.setCurrentIndex(1)

    def clear_search(self) -> None:
        self.search_text.clear()
        self.stock.setCurrentText('All')
        self.item_type.setCurrentIndex(0)
        self.refresh_tables()
        self.set_status('Database unfiltered.')

    def add_purchase(self) -> None:
        fields = ['Name', 'Specification', 'Type', 'Usage', 'Supplier', 'Quantity', 'Unit Price', 'Shipping', 'Received Date', 'Applied By', 'Responsible By']
        dialog = RecordDialog('Add Purchase', fields, submit=self.repository.add_purchase, parent=self,
                      autocomplete_provider=self.repository.autocomplete_values)
        dialog.error_reported.connect(self.show_error)
        self.run_dialog_operation(dialog, success='Purchase recorded.')

    def add_outflow(self) -> None:
        dialog = MaintenanceDialog(self.repository.add_maintenance, parent=self,
                       autocomplete_provider=self.repository.autocomplete_values)
        dialog.error_reported.connect(self.show_error)
        self.run_dialog_operation(dialog, success='Outflow recorded.')

    def add_equipment(self) -> None:
        dialog = EquipmentDialog(self.repository.add_equipment, parent=self)
        dialog.error_reported.connect(self.show_error)
        self.run_dialog_operation(dialog, success='Equipment added.')

    def update_field(self, table_key: str, record_id: int, field: str, value: str) -> None:
        self.run_operation(self.repository.update_field, table_key, record_id, field, value, success='Record updated.')

    def delete_selected(self) -> None:
        if self.tabs.currentIndex() == 0:
            self.show_error('Select an entry from one of the history or inventory tabs to delete.')
            return
        key = self.tab_keys[self.tabs.currentIndex() - 1]
        record_id = self.tables[key].selected_id()
        if record_id is None:
            self.show_error('Select an entry to delete.')
            return
        if QMessageBox.question(self, 'Delete entry', 'Delete the selected entry?') == QMessageBox.StandardButton.Yes:
            self.run_operation(self.repository.delete, key, record_id, success='Entry deleted.')

    def export(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(self, 'Export to Excel', 'inventory.xlsx', 'Excel files (*.xlsx)')
        if destination:
            self.run_operation(self.repository.export, destination, success=f'File saved to {destination}')

    def run_operation(self, operation, *args, success: str) -> None:
        try:
            operation(*args)
            self.refresh_tables()
            self.set_status(success)
        except Exception as error:
            self.show_error(error)
            self.refresh_tables()

    def run_dialog_operation(self, dialog: RecordDialog, *, success: str) -> None:
        if dialog.exec():
            try:
                self.refresh_tables()
                self.set_status(success)
            except Exception as error:
                self.show_error(error)

    def set_status(self, message: str) -> None:
        self.status.setText(message)
        self.status.setStyleSheet('')

    def show_error(self, error: Exception | str) -> None:
        self.status.setText(str(error))
        self.status.setStyleSheet('color: #b42318; font-weight: bold;')

    def show_job_description(self, description: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle('Job Description')
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        text_edit = QPlainTextEdit()
        text_edit.setPlainText(description)
        text_edit.setReadOnly(True)

        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)

        layout.addWidget(buttons)

        dialog.exec()

    def open_reference_files(self, paths: str) -> None:
        for path in paths.splitlines():
            if path.strip() and not QDesktopServices.openUrl(QUrl.fromLocalFile(path.strip())):
                self.show_error(f'Unable to open reference file: {path.strip()}')
