# IMS AstroBot — Workspace Copilot Instructions

**Project:** IMS AstroBot v2.0 — RAG-powered institutional AI assistant  
**Architecture:** Python (Streamlit UI + FastAPI REST API) + Spring Boot backend + ChromaDB + Ollama/Cloud LLMs  
**Date Updated:** March 2026

---

## 🎯 Quick Overview

IMS AstroBot is a **Retrieval-Augmented Generation (RAG) system** designed for institutional document Q&A:

1. **Upload documents** (PDF, DOCX, Excel, PowerPoint, HTML) → parsed & chunked
2. **Vector embedding** via `sentence-transformers` → stored in ChromaDB
3. **User asks question** → semantic search retrieves top-5 relevant chunks
4. **LLM generates answer** → routed through Ollama (local), Grok, or Gemini (cloud)
5. **Citations included** → source documents referenced in response

**Three frontends:**
- **Streamlit UI** (`app.py`) — For direct user interaction
- **FastAPI REST API** (`api_server.py`) — For Spring Boot / HTTP clients
- **Spring Boot** (`springboot-backend/`) — Proxy layer + future JPA persistence

---

## 📁 Project Structure & Key Files

```
.
├── app.py                          # Streamlit entry point (login, routing, role-based UI)
├── api_server.py                   # FastAPI REST server (for Spring Boot integration)
├── config.py                       # Centralized config (reads .env)
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (sensitive — NOT in git)
│
├── auth/
│   ├── auth.py                     # Session-based auth (Streamlit session_state)
│
├── database/
│   └── db.py                       # SQLite schema + CRUD: users, documents, query_logs
│
├── ingestion/                      # Document → embeddings pipeline
│   ├── parser.py                   # Multi-format parsers (PDF, DOCX, Excel, PPTX, HTML)
│   ├── chunker.py                  # Hybrid chunking (structure-aware + fixed-size overlap)
│   └── embedder.py                 # Embedding generation + ChromaDB storage
│
├── rag/
│   ├── retriever.py                # Semantic search & context formatting
│   ├── generator.py                # LLM response generation + fallback logic
│   └── providers/
│       ├── base.py                 # Abstract LLMProvider interface
│       ├── ollama_provider.py      # Local LLM via Ollama REST API
│       ├── groq_provider.py        # Grok API (xAI)
│       ├── gemini_provider.py      # Google Gemini API
│       └── manager.py              # ProviderManager (singleton) → fallback chain logic
│
├── views/
│   ├── chat.py                     # Chat page (semantic search + RAG generation)
│   └── admin.py                    # Admin dashboard (docs, users, AI settings, health)
│
├── data/
│   ├── uploads/                    # User-uploaded documents (transient)
│   ├── chroma_db/                  # ChromaDB persistent vector storage
│   └── astrobot.db                 # SQLite database (users, docs, query logs)
│
├── models/                         # Place GGUF model files here (e.g., phi-3.gguf)
│
├── springboot-backend/             # Spring Boot microservice (proxy to Python API)
│   ├── pom.xml                     # Maven config
│   ├── src/main/java/com/astrobot/
│   │   ├── AstroBotApplication.java
│   │   ├── controller/             # REST endpoints (ChatController, AuthController, etc.)
│   │   ├── service/
│   │   │   └── PythonApiService.java  # HTTP client that calls Python FastAPI
│   │   ├── dto/                    # Request/response POJOs
│   │   └── config/
│   │       └── WebConfig.java      # WebClient bean configuration
│   └── src/main/resources/
│       └── application.properties   # Spring Boot config
│
├── react-frontend/                 # Modern React UI (Vite)
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/             # Reusable UI components
│   │   ├── pages/                  # Page layouts (ChatPage, LoginPage, admin/)
│   │   ├── services/
│   │   │   └── api.js              # Axios client for FastAPI/Spring Boot
│   │   └── context/
│   │       └── AuthContext.jsx     # Authentication state management
│   └── index.html
│
└── [startup scripts]
    ├── start-all-servers.ps1       # PowerShell: Start all 3 servers
    ├── start-all-servers.bat       # Windows batch: Start all 3 servers
    ├── stop-all-servers.ps1        # PowerShell: Stop all servers
    └── stop-all-servers.bat        # Batch: Stop all servers
```

---

## 🔄 RAG Pipeline (Data Flow)

