"""Reusable editable table widget for SQLite records."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from .constants import TABLES


class RecordTable(QTableWidget):
    edit_requested = Signal(str, object, str, str)

    def __init__(self, table_key: str) -> None:
        _, columns = TABLES[table_key]
        super().__init__(0, len(columns))
        self.table_key, self.columns = table_key, columns
        self.setHorizontalHeaderLabels(columns)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.itemChanged.connect(self._request_edit)

    def set_records(self, rows: list[tuple]) -> None:
        self.blockSignals(True)
        self.setRowCount(0)
        for row_data in rows:
            row = self.rowCount()
            self.insertRow(row)
            for column, value in enumerate(row_data):
                item = QTableWidgetItem("" if value is None else str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(row, column, item)
        self.blockSignals(False)

    def selected_id(self) -> object | None:
        row = self.currentRow()
        item = self.item(row, 0) if row >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _request_edit(self, item: QTableWidgetItem) -> None:
        record_id = self.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.edit_requested.emit(self.table_key, record_id, self.columns[item.column()], item.text())
