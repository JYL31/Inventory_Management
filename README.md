# Inventory Management

A PySide6 desktop application for recording inventory purchases and outflows in
the included SQLite database.

## Run

Install the dependencies, then run the application from the `GUI` directory:

```powershell
pip install -r requirements.txt
cd GUI
python main.py
```

The application keeps the existing workflows: adding purchases, recording
outflow, filtering all three histories, inline edits, deletion with inventory
adjustment, and Excel export.
