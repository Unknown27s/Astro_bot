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
from tests.config import SQLITE_DB_PATH, ADMIN_USERNAME, ADMIN_PASSWORD


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(str(SQLITE_DB_PATH), timeout=10)
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

    # ── Feedback logs table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_logs (
            id TEXT PRIMARY KEY,
            trace_id TEXT NOT NULL,
            user_id TEXT,
            rating INTEGER NOT NULL,
            comment TEXT,
            source TEXT,
            recorded_in_langfuse INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Trace events table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trace_events (
            id TEXT PRIMARY KEY,
            trace_id TEXT,
            endpoint TEXT,
            user_id TEXT,
            username TEXT,
            status TEXT,
            query_preview TEXT,
            response_time_ms REAL,
            route_mode TEXT,
            retrieval_mode TEXT,
            chunks_count INTEGER DEFAULT 0,
            provider TEXT,
            model TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # ── Document question suggestions table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_question_suggestions (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            question TEXT NOT NULL,
            source_hint TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    # ── Conversation memory table (for semantic caching) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id TEXT PRIMARY KEY,
            query_text TEXT NOT NULL,
            response_text TEXT NOT NULL,
            sources TEXT,
            user_id TEXT,
            usage_count INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_accessed TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversation_memory_user 
        ON conversation_memory(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversation_memory_expires
        ON conversation_memory(expires_at)
    """)

    # ── Tags table (Phase 3) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#808080',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # ── Document-Tag Junction (many-to-many) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_tags (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            added_by TEXT,
            added_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            FOREIGN KEY (added_by) REFERENCES users(id),
            UNIQUE(document_id, tag_id)
        )
    """)

    # ── Classifications table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_classifications (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL UNIQUE,
            classification TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            auto_classified INTEGER DEFAULT 0,
            classified_by TEXT,
            classified_at TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (classified_by) REFERENCES users(id)
        )
    """)

    # ── Classification Templates table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classification_templates (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # ── Create indexes for tagging ──
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_tags_doc ON document_tags(document_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_tags_tag ON document_tags(tag_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_classification ON document_classifications(classification)
    """)

    # ── Rate Limiting Configuration table (Admin controlled) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit_configs (
            id TEXT PRIMARY KEY,
            endpoint TEXT UNIQUE NOT NULL,
            limit_requests INTEGER NOT NULL,
            limit_window_seconds INTEGER NOT NULL,
            enabled INTEGER DEFAULT 1,
            description TEXT,
            updated_by TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """)

    # ── Create index for rate limit lookups ──
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rate_limit_endpoint ON rate_limit_configs(endpoint)
    """)

    # ── Insert default rate limits if table is empty ──
    default_limits = [
        ('auth', 5, 60, 'Login/Register - brute-force protection'),
        ('chat', 5, 60, 'LLM queries - expensive operations'),
        ('documents/upload', 10, 60, 'Document uploads - resource intensive'),
        ('documents/tags', 30, 60, 'Tag management - moderate load'),
        ('documents/read', 60, 60, 'Read operations - list tags, documents'),
        ('documents/classify', 30, 60, 'Classification operations'),
        ('global', 100, 60, 'Global rate limit - all requests'),
    ]

    existing_limits = cursor.execute("SELECT COUNT(*) as cnt FROM rate_limit_configs").fetchone()['cnt']
    if existing_limits == 0:
        for endpoint, limit_req, window, desc in default_limits:
            cursor.execute(
                "INSERT INTO rate_limit_configs (id, endpoint, limit_requests, limit_window_seconds, description, updated_at) VALUES (?,?,?,?,?,?)",
                (str(uuid.uuid4()), endpoint, limit_req, window, desc, datetime.now().isoformat()),
            )

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

    # ── Announcements table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

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
    """Delete a user by ID, including related records."""
    conn = get_connection()
    try:
        # Delete related query logs
        conn.execute("DELETE FROM query_logs WHERE user_id = ?", (user_id,))
        # Delete related documents
        conn.execute("DELETE FROM documents WHERE uploaded_by = ?", (user_id,))
        # Delete user
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ═══════════════════════════════════════════
# DOCUMENT CRUD
# ═══════════════════════════════════════════

def add_document(
    filename: str,
    original_name: str,
    file_type: str,
    file_size: int,
    chunk_count: int,
    uploaded_by: str,
    source_type: str = None,
    source_domain: str = None,
    source_url: str = None,
) -> str:
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