### Phase 1: Document Ingestion
```
User uploads PDF/DOCX/etc.
    ↓
parser.py (PyPDF2, python-docx, openpyxl, etc.)
    ↓
Extracted text
    ↓
chunker.py (hybrid strategy)
  ├─ _split_by_headings() → sections [heading, content]
  ├─ _fixed_size_chunks() → 500-char chunks, 50-char overlap
  └─ Returns [{text, metadata}]
    ↓
embedder.py
  ├─ generate_embeddings() via sentence-transformers
  ├─ Store in ChromaDB with metadata
  └─ Update database record (chunk_count, status='processed')
```

### Phase 2: Query → Answer
```
User asks question
    ↓
retriever.py → retrieve_context()
  ├─ Embed question with same model as documents
  ├─ Cosine similarity search in ChromaDB
  ├─ Retrieve top-5 chunks + metadata
  └─ format_context_for_llm() → context string
    ↓
generator.py → generate_response()
  ├─ Build system prompt + user message (context + question)
  ├─ ProviderManager routes through provider chain:
  │   ├─ Primary provider (e.g., ollama)
  │   ├─ Fallback provider (e.g., grok)
  │   └─ Last resort: Ollama or context-only
  └─ Return response
    ↓
View layer (chat.py)
  ├─ Display response
  ├─ Show get_source_citations()
  └─ Log query + response in database
```

---

## ⚙️ Core Components Explained

### 1. Configuration (`config.py`)

**Load order:** `.env` → environment variables → hardcoded defaults

| Variable | Purpose | Default |
|----------|---------|---------|
| `LLM_MODE` | `local_only`, `cloud_only`, `hybrid` | `local_only` |
| `LLM_PRIMARY_PROVIDER` | `ollama`, `groq`, `gemini` | `ollama` |
| `LLM_FALLBACK_PROVIDER` | Secondary provider or `none` | `none` |
| `OLLAMA_BASE_URL` | Ollama REST API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name in Ollama | `qwen3:0.6b` |
| `EMBEDDING_MODEL` | Sentence-transformers model | `all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | Characters per chunk | `500` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `MODEL_TEMPERATURE` | LLM sampling (0=deterministic, 1=creative) | `0.3` |
| `MODEL_MAX_TOKENS` | Max response length | `512` |

### 2. Database (`database/db.py`)

**SQLite Schema:**

```sql
users
  ├─ id (TEXT PRIMARY KEY, UUID)
  ├─ username (UNIQUE)
  ├─ password_hash (SHA-256)
  ├─ role (admin | faculty | student)
  ├─ full_name
  ├─ created_at
  └─ is_active (0 or 1)

documents
  ├─ id (TEXT PRIMARY KEY, UUID)
  ├─ filename (original_name)
  ├─ file_type (.pdf, .docx, etc.)
  ├─ file_size
  ├─ chunk_count
  ├─ uploaded_by (FK → users.id)
  ├─ uploaded_at
  └─ status (processed | failed)

query_logs
  ├─ id (TEXT PRIMARY KEY, UUID)
  ├─ user_id (FK → users.id)
  ├─ username
  ├─ query_text
  ├─ response_text
  ├─ sources (JSON string)
  ├─ response_time_ms
  └─ created_at
```

**Key functions:**
- `init_db()` — Creates tables + default admin (user: `admin`, pass: `admin123`)
- `authenticate_user(username, password)` — Returns user dict or None
- `create_user(...)` — Insert new user
- `add_document(...)` — Record uploaded document
- `log_query(...)` — Record Q&A interaction

### 3. Chunking Strategy (`ingestion/chunker.py`)

**Hybrid approach:**

1. **Structural split** (`_split_by_headings`)
   - Detects markdown headings (`##`, `###`), page markers (`[Page 5]`), sheet names
   - Preserves document structure in metadata
   
2. **Fixed-size chunks** (`_fixed_size_chunks`)
   - 500 characters per chunk
   - 50-character overlap between chunks
   - Attempts to break at sentence boundaries (`.`, `!`, `?`, `\n\n`)

**Output per chunk:**
```python
{
  "text": "Extracted chunk text...",
  "metadata": {
    "source": "document_name.pdf",
    "heading": "Chapter 3 > Section 2",
    "chunk_index": 5
  }
}
```

### 4. Embedding & Vector Storage (`ingestion/embedder.py`)

- **Model:** `all-MiniLM-L6-v2` (384-dim embeddings, fast + accurate)
- **Storage:** ChromaDB (persistent vector DB, SQLite-backed)
- **Process:**
  - Text → embedding vector via `sentence_transformers.SentenceTransformer`
  - Store in ChromaDB collection per document
  - Metadata stored alongside (source, heading, doc_id)

### 5. Semantic Search (`rag/retriever.py`)

