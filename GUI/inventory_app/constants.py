"""Shared application constants."""

from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "Inventory.db"
TYPES = ("Bearing", "Consumables", "Electronics", "Lubricant", "Miscellaneous", "Pneumatics", "Tools")

TABLES = {
    "inventory": ("Inventory", ("ID", "Name", "Specification", "Type", "Usage", "Quantity", "Location", "Last Update")),
    "purchase": ("Purchase History", ("ID", "Name", "Specification", "Type", "Usage", "Supplier", "Quantity", "Unit Price", "Shipping", "Total Price", "Received Date", "Applied By", "Responsible By")),
    "outflow": ("Outflow History", ("Outflow ID", "Maintenance ID", "Part Name", "Specification", "Type", "Quantity", "Date")),
    "maintenance": ("Maintenance Record", ("ID", "Equipment ID", "Equipment Name", "Technician Name", "Job Description", "Start Time", "Finish Time", "Parts Used", "Reference Files")),
}
