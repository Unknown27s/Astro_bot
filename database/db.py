"""
IMS AstroBot — SQLite Database Layer
Handles schema creation, user management, document records, and query logs.

Improvements vs original:
  - PBKDF2-HMAC-SHA256 password hashing (replaces bare SHA-256)
  - _db() context manager — connections always closed, even on exception
  - UTC timestamps throughout (datetime.now(UTC))
  - _now() helper — one place to change timestamp format
  - sys.path hack removed — use proper package imports
  - add_document actually stores source_type / source_url columns
  - store_document_question_suggestions uses parameterized query (no .format())
  - _resolve_question_suggestion_column removed — schema is canonical now
  - cleanup_expired_memory imports moved to top of file
  - update_tag builds SET clause safely without string interpolation
  - Logging added throughout
  - DEFAULT_RATE_LIMITS extracted as a module constant (no duplication)
  - Type hints modernised (X | None instead of Optional[X])
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

from tests.config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    CONV_MIN_USAGE_FOR_KEEP,
    CONV_TTL_DAYS,
    SQLITE_DB_PATH,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    """UTC timestamp in ISO-8601 format used for every created_at / updated_at column."""
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Backwards-compatible raw SQLite connection.

    Some modules still use explicit conn/close flows; this helper keeps those
    call sites working while newer code can prefer the _db() context manager.
    """
    conn = sqlite3.connect(str(SQLITE_DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

@contextmanager
def _db() -> Generator[sqlite3.Connection, None, None]:
    """
    Yield a WAL-mode, foreign-key-enabled SQLite connection.
    Commits on clean exit, rolls back on exception, always closes.

    Usage:
        with _db() as conn:
            conn.execute(...)
    """
    conn = sqlite3.connect(str(SQLITE_DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Password hashing  (PBKDF2-HMAC-SHA256 — far stronger than bare SHA-256)
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 260_000
_HASH_SEP = "$"


def hash_password(password: str) -> str:
    """
    Return a salted PBKDF2-HMAC-SHA256 hash string.
    Format: pbkdf2$<hex-salt>$<hex-digest>
    """
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        _PBKDF2_ITERATIONS,
    ).hex()
    return _HASH_SEP.join(["pbkdf2", salt, digest])


def _verify_password(password: str, stored: str) -> bool:
    """Constant-time password verification. Handles both legacy SHA-256 and PBKDF2."""
    if stored.startswith("pbkdf2$"):
        try:
            _, salt, expected = stored.split(_HASH_SEP)
        except ValueError:
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            _PBKDF2_ITERATIONS,
        ).hex()
        return secrets.compare_digest(candidate, expected)

    # Legacy SHA-256 fallback (for existing rows — will be re-hashed on next login)
    legacy = hashlib.sha256(password.encode()).hexdigest()
    return secrets.compare_digest(legacy, stored)


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    """Add a column to an existing table if it doesn't already exist."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        logger.info("Added column %s.%s", table, column)


# ---------------------------------------------------------------------------
# Default rate limits (single source of truth)
# ---------------------------------------------------------------------------

_DEFAULT_RATE_LIMITS: list[tuple[str, int, int, str]] = [
    ("auth",               5,  60, "Login/Register — brute-force protection"),
    ("chat",               5,  60, "LLM queries — expensive operations"),
    ("documents/upload",  10,  60, "Document uploads — resource intensive"),
    ("documents/tags",    30,  60, "Tag management — moderate load"),
    ("documents/read",    60,  60, "Read operations — list tags, documents"),
    ("documents/classify",30,  60, "Classification operations"),
    ("global",           100,  60, "Global rate limit — all requests"),
]


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables, indexes, and seed data on first run."""
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL CHECK(role IN ('admin', 'faculty', 'student')),
                full_name     TEXT DEFAULT '',
                created_at    TEXT NOT NULL,
                is_active     INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS documents (
                id            TEXT PRIMARY KEY,
                filename      TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_type     TEXT NOT NULL,
                file_size     INTEGER DEFAULT 0,
                chunk_count   INTEGER DEFAULT 0,
                uploaded_by   TEXT,
                uploaded_at   TEXT NOT NULL,
                status        TEXT DEFAULT 'processed',
                source_type   TEXT DEFAULT 'uploaded',
                source_url    TEXT DEFAULT '',
                source_domain TEXT DEFAULT '',
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS query_logs (
                id               TEXT PRIMARY KEY,
                user_id          TEXT,
                username         TEXT,
                query_text       TEXT NOT NULL,
                response_text    TEXT,
                sources          TEXT,
                response_time_ms REAL,
                created_at       TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS feedback_logs (
                id                   TEXT PRIMARY KEY,
                trace_id             TEXT NOT NULL,
                user_id              TEXT,
                rating               INTEGER NOT NULL,
                comment              TEXT,
                source               TEXT,
                recorded_in_langfuse INTEGER DEFAULT 0,
                created_at           TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS trace_events (
                id               TEXT PRIMARY KEY,
                trace_id         TEXT,
                endpoint         TEXT,
                user_id          TEXT,
                username         TEXT,
                status           TEXT,
                query_preview    TEXT,
                response_time_ms REAL,
                route_mode       TEXT,
                retrieval_mode   TEXT,
                chunks_count     INTEGER DEFAULT 0,
                provider         TEXT,
                model            TEXT,
                created_at       TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS document_question_suggestions (
                id          TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                source_hint TEXT,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS conversation_memory (
                id            TEXT PRIMARY KEY,
                query_text    TEXT NOT NULL,
                response_text TEXT NOT NULL,
                sources       TEXT,
                user_id       TEXT,
                usage_count   INTEGER DEFAULT 1,
                created_at    TEXT NOT NULL,
                last_accessed TEXT,
                expires_at    TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS tags (
                id          TEXT PRIMARY KEY,
                name        TEXT UNIQUE NOT NULL,
                description TEXT,
                color       TEXT DEFAULT '#808080',
                created_by  TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS document_tags (
                id          TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                tag_id      TEXT NOT NULL,
                added_by    TEXT,
                added_at    TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id)      REFERENCES tags(id)      ON DELETE CASCADE,
                FOREIGN KEY (added_by)    REFERENCES users(id),
                UNIQUE(document_id, tag_id)
            );

            CREATE TABLE IF NOT EXISTS document_classifications (
                id              TEXT PRIMARY KEY,
                document_id     TEXT NOT NULL UNIQUE,
                classification  TEXT NOT NULL,
                confidence      REAL DEFAULT 1.0,
                auto_classified INTEGER DEFAULT 0,
                classified_by   TEXT,
                classified_at   TEXT NOT NULL,
                notes           TEXT,
                FOREIGN KEY (document_id)   REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (classified_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS classification_templates (
                id          TEXT PRIMARY KEY,
                name        TEXT UNIQUE NOT NULL,
                description TEXT,
                created_by  TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS rate_limit_configs (
                id                   TEXT PRIMARY KEY,
                endpoint             TEXT UNIQUE NOT NULL,
                limit_requests       INTEGER NOT NULL,
                limit_window_seconds INTEGER NOT NULL,
                enabled              INTEGER DEFAULT 1,
                description          TEXT,
                updated_by           TEXT,
                updated_at           TEXT NOT NULL,
                FOREIGN KEY (updated_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS announcements (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                author_name TEXT NOT NULL,
                content     TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );



            CREATE INDEX IF NOT EXISTS idx_conversation_memory_user
                ON conversation_memory(user_id);
            CREATE INDEX IF NOT EXISTS idx_conversation_memory_expires
                ON conversation_memory(expires_at);
            CREATE INDEX IF NOT EXISTS idx_tags_name
                ON tags(name);
            CREATE INDEX IF NOT EXISTS idx_document_tags_doc
                ON document_tags(document_id);
            CREATE INDEX IF NOT EXISTS idx_document_tags_tag
                ON document_tags(tag_id);
            CREATE INDEX IF NOT EXISTS idx_doc_classification
                ON document_classifications(classification);
            CREATE INDEX IF NOT EXISTS idx_rate_limit_endpoint
                ON rate_limit_configs(endpoint);
            CREATE INDEX IF NOT EXISTS idx_query_logs_user
                ON query_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_query_logs_created
                ON query_logs(created_at);


            -- ═══════════════════════════════════════════════════════════
            -- CUSTOM OBSERVABILITY (SQLite-based tracing)
            -- ═══════════════════════════════════════════════════════════

            CREATE TABLE IF NOT EXISTS obs_traces (
                trace_id       TEXT PRIMARY KEY,
                service        TEXT NOT NULL,
                operation      TEXT NOT NULL,
                user_id        TEXT,
                start_time     TEXT NOT NULL,
                end_time       TEXT,
                duration_ms    REAL,
                status         TEXT DEFAULT 'pending',
                error          TEXT,
                metadata       TEXT,
                created_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS obs_spans (
                span_id        TEXT PRIMARY KEY,
                trace_id       TEXT NOT NULL,
                parent_span_id TEXT,
                service        TEXT NOT NULL,
                operation      TEXT NOT NULL,
                start_time     TEXT NOT NULL,
                end_time       TEXT,
                duration_ms    REAL,
                status         TEXT DEFAULT 'pending',
                input_data     TEXT,
                output_data    TEXT,
                error          TEXT,
                tags           TEXT,
                created_at     TEXT NOT NULL,
                FOREIGN KEY (trace_id) REFERENCES obs_traces(trace_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_obs_traces_service
                ON obs_traces(service);
            CREATE INDEX IF NOT EXISTS idx_obs_traces_created
                ON obs_traces(created_at);
            CREATE INDEX IF NOT EXISTS idx_obs_spans_trace
                ON obs_spans(trace_id);
            CREATE INDEX IF NOT EXISTS idx_obs_spans_service
                ON obs_spans(service);
        """)

        # Migrate older databases that predate source columns on documents
        _ensure_column(conn, "documents", "source_type",   "TEXT DEFAULT 'uploaded'")
        _ensure_column(conn, "documents", "source_url",    "TEXT DEFAULT ''")
        _ensure_column(conn, "documents", "source_domain", "TEXT DEFAULT ''")

        # Seed default rate limits
        existing = conn.execute("SELECT COUNT(*) FROM rate_limit_configs").fetchone()[0]
        if existing == 0:
            conn.executemany(
                "INSERT INTO rate_limit_configs "
                "(id, endpoint, limit_requests, limit_window_seconds, description, updated_at) "
                "VALUES (?,?,?,?,?,?)",
                [
                    (_new_id(), ep, lim, win, desc, _now())
                    for ep, lim, win, desc in _DEFAULT_RATE_LIMITS
                ],
            )

        # Seed default admin
        admin_exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (ADMIN_USERNAME,)
        ).fetchone()
        if not admin_exists:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role, full_name, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (_new_id(), ADMIN_USERNAME, hash_password(ADMIN_PASSWORD),
                 "admin", "System Administrator", _now()),
            )
            logger.info("Default admin user created: %s", ADMIN_USERNAME)


# ═══════════════════════════════════════════════════════════════════════════
# USER CRUD
# ═══════════════════════════════════════════════════════════════════════════

def create_user(username: str, password: str, role: str, full_name: str = "") -> bool:
    """Create a new user. Returns True on success, False if username is taken."""
    try:
        with _db() as conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role, full_name, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (_new_id(), username, hash_password(password), role, full_name, _now()),
            )
        logger.info("User created: %s (%s)", username, role)
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authenticate a user by username + password.
    Re-hashes legacy SHA-256 passwords to PBKDF2 on first successful login.
    Returns the user dict or None.
    """
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
        ).fetchone()
        if not row:
            return None

        user = dict(row)
        if not _verify_password(password, user["password_hash"]):
            return None

        # Upgrade legacy SHA-256 hashes transparently
        if not user["password_hash"].startswith("pbkdf2$"):
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(password), user["id"]),
            )
            logger.info("Upgraded password hash for user: %s", username)

    return user


def get_all_users() -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, username, role, full_name, created_at, is_active "
            "FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def toggle_user_active(user_id: str, is_active: bool) -> bool:
    with _db() as conn:
        conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?", (int(is_active), user_id)
        )
    return True


def delete_user(user_id: str) -> bool:
    """Delete a user and their associated query logs. Documents are reassigned to NULL."""
    try:
        with _db() as conn:
            conn.execute("DELETE FROM query_logs WHERE user_id = ?",   (user_id,))
            conn.execute("UPDATE documents SET uploaded_by = NULL WHERE uploaded_by = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE id = ?",              (user_id,))
        logger.info("User deleted: %s", user_id)
        return True
    except Exception:
        logger.exception("Failed to delete user %s", user_id)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENT CRUD
# ═══════════════════════════════════════════════════════════════════════════

def add_document(
    filename: str,
    original_name: str,
    file_type: str,
    file_size: int,
    chunk_count: int,
    uploaded_by: str | None,
    source_type: str = "uploaded",
    source_domain: str = "",
    source_url: str = "",
) -> str:
    """Record a new document and return its ID."""
    doc_id = _new_id()
    with _db() as conn:
        conn.execute(
            "INSERT INTO documents "
            "(id, filename, original_name, file_type, file_size, chunk_count, "
            " uploaded_by, uploaded_at, source_type, source_domain, source_url) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (doc_id, filename, original_name, file_type, file_size, chunk_count,
             uploaded_by, _now(), source_type, source_domain, source_url),
        )
    return doc_id


def get_all_documents() -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_document(doc_id: str) -> dict | None:
    """Delete a document record and return its data (for vector store cleanup)."""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        if not row:
            return None
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    return dict(row)


# ═══════════════════════════════════════════════════════════════════════════
# TIMETABLE CRUD
# ═══════════════════════════════════════════════════════════════════════════

def add_timetable_entry(
    class_name: str,
    day: str,
    start_time: str,
    end_time: str,
    subject: str,
    room: str,
    uploaded_by: str | None,
) -> str:
    """Record a new timetable entry."""
    entry_id = _new_id()
    with _db() as conn:
        conn.execute(
            "INSERT INTO timetables "
            "(id, class_name, day, start_time, end_time, subject, room, uploaded_by, uploaded_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (entry_id, class_name, day, start_time, end_time, subject, room, uploaded_by, _now()),
        )
    return entry_id

def query_timetable(class_name: str, day: str, time_str: str = "") -> list[dict]:
    """Query timetables based on class, day, and an approximate time."""
    with _db() as conn:
        if time_str:
            rows = conn.execute(
                "SELECT * FROM timetables WHERE class_name LIKE ? AND day LIKE ? AND (start_time LIKE ? OR end_time LIKE ?)",
                (f"%{class_name}%", f"%{day}%", f"%{time_str}%", f"%{time_str}%")
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM timetables WHERE class_name LIKE ? AND day LIKE ?",
                (f"%{class_name}%", f"%{day}%")
            ).fetchall()
    return [dict(r) for r in rows]

def clear_timetable(class_name: str) -> int:
    """Delete all entries for a specific class."""
    with _db() as conn:
        cursor = conn.execute("DELETE FROM timetables WHERE class_name = ?", (class_name,))
        return cursor.rowcount



# ═══════════════════════════════════════════════════════════════════════════
# QUERY LOGS
# ═══════════════════════════════════════════════════════════════════════════

def log_query(
    user_id: str,
    username: str,
    query_text: str,
    response_text: str,
    sources: str,
    response_time_ms: float,
) -> None:
    with _db() as conn:
        conn.execute(
            "INSERT INTO query_logs "
            "(id, user_id, username, query_text, response_text, sources, response_time_ms, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (_new_id(), user_id, username, query_text, response_text,
             sources, response_time_ms, _now()),
        )


def get_query_logs(limit: int = 100) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM query_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
# FEEDBACK & TRACES
# ═══════════════════════════════════════════════════════════════════════════

def log_feedback(
    trace_id: str,
    user_id: str,
    rating: int,
    comment: str = "",
    source: str = "chat_ui",
    recorded_in_langfuse: bool = False,
) -> str:
    feedback_id = _new_id()
    with _db() as conn:
        conn.execute(
            "INSERT INTO feedback_logs "
            "(id, trace_id, user_id, rating, comment, source, recorded_in_langfuse, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (feedback_id, trace_id, user_id, rating, comment, source,
             int(recorded_in_langfuse), _now()),
        )
    return feedback_id


def log_trace_event(
    trace_id: str,
    endpoint: str,
    user_id: str | None = None,
    username: str | None = None,
    status: str = "ok",
    query_preview: str = "",
    response_time_ms: float = 0.0,
    route_mode: str = "",
    retrieval_mode: str = "",
    chunks_count: int = 0,
    provider: str = "",
    model: str = "",
    **extra: object,
) -> str:
    event_id = _new_id()
    with _db() as conn:
        conn.execute(
            "INSERT INTO trace_events "
            "(id, trace_id, endpoint, user_id, username, status, query_preview, "
            " response_time_ms, route_mode, retrieval_mode, chunks_count, provider, model, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, trace_id, endpoint, user_id, username, status,
             query_preview, response_time_ms, route_mode, retrieval_mode,
             chunks_count, provider, model, _now()),
        )
    return event_id


def get_trace_events(
    limit: int = 120,
    status: str | None = None,
    endpoint: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    sql = "SELECT * FROM trace_events WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if endpoint:
        sql += " AND endpoint = ?"
        params.append(endpoint)
    if provider:
        sql += " AND provider = ?"
        params.append(provider)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with _db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_trace_event_summary(window_minutes: int = 60) -> dict:
    window = f"-{int(window_minutes)} minutes"
    with _db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM trace_events WHERE datetime(created_at) >= datetime('now', ?)",
            (window,),
        ).fetchone()[0]
        avg_ms = conn.execute(
            "SELECT AVG(response_time_ms) FROM trace_events WHERE datetime(created_at) >= datetime('now', ?)",
            (window,),
        ).fetchone()[0]
        by_status = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM trace_events "
            "WHERE datetime(created_at) >= datetime('now', ?) GROUP BY status ORDER BY cnt DESC",
            (window,),
        ).fetchall()
        by_endpoint = conn.execute(
            "SELECT endpoint, COUNT(*) as cnt FROM trace_events "
            "WHERE datetime(created_at) >= datetime('now', ?) GROUP BY endpoint ORDER BY cnt DESC LIMIT 10",
            (window,),
        ).fetchall()
    return {
        "window_minutes": int(window_minutes),
        "total_events": total,
        "avg_response_ms": round(avg_ms, 1) if avg_ms else 0,
        "by_status": [dict(r) for r in by_status],
        "by_endpoint": [dict(r) for r in by_endpoint],
    }


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENT QUESTION SUGGESTIONS
# ═══════════════════════════════════════════════════════════════════════════

def store_document_question_suggestions(
    document_id: str,
    questions: list[str],
    source_hint: str | None = None,
) -> int:
    """Replace all question suggestions for a document. Returns count stored."""
    with _db() as conn:
        conn.execute(
            "DELETE FROM document_question_suggestions WHERE document_id = ?",
            (document_id,),
        )
        rows = [
            (_new_id(), document_id, q.strip(), source_hint, _now())
            for q in (questions or [])
            if q and q.strip()
        ]
        conn.executemany(
            "INSERT INTO document_question_suggestions "
            "(id, document_id, question_text, source_hint, created_at) VALUES (?,?,?,?,?)",
            rows,
        )
    return len(rows)


# ═══════════════════════════════════════════════════════════════════════════
# PRESET & AUTOCOMPLETE SUGGESTIONS
# ═══════════════════════════════════════════════════════════════════════════

PRESET_QUESTIONS: list[str] = [
    "What are the admission requirements?",
    "What is the fee structure for this semester?",
    "What are the hostel facilities available?",
    "What is the exam schedule?",
    "How to apply for scholarships?",
    "What are the placement statistics?",
    "What is the attendance policy?",
    "What courses are offered in Computer Science?",
    "What are the library timings?",
    "How to get a bonafide certificate?",
    "What is the anti-ragging policy?",
    "What are the sports facilities available?",
    "How to contact the student grievance cell?",
    "What is the syllabus for the current semester?",
    "What are the rules for internal assessment?",
]


def get_preset_questions(prefix: str = "", limit: int = 5) -> list[str]:
    if not prefix:
        return PRESET_QUESTIONS[:limit]
    prefix_lower = prefix.lower()
    return [q for q in PRESET_QUESTIONS if prefix_lower in q.lower()][:limit]


def get_suggestions(query_prefix: str, user_id: str | None = None, limit: int = 5) -> dict:
    """Return autocomplete suggestions grouped as recent / popular / preset."""
    recent: list[str] = []
    popular: list[str] = []
    seen: set[str] = set()

    if query_prefix and len(query_prefix) >= 2:
        pattern = f"%{query_prefix}%"
        with _db() as conn:
            if user_id:
                for row in conn.execute(
                    "SELECT DISTINCT query_text FROM query_logs "
                    "WHERE user_id = ? AND query_text LIKE ? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (user_id, pattern, limit),
                ).fetchall():
                    q = row["query_text"]
                    if q not in seen:
                        recent.append(q)
                        seen.add(q)

            for row in conn.execute(
                "SELECT query_text, COUNT(*) as cnt FROM query_logs "
                "WHERE query_text LIKE ? GROUP BY query_text "
                "ORDER BY cnt DESC LIMIT ?",
                (pattern, limit + len(seen)),
            ).fetchall():
                q = row["query_text"]
                if q not in seen:
                    popular.append(q)
                    seen.add(q)
                    if len(popular) >= limit:
                        break

    preset = [q for q in get_preset_questions(query_prefix, limit) if q not in seen]

    return {
        "recent":  recent[:limit],
        "popular": popular[:limit],
        "preset":  preset[:limit],
    }


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

def get_analytics() -> dict:
    with _db() as conn:
        total_queries  = conn.execute("SELECT COUNT(*) FROM query_logs").fetchone()[0]
        total_docs     = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        total_users    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        avg_ms         = conn.execute("SELECT AVG(response_time_ms) FROM query_logs").fetchone()[0]
        daily_queries  = conn.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM query_logs "
            "WHERE datetime(created_at) >= datetime('now', '-7 days') "
            "GROUP BY DATE(created_at) ORDER BY day"
        ).fetchall()
        top_users = conn.execute(
            "SELECT username, COUNT(*) as cnt FROM query_logs "
            "GROUP BY username ORDER BY cnt DESC LIMIT 5"
        ).fetchall()

    return {
        "total_queries":    total_queries,
        "total_documents":  total_docs,
        "total_users":      total_users,
        "avg_response_ms":  round(avg_ms, 1) if avg_ms else 0,
        "daily_queries":    [dict(r) for r in daily_queries],
        "top_users":        [dict(r) for r in top_users],
    }


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSATION MEMORY  (semantic cache)
# ═══════════════════════════════════════════════════════════════════════════

def store_memory(
    memory_id: str,
    query_text: str,
    response_text: str,
    sources: str,
    user_id: str | None = None,
    expires_at: str | None = None,
) -> None:
    now = _now()
    with _db() as conn:
        # Keep memory writes robust when callers pass a stale/unknown user id.
        effective_user_id = user_id
        if effective_user_id:
            user_exists = conn.execute(
                "SELECT 1 FROM users WHERE id = ?",
                (effective_user_id,),
            ).fetchone()
            if not user_exists:
                effective_user_id = None

        conn.execute(
            "INSERT INTO conversation_memory "
            "(id, query_text, response_text, sources, user_id, created_at, last_accessed, expires_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (memory_id, query_text, response_text, sources, effective_user_id, now, now, expires_at),
        )


def update_memory_usage(memory_id: str, similarity: float | None = None) -> None:
    with _db() as conn:
        conn.execute(
            "UPDATE conversation_memory "
            "SET usage_count = usage_count + 1, last_accessed = ? WHERE id = ?",
            (_now(), memory_id),
        )


def delete_memory(memory_id: str) -> bool:
    try:
        with _db() as conn:
            conn.execute("DELETE FROM conversation_memory WHERE id = ?", (memory_id,))
        return True
    except Exception:
        logger.exception("Failed to delete memory %s", memory_id)
        return False


def cleanup_expired_memory() -> int:
    """Delete expired and very old memory entries. Returns total rows removed."""
    with _db() as conn:
        c1 = conn.execute(
            "DELETE FROM conversation_memory "
            "WHERE expires_at IS NOT NULL "
            "AND datetime(expires_at) < datetime(?) "
            "AND usage_count < ?",
            (_now(), CONV_MIN_USAGE_FOR_KEEP),
        )
        c2 = conn.execute(
            "DELETE FROM conversation_memory "
            "WHERE datetime(created_at) < datetime('now', '-180 days')"
        )
    deleted = c1.rowcount + c2.rowcount
    logger.info("Cleaned up %d expired memory entries", deleted)
    return deleted


def invalidate_memory_by_source(source_doc: str) -> int:
    with _db() as conn:
        cursor = conn.execute(
            "DELETE FROM conversation_memory WHERE sources LIKE ?",
            (f"%{source_doc}%",),
        )
    return cursor.rowcount


def get_memory_stats() -> dict:
    with _db() as conn:
        total   = conn.execute("SELECT COUNT(*) FROM conversation_memory").fetchone()[0]
        avg_use = conn.execute("SELECT AVG(usage_count) FROM conversation_memory").fetchone()[0]
        by_user = conn.execute(
            "SELECT COALESCE(u.username, 'Global') as username, "
            "COUNT(*) as entries, AVG(cm.usage_count) as avg_usage "
            "FROM conversation_memory cm "
            "LEFT JOIN users u ON cm.user_id = u.id "
            "GROUP BY cm.user_id ORDER BY entries DESC"
        ).fetchall()
    return {
        "total_entries":        total,
        "avg_usage_per_entry":  round(avg_use, 2) if avg_use else 0,
        "by_user": [
            {
                "user_id":  r["username"],
                "username":  r["username"],
                "cnt":       r["entries"],
                "entries":   r["entries"],
                "avg_usage": round(r["avg_usage"], 2) if r["avg_usage"] else 0,
            }
            for r in by_user
        ],
    }


def memory_entry_exists(memory_id: str) -> bool:
    """Return True if the memory entry exists in SQLite."""
    with _db() as conn:
        row = conn.execute(
            "SELECT 1 FROM conversation_memory WHERE id = ?",
            (memory_id,),
        ).fetchone()
    return bool(row)


def clear_all_memory() -> int:
    with _db() as conn:
        cursor = conn.execute("DELETE FROM conversation_memory")
    return cursor.rowcount


# ═══════════════════════════════════════════════════════════════════════════
# TAGS & CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════

def create_tag(name: str, description: str, color: str, created_by: str) -> str | None:
    tag_id = _new_id()
    try:
        with _db() as conn:
            conn.execute(
                "INSERT INTO tags (id, name, description, color, created_by, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (tag_id, name, description, color, created_by, _now()),
            )
        return tag_id
    except sqlite3.IntegrityError:
        return None


def get_all_tags() -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT t.id, t.name, t.description, t.color, t.created_by, t.created_at, "
            "COUNT(dt.id) as usage_count "
            "FROM tags t LEFT JOIN document_tags dt ON t.id = dt.tag_id "
            "GROUP BY t.id ORDER BY t.created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_tag(
    tag_id: str,
    name: str | None = None,
    description: str | None = None,
    color: str | None = None,
) -> bool:
    fields: dict[str, object] = {}
    if name        is not None: fields["name"]        = name
    if description is not None: fields["description"] = description
    if color       is not None: fields["color"]       = color
    if not fields:
        return True

    set_clause = ", ".join(f"{col} = ?" for col in fields)
    params = list(fields.values()) + [tag_id]
    try:
        with _db() as conn:
            conn.execute(f"UPDATE tags SET {set_clause} WHERE id = ?", params)
        return True
    except Exception:
        logger.exception("Failed to update tag %s", tag_id)
        return False


def delete_tag(tag_id: str) -> bool:
    try:
        with _db() as conn:
            conn.execute("DELETE FROM document_tags WHERE tag_id = ?", (tag_id,))
            conn.execute("DELETE FROM tags WHERE id = ?",               (tag_id,))
        return True
    except Exception:
        logger.exception("Failed to delete tag %s", tag_id)
        return False


def add_tag_to_document(doc_id: str, tag_id: str, added_by: str) -> bool:
    try:
        with _db() as conn:
            conn.execute(
                "INSERT INTO document_tags (id, document_id, tag_id, added_by, added_at) "
                "VALUES (?,?,?,?,?)",
                (_new_id(), doc_id, tag_id, added_by, _now()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def remove_tag_from_document(doc_id: str, tag_id: str) -> bool:
    try:
        with _db() as conn:
            conn.execute(
                "DELETE FROM document_tags WHERE document_id = ? AND tag_id = ?",
                (doc_id, tag_id),
            )
        return True
    except Exception:
        return False


def get_document_tags(doc_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT t.id, t.name, t.description, t.color "
            "FROM tags t JOIN document_tags dt ON t.id = dt.tag_id "
            "WHERE dt.document_id = ? ORDER BY t.name",
            (doc_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def set_document_classification(
    doc_id: str,
    classification: str,
    confidence: float = 1.0,
    auto_classified: bool = False,
    classified_by: str | None = None,
    notes: str | None = None,
) -> bool:
    try:
        with _db() as conn:
            existing = conn.execute(
                "SELECT id FROM document_classifications WHERE document_id = ?", (doc_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE document_classifications "
                    "SET classification=?, confidence=?, auto_classified=?, "
                    "    classified_by=?, classified_at=?, notes=? "
                    "WHERE document_id=?",
                    (classification, confidence, int(auto_classified),
                     classified_by, _now(), notes, doc_id),
                )
            else:
                conn.execute(
                    "INSERT INTO document_classifications "
                    "(id, document_id, classification, confidence, auto_classified, "
                    " classified_by, classified_at, notes) VALUES (?,?,?,?,?,?,?,?)",
                    (_new_id(), doc_id, classification, confidence,
                     int(auto_classified), classified_by, _now(), notes),
                )
        return True
    except Exception:
        logger.exception("Failed to set classification for doc %s", doc_id)
        return False


def get_document_classification(doc_id: str) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM document_classifications WHERE document_id = ?", (doc_id,)
        ).fetchone()
    return dict(row) if row else None


def get_documents_by_classification(classification: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT d.* FROM documents d "
            "JOIN document_classifications dc ON d.id = dc.document_id "
            "WHERE dc.classification = ? ORDER BY d.uploaded_at DESC",
            (classification,),
        ).fetchall()
    return [dict(r) for r in rows]


def filter_documents_by_tags(tag_ids: list[str]) -> list[dict]:
    """Return documents that have ALL of the specified tags."""
    if not tag_ids:
        return []
    placeholders = ",".join("?" * len(tag_ids))
    with _db() as conn:
        rows = conn.execute(
            f"SELECT d.* FROM documents d "
            f"WHERE d.id IN ("
            f"  SELECT document_id FROM document_tags "
            f"  WHERE tag_id IN ({placeholders}) "
            f"  GROUP BY document_id HAVING COUNT(DISTINCT tag_id) = ?"
            f") ORDER BY d.uploaded_at DESC",
            tag_ids + [len(tag_ids)],
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════

def get_all_rate_limits() -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, endpoint, limit_requests, limit_window_seconds, "
            "enabled, description, updated_by, updated_at "
            "FROM rate_limit_configs ORDER BY endpoint"
        ).fetchall()
    return [dict(r) for r in rows]


def get_rate_limit(endpoint: str) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM rate_limit_configs WHERE endpoint = ?", (endpoint,)
        ).fetchone()
    return dict(row) if row else None


def update_rate_limit(
    endpoint: str,
    limit_requests: int,
    limit_window_seconds: int,
    enabled: bool = True,
    updated_by: str | None = None,
) -> bool:
    try:
        with _db() as conn:
            conn.execute(
                "UPDATE rate_limit_configs "
                "SET limit_requests=?, limit_window_seconds=?, enabled=?, "
                "    updated_by=?, updated_at=? "
                "WHERE endpoint=?",
                (limit_requests, limit_window_seconds, int(enabled),
                 updated_by, _now(), endpoint),
            )
        return True
    except Exception:
        return False


def toggle_rate_limit(endpoint: str, enabled: bool, updated_by: str | None = None) -> bool:
    try:
        with _db() as conn:
            conn.execute(
                "UPDATE rate_limit_configs SET enabled=?, updated_by=?, updated_at=? "
                "WHERE endpoint=?",
                (int(enabled), updated_by, _now(), endpoint),
            )
        return True
    except Exception:
        return False


def reset_rate_limits_to_default() -> bool:
    try:
        with _db() as conn:
            for ep, lim, win, _ in _DEFAULT_RATE_LIMITS:
                conn.execute(
                    "UPDATE rate_limit_configs "
                    "SET limit_requests=?, limit_window_seconds=?, enabled=1, updated_at=? "
                    "WHERE endpoint=?",
                    (lim, win, _now(), ep),
                )
        return True
    except Exception:
        logger.exception("Failed to reset rate limits")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# ANNOUNCEMENTS
# ═══════════════════════════════════════════════════════════════════════════

def create_announcement(user_id: str, author_name: str, content: str) -> str:
    ann_id = _new_id()
    with _db() as conn:
        conn.execute(
            "INSERT INTO announcements (id, user_id, author_name, content, created_at) "
            "VALUES (?,?,?,?,?)",
            (ann_id, user_id, author_name, content, _now()),
        )
    return ann_id


def get_recent_announcements(limit: int = 50) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM announcements ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def delete_announcement(
    announcement_id: str,
    requesting_user_id: str,
    requesting_user_role: str,
) -> bool:
    """Admins can delete any announcement; authors can delete their own."""
    with _db() as conn:
        row = conn.execute(
            "SELECT id, user_id FROM announcements WHERE id = ?", (announcement_id,)
        ).fetchone()
        if not row:
            return False

        is_admin  = requesting_user_role == "admin"
        is_author = row["user_id"] == requesting_user_id
        if not is_admin and not is_author:
            return False

        conn.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM OBSERVABILITY (SQLite-based tracing)
# ═══════════════════════════════════════════════════════════════════════════

def start_trace(trace_id: str, service: str, operation: str, user_id: str | None = None, metadata: dict | None = None) -> bool:
    """Start a new trace (root of a distributed trace)."""
    try:
        with _db() as conn:
            conn.execute(
                """INSERT INTO obs_traces
                   (trace_id, service, operation, user_id, start_time, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (trace_id, service, operation, user_id, _now(),
                 str(metadata or {}), _now())
            )
        return True
    except Exception as e:
        logger.warning(f"Failed to start trace: {e}")
        return False


def end_trace(trace_id: str, status: str = "success", error: str | None = None) -> bool:
    """End a trace and compute total duration."""
    try:
        with _db() as conn:
            conn.execute(
                """UPDATE obs_traces
                   SET status = ?, error = ?, end_time = ?,
                       duration_ms = CAST((julianday(?) - julianday(start_time)) * 86400000 AS REAL)
                   WHERE trace_id = ?""",
                (status, error, _now(), _now(), trace_id)
            )
        return True
    except Exception as e:
        logger.warning(f"Failed to end trace: {e}")
        return False


def start_span(trace_id: str, span_id: str, service: str, operation: str,
               input_data: dict | None = None, parent_span_id: str | None = None) -> bool:
    """Start a new span within a trace."""
    try:
        with _db() as conn:
            conn.execute(
                """INSERT INTO obs_spans
                   (span_id, trace_id, parent_span_id, service, operation,
                    start_time, input_data, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (span_id, trace_id, parent_span_id, service, operation,
                 _now(), str(input_data or {}), _now())
            )
        return True
    except Exception as e:
        logger.warning(f"Failed to start span: {e}")
        return False


def end_span(span_id: str, status: str = "success", output_data: dict | None = None,
             error: str | None = None, tags: dict | None = None) -> bool:
    """End a span and compute duration."""
    try:
        with _db() as conn:
            conn.execute(
                """UPDATE obs_spans
                   SET status = ?, error = ?, output_data = ?, tags = ?,
                       end_time = ?,
                       duration_ms = CAST((julianday(?) - julianday(start_time)) * 86400000 AS REAL)
                   WHERE span_id = ?""",
                (status, error, str(output_data or {}), str(tags or {}),
                 _now(), _now(), span_id)
            )
        return True
    except Exception as e:
        logger.warning(f"Failed to end span: {e}")
        return False


def get_traces(limit: int = 50, offset: int = 0, days: int = 7) -> list[dict]:
    """Get recent traces."""
    try:
        cutoff_time = datetime.now(timezone.utc).isoformat()
        # Simple approximation: 1 day ≈ 86400 seconds
        with _db() as conn:
            rows = conn.execute(
                """SELECT trace_id, service, operation, user_id, duration_ms,
                          status, error, created_at
                   FROM obs_traces
                   WHERE created_at >= datetime('now', '-' || ? || ' days')
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (days, limit, offset)
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Failed to get traces: {e}")
        return []


def get_spans_for_trace(trace_id: str) -> list[dict]:
    """Get all spans for a specific trace."""
    try:
        with _db() as conn:
            rows = conn.execute(
                """SELECT span_id, service, operation, duration_ms, status,
                          error, start_time
                   FROM obs_spans
                   WHERE trace_id = ?
                   ORDER BY start_time ASC""",
                (trace_id,)
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Failed to get spans: {e}")
        return []


def get_observability_metrics(days: int = 7) -> dict:
    """Get aggregate observability metrics."""
    try:
        with _db() as conn:
            # Total traces
            total = conn.execute(
                """SELECT COUNT(*) as cnt FROM obs_traces
                   WHERE created_at >= datetime('now', '-' || ? || ' days')""",
                (days,)
            ).fetchone()["cnt"]

            # Average latency
            avg_latency = conn.execute(
                """SELECT AVG(duration_ms) as avg FROM obs_traces
                   WHERE created_at >= datetime('now', '-' || ? || ' days')
                   AND duration_ms IS NOT NULL""",
                (days,)
            ).fetchone()["avg"] or 0

            # Error count
            errors = conn.execute(
                """SELECT COUNT(*) as cnt FROM obs_traces
                   WHERE created_at >= datetime('now', '-' || ? || ' days')
                   AND status = 'error'""",
                (days,)
            ).fetchone()["cnt"]

            # By service
            by_service = conn.execute(
                """SELECT service, COUNT(*) as count, AVG(duration_ms) as avg_latency
                   FROM obs_traces
                   WHERE created_at >= datetime('now', '-' || ? || ' days')
                   GROUP BY service
                   ORDER BY count DESC""",
                (days,)
            ).fetchall()

        return {
            "period_days": days,
            "total_traces": total,
            "avg_latency_ms": round(avg_latency, 2),
            "error_count": errors,
            "error_rate_percent": round((errors / total * 100) if total > 0 else 0, 2),
            "by_service": [dict(r) for r in by_service]
        }
    except Exception as e:
        logger.warning(f"Failed to compute metrics: {e}")
        return {}


# ---------------------------------------------------------------------------
# Initialise on import (guarded so test modules can patch SQLITE_DB_PATH first)
# ---------------------------------------------------------------------------
init_db()