- **Search method:** Cosine similarity (ChromaDB handles this)
- **Distance → Similarity:** `similarity = 1 - (distance / 2)` (ChromaDB returns normalized distance)
- **Top-K:** Default 5 results
- **Context formatting:**
  - Prepends source info: `[Source: filename > Heading | Relevance: 85%]`
  - Join all chunks with `\n\n` separator

### 6. LLM Provider Chain (`rag/providers/manager.py`)

**ProviderManager is a singleton** that manages fallback logic.

**Modes:**
- **`local_only`** → Ollama (REST API to local server)
- **`cloud_only`** → PRIMARY cloud provider → FALLBACK cloud provider
- **`hybrid`** → PRIMARY provider → FALLBACK provider → Ollama as last resort

**Generation flow:**
```python
try PRIMARY provider
  if success: return response
  else: try FALLBACK provider
    if success: return response
    else (in hybrid): try Ollama
      if success: return response
      else: return fallback_response() [context-only]
```

**Provider interfaces** (`rag/providers/`):
- `base.py` — Abstract `LLMProvider` (generate, is_available, get_status)
- `ollama_provider.py` — REST API to local Ollama service
- `groq_provider.py` — Grok API (xAI cloud)
- `gemini_provider.py` — Google Gemini API

### 7. Authentication (`auth/auth.py`)

- **Type:** Session-based (Streamlit `st.session_state`)
- **Flow:**
  1. User enters credentials on login page
  2. `authenticate_user(username, password)` queries database
  3. Compares SHA-256 hash
  4. Sets `st.session_state` (user_id, username, role)
- **Roles:** `admin`, `faculty`, `student` (role-based UI routing)

### 8. Streamlit UI (`app.py`, `views/`)

**Page structure:**
- **Login page** → Unauthenticated users
- **Chat page** (`views/chat.py`) → Faculty/students ask questions
- **Admin dashboard** (`views/admin.py`) → Admins only
  - Document management (upload, delete, view stats)
  - User management (create, enable/disable, delete)
  - AI Settings (swap models, tune parameters, edit system prompt)
  - System Health (SQLite, ChromaDB, LLM providers, embeddings, uploads)

### 9. FastAPI REST API (`api_server.py`)

**Endpoints exposed for Spring Boot / HTTP clients:**

```
POST /api/login
  Request: {username, password}
  Response: {token, user: {id, username, role}}

POST /api/register
  Request: {username, password, role, full_name}

POST /api/chat
  Request: {query, user_id, username}
  Response: {response, sources: [{text, source, score}], citations, response_time_ms}

POST /api/documents/upload
  Request: multipart file upload
  Response: {id, filename, chunk_count, status}

GET /api/documents
  Response: {total, items: [{id, filename, chunk_count, uploaded_at, status}]}

POST /api/admin/users
  Request: {username, password, role, full_name}
  Response: {id, created: true}

GET /api/admin/analytics
  Response: {total_queries, daily_trends, top_users, avg_response_time}

GET /api/health
  Response: {sqlite, chromadb, llm_mode, llm_ollama, embeddings, uploads}
```

### 10. Spring Boot Backend (`springboot-backend/`)

**Role:** Proxy layer between React frontend and Python FastAPI

- **Key service:** `PythonApiService.java`
  - Uses `WebClient` for async HTTP to Python API
  - Caches responses where applicable
- **Controllers:** `ChatController`, `AuthController`, `DocumentController`, etc.
- **DTOs:** Request/response POJOs (mimic Python FastAPI models)
- **Configuration:** `WebConfig.java` (WebClient bean, CORS, error handling)

**Integration flow:**
```
React Frontend → Spring Boot ChatController → PythonApiService → FastAPI → RAG Pipeline
                   ↓                                                    ↓
                   Response (JSON)                                  Response (JSON)
```

---

## 🚀 Building & Running

### Prerequisites
- Python 3.9+
- Java 17+ (for Spring Boot)
- Node.js 18+ (for React frontend)
- Ollama running (if using local LLM mode)

### Python setup

1. **Create virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Create `.env` file:**
   ```env
   LLM_MODE=local_only
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=qwen3:0.6b
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   CHUNK_SIZE=500
   CHUNK_OVERLAP=50
   MODEL_TEMPERATURE=0.3
   MODEL_MAX_TOKENS=512
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin123
   UPLOAD_DIR=./data/uploads
   CHROMA_PERSIST_DIR=./data/chroma_db
   SQLITE_DB_PATH=./data/astrobot.db
   ```

### Running servers

**Option 1: PowerShell script (all 3 servers)**
```powershell
.\start-all-servers.ps1
```

**Option 2: Individual startup**