def log_feedback(
    trace_id: str,
    user_id: str,
    rating: int,
    comment: str = "",
    source: str = "chat_ui",
    recorded_in_langfuse: bool = False,
) -> str:
    """Persist user feedback for chat responses and return the feedback ID."""
    feedback_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO feedback_logs
            (id, trace_id, user_id, rating, comment, source, recorded_in_langfuse, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                trace_id,
                user_id,
                rating,
                comment,
                source,
                1 if recorded_in_langfuse else 0,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return feedback_id
    finally:
        conn.close()


def log_trace_event(
    trace_id: str,
    endpoint: str,
    user_id: str = None,
    username: str = None,
    status: str = "ok",
    query_preview: str = "",
    response_time_ms: float = 0.0,
    route_mode: str = "",
    retrieval_mode: str = "",
    chunks_count: int = 0,
    provider: str = "",
    model: str = "",
) -> str:
    """Persist a trace event for monitoring and return its ID."""
    event_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO trace_events
            (id, trace_id, endpoint, user_id, username, status, query_preview,
             response_time_ms, route_mode, retrieval_mode, chunks_count, provider, model, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                trace_id,
                endpoint,
                user_id,
                username,
                status,
                query_preview,
                response_time_ms,
                route_mode,
                retrieval_mode,
                chunks_count,
                provider,
                model,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return event_id
    finally:
        conn.close()


def get_trace_events(
    limit: int = 120,
    status: str = None,
    endpoint: str = None,
    provider: str = None,
) -> list[dict]:
    """Get recent trace events with optional filters."""
    conn = get_connection()
    try:
        query = "SELECT * FROM trace_events WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if endpoint:
            query += " AND endpoint = ?"
            params.append(endpoint)
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_trace_event_summary(window_minutes: int = 60) -> dict:
    """Summarize recent trace events for dashboard monitoring."""
    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) as cnt FROM trace_events WHERE created_at >= datetime('now', ?)",
            (f"-{int(window_minutes)} minutes",),
        ).fetchone()["cnt"]
        avg_response = conn.execute(
            "SELECT AVG(response_time_ms) as avg_ms FROM trace_events WHERE created_at >= datetime('now', ?)",
            (f"-{int(window_minutes)} minutes",),
        ).fetchone()["avg_ms"]
        by_status = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM trace_events WHERE created_at >= datetime('now', ?) GROUP BY status ORDER BY cnt DESC",
            (f"-{int(window_minutes)} minutes",),
        ).fetchall()
        by_endpoint = conn.execute(
            "SELECT endpoint, COUNT(*) as cnt FROM trace_events WHERE created_at >= datetime('now', ?) GROUP BY endpoint ORDER BY cnt DESC LIMIT 10",
            (f"-{int(window_minutes)} minutes",),
        ).fetchall()
        return {
            "window_minutes": int(window_minutes),
            "total_events": total,
            "avg_response_ms": round(avg_response, 1) if avg_response else 0,
            "by_status": [dict(row) for row in by_status],
            "by_endpoint": [dict(row) for row in by_endpoint],
        }
    finally:
        conn.close()


def store_document_question_suggestions(document_id: str, questions: list[str], source_hint: str = None) -> int:
    """Persist generated question suggestions for a document and return the count stored."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM document_question_suggestions WHERE document_id = ?", (document_id,))
        stored = 0
        for question in questions or []:
            cleaned = (question or "").strip()
            if not cleaned:
                continue
            conn.execute(
                """
                INSERT INTO document_question_suggestions
                (id, document_id, question, source_hint, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), document_id, cleaned, source_hint, datetime.now().isoformat()),
            )
            stored += 1
        conn.commit()
        return stored
    finally:
        conn.close()


# ── Preset Suggestion Questions ──
PRESET_QUESTIONS = [
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
    "What is the syllabus for current semester?",
    "What are the rules for internal assessment?",
]


def get_preset_questions(prefix: str = "", limit: int = 5) -> list[str]:
    """Get preset/common questions that match a prefix."""
    if not prefix:
        return PRESET_QUESTIONS[:limit]
    prefix_lower = prefix.lower()
    matching = [q for q in PRESET_QUESTIONS if prefix_lower in q.lower()]
    return matching[:limit]


