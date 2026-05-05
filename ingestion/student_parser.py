"""
student_parser.py — Parse CSV/XLSX uploads for student data, marks, and unified sheets.

Functions:
    parse_students_csv(content, file_ext)  -> list[dict]
    parse_marks_csv(content, file_ext)     -> list[dict]
    parse_unified_csv(content, file_ext)   -> list[dict]

All functions accept raw file bytes and a file extension string (".csv" or ".xlsx"),
returning a list of row-dicts with normalised column names.
"""

import io
import csv
import logging

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────

def _normalise_key(key: str) -> str:
    """Lowercase, strip whitespace, replace spaces/hyphens with underscores."""
    return key.strip().lower().replace(" ", "_").replace("-", "_")


def _read_rows(content: bytes, file_ext: str) -> list[dict]:
    """
    Read raw bytes as CSV or XLSX and return a list of dicts
    with normalised column keys.
    """
    if file_ext == ".xlsx":
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "openpyxl is required to parse .xlsx files. "
                "Install it with: pip install openpyxl"
            )
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        raw_headers = next(rows_iter, None)
        if not raw_headers:
            return []
        headers = [_normalise_key(str(h)) if h else f"col_{i}" for i, h in enumerate(raw_headers)]
        result = []
        for row in rows_iter:
            row_dict = {}
            for h, v in zip(headers, row):
                row_dict[h] = v if v is not None else ""
            if any(str(v).strip() for v in row_dict.values()):
                result.append(row_dict)
        wb.close()
        return result
    else:
        # Default: CSV
        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            return []
        result = []
        for row in reader:
            normalised = {_normalise_key(k): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
            if any(str(v).strip() for v in normalised.values()):
                result.append(normalised)
        return result


def _safe_int(val, default: int = 0) -> int:
    """Convert a value to int, returning default on failure."""
    if val is None or str(val).strip() == "":
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _safe_float(val, default: float = 0.0) -> float:
    """Convert a value to float, returning default on failure."""
    if val is None or str(val).strip() == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


# ── Public parsers ───────────────────────────────────────

def parse_students_csv(content: bytes, file_ext: str = ".csv") -> list[dict]:
    """
    Parse a student master-data CSV/XLSX.

    Expected columns (case-insensitive, flexible naming):
        roll_no, name, email, phone, department, semester, gpa

    Returns a list of dicts ready for DB insertion.
    """
    rows = _read_rows(content, file_ext)
    if not rows:
        return []

    students = []
    for row in rows:
        roll_no = str(row.get("roll_no", "") or row.get("rollno", "") or row.get("roll_number", "") or "").strip()
        if not roll_no:
            logger.debug("Skipping student row without roll_no: %s", row)
            continue

        students.append({
            "roll_no": roll_no,
            "name": str(row.get("name", "") or row.get("student_name", "") or "").strip(),
            "email": str(row.get("email", "") or row.get("email_id", "") or "").strip(),
            "phone": str(row.get("phone", "") or row.get("mobile", "") or row.get("phone_no", "") or "").strip(),
            "department": str(row.get("department", "") or row.get("dept", "") or row.get("branch", "") or "").strip(),
            "semester": _safe_int(row.get("semester") or row.get("sem")),
            "gpa": _safe_float(row.get("gpa") or row.get("cgpa")),
        })

    logger.info("Parsed %d student records from uploaded file", len(students))
    return students


def parse_marks_csv(content: bytes, file_ext: str = ".csv") -> list[dict]:
    """
    Parse a student-marks CSV/XLSX.

    Expected columns (case-insensitive, flexible naming):
        roll_no, subject_code, subject_name, semester,
        internal_marks, external_marks, grade

    Returns a list of dicts ready for DB insertion.
    """
    rows = _read_rows(content, file_ext)
    if not rows:
        return []

    marks = []
    for row in rows:
        roll_no = str(row.get("roll_no", "") or row.get("rollno", "") or row.get("roll_number", "") or "").strip()
        subject_code = str(row.get("subject_code", "") or row.get("sub_code", "") or row.get("course_code", "") or "").strip()

        if not roll_no or not subject_code:
            logger.debug("Skipping marks row (missing roll_no/subject_code): %s", row)
            continue

        marks.append({
            "roll_no": roll_no,
            "subject_code": subject_code,
            "subject_name": str(row.get("subject_name", "") or row.get("sub_name", "") or row.get("course_name", "") or "").strip(),
            "semester": _safe_int(row.get("semester") or row.get("sem")),
            "internal_marks": _safe_float(row.get("internal_marks") or row.get("internal") or row.get("ia_marks")),
            "external_marks": _safe_float(row.get("external_marks") or row.get("external") or row.get("ea_marks")),
            "grade": str(row.get("grade", "") or "").strip(),
        })

    logger.info("Parsed %d marks records from uploaded file", len(marks))
    return marks


def parse_unified_csv(content: bytes, file_ext: str = ".csv") -> list[dict]:
    """
    Parse a unified CSV/XLSX containing both student details and marks in every row.

    Expected columns (case-insensitive, flexible naming):
        roll_no, name, email, phone, department, semester,
        subject_code, subject_name, subject_semester, internal_marks, external_marks, grade

    Returns a list of dicts with all fields merged per row.
    """
    rows = _read_rows(content, file_ext)
    if not rows:
        return []

    unified = []
    for row in rows:
        roll_no = str(row.get("roll_no", "") or row.get("rollno", "") or row.get("roll_number", "") or "").strip()
        if not roll_no:
            logger.debug("Skipping unified row without roll_no: %s", row)
            continue

        unified.append({
            # Student fields
            "roll_no": roll_no,
            "name": str(row.get("name", "") or row.get("student_name", "") or "").strip(),
            "email": str(row.get("email", "") or row.get("email_id", "") or "").strip(),
            "phone": str(row.get("phone", "") or row.get("mobile", "") or row.get("phone_no", "") or "").strip(),
            "department": str(row.get("department", "") or row.get("dept", "") or row.get("branch", "") or "").strip(),
            "semester": _safe_int(row.get("semester") or row.get("sem")),
            # Marks fields
            "subject_code": str(row.get("subject_code", "") or row.get("sub_code", "") or row.get("course_code", "") or "").strip(),
            "subject_name": str(row.get("subject_name", "") or row.get("sub_name", "") or row.get("course_name", "") or "").strip(),
            "subject_semester": _safe_int(row.get("subject_semester") or row.get("sub_semester") or row.get("semester") or row.get("sem")),
            "internal_marks": _safe_float(row.get("internal_marks") or row.get("internal") or row.get("ia_marks")),
            "external_marks": _safe_float(row.get("external_marks") or row.get("external") or row.get("ea_marks")),
            "grade": str(row.get("grade", "") or "").strip(),
        })

    logger.info("Parsed %d unified records from uploaded file", len(unified))
    return unified
