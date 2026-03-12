# IMS AstroBot — Developer Quick Reference

**TL;DR version of workspace instructions. Print this or bookmark it.**

---

## 🚀 Quick Start (< 5 minutes)

### Setup
```powershell
# 1. Activate venv
.\venv\Scripts\Activate.ps1

# 2. Install deps
pip install -r requirements.txt

# 3. Create .env
COPY config.example.md .env  # Then edit with your settings

# 4. Start servers
.\start-all-servers.ps1
```

### Access Points
- **Streamlit:** http://localhost:8501
- **FastAPI docs:** http://localhost:8000/docs
- **Spring Boot:** http://localhost:8080

---

## 🔑 Key Commands

### Working with SQLite
```python
# Initialize DB + default admin (admin/admin123)
from database.db import init_db
init_db()

# Authenticate user
from database.db import authenticate_user
user = authenticate_user("admin", "admin123")
# Returns: {id, username, role, full_name, created_at, is_active}

# Create new user
from database.db import create_user
create_user("bob", "pass123", "faculty", "Bob Smith")

# Log query
from database.db import log_query
log_query(user_id, query_text, response_text, sources_json, time_ms)
```

### Working with Embeddings
```python
# Generate embeddings
from ingestion.embedder import generate_embeddings
embeddings = generate_embeddings(["Hello world", "Another sentence"])
# Returns: [[384 floats], [384 floats]]

# Get ChromaDB collection
from ingestion.embedder import get_collection
collection = get_collection()
print(collection.count())  # Total vectors stored

# Add document to ChromaDB
from ingestion.embedder import add_document_to_chromadb
add_document_to_chromadb("data/uploads/policy.pdf", "policy.pdf")
```

### Working with RAG
```python
# Retrieve context
from rag.retriever import retrieve_context
chunks = retrieve_context("What is leave policy?", top_k=5)
# Returns: [{text, source, heading, score, doc_id}, ...]

# Format context
from rag.retriever import format_context_for_llm
context = format_context_for_llm(chunks)
# Returns: formatted string for LLM

# Generate response
from rag.generator import generate_response
response = generate_response("What is leave policy?", context)
# Returns: LLM-generated answer string
```

### LLM Provider Status
```python
# Check provider status
from rag.providers.manager import get_manager
mgr = get_manager()
statuses = mgr.get_all_statuses()
# Returns: {"ollama": {status, message}, "grok": {...}, ...}

# Check if any provider available
if mgr.is_any_available():
    print("LLM ready!")
else:
    print("All providers down!")

# Reset manager (after config changes)
from rag.providers.manager import reset_manager
reset_manager()
```

---

## 📋 Configuration

### .env File
```env
# LLM Mode
LLM_MODE=local_only              # local_only, cloud_only, hybrid
LLM_PRIMARY_PROVIDER=ollama      # ollama, groq, gemini
LLM_FALLBACK_PROVIDER=none       # none, groq, gemini

# Local LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:0.6b

# Cloud LLMs
GROK_API_KEY=xai-xxx...
GROK_MODEL=grok-3
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash

# LLM Parameters
MODEL_TEMPERATURE=0.3            # 0 = deterministic, 1 = creative
MODEL_MAX_TOKENS=512

# Embedding
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

## ⚡ Common Workflows

### Upload Document (Admin)
```python
from ingestion.parser import parse_pdf  # or others
from ingestion.chunker import chunk_document
from ingestion.embedder import add_document_to_chromadb
from database.db import add_document
import uuid

# 1. Parse
text = parse_pdf("policy.pdf")

# 2. Chunk
chunks = chunk_document(text, "policy.pdf")

# 3. Embed
doc_id = str(uuid.uuid4())
add_document_to_chromadb(doc_id, chunks)

# 4. Log
add_document(
    id=doc_id,
    filename="policy.pdf",
    chunk_count=len(chunks),
    uploaded_by=admin_user_id
)
```

### User Asks Question (Faculty/Student)
```python
from rag.retriever import retrieve_context, format_context_for_llm
from rag.generator import generate_response

query = "What is annual leave?"

# 1. Retrieve
chunks = retrieve_context(query, top_k=5)

# 2. Format
context = format_context_for_llm(chunks)

# 3. Generate
response = generate_response(query, context)

# 4. Show to user
print(response)
```

### Switch LLM Provider
```python
# In .env:
# LLM_MODE=local_only → LLM_MODE=hybrid
# LLM_PRIMARY_PROVIDER=ollama → LLM_PRIMARY_PROVIDER=groq