def get_suggestions(query_prefix: str, user_id: str = None, limit: int = 5) -> dict:
    """
    Get autocomplete suggestions from query_logs.

    Returns:
        Dict with 'recent' (user's own), 'popular' (all users), and 'preset' lists.
    """
    conn = get_connection()
    try:
        recent = []
        popular = []
        seen = set()  # track seen queries for deduplication

        if query_prefix and len(query_prefix) >= 2:
            search_pattern = f"%{query_prefix}%"

            # 1) User's recent queries
            if user_id:
                rows = conn.execute(
                    """SELECT DISTINCT query_text FROM query_logs
                       WHERE user_id = ? AND query_text LIKE ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (user_id, search_pattern, limit),
                ).fetchall()
                for row in rows:
                    q = row["query_text"]
                    if q not in seen:
                        recent.append(q)
                        seen.add(q)

            # 2) Popular queries across all users
            rows = conn.execute(
                """SELECT query_text, COUNT(*) as cnt FROM query_logs
                   WHERE query_text LIKE ?
                   GROUP BY query_text
                   ORDER BY cnt DESC LIMIT ?""",
                (search_pattern, limit + len(seen)),
            ).fetchall()
            for row in rows:
                q = row["query_text"]
                if q not in seen:
                    popular.append(q)
                    seen.add(q)
                    if len(popular) >= limit:
                        break

        # 3) Preset questions (always included, filtered by prefix)
        preset = get_preset_questions(query_prefix, limit)
        # Remove presets already in recent/popular
        preset = [q for q in preset if q not in seen]

        return {
            "recent": recent[:limit],
            "popular": popular[:limit],
            "preset": preset[:limit],
        }
    finally:
        conn.close()


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


# ═══════════════════════════════════════════
# CONVERSATION MEMORY (Semantic Cache)
# ═══════════════════════════════════════════

def store_memory(memory_id: str, query_text: str, response_text: str, sources: str, user_id: str = None, expires_at: str = None):
    """Store a conversation memory entry in SQLite."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO conversation_memory 
               (id, query_text, response_text, sources, user_id, created_at, last_accessed, expires_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (memory_id, query_text, response_text, sources, user_id, datetime.now().isoformat(), datetime.now().isoformat(), expires_at),
        )
        conn.commit()
    finally:
        conn.close()


def update_memory_usage(memory_id: str, similarity: float = None):
    """Increment usage count and update last_accessed timestamp."""
    conn = get_connection()
    try:
        # Just update usage count and last accessed time
        # (similarity parameter kept for compatibility but not stored)
        conn.execute(
            "UPDATE conversation_memory SET usage_count = usage_count + 1, last_accessed = ? WHERE id = ?",
            (datetime.now().isoformat(), memory_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_memory(memory_id: str) -> bool:
    """Delete a memory entry by ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM conversation_memory WHERE id = ?", (memory_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def cleanup_expired_memory() -> int:
    """Delete expired memory entries and low-usage old entries. Returns count deleted."""
    from tests.config import CONV_TTL_DAYS, CONV_MIN_USAGE_FOR_KEEP
    
    conn = get_connection()
    try:
        # Delete entries past TTL (unless high usage)
        cursor = conn.execute(
            """DELETE FROM conversation_memory 
               WHERE expires_at IS NOT NULL AND expires_at < ? 
               AND usage_count < ?""",
            (datetime.now().isoformat(), CONV_MIN_USAGE_FOR_KEEP),
        )
        deleted_ttl = cursor.rowcount
        
        # Also delete very old entries (>180 days) regardless of usage
        cursor = conn.execute(
            """DELETE FROM conversation_memory 
               WHERE created_at < datetime('now', '-180 days')""",
        )
        deleted_old = cursor.rowcount
        
        conn.commit()
        return deleted_ttl + deleted_old
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def invalidate_memory_by_source(source_doc: str):
    """Delete memory entries that reference a specific source document. Returns count deleted."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM conversation_memory WHERE sources LIKE ?",
            (f"%{source_doc}%",),
        )
        deleted = cursor.rowcount
        conn.commit()
        return deleted
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_memory_stats() -> dict:
    """Get statistics about stored memories."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as cnt FROM conversation_memory").fetchone()["cnt"]
        
        # Query with LEFT JOIN to get actual usernames from users table
        by_user_raw = conn.execute("""
            SELECT 
                COALESCE(u.username, 'Global') as username,
                COUNT(*) as cnt, 
                AVG(cm.usage_count) as avg_usage
            FROM conversation_memory cm
            LEFT JOIN users u ON cm.user_id = u.id
            GROUP BY cm.user_id
            ORDER BY cnt DESC
        """).fetchall()
        
        avg_usage = conn.execute("SELECT AVG(usage_count) as avg FROM conversation_memory").fetchone()["avg"]
        
        # Transform by_user data to match React expectations
        by_user = []
        for row in by_user_raw:
            by_user.append({
                "username": row["username"],
                "entries": row["cnt"],
                "avg_usage": round(row["avg_usage"], 2) if row["avg_usage"] else 0
            })
        
        return {
            "total_entries": total,
            "avg_usage_per_entry": round(avg_usage, 2) if avg_usage else 0,
            "by_user": by_user,
        }
    finally:
        conn.close()


def clear_all_memory() -> int:
    """Clear all conversation memory entries. Returns count deleted."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM conversation_memory")
        deleted = cursor.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()


# ═══════════════════════════════════════════
# TAGS & CLASSIFICATION (Phase 3)
# ═══════════════════════════════════════════

def create_tag(name: str, description: str, color: str, created_by: str) -> Optional[str]:
    """Create a new tag. Returns tag ID or None."""
    tag_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO tags (id, name, description, color, created_by, created_at) VALUES (?,?,?,?,?,?)",
            (tag_id, name, description, color, created_by, datetime.now().isoformat()),
        )
        conn.commit()
        return tag_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_all_tags() -> list[dict]:
    """Get all tags with usage counts."""
    conn = get_connection()
    try:
        tags = conn.execute("""
            SELECT t.id, t.name, t.description, t.color, t.created_by, t.created_at,
                   COUNT(dt.id) as usage_count
            FROM tags t
            LEFT JOIN document_tags dt ON t.id = dt.tag_id
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """).fetchall()
        return [dict(t) for t in tags]
    finally:
        conn.close()


