"""Parse timetable CSV/XLSX into normalized dict rows.
Expected columns (any of):
 - course_code / class_name / course
 - course_name / subject / subject_name
 - department
 - semester
 - section
 - day
 - start_time
 - end_time
 - room
 - instructor

Returns list[dict].
"""
import csv
import io

def parse_timetable_csv(content: bytes, file_ext: str) -> list[dict]:
    if file_ext == ".xlsx":
        try:
            import openpyxl
            from io import BytesIO
            wb = openpyxl.load_workbook(BytesIO(content))
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [str(h).lower().strip() for h in rows[0]]
            result = []
            for row in rows[1:]:
                if any(row):
                    result.append(dict(zip(headers, row)))
            return result
        except Exception as e:
            raise ValueError(f"Failed to parse XLSX: {e}")
    else:
        try:
            text = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text))
            return [dict(row) for row in reader]
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")
import pandas as pd
import io
import re
from typing import List, Dict

def parse_timetable_to_entries(content: bytes, file_ext: str, class_name: str) -> List[Dict[str, str]]:
    """
    Parses a timetable Excel/CSV into a list of structured entries.
    Assumes standard college grid format:
    Top-left cell might be 'Day/Time', columns are Times, rows are Days.
    """
    if file_ext == '.csv':
        # Decode bytes to string
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')
        df = pd.read_csv(io.StringIO(text))
    else:
        df = pd.read_excel(io.BytesIO(content))

    # Clean up empty columns/rows
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    # Assuming first column contains days (Monday, Tuesday...)
    # and headers contain Times (08:30-09:30)
    days_col = df.columns[0]
    times = df.columns[1:]

    entries = []
    
    for index, row in df.iterrows():
        day_val = str(row[days_col]).strip()
        if not day_val or day_val.lower() == 'nan':
            continue
            
        for time_col in times:
            cell_val = str(row[time_col]).strip()
            if cell_val and cell_val.lower() != 'nan':
                # Attempt to extract room from Subject (Room) pattern
                subject = cell_val
                room = "TBD"
                
                # Look for patterns like "Physics (104)" or "Maths-101"
                match = re.search(r'\((.*?)\)|-([\w\d]+)$', cell_val)
                if match:
                    room = match.group(1) if match.group(1) else match.group(2)
                    subject = cell_val.replace(match.group(0), "").strip()

                time_clean = str(time_col).strip()
                start_time = time_clean.split('-')[0] if '-' in time_clean else time_clean
                end_time = time_clean.split('-')[1] if '-' in time_clean else time_clean

                entries.append({
                    "class_name": class_name,
                    "day": day_val,
                    "start_time": start_time.strip(),
                    "end_time": end_time.strip(),
                    "subject": subject,
                    "room": room.strip()
                })

    return entries