# After changing .env:
from rag.providers.manager import reset_manager
reset_manager()

# Now provider chain uses new settings
```

---

## 🐛 Debugging

### Test if Embeddings Work
```python
from ingestion.embedder import generate_embeddings
v = generate_embeddings(["test"])
print(len(v[0]))  # Should print: 384
```

### Test ChromaDB Connection
```python
from ingestion.embedder import get_collection
c = get_collection()
print(f"Total vectors: {c.count()}")
```

### Test Ollama
```python
from rag.providers.ollama_provider import OllamaProvider
llm = OllamaProvider("http://localhost:11434", "qwen3:0.6b")
print(llm.is_available())  # True or False
print(llm.get_status())    # {status, message}
```

### Test Grok API
```python
from rag.providers.groq_provider import GroqProvider
import os
llm = GroqProvider(os.getenv("GROK_API_KEY"), "grok-3")
print(llm.is_available())  # True or False
```

### View Database
```python
from database.db import get_connection

conn = get_connection()

# Users
users = conn.execute("SELECT * FROM users").fetchall()
for u in users:
    print(u)

# Documents
docs = conn.execute("SELECT * FROM documents").fetchall()
for d in docs:
    print(d)

# Recent queries
queries = conn.execute(
    "SELECT * FROM query_logs ORDER BY created_at DESC LIMIT 10"
).fetchall()
for q in queries:
    print(q)

conn.close()
```

---

## 📊 Performance Targets

| Operation | Target | Actual (Good) | Actual (Bad) |
|-----------|--------|---------------|-------------|
| Question embed | <20ms | 15ms | 50ms+ |
| ChromaDB search | <15ms | 10ms | 100ms+ |
| Ollama response | 300–800ms | 500ms | 2000ms+ |
| Grok response | 500–1500ms | 1000ms | 3000ms+ |
| Total query | 350–2000ms | 850ms | 5000ms+ |
| Document upload | 5–30s | 15s | 60s+ |

---

## 🛠️ Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "No LLM available" | Ollama not running | `ollama serve` in terminal |
| Embedding timeout | First time download | Wait 1–2 min, check internet |
| ChromaDB error | Corrupted data | Delete `data/chroma_db/`, re-upload docs |
| SQLite locked | Multiple writers | Restart servers |
| Streamlit crash | Missing imports | Check `.github/copilot-instructions.md` |
| Spring Boot 503 | FastAPI down | Check `uvicorn api_server:app` running |

---

## 📚 Key Files Map

```
🎯 Starting point:        config.py (all settings here)
🔍 Search:               rag/retriever.py (get chunks)
🤖 Generation:           rag/generator.py (call LLM)
💾 Database:             database/db.py (CRUD)
📄 Ingestion:            ingestion/ (parse, chunk, embed)
🌐 API:                  api_server.py (FastAPI endpoints)
🎨 UI:                   views/ (Streamlit pages)
```

---

## 🔗 API Endpoints

All endpoints return JSON. FastAPI auto-docs: http://localhost:8000/docs

```
POST /api/login
  Body: {username, password}
  Response: {token, user}

POST /api/chat
  Body: {query, user_id, username}
  Response: {response, sources, citations, response_time_ms}

POST /api/documents/upload
  Body: multipart file
  Response: {id, filename, chunk_count, status}

GET /api/documents
  Response: {total, items}

GET /api/health
  Response: {sqlite, chromadb, llm_mode, ...}

POST /api/admin/users
  Body: {username, password, role, full_name}
  Response: {id, created}

GET /api/admin/analytics
  Response: {total_queries, daily_trends, top_users, avg_response_time}
```

---

## 🎯 Development Principles

✅ **DO:**
- Check `config.py` first for all settings
- Use `get_connection()` for DB access
- Call `reset_manager()` after .env changes
- Log errors, not silently fail
- Test with various document types

❌ **DON'T:**
- Hardcode paths (use `config.py`)
- Mix provider logic in views (`ProviderManager` handles it)
- Assume Ollama always running (test `is_available()`)
- Forget parameterized SQL queries (`?` placeholders)
- Load all documents into memory (use ChromaDB)

---

## 📞 When Stuck

1. **Check logs:** `streamlit run app.py 2>&1 | tee debug.log`
2. **Test isolated:** Run individual functions from Python REPL
3. **Read docstrings:** `help(function_name)`
4. **Check `.env`:** All settings there
5. **Review ARCHITECTURE.md:** Detailed explanation of each component

---

**Version:** 2.0.0 | **Updated:** March 2026 | **Questions?** See copilot-instructions.md
