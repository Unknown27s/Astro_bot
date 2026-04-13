# 📋 Quick Reference — Developer Cheat Sheet

**All commands, configurations, and quick lookups on one page.**

---

## 🔑 Configuration

### .env Template
```env
# LLM Mode: local_only, cloud_only, hybrid
LLM_MODE=local_only
LLM_PRIMARY_PROVIDER=ollama
LLM_FALLBACK_PROVIDER=none

# Local LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:0.6b

# Cloud LLMs
GROK_API_KEY=xai-xxx...
GROK_MODEL=grok-3
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash

# LLM Parameters
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=512

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Paths
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIR=./data/chroma_db
SQLITE_DB_PATH=./data/astrobot.db

# Auth
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

## 🚀 Quick Commands

### Database
```python
# Initialize DB + default admin
from database.db import init_db
init_db()

# Authenticate user
from database.db import authenticate_user
user = authenticate_user("admin", "admin123")
print(user)  # {id, username, role, ...}

# Create user
from database.db import create_user
create_user("bob", "pass123", "faculty", "Bob Smith")

# Log query
from database.db import log_query
log_query(user_id, query_text, response_text, sources_json, time_ms)
```

### Embeddings
```python
# Generate embeddings
from ingestion.embedder import generate_embeddings
embeddings = generate_embeddings(["Hello world"])
print(len(embeddings[0]))  # 384

# Get ChromaDB collection
from ingestion.embedder import get_collection
collection = get_collection()
print(collection.count())  # Total vectors
```

### RAG Pipeline
```python
# Retrieve context
from rag.retriever import retrieve_context
chunks = retrieve_context("What is leave policy?", top_k=5)

# Format context
from rag.retriever import format_context_for_llm
context = format_context_for_llm(chunks)

# Generate response
from rag.generator import generate_response
response = generate_response("What is leave policy?", context)
```

### LLM Providers
```python
# Get manager
from rag.providers.manager import get_manager
mgr = get_manager()

# Check all statuses
statuses = mgr.get_all_statuses()
print(statuses)

# Check if any available
if mgr.is_any_available():
    print("Ready!")

# Reset after config change
from rag.providers.manager import reset_manager
reset_manager()
```

---

## 📊 Performance Targets

| Operation | Target | Good | Bad |
|-----------|--------|------|-----|
| Embed question | <20ms | 15ms | 50ms+ |
| Search | <15ms | 10ms | 100ms+ |
| Ollama response | 300–800ms | 500ms | 2000ms+ |
| Grok response | 500–1500ms | 1000ms | 3000ms+ |
| Total (local) | 350–860ms | 650ms | 5000ms+ |

---

## 🐛 Debugging

### Test Embeddings
```python
from ingestion.embedder import generate_embeddings
v = generate_embeddings(["test"])
assert len(v[0]) == 384, "Embedding size wrong!"
```

### Test ChromaDB
```python
from ingestion.embedder import get_collection
col = get_collection()
print(f"Vectors: {col.count()}")
```

### Test Ollama
```python
from rag.providers.ollama_provider import OllamaProvider
llm = OllamaProvider("http://localhost:11434", "qwen3:0.6b")
print(f"Available: {llm.is_available()}")
print(f"Status: {llm.get_status()}")
```

### Test Auth
```python
from database.db import authenticate_user
user = authenticate_user("admin", "admin123")
assert user is not None, "Auth failed!"
```

### View Database
```python
from database.db import get_connection
conn = get_connection()
users = conn.execute("SELECT * FROM users").fetchall()
for u in users:
    print(u)
conn.close()
```

---

## 📁 Key Files Map

| Task | File |
|------|------|
| Configuration | `config.py` |
| Database CRUD | `database/db.py` |
| User Auth | `auth/auth.py` |
| Document Parsing | `ingestion/parser.py` |
| Text Chunking | `ingestion/chunker.py` |
| Embeddings | `ingestion/embedder.py` |
| Search | `rag/retriever.py` |
| LLM Generation | `rag/generator.py` |
| Provider Management | `rag/providers/manager.py` |
| Streamlit UI | `app.py`, `views/` |
| FastAPI REST | `api_server.py` |

---

## 🔗 API Endpoints

### Document Upload (Admin Only)

**Endpoint:** `POST /api/documents/upload`

**Required Parameters:**
- `file` (FormData, required): PDF/DOCX/TXT file
- `uploaded_by` (FormData, required): Admin user ID

**Response:** 200 OK
```json
{
  "doc_id": "doc-123",
  "filename": "course_handbook.pdf",
  "chunks_indexed": 45,
  "file_size": 1024000,
  "suggested_questions": [
    "Can you summarize key points from course handbook?",
    "What does the section 'Attendance Policy' explain?"
  ]
}
```

**Error Responses:**
- `400`: Missing `uploaded_by` or unsupported file type
- `403`: User is not an admin (❌ Only administrators can upload documents)
- `404`: User not found
- `413`: File too large (max 50MB)
- `422`: PDF is password-protected or parsing failed

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf" \
  -F "uploaded_by=admin-user-id"
```

### Other Endpoints

```
POST /api/login
POST /api/register
POST /api/chat
GET /api/documents
POST /api/admin/users
GET /api/admin/analytics
GET /api/health
```

See FastAPI docs: http://localhost:8000/docs

---

## ✅ Quick Checklist

Before submitting code:
- [ ] Follows PEP 8
- [ ] Has type hints
- [ ] Has docstrings
- [ ] No hardcoded values
- [ ] Parameterized SQL queries
- [ ] Error handling
- [ ] Tested locally
- [ ] Follows conventions

---

**See full documentation in:** [../README.md](../README.md)
