# 📊 Database Schema & Design

**Complete SQLite database structure, relationships, and design patterns.**

*Audience: Backend developers, AI agents, architects | Time: 10 minutes*

---

## 📋 Table of Contents

1. [Database Overview](#-database-overview)
2. [Schema Diagram](#-schema-diagram)
3. [Tables Reference](#-tables-reference)
4. [Relationships](#-relationships)
5. [CRUD Operations](#-crud-operations)
6. [Design Patterns](#-design-patterns)
7. [Query Examples](#-query-examples)

---

## 🎯 Database Overview

### What's Stored?

```
SQLite Database (./data/astrobot.db)
├── users ..................... Who can access the system
├── documents ................ What documents are uploaded
└── query_logs ............... Q&A history for analytics
```

### Why SQLite?

| Feature | Benefit |
|---------|---------|
| Serverless | No separate DB server needed |
| File-based | Portable, easy backup |
| ACID compliant | Data integrity guaranteed |
| WAL mode | Concurrent reads while writing |
| Small footprint | 100 MB database handles 1M+ records |

### Storage Location

```
d:\Harish Kumar\Project\Astro_botV2\Astro_bot\
└── data/
    └── astrobot.db ................... Main database file (100-500 MB)
```

---

## 📐 Schema Diagram

```
┌─────────────────────┐
│      users          │
├─────────────────────┤
│ id (PK)             │────────┐
│ username (UNIQUE)   │        │
│ password_hash       │        │
│ role                │        │
│ full_name           │        │
│ email               │        │
│ is_active           │        │
│ created_at          │        │
│ last_login          │        │
└─────────────────────┘        │
                               │
                               │ FK: uploaded_by
                               │
                        ┌──────▼──────────────┐
                        │    documents        │
                        ├─────────────────────┤
                        │ id (PK)             │────────┐
                        │ filename            │        │
                        │ file_type           │        │
                        │ file_size           │        │
                        │ chunk_count         │        │
                        │ uploaded_by (FK)    │        │
                        │ uploaded_at         │        │
                        │ status              │        │
                        └─────────────────────┘        │
                               ▲                       │
                               │ FK: doc_id            │
                               │                       │
                        ┌──────┴──────────────┐        │
                        │   query_logs        │        │
                        ├─────────────────────┤        │
                        │ id (PK)             │        │
                        │ query_text          │        │
                        │ response_text       │        │
                        │ user_id (FK)        │◄───────┘
                        │ doc_id (FK)         │
                        │ sources (JSON)      │
                        │ response_time_ms    │
                        │ created_at          │
                        └─────────────────────┘
```

---

## 📋 Tables Reference

### Table 1: `users`

**Purpose:** Store user accounts and authentication

**Schema:**

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,              -- UUID (auto-generated)
    username TEXT UNIQUE NOT NULL,    -- Login username
    password_hash TEXT NOT NULL,      -- SHA-256 hash (never store plaintext!)
    role TEXT NOT NULL,               -- 'admin' | 'faculty' | 'student'
    full_name TEXT,                   -- Display name
    email TEXT UNIQUE,                -- Contact email
    is_active INTEGER DEFAULT 1,      -- 0 = disabled, 1 = active
    created_at TEXT NOT NULL,         -- ISO timestamp (2024-03-15T10:30:45)
    last_login TEXT,                  -- ISO timestamp of last login
    CHECK(role IN ('admin', 'faculty', 'student'))
);
```

**Indexes:**

```sql
CREATE UNIQUE INDEX idx_username ON users(username);
CREATE UNIQUE INDEX idx_email ON users(email);
CREATE INDEX idx_role ON users(role);
CREATE INDEX idx_is_active ON users(is_active);
```

**Example Records:**

```
id: "550e8400-e29b-41d4-a716-446655440000"
username: "admin"
password_hash: "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
role: "admin"
full_name: "Administrator"
email: "admin@institution.edu"
is_active: 1
created_at: "2024-01-01T00:00:00"
last_login: "2024-03-20T14:32:10"

id: "660e8400-e29b-41d4-a716-446655440001"
username: "prof_smith"
password_hash: "5d41402abc4b2a76b9719d911017c592"
role: "faculty"
full_name: "Dr. Smith"
email: "smith@institution.edu"
is_active: 1
created_at: "2024-02-15T10:30:00"
last_login: "2024-03-20T09:15:00"
```

**Key Constraints:**
- ✅ `id` is primary key (unique, never null)
- ✅ `username` is unique (no duplicates)
- ✅ `email` is unique (no duplicates)
- ✅ `role` limited to 3 values
- ✅ `is_active` is 0 or 1 (boolean)

### Table 2: `documents`

**Purpose:** Track uploaded documents and their processing status

**Schema:**

```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,              -- UUID (auto-generated)
    filename TEXT NOT NULL,           -- Original filename (e.g., "course_syllabus.pdf")
    file_type TEXT NOT NULL,          -- Extension (.pdf, .docx, .xlsx, etc.)
    file_size INTEGER,                -- Bytes (for storage quota tracking)
    chunk_count INTEGER,              -- Number of chunks after processing
    uploaded_by TEXT NOT NULL,        -- FK to users.id (who uploaded)
    uploaded_at TEXT NOT NULL,        -- ISO timestamp
    status TEXT NOT NULL,             -- 'processing' | 'processed' | 'failed'
    error_message TEXT,               -- If failed, why?
    chroma_collection_id TEXT,        -- Reference to ChromaDB collection
    FOREIGN KEY(uploaded_by) REFERENCES users(id),
    CHECK(status IN ('processing', 'processed', 'failed')),
    CHECK(file_type IN ('.pdf', '.docx', '.xlsx', '.pptx', '.html', '.txt'))
);
```

**Indexes:**

```sql
CREATE INDEX idx_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_status ON documents(status);
CREATE INDEX idx_uploaded_at ON documents(uploaded_at);
```

**Example Records:**

```
id: "770e8400-e29b-41d4-a716-446655440000"
filename: "CS101_Syllabus_2024.pdf"
file_type: ".pdf"
file_size: 245860
chunk_count: 24
uploaded_by: "660e8400-e29b-41d4-a716-446655440001"
uploaded_at: "2024-03-15T10:30:00"
status: "processed"
error_message: NULL
chroma_collection_id: "cs101_syllabus_2024"

id: "770e8400-e29b-41d4-a716-446655440001"
filename: "Course_Videos.mp4"
file_type: ".mp4"
file_size: 1073741824
uploaded_by: "550e8400-e29b-41d4-a716-446655440000"
uploaded_at: "2024-03-20T08:00:00"
status: "failed"
error_message: "Unsupported file type: .mp4"
chroma_collection_id: NULL
```

**Key Constraints:**
- ✅ `id` is primary key
- ✅ `uploaded_by` references `users.id` (can't upload if user doesn't exist)
- ✅ `status` limited to 3 values
- ✅ `file_type` validates supported formats

**Related Properties:**
- If `status == 'processed'`: `chunk_count > 0`
- If `status == 'failed'`: `error_message` is not null
- If `status == 'processing'`: Usually temporary (should complete within 2-3 hours)

### Table 3: `query_logs`

**Purpose:** Record Q&A interactions for analytics and debugging

**Schema:**

```sql
CREATE TABLE query_logs (
    id TEXT PRIMARY KEY,              -- UUID (auto-generated)
    user_id TEXT NOT NULL,            -- FK to users.id (who asked)
    query_text TEXT NOT NULL,         -- The question (e.g., "What's the midterm date?")
    response_text TEXT,               -- The answer generated
    sources TEXT,                     -- JSON list of source documents used
    response_time_ms INTEGER,         -- How long it took (milliseconds)
    llm_provider TEXT,                -- Which LLM was used ('ollama', 'grok', 'gemini', etc.)
    model_name TEXT,                  -- Specific model (e.g., 'qwen3:0.6b', 'grok-3')
    confidence_score REAL,            -- 0.0-1.0 (how confident is the AI?)
    created_at TEXT NOT NULL,         -- ISO timestamp
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

**Indexes:**

```sql
CREATE INDEX idx_user_id ON query_logs(user_id);
CREATE INDEX idx_created_at ON query_logs(created_at);
CREATE INDEX idx_llm_provider ON query_logs(llm_provider);
```

**Example Records:**

```
id: "880e8400-e29b-41d4-a716-446655440000"
user_id: "660e8400-e29b-41d4-a716-446655440001"
query_text: "What books are required for this course?"
response_text: "The required books are: 1) Introduction to CS by Turing, 2) Data Structures by Knuth"
sources: "[{'source': 'CS101_Syllabus_2024.pdf', 'page': 3, 'relevance': 0.94}]"
response_time_ms: 487
llm_provider: "ollama"
model_name: "qwen3:0.6b"
confidence_score: 0.87
created_at: "2024-03-20T14:32:10"

id: "880e8400-e29b-41d4-a716-446655440001"
user_id: "550e8400-e29b-41d4-a716-446655440000"
query_text: "How do I drop a course?"
response_text: "To drop a course, follow these steps: 1) Visit registrar office, 2) Fill form, 3) Get approval"
sources: "[{'source': 'Academic_Policies.pdf', 'relevance': 0.89}]"
response_time_ms: 523
llm_provider: "grok"
model_name: "grok-3"
confidence_score: 0.92
created_at: "2024-03-20T15:15:22"
```

**Key Constraints:**
- ✅ `id` is primary key
- ✅ `user_id` references `users.id` (can't log without user)
- ✅ `response_time_ms` is positive integer
- ✅ `confidence_score` is 0.0-1.0

**JSON Format for `sources`:**

```json
[
  {
    "source": "CS101_Syllabus_2024.pdf",
    "page": 3,
    "chunk_index": 5,
    "relevance": 0.94,
    "text_preview": "The required books are..."
  },
  {
    "source": "Course_Readings.txt",
    "relevance": 0.78,
    "text_preview": "Additional resources..."
  }
]
```

---

## 🔗 Relationships

### Foreign Keys

**1. documents.uploaded_by → users.id**

```sql
FOREIGN KEY(uploaded_by) REFERENCES users(id)
ON DELETE CASCADE  -- If user deleted, delete their documents too
```

**When a faculty uploads a document:**
```
users table has: id = "prof_smith_id"
    ↓
documents table records: uploaded_by = "prof_smith_id"
    ↓
If professor leaves: DELETE users WHERE id = "prof_smith_id"
    ↓
Cascade: All their documents deleted automatically
```

**2. query_logs.user_id → users.id**

```sql
FOREIGN KEY(user_id) REFERENCES users(id)
ON DELETE CASCADE  -- If user deleted, delete their query history
```

**When a student asks a question:**
```
users table has: id = "student_id"
    ↓
query_logs table records: user_id = "student_id"
    ↓
If student leaves: DELETE users WHERE id = "student_id"
    ↓
Cascade: All their query history deleted automatically
```

### Referential Integrity

**What this means:**

```
✅ VALID:    query_logs.user_id = "prof_smith_id" (exists in users)
❌ INVALID:  query_logs.user_id = "nonexistent_id" (not in users)
             → SQLite rejects the insert
```

---

## 🔄 CRUD Operations

### CREATE (Insert)

#### Create User (Admin function)

```python
import uuid
import hashlib
from datetime import datetime

def create_user(username, password, role, full_name, email):
    """Insert new user"""
    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    created_at = datetime.now().isoformat()
    
    query = """
    INSERT INTO users (id, username, password_hash, role, full_name, email, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
    """
    
    cursor.execute(query, (user_id, username, password_hash, role, full_name, email, created_at))
    connection.commit()
    
    return user_id
```

#### Add Document Record

```python
def add_document(filename, file_type, file_size, uploaded_by):
    """Insert document record (status = processing initially)"""
    doc_id = str(uuid.uuid4())
    uploaded_at = datetime.now().isoformat()
    
    query = """
    INSERT INTO documents (id, filename, file_type, file_size, uploaded_by, uploaded_at, status)
    VALUES (?, ?, ?, ?, ?, ?, 'processing')
    """
    
    cursor.execute(query, (doc_id, filename, file_type, file_size, uploaded_by, uploaded_at))
    connection.commit()
    
    return doc_id
```

#### Log Query

```python
def log_query(user_id, query_text, response_text, sources, response_time_ms, llm_provider, model_name, confidence):
    """Log Q&A interaction"""
    log_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    sources_json = json.dumps(sources)  # Convert list to JSON
    
    query = """
    INSERT INTO query_logs (id, user_id, query_text, response_text, sources, response_time_ms, 
                            llm_provider, model_name, confidence_score, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(query, (
        log_id, user_id, query_text, response_text, sources_json,
        response_time_ms, llm_provider, model_name, confidence, created_at
    ))
    connection.commit()
```

### READ (Select)

#### Authenticate User

```python
def authenticate_user(username, password):
    """Verify login credentials"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    query = "SELECT id, role, full_name FROM users WHERE username = ? AND password_hash = ? AND is_active = 1"
    cursor.execute(query, (username, password_hash))
    
    result = cursor.fetchone()
    if result:
        return {"user_id": result[0], "role": result[1], "full_name": result[2]}
    else:
        return None
```

#### Get All Documents

```python
def get_documents(status=None):
    """List documents, optionally filtered by status"""
    if status:
        query = "SELECT id, filename, file_type, chunk_count, uploaded_at, status FROM documents WHERE status = ?"
        cursor.execute(query, (status,))
    else:
        query = "SELECT id, filename, file_type, chunk_count, uploaded_at, status FROM documents"
        cursor.execute(query)
    
    return cursor.fetchall()
```

#### Get User Query History

```python
def get_user_queries(user_id, limit=100):
    """Get last 100 queries from a user"""
    query = """
    SELECT id, query_text, response_text, response_time_ms, created_at 
    FROM query_logs 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT ?
    """
    cursor.execute(query, (user_id, limit))
    return cursor.fetchall()
```

### UPDATE (Modify)

#### Update Document Status

```python
def update_document_status(doc_id, status, chunk_count=None, error_message=None):
    """Mark document as processed or failed"""
    query = """
    UPDATE documents 
    SET status = ?, chunk_count = ?, error_message = ? 
    WHERE id = ?
    """
    cursor.execute(query, (status, chunk_count, error_message, doc_id))
    connection.commit()
```

**Example:**
```python
# Mark as processed
update_document_status("doc_123", "processed", chunk_count=24)

# Mark as failed
update_document_status("doc_123", "failed", error_message="PDF corrupted")
```

#### Disable User

```python
def disable_user(user_id):
    """Deactivate user account"""
    query = "UPDATE users SET is_active = 0 WHERE id = ?"
    cursor.execute(query, (user_id,))
    connection.commit()
```

### DELETE (Remove)

#### Delete Document

```python
def delete_document(doc_id):
    """Remove document record"""
    query = "DELETE FROM documents WHERE id = ?"
    cursor.execute(query, (doc_id,))
    connection.commit()
```

**Cascade behavior:**
- If documents was uploaded by user, and user is deleted → document deleted
- NOT applied the other way (deleting document doesn't delete user)

---

## 🎨 Design Patterns

### Pattern 1: Soft Deletes (Recommended)

**Instead of deleting, just deactivate:**

```python
# DON'T do this:
DELETE FROM users WHERE id = ?

# DO this:
UPDATE users SET is_active = 0 WHERE id = ?
```

**Benefits:**
```
✅ Preserves query_logs history (still see "who asked what")
✅ Can restore user later if needed
✅ Maintains referential integrity
✅ Better for auditing
```

### Pattern 2: UUID for Primary Keys

**Why not auto-increment (1, 2, 3...)?**

```sql
-- DON'T: Auto-increment IDs
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Bad: sequential, guessable
    username TEXT
);

-- DO: UUID
import uuid
user_id = str(uuid.uuid4())  # "550e8400-e29b-41d4-a716-446655440000"
```

**Benefits of UUID:**
- ✅ Unique across systems (can merge databases)
- ✅ Non-sequential (can't guess next ID)
- ✅ Distributable (no central counter needed)
- ✅ Industry standard

### Pattern 3: ISO Timestamps

**Don't store dates as strings, use ISO 8601:**

```python
# DON'T: Non-standard format
created_at = "03/15/2024"       # Ambiguous: US or European?

# DO: ISO 8601
from datetime import datetime
created_at = datetime.now().isoformat()  # "2024-03-15T10:30:45.123456"
```

**Benefits:**
- ✅ Unambiguous worldwide
- ✅ Sortable as string (earliest first)
- ✅ Includes time + timezone info
- ✅ Standard for databases & APIs

### Pattern 4: Parameterized Queries

**Prevent SQL injection:**

```python
# DON'T: String concatenation (VULNERABLE!)
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)  # If username = "admin' --", this breaks!

# DO: Parameterized queries
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))  # Safe!
```

**Why?**
- ✅ Prevents SQL injection attacks
- ✅ Automatic escaping
- ✅ Best practice everywhere

### Pattern 5: Transactions

**Ensure data consistency:**

```python
# DON'T: Multiple independent operations
cursor.execute("INSERT INTO documents ...")
chunk_count = count_chunks()
cursor.execute("UPDATE documents SET chunk_count = ?", (chunk_count,))
# If it crashes between INSERT and UPDATE → inconsistent state!

# DO: Wrap in transaction
try:
    cursor.execute("INSERT INTO documents ...")
    chunk_count = count_chunks()
    cursor.execute("UPDATE documents SET chunk_count = ?", (chunk_count,))
    connection.commit()  # Only commit if ALL succeeded
except Exception as e:
    connection.rollback()  # Undo everything
    raise
```

---

## 📝 Query Examples

### Analytics: Top Users

```python
def get_top_users(limit=10):
    """Who asked the most questions?"""
    query = """
    SELECT u.username, COUNT(ql.id) as query_count, AVG(ql.response_time_ms) as avg_response_time
    FROM users u
    LEFT JOIN query_logs ql ON u.id = ql.user_id
    GROUP BY u.id
    ORDER BY query_count DESC
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    return cursor.fetchall()
```

**Output:**
```
username           | query_count | avg_response_time
prof_smith         | 245         | 512 ms
student_alice      | 189         | 487 ms
prof_johnson       | 156         | 534 ms
```

### Analytics: Popular Documents

```python
def get_popular_documents():
    """Which documents are used in Q&A?"""
    query = """
    SELECT d.filename, COUNT(ql.id) as times_used, AVG(CAST(INSTR(ql.sources, d.filename) > 0 AS INTEGER)) as relevance_avg
    FROM documents d
    LEFT JOIN query_logs ql ON ql.sources LIKE '%' || d.filename || '%'
    GROUP BY d.id
    ORDER BY times_used DESC
    """
    cursor.execute(query)
    return cursor.fetchall()
```

### Maintenance: Find Old Processed Documents

```python
def get_old_documents(days=90):
    """Documents not used in 90 days"""
    query = """
    SELECT d.id, d.filename, d.uploaded_at
    FROM documents d
    WHERE d.status = 'processed'
    AND (
        SELECT COUNT(*) 
        FROM query_logs ql 
        WHERE ql.sources LIKE '%' || d.filename || '%'
        AND ql.created_at > datetime('now', '-90 days')
    ) = 0
    """
    cursor.execute(query)
    return cursor.fetchall()
```

### Security: Find Inactive Users

```python
def get_inactive_users(days=30):
    """Users who haven't logged in 30 days"""
    query = """
    SELECT id, username, full_name, last_login
    FROM users
    WHERE last_login < datetime('now', '-30 days')
    AND is_active = 1
    """
    cursor.execute(query)
    return cursor.fetchall()
```

---

## 📊 Key Statistics to Track

**In your monitoring/admin dashboard:**

```python
# User Stats
SELECT COUNT(*) as total_users FROM users WHERE is_active = 1;
SELECT COUNT(*) FROM users WHERE role = 'faculty';
SELECT COUNT(*) FROM users WHERE role = 'student';

# Document Stats
SELECT COUNT(*) as total_documents FROM documents WHERE status = 'processed';
SELECT SUM(chunk_count) as total_chunks FROM documents WHERE status = 'processed';
SELECT SUM(file_size) as total_storage FROM documents WHERE status = 'processed';

# Query Stats
SELECT COUNT(*) as total_queries FROM query_logs;
SELECT AVG(response_time_ms) as avg_response_time FROM query_logs;
SELECT MAX(response_time_ms) as max_response_time FROM query_logs;

# Error Stats
SELECT COUNT(*) as failed_documents FROM documents WHERE status = 'failed';
```

---

## 🔐 Security Best Practices

### ✅ DO

- ✅ Always hash passwords (SHA-256 minimum, bcrypt better)
- ✅ Use parameterized queries (prevent SQL injection)
- ✅ Validate input on INSERT/UPDATE
- ✅ Soft-delete sensitive data (rather than hard-delete)
- ✅ Log access to sensitive data
- ✅ Backup database regularly

### ❌ DON'T

- ❌ Store plaintext passwords
- ❌ Use string concatenation for queries
- ❌ Skip foreign key constraints
- ❌ Hard-delete user data
- ❌ Return raw database errors to users
- ❌ Expose IDs in URLs (e.g., `/user/1`, `/user/2`)

---

## 📌 Summary

| Concept | Key Point |
|---------|-----------|
| **users** | Authentication + role-based access |
| **documents** | Track uploads, chunks, processing status |
| **query_logs** | Audit trail + analytics data |
| **ForeignKeys** | Maintain data consistency |
| **UUID PKs** | Non-sequential, globally unique IDs |
| **Parameterized queries** | Prevent SQL injection |
| **Transactions** | Ensure consistency across operations |

✅ You now understand the complete database structure!

Next: [ARCHITECTURE.md](ARCHITECTURE.md) or [DIAGRAMS.md](DIAGRAMS.md)

