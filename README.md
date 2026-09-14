# Finanzas del Triciclo

Desktop finance management application for a small tricycle rental operation, built with **Python, Tkinter and SQLite**.

The project was created around a real operational need: recording daily income and expenses, calculating revenue distribution, tracking driver earnings, reviewing monthly/annual performance, and exporting data for reporting.

> **Portfolio note:** this public repository contains only synthetic demo data. No real driver names, expenses, notes, backups or financial records are included.

## What the application manages

- Daily tricycle income by driver
- Other income that does not generate driver salary
- Automatic revenue distribution between driver, owner and vehicle fund
- Expense tracking by category
- Driver activation/deactivation
- Monthly driver earnings
- Global financial indicators
- Annual month-by-month summary
- Movement search and filtering
- Excel export
- SQLite database import/export and automatic backups

## Business rules implemented

For normal tricycle income:

- Driver: **25%**
- Owner: **25%**
- Both shares are rounded down to the nearest multiple of **50**
- The tricycle fund receives the remaining amount
- Opening balance belongs entirely to the owner
- Amounts are stored as whole numbers

These rules are implemented in the service layer rather than the UI.

## Technical highlights

- Python desktop application using Tkinter/ttk
- SQLite persistence with migrations for older database versions
- Separation between UI, services, database and utility modules
- Transaction-safe database operations
- Search/filtering across income and expenses
- Excel export with `openpyxl`
- Backup, database import and export workflows
- PyInstaller build script for Windows deployment
- Local database stored beside the application/executable

## Demo database

The repository includes `data/demo.db`, a SQLite database created specifically for portfolio review.

It contains synthetic examples of:

- Three demo drivers (two active, one inactive)
- Opening balance
- Tricycle income across multiple months
- Other income
- Expenses across multiple categories
- Enough activity to populate the dashboard and annual reports

No record in the demo database represents a real person or transaction.

## Run the demo on Windows

1. Install Python 3.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run:

```text
ejecutar_demo.bat
```

`ejecutar_demo.bat` copies `data/demo.db` to the local working database `renta_triciclo.db` and starts the application.

> `renta_triciclo.db` is ignored by Git so a local or real operational database is never intended to be committed.

To restore the demo manually:

```bash
python scripts/reset_demo.py
```

## Run with an empty/local database

```bash
python main.py
```

If `renta_triciclo.db` does not exist, the application creates the required SQLite structure automatically.

## Project structure

```text
finanzas-triciclo/
├── data/
│   └── demo.db
├── scripts/
│   ├── create_demo_db.py
│   └── reset_demo.py
├── main.py
├── config.py
├── database.py
├── services.py
├── utils.py
├── ui.py
├── logo.ico
├── requirements.txt
├── ejecutar_app.bat
├── ejecutar_demo.bat
├── compilar_exe.bat
└── README.md
```

## Build a Windows executable

The project includes `compilar_exe.bat`, which installs/updates PyInstaller and creates a Windows build in `dist/FinanzasTriciclo/`.

## Privacy and portfolio safety

The original operational database, backups, compiled binaries, virtual environment, caches and historical ZIP files are not included in this public version.

The only privacy-related source-code change in the portfolio copy is replacing the original default driver names with generic demo names. Business calculations and application behavior were left unchanged.

## Development approach

This project has been useful for practicing and applying:

- Translating real business rules into software logic
- SQLite schema evolution and migrations
- Desktop UI design
- Transactional CRUD workflows
- Financial summaries and reporting
- Excel export
- Backup/import/export workflows
- Packaging a Python desktop application for Windows
- Preparing a privacy-safe public portfolio version

## Status

Active personal/business project. This repository is the privacy-safe portfolio edition.

---

**Author:** Daisniel Perez Breto  
[LinkedIn](https://www.linkedin.com/in/daisniel-perez-breto)
