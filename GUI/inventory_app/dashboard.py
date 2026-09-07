"""Dashboard widgets for the inventory application's start-up view."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)


class MetricCard(QFrame):
    def __init__(self, label: str, accent: str) -> None:
        super().__init__()
        self.setObjectName('metricCard')
        self.setStyleSheet(f'''QFrame#metricCard {{ background: white; border: 1px solid #dce3ea;
            border-left: 5px solid {accent}; border-radius: 8px; }}''')
        layout = QVBoxLayout(self)
        caption = QLabel(label.upper())
        caption.setStyleSheet('color: #667085; font-size: 11px; font-weight: 600;')
        self.value = QLabel('0')
        self.value.setStyleSheet('color: #172b4d; font-size: 28px; font-weight: 700;')
        layout.addWidget(caption)
        layout.addWidget(self.value)

    def set_value(self, value: int) -> None:
        self.value.setText(f'{value:,}')


class Dashboard(QWidget):
    """A live snapshot of stock levels, alerts, and recent movement."""
    def __init__(self, add_purchase, add_outflow, show_inventory) -> None:
        super().__init__()
        self._build_ui(add_purchase, add_outflow, show_inventory)

    def _build_ui(self, add_purchase, add_outflow, show_inventory) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        heading = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('Inventory dashboard')
        title.setStyleSheet('font-size: 26px; font-weight: 700; color: #172b4d;')
        subtitle = QLabel('Keep stock available and respond to shortages before they affect operations.')
        subtitle.setStyleSheet('color: #667085;')
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        heading.addLayout(title_box)
        heading.addStretch()
        for label, callback in (('Record purchase', add_purchase), ('Record outflow', add_outflow), ('View inventory', show_inventory)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            heading.addWidget(button)
        layout.addLayout(heading)

        metrics = QGridLayout()
        self.cards = {
            'part_count': MetricCard('Tracked parts', '#2f80ed'),
            'units_on_hand': MetricCard('Units on hand', '#27ae60'),
            'low_stock_count': MetricCard('Low stock (1–5)', '#f2994a'),
            'out_of_stock_count': MetricCard('Out of stock', '#eb5757'),
        }
        for column, card in enumerate(self.cards.values()):
            metrics.addWidget(card, 0, column)
        layout.addLayout(metrics)

        tables = QHBoxLayout()
        self.low_stock = self._table(('Part', 'Specification', 'Type', 'Qty', 'Location', 'Updated'))
        self.maintenance_activity = self._table(('Equipment', 'Equipment Name', 'Technician', 'Job', 'Finish Time'))
        self.activity = self._table(('Movement', 'Part', 'Specification', 'Change', 'Date'))
        self.type_breakdown = self._table(('Type', 'Parts', 'Units'))
        left = QVBoxLayout()
        left.addWidget(self._section('Stock attention', 'Parts needing replenishment (five or fewer units).', self.low_stock), 3)
        left.addWidget(self._section('Recent maintenance', 'The ten latest completed maintenance activities.', self.maintenance_activity), 2)
        tables.addLayout(left, 3)
        right = QVBoxLayout()
        right.addWidget(self._section('Recent activity', 'Latest purchases and outflows.', self.activity), 3)
        right.addWidget(self._section('Stock by type', 'Current spread across spare-part categories.', self.type_breakdown), 2)
        tables.addLayout(right, 2)
        layout.addLayout(tables, 1)

    @staticmethod
    def _table(headers: tuple[str, ...]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        return table

    @staticmethod
    def _section(title: str, subtitle: str, table: QTableWidget) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet('QFrame { background: white; border: 1px solid #dce3ea; border-radius: 8px; }')
        layout = QVBoxLayout(panel)
        heading = QLabel(title)
        heading.setStyleSheet('font-size: 16px; font-weight: 700; color: #172b4d; border: none;')
        hint = QLabel(subtitle)
        hint.setStyleSheet('color: #667085; border: none;')
        layout.addWidget(heading)
        layout.addWidget(hint)
        layout.addWidget(table, 1)
        return panel

    def refresh(self, data: dict[str, list[tuple] | int]) -> None:
        for key, card in self.cards.items():
            card.set_value(int(data[key]))
        self._set_rows(self.low_stock, data['low_stock'])
        self._set_rows(self.maintenance_activity, data['maintenance_activity'])
        self._set_rows(self.type_breakdown, data['type_breakdown'])
        activity_rows = [(kind, name, specification, f'{change:+d}', movement_date)
                         for kind, name, specification, change, movement_date, _ in data['activity']]
        self._set_rows(self.activity, activity_rows)

    @staticmethod
    def _set_rows(table: QTableWidget, rows: list[tuple]) -> None:
        table.setRowCount(0)
        for row_data in rows:
            row = table.rowCount()
            table.insertRow(row)
            for column, value in enumerate(row_data):
                item = QTableWidgetItem('' if value is None else str(value))
                if table is not None and table.horizontalHeaderItem(column).text() in ('Qty', 'Change'):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, column, item)
