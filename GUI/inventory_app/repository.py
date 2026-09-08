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
            self._migrate_maintenance_schema(database)
            self._migrate_outflow_schema(database)
            yield database
            database.commit()
        except Exception:
            database.rollback()
            raise
        finally:
            database.close()

    @staticmethod
    def _migrate_maintenance_schema(database: sqlite3.Connection) -> None:
        table_info = database.execute('PRAGMA table_info("Maintenance Record")').fetchall()
        if not table_info:
            return
        columns = [row[1] for row in table_info]
        if 'Reference Files' not in columns:
            database.execute('ALTER TABLE "Maintenance Record" ADD COLUMN "Reference Files" TEXT')
            columns.append('Reference Files')
        extra_date_columns = {'Date', 'Start Date', 'Finish Date'} & set(columns)
        if not extra_date_columns:
            return

        rows = database.execute('SELECT * FROM "Maintenance Record"').fetchall()
        values_by_column = [dict(zip(columns, row)) for row in rows]
        database.execute('''CREATE TABLE "Maintenance Record_new" (
                           ID INTEGER PRIMARY KEY,
                           "Equipment ID" TEXT NOT NULL,
                           "Equipment Name" TEXT NOT NULL,
                           "Technician Name" TEXT NOT NULL,
                           "Job Description" TEXT,
                           "Start Time" TEXT NOT NULL,
                           "Finish Time" TEXT NOT NULL,
                           "Parts Used" TEXT,
                           "Reference Files" TEXT
                       )''')
        for values in values_by_column:
            start_date = values.get('Start Date') or values.get('Date')
            finish_date = values.get('Finish Date') or values.get('Date')
            start_time = InventoryRepository._combine_date_time(start_date, values.get('Start Time'))
            finish_time = InventoryRepository._combine_date_time(finish_date, values.get('Finish Time'))
            database.execute('''INSERT INTO "Maintenance Record_new"
                               (ID, "Equipment ID", "Equipment Name", "Technician Name", "Job Description",
                                                                "Start Time", "Finish Time", "Parts Used", "Reference Files")
                                                             VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (values['ID'], values['Equipment ID'], values['Equipment Name'], values['Technician Name'],
                                                            values.get('Job Description'), start_time, finish_time, values.get('Parts Used'),
                                                            values.get('Reference Files')))
        database.execute('DROP TABLE "Maintenance Record"')
        database.execute('ALTER TABLE "Maintenance Record_new" RENAME TO "Maintenance Record"')

    @staticmethod
    def _combine_date_time(selected_date: str | None, selected_time: str | None) -> str:
        if selected_date and selected_time:
            return f'{selected_date} {selected_time}'
        return selected_time or selected_date or ''

    @staticmethod
    def _migrate_outflow_schema(database: sqlite3.Connection) -> None:
        table_info = database.execute('PRAGMA table_info("Outflow History")').fetchall()
        if not table_info:
            return

        columns = [row[1] for row in table_info]
        if 'Maintenance ID' in columns and 'Maintenace ID' not in columns:
            return

        legacy_maintenance_id = 'Maintenace ID' if 'Maintenace ID' in columns else 'Maintenance ID'
        rows = database.execute(
            f'SELECT "Outflow ID", "{legacy_maintenance_id}", "Part Name", Specification, Type, Quantity, Date FROM "Outflow History"'
        ).fetchall()

        if 'Maintenace ID' in columns and 'Maintenance ID' not in columns:
            database.execute('ALTER TABLE "Outflow History" RENAME COLUMN "Maintenace ID" TO "Maintenance ID"')
            return

        database.execute('''CREATE TABLE "Outflow History_new" (
                           "Outflow ID" INTEGER PRIMARY KEY,
                           "Maintenance ID" TEXT DEFAULT '',
                           "Part Name" TEXT NOT NULL,
                           Specification TEXT DEFAULT '',
                           Type TEXT DEFAULT '',
                           Quantity INTEGER NOT NULL,
                           Date TEXT
                       )''')
        for fallback_id, row in enumerate(rows, start=1):
            try:
                outflow_id = int(row[0])
            except (TypeError, ValueError):
                outflow_id = fallback_id
            database.execute('''INSERT INTO "Outflow History_new"
                               ("Outflow ID", "Maintenance ID", "Part Name", Specification, Type, Quantity, Date)
                               VALUES(?, ?, ?, ?, ?, ?, ?)''', (outflow_id, *row[1:]))
        database.execute('DROP TABLE "Outflow History"')
        database.execute('ALTER TABLE "Outflow History_new" RENAME TO "Outflow History"')

    def records(self, table_key: str, text: str = "", item_type: str = "All", stock: str = "All") -> list[tuple]:
        table_name, _ = TABLES[table_key]
        clauses: list[str] = []
        values: list[object] = []
        if item_type != "All" and table_key in ('inventory', 'purchase', 'outflow'):
            clauses.append('Type = ?')
            values.append(item_type)
        if stock == "In Stock" and table_key in ('inventory', 'outflow'):
            clauses.append('Quantity >= 1')
        elif stock == "Out of Stock" and table_key in ('inventory', 'outflow'):
            clauses.append('Quantity < 1')
        if text:
            searchable = {
                'equipment': ('Equipment ID', 'Equipment Name', 'Model', 'Serial Number', 'Location'),
                'outflow': ('Part Name', 'Specification'),
                'maintenance': ('ID', 'Equipment ID', 'Equipment Name', 'Technician Name', 'Job Description', 'Parts Used'),
            }.get(table_key, ('Name', 'Specification', 'Usage'))
            search_value = f'%{text}%'
            search_clauses = [f'"{field}" LIKE ?' for field in searchable]
            values.extend([search_value] * len(searchable))
            if table_key == 'equipment':
                search_clauses.append(
                    'EXISTS (SELECT 1 FROM "Maintenance Record" AS maintenance '
                    'WHERE maintenance."ID" LIKE ? '
                    'AND maintenance."Equipment ID" = "Equipment List"."Equipment ID")'
                )
                values.append(search_value)
            clauses.append('(' + ' OR '.join(search_clauses) + ')')
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as database:
            return database.execute(f'SELECT * FROM "{table_name}"{where}', values).fetchall()

    def autocomplete_values(self, field: str) -> list[str]:
        sources = {
            'Part Name': (('Inventory', 'Name'),),
            'Specification': (('Inventory', 'Specification'),),
            'Equipment ID': (('Equipment List', 'Equipment ID'),),
            'Equipment Name': (('Equipment List', 'Equipment Name'),),
            'Search': (
                ('Inventory', 'Name'),
                ('Inventory', 'Specification'),
                ('Equipment List', 'Equipment ID'),
                ('Equipment List', 'Equipment Name'),
            ),
        }
        selected_sources = sources.get(field, ())
        if not selected_sources:
            return []
        selects = [f'SELECT "{column}" AS value FROM "{table}"' for table, column in selected_sources]
        query = (
            'SELECT DISTINCT value FROM (' + ' UNION ALL '.join(selects) + ') '
            'WHERE value IS NOT NULL AND TRIM(value) <> "" '
            'ORDER BY value COLLATE NOCASE'
        )
        with self.connection() as database:
            return [str(row[0]) for row in database.execute(query).fetchall()]

    def equipment_name(self, equipment_id: str) -> str | None:
        with self.connection() as database:
            row = database.execute(
                'SELECT "Equipment Name" FROM "Equipment List" WHERE "Equipment ID"=? COLLATE NOCASE',
                (equipment_id.strip(),),
            ).fetchone()
        return str(row[0]) if row else None

    def dashboard_data(self) -> dict[str, list[tuple] | int]:
        """Return the live, action-oriented information shown on the home dashboard."""
        with self.connection() as database:
            totals = database.execute('''
                SELECT COUNT(*),
                       COALESCE(SUM(CASE WHEN Quantity > 0 THEN Quantity ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN Quantity BETWEEN 1 AND 5 THEN 1 ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN Quantity < 1 THEN 1 ELSE 0 END), 0)
                FROM Inventory
            ''').fetchone()
            low_stock = database.execute('''
                SELECT Name, Specification, Type, Quantity, Location, "Last Update"
                FROM Inventory
                WHERE Quantity <= 5
                ORDER BY Quantity ASC, "Last Update" DESC, Name ASC
                LIMIT 10
            ''').fetchall()
            maintenance_activity = database.execute('''
                SELECT "Equipment ID", "Equipment Name", "Technician Name", "Job Description", "Finish Time"
                FROM "Maintenance Record"
                ORDER BY "Finish Time" DESC
                LIMIT 10
            ''').fetchall()
            type_breakdown = database.execute('''
                SELECT Type, COUNT(*), COALESCE(SUM(Quantity), 0)
                FROM Inventory
                GROUP BY Type
                ORDER BY COUNT(*) DESC, Type ASC
            ''').fetchall()
            activity = database.execute('''
                SELECT 'Purchase', Name, Specification, Quantity, "Received Date", ID
                FROM "Purchase History"
                UNION ALL
                SELECT 'Outflow', "Part Name", Specification, -Quantity, Date, "Outflow ID"
                FROM "Outflow History"
                ORDER BY 5 DESC
                LIMIT 10
            ''').fetchall()
        return {
            'part_count': totals[0],
            'units_on_hand': totals[1],
            'low_stock_count': totals[2],
            'out_of_stock_count': totals[3],
            'low_stock': low_stock,
            'maintenance_activity': maintenance_activity,
            'type_breakdown': type_breakdown,
            'activity': activity,
        }

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
        if quantity_number <= 0:
            raise ValueError("Quantity must be a positive whole number.")
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

    def add_equipment(self, values: dict[str, str]) -> None:
        required = ('Equipment ID', 'Equipment Name', 'Location')
        if any(not values.get(field, '').strip() for field in required):
            raise ValueError('Equipment ID, equipment name, and location are required.')
        try:
            with self.connection() as database:
                database.execute('''INSERT INTO "Equipment List"
                                   ("Equipment ID", "Equipment Name", Model, "Serial Number", Location)
                                   VALUES(?, ?, ?, ?, ?)''',
                                 tuple(values.get(field, '').strip() for field in
                                       ('Equipment ID', 'Equipment Name', 'Model', 'Serial Number', 'Location')))
        except sqlite3.IntegrityError as error:
            raise ValueError(f'Equipment ID already exists: {values["Equipment ID"].strip()}.') from error

    def add_maintenance(self, maintenance: dict[str, str], parts: list[dict[str, str]]) -> None:
        quantities: list[int] = []
        for part in parts:
            try:
                quantity = int(part['Quantity'])
            except ValueError as error:
                raise ValueError("Quantity must be an integer.") from error
            if quantity <= 0:
                raise ValueError("Quantity must be a positive whole number.")
            quantities.append(quantity)

        parts_text = '\n'.join(
            f"{part['Part Name'].strip()} {part['Specification'].strip()} {' x '} {quantity}"
            for part, quantity in zip(parts, quantities)
        )
        today = str(date.today())
        with self.connection() as database:
            equipment_id = maintenance['Equipment ID'].strip()
            equipment = database.execute(
                'SELECT 1 FROM "Equipment List" WHERE "Equipment ID"=?',
                (equipment_id,),
            ).fetchone()
            if not equipment:
                raise ValueError(f"Equipment ID not found in Equipment List: {equipment_id}.")
            finish_date = maintenance['Finish Time'].split(' ')[0]
            database.execute('''INSERT INTO "Maintenance Record"
                         ("Equipment ID", "Equipment Name", "Technician Name", "Job Description", "Start Time", "Finish Time", "Parts Used", "Reference Files")
                         VALUES(?, ?, ?, ?, ?, ?, ?, ?)''',
                             tuple(maintenance[field].strip() for field in
                             ('Equipment ID', 'Equipment Name', 'Technician Name', 'Job Description', 'Start Time', 'Finish Time'))
                             + (parts_text, maintenance.get('Reference Files', '').strip()))
            maintenance_id = database.execute('SELECT last_insert_rowid()').fetchone()[0]
            outflow_date = finish_date
            for part, quantity in zip(parts, quantities):
                name, specification = part['Part Name'].strip(), part['Specification'].strip()
                inventory = database.execute(
                    'SELECT Quantity FROM Inventory WHERE Name=? AND Specification=?',
                    (name, specification),
                ).fetchone()
                if not inventory:
                    raise ValueError(f"No matching item exists in inventory: {name}.")
                if quantity > inventory[0]:
                    raise ValueError(f"Only {inventory[0]} item(s) are available for {name}.")
                database.execute('UPDATE Inventory SET Quantity=Quantity-?, "Last Update"=? WHERE Name=? AND Specification=?',
                                 (quantity, today, name, specification))
                database.execute('''INSERT INTO "Outflow History"
                                    ("Maintenance ID", "Part Name", "Specification", "Type", "Quantity", "Date")
                                     VALUES(?, ?, ?, ?, ?, ?)''',
                                     (str(maintenance_id), name, specification, part['Type'], quantity, outflow_date))
            database.execute('UPDATE "Equipment List" SET "Last Maintenance"=? WHERE "Equipment ID"=?',
                             (finish_date, equipment_id))

    def add_outflow(self, values: dict[str, str]) -> None:
        """Preserve the legacy single-item API for callers outside the UI."""
        self.add_maintenance(
            {field: values.get(field, '') for field in ('Equipment ID', 'Equipment Name', 'Technician Name', 'Job Description', 'Start Time', 'Finish Time')},
            [{'Part Name': values['Name'], 'Specification': values['Specification'], 'Type': values['Type'], 'Quantity': values['Quantity']}],
        )

    def update_field(self, table_key: str, record_id: int, field: str, value: str) -> None:
        table_name, fields = TABLES[table_key]
        if field not in fields or field == 'ID':
            raise ValueError("The ID field cannot be edited.")
        id_field = fields[0]
        with self.connection() as database:
            database.execute(f'UPDATE "{table_name}" SET "{field}"=? WHERE "{id_field}"=?', (value or None, record_id))
            if table_key == 'inventory':
                database.execute('UPDATE Inventory SET "Last Update"=? WHERE "ID"=?', (str(date.today()), record_id))

    def delete(self, table_key: str, record_id: int) -> None:
        table_name, _ = TABLES[table_key]
        with self.connection() as database:
            if table_key in ('purchase', 'outflow'):
                name_field = 'Name' if table_key == 'purchase' else 'Part Name'
                id_field = 'ID' if table_key == 'purchase' else 'Outflow ID'
                history = database.execute(
                    f'SELECT "{name_field}", Specification, Quantity FROM "{table_name}" WHERE "{id_field}"=?',
                    (record_id,),
                ).fetchone()
                if history:
                    adjustment = -history[2] if table_key == 'purchase' else history[2]
                    database.execute('UPDATE Inventory SET Quantity=Quantity+?, "Last Update"=? WHERE Name=? AND Specification=?',
                                     (adjustment, str(date.today()), history[0], history[1]))
            id_field = TABLES[table_key][1][0]
            database.execute(f'DELETE FROM "{table_name}" WHERE "{id_field}"=?', (record_id,))
            if table_key in ('inventory', 'purchase'):
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