```powershell
# Terminal 1: Streamlit UI
streamlit run app.py

# Terminal 2: FastAPI REST server
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Spring Boot (from springboot-backend/)
./mvnw spring-boot:run
```

**Access points:**
- Streamlit UI: `http://localhost:8501`
- FastAPI Docs: `http://localhost:8000/docs`
- Spring Boot: `http://localhost:8080`
- React Frontend: `http://localhost:5173` (if running `npm run dev`)

---

## 🛠️ Development Conventions

### Python Code Style
- **Format:** Follow PEP 8 (black, flake8)
- **Type hints:** Use type annotations for function signatures
- **Docstrings:** Module + function docstrings with purpose, args, returns
- **Imports:** Group in order: stdlib → third-party → local
- **Error handling:** Explicit try/except with custom exceptions where appropriate

### File & Module Organization
- **One responsibility per module** (e.g., `chunker.py` = chunking, not embedding)
- **Config in `config.py`** — Never hardcode paths or magic numbers
- **Helper functions prefixed with `_`** (private convention)
- **Lazy imports in functions** — Avoid circular imports (e.g., in `app.py`, delay RAG imports)

### Database
- **Use parameterized queries** (`?` placeholders) to prevent SQL injection
- **Always close connections** — Use try/finally or context managers
- **UUIDs for PKs** — `str(uuid.uuid4())`
- **Timestamps in ISO format** — `datetime.now().isoformat()`

### RAG Pipeline
- **Retriever must return predictable structure** — Always include `{text, source, heading, score, doc_id}`
- **Context formatting is centralized** — `retriever.py::format_context_for_llm()`
- **Provider chain is routed by ProviderManager** — Never hardcode provider logic in views
- **All embeddings use same model** — Configured globally in `config.py`

### Streamlit UI
- **Check auth early** — `@require_auth()` decorator or guard at page start
- **Use `st.session_state` for all state** — Not local variables
- **Sidebar for navigation** — Keep main area focused on primary task
- **Health checks lightweight** — Admin-only, non-blocking status display

### Spring Boot
- **Use WebClient for async HTTP** — Not RestTemplate
- **Centralize Python API URL** — In `application.properties`
- **Map Python DTOs to Java POJOs** — Avoid mixing layers
- **Handle fallback gracefully** — If Python API unavailable, return 503 or cached response

### React Frontend
- **Component-based architecture** — One component per file
- **API calls via `services/api.js`** — Centralized axios client
- **Authentication in `AuthContext`** — Global state for user + token
- **Responsive design** — Tailwind CSS or similar utility-first framework

### Common Pitfalls
- ❌ **Don't embed credentials in code** — Use `.env` + `config.py`
- ❌ **Don't load all documents into memory** — Use chunking + ChromaDB
- ❌ **Don't hardcode provider names** — Use `config.py` + `ProviderManager`
- ❌ **Don't skip error handling in RAG pipeline** — Fallback is critical
- ❌ **Don't assume Ollama is always running** — Handle connection errors gracefully

---

## 📊 Program Execution Rate & Performance

### Typical Query Latency (end-to-end)

| Component | Operation | Time (ms) |
|-----------|-----------|-----------|
| **Embedding** | Question embedding (all-MiniLM-L6-v2) | 10–20 |
| **Retrieval** | ChromaDB search (top-5) | 5–15 |
| **Context format** | Format chunks + citations | 2–5 |
| **LLM generation** | Ollama (qwen3:0.6b, 512 tokens) | 300–800 |
| **Cloud API** | Grok/Gemini (with network latency) | 500–2000 |
| **Total (local)** | Ollama path | **~350–860 ms** |
| **Total (cloud)** | Grok/Gemini path | **~550–2050 ms** |

### Throughput
- **Single-threaded:** ~1–2 queries/second (local), ~0.5–1 query/second (cloud)
- **Concurrent (FastAPI):** ~5–10 concurrent requests (depends on LLM throttling)
- **Database:** SQLite handles ~100+ writes/second; WAL mode enables concurrent reads

### Memory Usage
- **Streamlit + RAG pipeline:** ~800 MB base
- **Embedding model loaded:** +400–500 MB (lazy-loaded on first use)
- **ChromaDB in-memory cache:** +200–300 MB (grows with document count)
- **LLM (if local GGUF):** +2–4 GB (depends on model size; Phi-3 ≈ 2 GB)
- **Spring Boot:** ~300–500 MB base (no LLM locally)

