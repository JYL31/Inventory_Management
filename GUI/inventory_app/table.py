"""Reusable editable table widget for SQLite records."""

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from .constants import TABLES


class RecordTable(QTableWidget):
    edit_requested = Signal(str, object, str, str)
    description_requested = Signal(str)
    reference_files_requested = Signal(str)

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

    @staticmethod
    def _description_preview(value: object, max_length: int = 100) -> str:
        if value is None:
            return ""

        text = str(value).strip()

        # Keep paragraphs visually separated in the tooltip,
        # but make the table preview compact.
        preview = " ".join(text.split())

        if len(preview) > max_length:
            return preview[:max_length].rstrip() + "..."

        return preview

    @staticmethod
    def _display_value(value: object, column: int, table_key: str) -> str:
        if value is None:
            return ""
        if table_key == 'purchase' and column in (7, 8, 9):
            try:
                return format(Decimal(str(value)).quantize(Decimal('0.01')), '.2f')
            except (InvalidOperation, ValueError, TypeError):
                return str(value)
        return str(value)

    def set_records(self, rows: list[tuple]) -> None:
        self.blockSignals(True)
        self.setRowCount(0)
        for row_data in rows:
            row = self.rowCount()
            self.insertRow(row)
            for column, value in enumerate(row_data):
                text = self._display_value(value, column, self.table_key)

                # Job Description: show a compact preview,
                # while keeping the complete text in UserRole.
                if self.table_key == 'maintenance' and (column == 4 or column == 7):
                    full_description = "" if value is None else str(value)
                    text = self._description_preview(full_description)

                    item = QTableWidgetItem(text)

                    # Keep the original full description attached to the item.
                    item.setData(Qt.ItemDataRole.UserRole, full_description)

                    # Show the complete description when hovering.
                    item.setToolTip(full_description)

                    # Don't allow Job Description to enter normal cell editing.
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                else:
                    item = QTableWidgetItem(text)

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

    def mouseDoubleClickEvent(self, event) -> None:
        item = self.itemAt(event.position().toPoint())

        if item is not None and self.table_key == 'maintenance' and item.column() == 8:
            self.reference_files_requested.emit(str(item.text()))
            return

        if (
            item is not None
            and self.table_key == 'maintenance'
            and (item.column() == 4 or item.column() == 7)
        ):
            description = item.data(Qt.ItemDataRole.UserRole) or ""
            self.description_requested.emit(str(description))
            return

        super().mouseDoubleClickEvent(event)