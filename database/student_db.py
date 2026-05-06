"""Student and Marks database operations."""
import logging
from database.institute_db import get_institute_connection, _new_id, _now

logger = logging.getLogger(__name__)


def add_student(
    roll_no: str,
    name: str,
    email: str = "",
    phone: str = "",
    department: str = "",
    semester: int = 0,
    gpa: float = 0.0,
) -> str:
    student_id = _new_id()
    with get_institute_connection() as conn:
        conn.execute(
            "INSERT INTO students (id, roll_no, name, email, phone, department, semester, gpa, uploaded_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (student_id, roll_no, name, email, phone, department, semester, gpa, _now()),
        )
    return student_id


def bulk_add_students(students_list: list[dict]) -> int:
    count = 0
    with get_institute_connection() as conn:
        for s in students_list:
            try:
                conn.execute(
                    "INSERT INTO students (id, roll_no, name, email, phone, department, semester, gpa, uploaded_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        _new_id(),
                        s.get("roll_no"),
                        s.get("name"),
                        s.get("email", ""),
                        s.get("phone", ""),
                        s.get("department", ""),
                        s.get("semester", 0),
                        s.get("gpa", 0.0),
                        _now(),
                    ),
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to insert student: {e}")
    return count


def query_student_by_roll_no(roll_no: str) -> dict | None:
    with get_institute_connection() as conn:
        row = conn.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
    return dict(row) if row else None


def bulk_add_student_marks(marks_list: list[dict]) -> int:
    count = 0
    with get_institute_connection() as conn:
        for m in marks_list:
            try:
                student_id = m.get("student_id")
                if not student_id and m.get("roll_no"):
                    st = conn.execute(
                        "SELECT id FROM students WHERE roll_no = ?",
                        (m.get("roll_no"),),
                    ).fetchone()
                    student_id = dict(st)["id"] if st else None
                if student_id:
                    internal = float(m.get("internal_marks", 0.0))
                    external = float(m.get("external_marks", 0.0))
                    conn.execute(
                        "INSERT INTO student_marks (id, student_id, subject_code, subject_name, semester, internal_marks, external_marks, total_marks, grade, uploaded_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            _new_id(),
                            student_id,
                            m.get("subject_code"),
                            m.get("subject_name"),
                            m.get("semester", 1),
                            internal,
                            external,
                            internal + external,
                            m.get("grade", ""),
                            _now(),
                        ),
                    )
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to insert marks: {e}")
    return count


def query_student_marks(roll_no: str = "", subject_code: str = "", semester: int = 0) -> list[dict]:
    with get_institute_connection() as conn:
        if roll_no:
            st = conn.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
            if not st:
                return []
            student_id = dict(st)["id"]
            if subject_code:
                rows = conn.execute(
                    "SELECT * FROM student_marks WHERE student_id = ? AND subject_code = ?",
                    (student_id, subject_code),
                ).fetchall()
            elif semester:
                rows = conn.execute(
                    "SELECT * FROM student_marks WHERE student_id = ? AND semester = ?",
                    (student_id, semester),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM student_marks WHERE student_id = ?",
                    (student_id,),
                ).fetchall()
        else:
            return []
    return [dict(r) for r in rows]


def build_student_context(roll_no: str, max_marks: int = 20) -> str | None:
    student = query_student_by_roll_no(roll_no)
    if not student:
        return None

    lines = ["Student Profile:"]
    lines.append(f"- Roll No: {student.get('roll_no', '')}")
    lines.append(f"- Name: {student.get('name', '')}")
    if student.get("department"):
        lines.append(f"- Department: {student.get('department')}")
    if student.get("semester") is not None:
        lines.append(f"- Semester: {student.get('semester')}")
    if student.get("gpa") is not None:
        lines.append(f"- GPA: {student.get('gpa')}")

    marks = query_student_marks(roll_no=roll_no)
    if marks:
        lines.append("Student Marks:")
        for row in marks[:max_marks]:
            subject_code = row.get("subject_code") or ""
            subject_name = row.get("subject_name") or ""
            semester = row.get("semester")
            internal = row.get("internal_marks")
            external = row.get("external_marks")
            total = row.get("total_marks")
            grade = row.get("grade") or ""
            line = f"- {subject_code} {subject_name}".strip()
            if semester is not None:
                line += f" (Sem {semester})"
            parts = []
            if internal is not None:
                parts.append(f"internal {internal}")
            if external is not None:
                parts.append(f"external {external}")
            if total is not None:
                parts.append(f"total {total}")
            if grade:
                parts.append(f"grade {grade}")
            if parts:
                line += f": {', '.join(parts)}"
            lines.append(line)

        if len(marks) > max_marks:
            lines.append(f"... and {len(marks) - max_marks} more records")

    return "\n".join(lines)
