"""SQLite persistence and business operations for inventory records."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator

import pandas as pd

from .constants import DATABASE_PATH, TABLES


class InventoryRepository:
    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        database = sqlite3.connect(self.database_path)
        try:
            yield database
            database.commit()
        except Exception:
            database.rollback()
            raise
        finally:
            database.close()

    def records(self, table_key: str, text: str = "", item_type: str = "All", stock: str = "All") -> list[tuple]:
        table_name, _ = TABLES[table_key]
        clauses: list[str] = []
        values: list[object] = []
        if item_type != "All":
            clauses.append('Type = ?')
            values.append(item_type)
        if stock == "In Stock":
            clauses.append('Quantity >= 1')
        elif stock == "Out of Stock":
            clauses.append('Quantity < 1')
        if text:
            searchable = ('Name', 'Specification', 'Usage') if table_key != 'outflow' else ('Name', 'Specification')
            clauses.append('(' + ' OR '.join(f'"{field}" LIKE ?' for field in searchable) + ')')
            values.extend([f'%{text}%'] * len(searchable))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as database:
            return database.execute(f'SELECT * FROM "{table_name}"{where}', values).fetchall()

    def add_purchase(self, values: dict[str, str]) -> None:
        name, quantity, item_type = values['Name'].strip(), values['Quantity'].strip(), values['Type']
        if not name or not quantity:
            raise ValueError("Name and quantity are required.")
        if item_type == "Select a Type":
            raise ValueError("Select an item type.")
        try:
            quantity_number = int(quantity)
            unit_price = self._number_or_none(values['Unit Price'], 'Unit price')
            shipping = self._number_or_none(values['Shipping'], 'Shipping')
        except ValueError as error:
            raise ValueError(str(error)) from error
        today = str(date.today())
        specification = values['Specification'].strip()
        total = None if unit_price is None else quantity_number * unit_price + (shipping or 0)
        with self.connection() as database:
            database.execute(
                '''INSERT INTO Inventory(Name, Specification, Type, Usage, Quantity, "Last Update")
                   VALUES(?, ?, ?, ?, COALESCE((SELECT Quantity FROM Inventory WHERE Name=? AND Specification=?), 0) + ?, ?)
                   ON CONFLICT(Name, Specification) DO UPDATE SET Quantity=excluded.Quantity, "Last Update"=excluded."Last Update"''',
                (name, specification, item_type, values['Usage'].strip(), name, specification, quantity_number, today),
            )
            database.execute(
                '''INSERT INTO "Purchase History"(Name, Specification, Type, Usage, Supplier, Quantity, "Unit Price", Shipping, "Total Price", "Received Date", "Applied By", "Responsible By")
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, specification, item_type, values['Usage'].strip(), values['Supplier'].strip(), quantity_number,
                 unit_price, shipping, total, values['Received Date'].strip(), values['Applied By'].strip(), values['Responsible By'].strip()),
            )

    def add_outflow(self, values: dict[str, str]) -> None:
        name, specification = values['Name'].strip(), values['Specification'].strip()
        if not name or not values['Quantity'].strip():
            raise ValueError("Name and quantity are required.")
        if values['Type'] == "Select a Type":
            raise ValueError("Select an item type.")
        try:
            quantity = int(values['Quantity'])
        except ValueError as error:
            raise ValueError("Quantity must be an integer.") from error
        with self.connection() as database:
            exists = database.execute('SELECT 1 FROM Inventory WHERE Name=? AND Specification=?', (name, specification)).fetchone()
            if not exists:
                raise ValueError("No matching item exists in inventory.")
            database.execute('UPDATE Inventory SET Quantity=Quantity-?, "Last Update"=? WHERE Name=? AND Specification=?',
                             (quantity, str(date.today()), name, specification))
            database.execute('''INSERT INTO "Outflow History"(Name, Specification, Type, Quantity, Description, Date)
                                VALUES(?, ?, ?, ?, ?, ?)''',
                             (name, specification, values['Type'], quantity, values['Description'].strip(), values['Date'].strip()))

    def update_field(self, table_key: str, record_id: int, field: str, value: str) -> None:
        table_name, fields = TABLES[table_key]
        if field not in fields or field == 'ID':
            raise ValueError("The ID field cannot be edited.")
        with self.connection() as database:
            database.execute(f'UPDATE "{table_name}" SET "{field}"=? WHERE ID=?', (value or None, record_id))
            if table_key == 'inventory':
                database.execute('UPDATE Inventory SET "Last Update"=? WHERE ID=?', (str(date.today()), record_id))

    def delete(self, table_key: str, record_id: int) -> None:
        table_name, _ = TABLES[table_key]
        with self.connection() as database:
            if table_key in ('purchase', 'outflow'):
                history = database.execute(f'SELECT Name, Specification, Quantity FROM "{table_name}" WHERE ID=?', (record_id,)).fetchone()
                if history:
                    adjustment = -history[2] if table_key == 'purchase' else history[2]
                    database.execute('UPDATE Inventory SET Quantity=Quantity+?, "Last Update"=? WHERE Name=? AND Specification=?',
                                     (adjustment, str(date.today()), history[0], history[1]))
            database.execute(f'DELETE FROM "{table_name}" WHERE ID=?', (record_id,))
            database.execute(f'UPDATE "{table_name}" SET ID = (SELECT COUNT(*) FROM "{table_name}" AS prior WHERE prior.rowid <= "{table_name}".rowid)')

    def export(self, destination: str) -> None:
        with self.connection() as database, pd.ExcelWriter(destination) as writer:
            for _, (table_name, _) in TABLES.items():
                pd.read_sql_query(f'SELECT * FROM "{table_name}"', database).to_excel(writer, sheet_name=table_name[:31], index=False)

    @staticmethod
    def _number_or_none(value: str, label: str) -> float | None:
        if not value.strip():
            return None
        try:
            return float(value)
        except ValueError as error:
            raise ValueError(f"{label} must be a number.") from error
