"""
Small helper to generate an Excel (.xlsx) timetable from the CSV sample.
Requires: openpyxl
Run:
    python scripts/generate_timetable_xlsx.py
Output:
    react-frontend/public/sample_data/timetable.xlsx
"""
import csv
from pathlib import Path

try:
    from openpyxl import Workbook
except ImportError:
    raise SystemExit("Please install openpyxl: pip install openpyxl")

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / 'react-frontend' / 'public' / 'sample_data' / 'timetable.csv'
XLSX_PATH = ROOT / 'react-frontend' / 'public' / 'sample_data' / 'timetable.xlsx'

wb = Workbook()
ws = wb.active
ws.title = 'Timetable'

with CSV_PATH.open(newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for r, row in enumerate(reader, start=1):
        for c, val in enumerate(row, start=1):
            ws.cell(row=r, column=c, value=val)

wb.save(XLSX_PATH)
print(f"Written {XLSX_PATH}")