### Scalability Considerations
- **Single-threaded Streamlit:** One user session at a time
- **FastAPI:** Handle 10–50 concurrent users comfortably
- **ChromaDB:** Up to 1M+ embeddings feasible; performance degrades beyond 10M
- **SQLite:** ~1M records handled well; consider PostgreSQL for >10M
- **Cloud LLMs:** Rate-limited by API quota (Grok: 120 req/min, Gemini: varies)

---

## 🔐 Security Considerations

1. **Authentication:** SHA-256 password hashing (consider bcrypt for production)
2. **API access:** FastAPI CORS allows `["*"]` — restrict to specific origins in production
3. **Sensitive data:** API keys (Grok, Gemini) stored in `.env` + environment variables
4. **Database:** SQLite with WAL mode; use parameterized queries
5. **Document uploads:** Validate file types, scan for malware, limit file size
6. **Rate limiting:** Not implemented; consider FastAPI RateLimiter or reverse proxy

---

## 🧪 Testing & Debugging

### Quick checks

```python
# Test embedding model
from ingestion.embedder import generate_embeddings
vec = generate_embeddings(["Hello world"])
print(len(vec[0]))  # Should be 384 (for all-MiniLM-L6-v2)

# Test ChromaDB connection
from ingestion.embedder import get_collection
col = get_collection()
print(col.count())  # Number of vectors stored

# Test Ollama availability
from rag.providers.ollama_provider import OllamaProvider
llm = OllamaProvider("http://localhost:11434", "qwen3:0.6b")
print(llm.is_available())  # True or False

# Test provider manager fallback
from rag.providers.manager import get_manager
mgr = get_manager()
statuses = mgr.get_all_statuses()
print(statuses)  # Provider health + LLM mode
```

### Logging

- Configure Python logging for debugging (recommended: add to `config.py`)
- Streamlit logs to console; FastAPI logs to stdout
- Query logs stored in SQLite for analytics

---

## 📚 Key Files Quick Reference

| File | Purpose | Key Functions |
|------|---------|---|
| `app.py` | Streamlit entry point | `render_health_sidebar()`, page routing |
| `config.py` | Central config | All env variables, paths, defaults |
| `database/db.py` | SQLite CRUD | `init_db()`, `authenticate_user()`, `log_query()` |
| `ingestion/chunker.py` | Doc chunking | `chunk_document()`, `_split_by_headings()` |
| `ingestion/embedder.py` | Embedding + storage | `generate_embeddings()`, `add_document_to_chromadb()` |
| `rag/retriever.py` | Semantic search | `retrieve_context()`, `format_context_for_llm()` |
| `rag/generator.py` | LLM generation | `generate_response()`, `get_llm_status()` |
| `rag/providers/manager.py` | Provider routing | `get_manager()`, `ProviderManager.generate()` |
| `api_server.py` | FastAPI REST API | All `/api/*` endpoints |
| `springboot-backend/src/main/java/com/astrobot/service/PythonApiService.java` | Java→Python bridge | Async HTTP to FastAPI |

---

## 🤖 For AI Agent Use

When working with this codebase:

1. **Always check `.env` configuration first** — Understand LLM mode, provider settings
2. **Trace data flow:** Document → Parser → Chunker → Embedder → ChromaDB → Retriever → LLM
3. **Test provider chain:** Use `get_manager().get_all_statuses()` to verify fallback availability
4. **Error handling is critical:** Provide fallbacks (context-only, cached response, user message)
5. **Concurrency:** FastAPI can handle multiple requests; Streamlit single-threaded
6. **Ask about `.env` and running services** before assuming config

---

## 📞 Support & Debugging

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "No LLM provider available" | Ollama not running OR credentials invalid | Start Ollama: `ollama serve` |
| ChromaDB errors | `chroma_db/` missing or corrupted | Delete `data/chroma_db/`, re-upload docs |
| Embedding model timeout | First-time download or network issue | Check internet, can take 1–2 min on first run |
| Spring Boot can't reach Python API | FastAPI not running on :8000 | `uvicorn api_server:app --port 8000` |
| SQLite "database is locked" | Multiple writers (rare) | Restart servers (WAL mode prevents most contention) |

### Enable debug logging

In `config.py` or `.env`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📝 Version Info

- **Project version:** 2.0.0
- **Python:** 3.9+
- **Spring Boot:** 3.2.4
- **Node.js:** 18+
- **Key packages:**
  - `streamlit>=1.30.0`
  - `fastapi>=0.110.0`
  - `sentence-transformers>=2.2.0`
  - `chromadb>=0.4.22`
  - `requests>=2.31.0`

---

**Last Updated:** March 2026  
**Maintainer Notes:** This codebase is designed for institutional AI assistance with RAG. Always prioritize document accuracy, source attribution, and fallback graceful degradation.
