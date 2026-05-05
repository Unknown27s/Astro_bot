import sqlite3
from pathlib import Path
from config import DATA_DIR
import logging
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

INSTITUTE_DB_PATH = DATA_DIR / "institute_data.db"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _new_id() -> str:
    return str(uuid.uuid4())

def get_institute_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(INSTITUTE_DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_institute_db():
    with get_institute_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS timetables (
                id          TEXT PRIMARY KEY,
                class_name  TEXT NOT NULL,
                day         TEXT NOT NULL,
                start_time  TEXT NOT NULL,
                end_time    TEXT NOT NULL,
                subject     TEXT NOT NULL,
                room        TEXT NOT NULL,
                uploaded_by TEXT,
                uploaded_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS students (
                id          TEXT PRIMARY KEY,
                roll_no     TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                email       TEXT,
                phone       TEXT,
                department  TEXT,
                semester    INTEGER,
                gpa         REAL,
                uploaded_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS student_marks (
                id            TEXT PRIMARY KEY,
                student_id    TEXT NOT NULL,
                subject_code  TEXT NOT NULL,
                subject_name  TEXT NOT NULL,
                semester      INTEGER,
                internal_marks REAL,
                external_marks REAL,
                total_marks   REAL,
                grade         TEXT,
                uploaded_at   TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_timetables_class ON timetables(class_name);
            CREATE INDEX IF NOT EXISTS idx_timetables_day ON timetables(day);
            CREATE INDEX IF NOT EXISTS idx_students_roll_no ON students(roll_no);
            CREATE INDEX IF NOT EXISTS idx_student_marks_student ON student_marks(student_id);
            CREATE INDEX IF NOT EXISTS idx_student_marks_subject ON student_marks(subject_code);
        """)

def execute_readonly_query(sql: str) -> list[dict] | str:
    """Execute a query in a strictly read-only connection."""
    # To enforce read-only in SQLite, we use uri=True and mode=ro
    try:
        # SQLite needs the file to exist before opening in read-only mode
        if not INSTITUTE_DB_PATH.exists():
            return "Error: Database does not exist yet."
            
        # Basic sanity check
        sql_lower = sql.lower()
        if any(bad in sql_lower for bad in ["insert ", "update ", "delete ", "drop ", "alter ", "create "]):
            return "Error: Only SELECT queries are allowed for security."
            
        conn = sqlite3.connect(f"file:{INSTITUTE_DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Text-to-SQL Execution Error: {e}")
        return f"Database Error: {e}"

def get_schema_for_llm() -> str:
    """Returns the schema representation for the LLM prompt."""
    return '''
Table: timetables
Columns: id, class_name, day, start_time, end_time, subject, room, uploaded_by, uploaded_at

Table: students
Columns: id, roll_no, name, email, phone, department, semester, gpa, uploaded_at

Table: student_marks
Columns: id, student_id, subject_code, subject_name, semester, internal_marks, external_marks, total_marks, grade, uploaded_at
'''

def upsert_unified_data(rows: list[dict], uploaded_by: str = None) -> dict:
    """
    Process a unified upload sheet containing both student details and marks.
    Rows should have:
    - roll_no, name, email, phone, department, semester (for student)
    - subject_code, subject_name, subject_semester, internal_marks, external_marks, grade (for marks)

    Returns a dict: {"students_upserted": int, "marks_inserted": int}
    """
    marks_added = 0
    students_upserted = 0
    with get_institute_connection() as conn:
        for row in rows:
            roll_no = row.get("roll_no")
            if not roll_no:
                continue
                
            # 1. Upsert Student
            student = conn.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
            if student:
                student_id = student["id"]
                conn.execute(
                    "UPDATE students SET name = COALESCE(?, name), department = COALESCE(?, department), semester = COALESCE(?, semester) WHERE id = ?",
                    (row.get("name"), row.get("department"), row.get("semester"), student_id)
                )
            else:
                student_id = _new_id()
                conn.execute(
                    "INSERT INTO students (id, roll_no, name, email, phone, department, semester, gpa, uploaded_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (student_id, roll_no, row.get("name", ""), row.get("email", ""), row.get("phone", ""), 
                     row.get("department", ""), row.get("semester", 0), 0.0, _now())
                )
            students_upserted += 1
                
            # 2. Insert Marks
            subject_code = row.get("subject_code")
            if subject_code:
                try:
                    internal = float(row.get("internal_marks", 0.0))
                except (ValueError, TypeError):
                    internal = 0.0
                try:
                    external = float(row.get("external_marks", 0.0))
                except (ValueError, TypeError):
                    external = 0.0
                
                existing_mark = conn.execute(
                    "SELECT id FROM student_marks WHERE student_id = ? AND subject_code = ?", 
                    (student_id, subject_code)
                ).fetchone()
                
                if existing_mark:
                    conn.execute(
                        "UPDATE student_marks SET internal_marks = ?, external_marks = ?, total_marks = ?, grade = ? WHERE id = ?",
                        (internal, external, internal + external, row.get("grade", ""), existing_mark["id"])
                    )
                else:
                    conn.execute(
                        "INSERT INTO student_marks (id, student_id, subject_code, subject_name, semester, internal_marks, external_marks, total_marks, grade, uploaded_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (_new_id(), student_id, subject_code, row.get("subject_name", ""), row.get("subject_semester", 1),
                         internal, external, internal + external, row.get("grade", ""), _now())
                    )
                marks_added += 1
        conn.commit()
    return {"students_upserted": students_upserted, "marks_inserted": marks_added}