def update_tag(tag_id: str, name: str = None, description: str = None, color: str = None) -> bool:
    """Update tag properties."""
    conn = get_connection()
    try:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if color is not None:
            updates.append("color = ?")
            params.append(color)

        if updates:
            params.append(tag_id)
            conn.execute(f"UPDATE tags SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def delete_tag(tag_id: str) -> bool:
    """Delete a tag and its associations."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM document_tags WHERE tag_id = ?", (tag_id,))
        conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def add_tag_to_document(doc_id: str, tag_id: str, added_by: str) -> bool:
    """Add a tag to a document."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO document_tags (id, document_id, tag_id, added_by, added_at) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), doc_id, tag_id, added_by, datetime.now().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_tag_from_document(doc_id: str, tag_id: str) -> bool:
    """Remove a tag from a document."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM document_tags WHERE document_id = ? AND tag_id = ?", (doc_id, tag_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_document_tags(doc_id: str) -> list[dict]:
    """Get all tags for a document."""
    conn = get_connection()
    try:
        tags = conn.execute("""
            SELECT t.id, t.name, t.description, t.color
            FROM tags t
            JOIN document_tags dt ON t.id = dt.tag_id
            WHERE dt.document_id = ?
            ORDER BY t.name
        """, (doc_id,)).fetchall()
        return [dict(t) for t in tags]
    finally:
        conn.close()


def set_document_classification(doc_id: str, classification: str, confidence: float = 1.0, auto_classified: bool = False, classified_by: str = None, notes: str = None) -> bool:
    """Set or update classification for a document."""
    conn = get_connection()
    try:
        # Check if already exists
        existing = conn.execute("SELECT id FROM document_classifications WHERE document_id = ?", (doc_id,)).fetchone()

        if existing:
            conn.execute(
                "UPDATE document_classifications SET classification = ?, confidence = ?, auto_classified = ?, classified_by = ?, classified_at = ?, notes = ? WHERE document_id = ?",
                (classification, confidence, int(auto_classified), classified_by, datetime.now().isoformat(), notes, doc_id),
            )
        else:
            conn.execute(
                "INSERT INTO document_classifications (id, document_id, classification, confidence, auto_classified, classified_by, classified_at, notes) VALUES (?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), doc_id, classification, confidence, int(auto_classified), classified_by, datetime.now().isoformat(), notes),
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_document_classification(doc_id: str) -> Optional[dict]:
    """Get classification for a document."""
    conn = get_connection()
    try:
        classification = conn.execute("SELECT * FROM document_classifications WHERE document_id = ?", (doc_id,)).fetchone()
        return dict(classification) if classification else None
    finally:
        conn.close()


def get_documents_by_classification(classification: str) -> list[dict]:
    """Get all documents with a specific classification."""
    conn = get_connection()
    try:
        docs = conn.execute("""
            SELECT d.* FROM documents d
            JOIN document_classifications dc ON d.id = dc.document_id
            WHERE dc.classification = ?
            ORDER BY d.uploaded_at DESC
        """, (classification,)).fetchall()
        return [dict(d) for d in docs]
    finally:
        conn.close()


def filter_documents_by_tags(tag_ids: list[str]) -> list[dict]:
    """Get documents that have ALL of the specified tags."""
    if not tag_ids:
        return []

    conn = get_connection()
    try:
        placeholders = ','.join(['?' for _ in tag_ids])
        docs = conn.execute(f"""
            SELECT d.* FROM documents d
            WHERE d.id IN (
                SELECT document_id FROM document_tags
                WHERE tag_id IN ({placeholders})
                GROUP BY document_id
                HAVING COUNT(DISTINCT tag_id) = ?
            )
            ORDER BY d.uploaded_at DESC
        """, tag_ids + [len(tag_ids)]).fetchall()
        return [dict(d) for d in docs]
    finally:
        conn.close()


# ═══════════════════════════════════════════
# RATE LIMITING CONFIGURATION (Admin)
# ═══════════════════════════════════════════

def get_all_rate_limits() -> list[dict]:
    """Get all rate limit configurations."""
    conn = get_connection()
    try:
        limits = conn.execute("""
            SELECT id, endpoint, limit_requests, limit_window_seconds, enabled, description, updated_by, updated_at
            FROM rate_limit_configs
            ORDER BY endpoint
        """).fetchall()
        return [dict(l) for l in limits]
    finally:
        conn.close()


def get_rate_limit(endpoint: str) -> Optional[dict]:
    """Get rate limit configuration for a specific endpoint."""
    conn = get_connection()
    try:
        limit = conn.execute(
            "SELECT id, endpoint, limit_requests, limit_window_seconds, enabled, description, updated_by, updated_at FROM rate_limit_configs WHERE endpoint = ?",
            (endpoint,)
        ).fetchone()
        return dict(limit) if limit else None
    finally:
        conn.close()


def update_rate_limit(endpoint: str, limit_requests: int, limit_window_seconds: int, enabled: bool = True, updated_by: str = None) -> bool:
    """Update rate limit configuration for an endpoint."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE rate_limit_configs SET limit_requests = ?, limit_window_seconds = ?, enabled = ?, updated_by = ?, updated_at = ? WHERE endpoint = ?",
            (limit_requests, limit_window_seconds, int(enabled), updated_by, datetime.now().isoformat(), endpoint)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def toggle_rate_limit(endpoint: str, enabled: bool, updated_by: str = None) -> bool:
    """Enable/disable rate limiting for an endpoint."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE rate_limit_configs SET enabled = ?, updated_by = ?, updated_at = ? WHERE endpoint = ?",
            (int(enabled), updated_by, datetime.now().isoformat(), endpoint)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def reset_rate_limits_to_default() -> bool:
    """Reset all rate limits to default values."""
    conn = get_connection()
    try:
        default_limits = [
            ('auth', 5, 60),
            ('chat', 5, 60),
            ('documents/upload', 10, 60),
            ('documents/tags', 30, 60),
            ('documents/read', 60, 60),
            ('documents/classify', 30, 60),
            ('global', 100, 60),
        ]

        for endpoint, limit_req, window in default_limits:
            conn.execute(
                "UPDATE rate_limit_configs SET limit_requests = ?, limit_window_seconds = ?, enabled = 1, updated_at = ? WHERE endpoint = ?",
                (limit_req, window, datetime.now().isoformat(), endpoint)
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


# ═══════════════════════════════════════════
# ANNOUNCEMENTS
# ═══════════════════════════════════════════

def create_announcement(user_id: str, author_name: str, content: str) -> str:
    """Create a new global announcement."""
    announcement_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO announcements (id, user_id, author_name, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (announcement_id, user_id, author_name, content, datetime.now().isoformat())
        )
        conn.commit()
        return announcement_id
    finally:
        conn.close()

def get_recent_announcements(limit: int = 50) -> list[dict]:
    """Get the most recent announcements."""
    conn = get_connection()
    try:
        announcements = conn.execute(
            "SELECT * FROM announcements ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(a) for a in announcements]
    finally:
        conn.close()


def delete_announcement(announcement_id: str, requesting_user_id: str, requesting_user_role: str) -> bool:
    """Delete an announcement. Admins can delete any; authors can delete their own.
    
    Returns True if deleted, False if not found or unauthorized.
    """
    conn = get_connection()
    try:
        ann = conn.execute(
            "SELECT id, user_id FROM announcements WHERE id = ?",
            (announcement_id,)
        ).fetchone()
        
        if not ann:
            return False
        
        # Authorization: admin can delete any, author can delete own
        is_admin = requesting_user_role == 'admin'
        is_author = ann['user_id'] == requesting_user_id
        
        if not is_admin and not is_author:
            return False
        
        conn.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
        conn.commit()
        return True
    finally:
        conn.close()

# Initialize on import
init_db()
