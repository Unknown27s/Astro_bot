"""
IMS AstroBot — SQLite Database Layer
Handles schema creation, user management, document records, and query logs.
"""

import sqlite3
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SQLITE_DB_PATH, ADMIN_USERNAME, ADMIN_PASSWORD


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def hash_password(password: str) -> str:
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Initialize all database tables and default admin user."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'faculty', 'student')),
            full_name TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)

    # ── Documents table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            chunk_count INTEGER DEFAULT 0,
            uploaded_by TEXT,
            uploaded_at TEXT NOT NULL,
            status TEXT DEFAULT 'processed',
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    """)

    # ── Query logs table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            username TEXT,
            query_text TEXT NOT NULL,
            response_text TEXT,
            sources TEXT,
            response_time_ms REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Create default admin if not exists ──
    admin_exists = cursor.execute(
        "SELECT 1 FROM users WHERE username = ?", (ADMIN_USERNAME,)
    ).fetchone()

    if not admin_exists:
        cursor.execute(
            "INSERT INTO users (id, username, password_hash, role, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                ADMIN_USERNAME,
                hash_password(ADMIN_PASSWORD),
                "admin",
                "System Administrator",
                datetime.now().isoformat(),
            ),
        )

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════
# USER CRUD
# ═══════════════════════════════════════════

def create_user(username: str, password: str, role: str, full_name: str = "") -> bool:
    """Create a new user. Returns True on success."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO users (id, username, password_hash, role, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), username, hash_password(password), role, full_name, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user. Returns user dict or None."""
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
        (username, hash_password(password)),
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_users() -> list[dict]:
    """Get all users."""
    conn = get_connection()
    users = conn.execute("SELECT id, username, role, full_name, created_at, is_active FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(u) for u in users]


def toggle_user_active(user_id: str, is_active: bool) -> bool:
    """Enable/disable a user account."""
    conn = get_connection()
    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (int(is_active), user_id))
    conn.commit()
    conn.close()
    return True


def delete_user(user_id: str) -> bool:
    """Delete a user by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


# ═══════════════════════════════════════════
# DOCUMENT CRUD
# ═══════════════════════════════════════════

def add_document(filename: str, original_name: str, file_type: str, file_size: int, chunk_count: int, uploaded_by: str) -> str:
    """Record a new document. Returns document ID."""
    doc_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        "INSERT INTO documents (id, filename, original_name, file_type, file_size, chunk_count, uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?,?)",
        (doc_id, filename, original_name, file_type, file_size, chunk_count, uploaded_by, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return doc_id


def get_all_documents() -> list[dict]:
    """Get all document records."""
    conn = get_connection()
    docs = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    conn.close()
    return [dict(d) for d in docs]


def delete_document(doc_id: str) -> Optional[dict]:
    """Delete a document record and return its info for cleanup."""
    conn = get_connection()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if doc:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        return dict(doc)
    conn.close()
    return None


# ═══════════════════════════════════════════
# QUERY LOGS
# ═══════════════════════════════════════════

def log_query(user_id: str, username: str, query_text: str, response_text: str, sources: str, response_time_ms: float):
    """Log a query and response."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO query_logs (id, user_id, username, query_text, response_text, sources, response_time_ms, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), user_id, username, query_text, response_text, sources, response_time_ms, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_query_logs(limit: int = 100) -> list[dict]:
    """Get recent query logs."""
    conn = get_connection()
    logs = conn.execute("SELECT * FROM query_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(l) for l in logs]


def get_analytics() -> dict:
    """Get usage analytics summary."""
    conn = get_connection()
    total_queries = conn.execute("SELECT COUNT(*) as cnt FROM query_logs").fetchone()["cnt"]
    total_docs = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
    total_users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
    avg_response = conn.execute("SELECT AVG(response_time_ms) as avg_ms FROM query_logs").fetchone()["avg_ms"]

    # Queries per day (last 7 days)
    daily_queries = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt 
        FROM query_logs 
        WHERE created_at >= datetime('now', '-7 days')
        GROUP BY DATE(created_at) 
        ORDER BY day
    """).fetchall()

    # Top querying users
    top_users = conn.execute("""
        SELECT username, COUNT(*) as cnt 
        FROM query_logs 
        GROUP BY username 
        ORDER BY cnt DESC 
        LIMIT 5
    """).fetchall()

    conn.close()

    return {
        "total_queries": total_queries,
        "total_documents": total_docs,
        "total_users": total_users,
        "avg_response_ms": round(avg_response, 1) if avg_response else 0,
        "daily_queries": [dict(d) for d in daily_queries],
        "top_users": [dict(u) for u in top_users],
    }


# Initialize on import
init_db()
