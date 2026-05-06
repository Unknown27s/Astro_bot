# 🎓 Complete AstroBot System Understanding

**Comprehensive overview of every component, how they work, and why they're designed this way.**

*Read time: 30 minutes | Audience: Everyone (developers, architects, AI agents)*

> **Last Updated:** May 2026 — Reflects the full v2.0 codebase including advanced RAG features,
> SQL Agent, Voice-to-Text, Conversation Memory, Rate Limiting, and Observability.

---

## 📋 Table of Contents

1. [System Overview](#-system-overview)
2. [Three-Tier Architecture](#-three-tier-architecture)
3. [RAG Pipeline Explained](#-rag-pipeline-explained)
4. [Advanced Retrieval Features](#-advanced-retrieval-features)
5. [Query Routing System](#-query-routing-system)
6. [Component Deep Dive](#-component-deep-dive)
7. [Data Stores](#-data-stores)
8. [Data Flow](#-data-flow)
9. [Performance Characteristics](#-performance-characteristics)
10. [Key Design Decisions](#-key-design-decisions)
11. [Common Workflows](#-common-workflows)
12. [Configuration Reference](#-configuration-reference)

---

## 🎯 System Overview

### What is AstroBot?

**AstroBot v2.0** is a **Retrieval-Augmented Generation (RAG) system** designed to answer questions about institutional documents through semantic search + AI. It serves students, faculty, and admins of Rajalakshmi Institute of Technology (RIT) / IMS.

**Simple flow:**
```
User uploads 50 PDFs about courses
    ↓
System extracts text → chunks → embeddings → stores in ChromaDB
    ↓
User asks: "Which courses are offered in Spring semester?"
    ↓
Query Router classifies query → picks retrieval strategy
    ↓
Hybrid retrieval (BM25 + dense) finds top chunks
    ↓
LLM generates answer grounded in retrieved context, with citations
    ↓
User sees answer + original document references
```

### Why RAG?

| Problem | RAG Solution |
|---------|--------------|
| LLM doesn't know about your documents | RAG provides documents to LLM |
| LLM has outdated knowledge cutoff | RAG always uses latest documents |
| LLM sometimes "hallucinates" answers | RAG grounds answers in documents |
| Can't trace answer source | RAG provides citations |
| Slow responses for repeated questions | Semantic cache (memory) returns instantly |

---

## 🏗️ Three-Tier Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌──────────────────┬──────────────┬──────────────────┐   │
│  │  Streamlit UI    │  React UI    │  Spring Boot API │   │
│  │  (Python)        │  (Vite/JSX)  │  (Java proxy)   │   │
│  └──────────────────┴──────────────┴──────────────────┘   │
│               (User-facing interfaces)                      │
└───────────────────────┬────────────────────────────────────┘
                        │ HTTP/WebSocket
┌───────────────────────▼────────────────────────────────────┐
│                   APPLICATION LAYER                         │
│  ┌──────────────────┬──────────────┬──────────────────┐   │
│  │  FastAPI REST    │  RAG Pipeline│  Auth & DB       │   │
│  │  api_server.py   │  (rag/*.py)  │  Layer           │   │
│  └──────────────────┴──────────────┴──────────────────┘   │
│  ┌──────────────────┬──────────────┬──────────────────┐   │
│  │  Rate Limiter    │  Middleware  │  Observability   │   │
│  │  (slowapi)       │  (tracking)  │  (SQLite tracer) │   │
│  └──────────────────┴──────────────┴──────────────────┘   │
│               (Business logic, AI, security)                │
└───────────────────────┬────────────────────────────────────┘
                        │ Local Storage / APIs
┌───────────────────────▼────────────────────────────────────┐
│                     DATA LAYER                              │
│  ┌──────────────┬──────────────┬──────────┬────────────┐  │
│  │ SQLite main  │ SQLite inst. │ ChromaDB │  File Store│  │
│  │ astrobot.db  │institute_db  │ (Vectors)│  uploads/  │  │
│  └──────────────┴──────────────┴──────────┴────────────┘  │
│               (Persistent storage)                          │
└────────────────────────────────────────────────────────────┘
```

### Tier 1: Presentation (User Interfaces)

| Interface | Purpose | Users |
|-----------|---------|-------|
| **Streamlit UI** (`app.py`) | Chat + admin dashboard | Faculty, students, admins |
| **React Frontend** (`react-frontend/`) | Modern web UI | External users, students |
| **Spring Boot** (`springboot-backend/`) | Java proxy to FastAPI | Mobile apps, integrations |

### Tier 2: Application (Business Logic)

| Component | File(s) | Purpose |
|-----------|---------|---------|
| **FastAPI REST API** | `api_server.py` | 30+ REST endpoints |
| **Query Router** | `rag/query_router.py` | Classifies query to best strategy |
| **Retriever** | `rag/retriever.py` | Hybrid BM25+dense search |
| **Generator** | `rag/generator.py` | LLM response + streaming |
| **Memory** | `rag/memory.py` | Semantic cache (ChromaDB) |
| **SQL Agent** | `rag/tools/sql_agent.py` | Text-to-SQL for structured data |
| **FAQ Retriever** | `rag/faq_retriever.py` | Q→Q semantic FAQ matching |
| **Voice-to-Text** | `rag/voice_to_text.py` | Whisper audio transcription |
| **Rate Limiter** | `middleware/rate_limiter.py` | Per-user + IP rate limiting |
| **Observability** | `rag/observability/` | SQLite tracing + Langfuse opt. |
| **Auth** | `auth/auth.py` | Streamlit session-based auth |

### Tier 3: Data (Storage)

| Storage | File/Path | Data Stored |
|---------|-----------|-------------|
| **SQLite (main)** | `data/astrobot.db` | Users, documents, query logs, memory, traces, rate limits, announcements, suggestions |
| **SQLite (institute)** | `data/institute_data.db` | Timetables, students, marks |
| **ChromaDB** | `data/chroma_db/` | Document embeddings, FAQ embeddings, conversation memory vectors |
| **File System** | `data/uploads/` | Uploaded PDF/DOCX/XLSX/CSV/PPTX/HTML files |

---

## 🔄 RAG Pipeline Explained

### What is RAG?

**RAG = Retrieval-Augmented Generation**

```
Traditional LLM:  Question → LLM → Answer (may hallucinate)

RAG System:       Question → (1) Search documents → (2) AI answers from docs
                                     ↓
                               Relevant context
```

### The Four Phases

#### Phase 1: Document Ingestion (one-time, on admin upload)

```
Admin uploads: "Syllabus 2024.pdf"
    ↓
[PARSER]  — ingestion/parser.py
    Extract text from PDF (PyPDF2), DOCX (python-docx),
    Excel (openpyxl), PPTX (python-pptx), HTML (BeautifulSoup)
    ↓ Raw text (e.g., 10,000 characters)
[CHUNKER] — ingestion/chunker.py
    Stage 1: Split by headings / page markers / sheet names
    Stage 2: Fixed 500-char chunks with 50-char overlap
    ↓ 20 chunks [{text, metadata: {source, heading, chunk_index}}]
[EMBEDDER] — ingestion/embedder.py
    Convert each chunk → 384-dim vector (all-MiniLM-L6-v2)
    Store in ChromaDB with metadata
    ↓ ChromaDB updated
[DATABASE] — database/db.py
    Mark document as "processed", store chunk_count
```

#### Phase 2: Query → Routing (on user question)

```
User asks: "What courses are offered?"
    ↓
[QUERY ROUTER] — rag/query_router.py
    Keyword signal analysis → assigns one of 8 routes:
      official_site | document | faq | hybrid |
      general_chat | timetable | student_marks | unclear
    ↓ QueryRoute(mode="official_site", confidence=0.75, ...)
```

#### Phase 3: Retrieval (based on route)

```
Route: "document" or "official_site" or "faq"
    ↓
[RETRIEVER] — rag/retriever.py
    Mode 1: Dense-only
      Embed query → ChromaDB cosine similarity search
    Mode 2: Hybrid (default)
      Dense search (top 20 candidates, weight 0.7)
      BM25 keyword search (top 40 candidates, weight 0.3)
      Reciprocal Rank Fusion to merge results
    Optional HyDE:
      LLM generates hypothetical doc snippet → embed → retrieve
    Optional Query Expansion:
      LLM rewrites query N times → retrieve for each → RRF merge
    Optional FlashRank Reranker:
      Neural reranking after retrieval (ms-marco-MiniLM-L-12-v2)
    ↓ Top-5 chunks with scores [{text, source, heading, score}]

Route: "timetable" or "student_marks"
    ↓
[SQL AGENT] — rag/tools/sql_agent.py
    LLM writes SQLite SELECT query from schema
    Execute read-only against institute_data.db
    LLM synthesizes natural language answer
    ↓ Structured answer from database

Route: "general_chat"
    ↓
[DIRECT LLM] — rag/generator.py::generate_response_direct()
    No retrieval — direct LLM call
```

#### Phase 4: Generation (AI creates the answer)

```
[MEMORY CHECK] — rag/memory.py
    Search ChromaDB semantic cache for similar past query
    Hit (similarity > 0.88): Return cached answer instantly (<5ms)
    Miss: Proceed to LLM generation
    ↓
[GENERATOR] — rag/generator.py
    Build prompt: system_prompt + context + user question
    ProviderManager tries: Primary → Fallback → Ollama last resort
    Returns response dict: {response, from_memory, memory_id}
    ↓
[MEMORY STORE] — rag/memory.py
    Store Q+A pair in ChromaDB + SQLite for future cache hits
    ↓
[OBSERVABILITY] — rag/observability/sqlite_tracer.py
    Record trace (request), spans (steps), durations in SQLite
    ↓
Response returned to user with citations
```

---

## 🚀 Advanced Retrieval Features

### Hybrid Retrieval (BM25 + Dense)

The retriever (`rag/retriever.py`) implements a production-grade hybrid search combining two complementary signals:

| Method | Signal type | Strength |
|--------|-------------|---------|
| **Dense** (ChromaDB cosine) | Semantic meaning | Handles synonyms, rephrasing |
| **BM25** (TF-IDF keyword) | Exact term match | Handles acronyms, codes |

**Fusion:** Candidates from both methods are merged using a weighted score:
```
hybrid_score = (0.7 * dense_score) + (0.3 * BM25_score)
```
A minimum score threshold (`MIN_SCORE_THRESHOLD = 0.20`) drops irrelevant chunks before returning results.

### HyDE (Hypothetical Document Embeddings)

When enabled (`HYDE_ENABLED=true`), and only when retrieval scores are below threshold (`HYDE_TRIGGER_SCORE=0.58`):

```
User question: "What is the scholarship procedure?"
    ↓
LLM generates hypothetical answer snippet (~180 tokens):
  "Scholarship applications must be submitted by the 15th of each month..."
    ↓
Embed the hypothetical text → search ChromaDB
    ↓
Blend scores: 0.6 × hypothetical_score + 0.4 × original_score
```

HyDE acts as query amplification for weak or ambiguous queries, generating a "what a good answer would look like" to improve retrieval.

### Query Expansion (Reciprocal Rank Fusion)

When enabled (`QUERY_EXPANSION_ENABLED=true`) and retrieval scores are low:

```
Original: "hostel facilities"
    ↓ LLM generates N=3 rewrites:
  Variant 1: "dormitory amenities campus residence"
  Variant 2: "accommodation services for students"
  Variant 3: "on-campus housing features"
    ↓
Retrieve separately for each variant + original
    ↓
Merge all 4 result lists using Reciprocal Rank Fusion (RRF):
  score = Σ 1/(k + rank) for each ranked list (k=60 default)
```

RRF is rank-based (scale-invariant) so different embedding score ranges don't skew the merge.

### Full-Page RAG

When a query matches a page that has very high relevance (`FULL_PAGE_RAG_ENABLED=true`):
- All chunks belonging to the same page/section are grouped by page_index
- Page-rank scoring: `best_chunk × 0.6 + avg_top3 × 0.3 + coverage × 0.1`
- Returns up to `FULL_PAGE_MAX_CHARS_PER_PAGE=4000` characters per page

### FlashRank Reranker

After initial retrieval, a neural reranker (`rag/reranker.py`) can be applied:
- Uses **FlashRank** with `ms-marco-MiniLM-L-12-v2` ONNX model
- Runs on CPU in milliseconds (no GPU needed)
- Re-scores candidates based on query-passage relevance
- Falls back gracefully if FlashRank is not installed

---

## 🗺️ Query Routing System

### Overview (`rag/query_router.py`)

Every incoming query is classified by `classify_query_route()` before any retrieval occurs. This prevents unnecessary ChromaDB searches and routes specialized queries to dedicated handlers.

### Eight Routes

| Route | Trigger Signals | Handler |
|-------|----------------|---------|
| `timetable` | "timetable", "schedule", "period", "class room" | SQL Agent → `institute_data.db` |
| `student_marks` | "marks", "score", "grade", "cgpa", "result", "semester" | SQL Agent → `institute_data.db` |
| `general_chat` | "hello", "hi", "good morning", "who are you" (no inst. signals) | Direct LLM (no retrieval) |
| `faq` | FAQ question words + institutional signals | FAQ ChromaDB collection |
| `official_site` | "college", "campus", "admission", "placement", "fee" | ChromaDB (official site docs) |
| `document` | "policy", "handbook", "syllabus", "regulation", "rag", "pdf" | ChromaDB (uploaded docs) |
| `hybrid` | Both official + document signals (tied score) | ChromaDB (combined) |
| `unclear` | No strong signals | ChromaDB (default fallback) |

### Fast Heuristic Tool Router (`rag/llm_router.py`)

Before the query router, a zero-latency heuristic (`get_tool_for_query()`) checks for SQL keywords:
- If matched → returns `"sql_agent"` immediately
- If not matched → returns `"none"` → query router classifies further

This avoids the 1–3s LLM routing overhead of earlier versions.

### Routing Flow

```
User query
    ↓
llm_router.get_tool_for_query()  [<1ms, keyword check]
    ├─ "sql_agent" → SQL Agent (timetable/marks)
    └─ "none" → classify_query_route() [regex/keyword]
                    ├─ timetable     → SQL Agent
                    ├─ student_marks → SQL Agent
                    ├─ general_chat  → Direct LLM
                    ├─ faq           → FAQ ChromaDB
                    ├─ official_site → Document ChromaDB
                    ├─ document      → Document ChromaDB
                    ├─ hybrid        → Both sources
                    └─ unclear       → Document ChromaDB
```

**Forced Database Mode:** Faculty/Admin users can prefix a query with `@Database` to bypass routing and force the SQL Agent for timetable/marks lookups. Students can type it, but the prefix is ignored and treated as a normal query.

---

## 🔧 Component Deep Dive

### Configuration (`config.py` + `tests/config.py`)

The single source of truth for all runtime settings. Loads from `.env` → environment variables → hardcoded defaults.

`tests/config.py` re-exports everything from `config.py` and adds test-only overrides via `TEST_*` environment variables. Most production modules import from `tests.config` for backward compatibility.

Key config groups:
- **Paths**: `BASE_DIR`, `UPLOAD_DIR`, `CHROMA_PERSIST_DIR`, `SQLITE_DB_PATH`
- **LLM**: `LLM_MODE`, `LLM_PRIMARY_PROVIDER`, `LLM_FALLBACK_PROVIDER`, model names + keys
- **Retrieval**: `RETRIEVAL_MODE`, `HYBRID_DENSE_WEIGHT`, `HYDE_ENABLED`, `QUERY_EXPANSION_ENABLED`
- **Memory**: `CONV_ENABLED`, `CONV_MATCH_THRESHOLD`, `CONV_TTL_DAYS`
- **Rate Limits**: `RATE_LIMIT_CHAT`, `RATE_LIMIT_UPLOAD`, `RATE_LIMIT_GLOBAL`
- **Observability**: `LANGFUSE_ENABLED`, `SENTRY_DSN`, `LOG_LEVEL`

### Document Ingestion Module (`ingestion/`)

> **Note:** The `ingestion/` directory contains `parser.py`, `chunker.py`, and `embedder.py`. These provide the ingestion pipeline referenced throughout the codebase.

**`ingestion/parser.py`** — Multi-format text extraction:

| Format | Library | Notes |
|--------|---------|-------|
| PDF | PyPDF2 | Page-by-page extraction |
| DOCX | python-docx | Paragraphs + tables |
| XLSX/CSV | openpyxl | Sheet names as headings |
| PPTX | python-pptx | Slides + speaker notes |
| HTML/HTM | BeautifulSoup | Strips tags, preserves text |
| TXT | Built-in | Direct read |

**`ingestion/chunker.py`** — Hybrid chunking strategy:
- Stage 1: Structural split on markdown headings, `[Page N]` markers, sheet names
- Stage 2: Fixed 500-char chunks with 50-char overlap, breaking at sentence boundaries
- Output: `[{text, metadata: {source, heading, chunk_index}}]`

**`ingestion/embedder.py`** — Embedding + ChromaDB storage:
- Uses `sentence-transformers` model `all-MiniLM-L6-v2` (384 dimensions)
- Model is lazy-loaded on first use and cached
- Functions: `generate_embeddings()`, `store_chunks()`, `delete_doc_chunks()`, `get_collection()`, `get_collection_stats()`, `get_chroma_client()`

### Authentication (`auth/auth.py`)

Session-based auth using Streamlit `st.session_state`:

```
Login:
  1. auth.login(username, password)
  2. database.db.authenticate_user() → PBKDF2-HMAC-SHA256 password check
  3. On success: populate session_state {user_id, username, role}

Roles: admin | faculty | student
  - admin: full access (documents, users, AI settings, health, memory)
  - faculty: chat + upload
  - student: chat only
```

The FastAPI API server uses JWT-style tokens (via header `X-User-ID`) for REST auth.

### Database Layer (`database/`)

**`database/db.py`** — Main SQLite (PBKDF2 hashing, WAL mode):

```
Tables:
  users          — id, username, password_hash, password_salt, role, full_name, is_active
  documents      — id, filename, file_type, file_size, chunk_count, source_type, source_url,
                   uploaded_by, status, classification, tags
  query_logs     — id, user_id, username, query_text, response_text, sources, response_time_ms,
                   route_mode, trace_id, feedback_rating, from_memory
  conversation_memory — id, query_text, response_text, sources, user_id, usage_count,
                        last_used_at, expires_at
  traces         — id, service, operation, user_id, status, duration_ms, error
  spans          — id, trace_id, service, operation, status, duration_ms, error, tags
  rate_limits    — key, limit_string, enabled, description
  announcements  — id, title, content, author, is_active
  question_suggestions — doc_id, questions_json
  feedback       — id, trace_id, user_id, rating, comment
```

Password security upgrade: PBKDF2-HMAC-SHA256 with per-user salts (replaces bare SHA-256 from earlier version).

**`database/institute_db.py`** — Separate SQLite for structured institutional data:

```
Tables:
  timetables     — id, class_name, day, start_time, end_time, subject, room, uploaded_by
  students       — id, roll_no, name, email, phone, department, semester, gpa
  student_marks  — id, student_id, subject_code, subject_name, semester,
                   internal_marks, external_marks, total_marks, grade
```

Also provides `get_schema_for_llm()` which returns a text description of all tables/columns for the SQL Agent's system prompt, and `execute_readonly_query()` which opens the database in read-only mode for security.

**`database/student_db.py`** — CRUD helpers for students/marks:
- `add_student()`, `bulk_add_students()`, `query_student_by_roll_no()`
- `bulk_add_student_marks()`, `query_student_marks()`

### Conversation Memory / Semantic Cache (`rag/memory.py`)

Avoids redundant LLM calls by caching Q&A pairs as vectors in ChromaDB:

```
On every query:
  1. query_memory(query) → embed query → ChromaDB cosine search
     ├─ Similarity > 0.88 (CONV_MATCH_THRESHOLD) → CACHE HIT
     │   Return cached response in <5ms
     └─ Miss → Proceed to full RAG pipeline

After LLM generates response:
  2. add_memory_entry(query, response, sources) 
     → Store in ChromaDB (vector) + SQLite (metadata + TTL)

Cleanup:
  cleanup_old_memory() → remove entries older than CONV_TTL_DAYS (90 days)
  invalidate_memory_by_source(doc_id) → delete memory from re-uploaded docs
```

Configuration knobs:
- `CONV_ENABLED` — feature on/off
- `CONV_MATCH_THRESHOLD` — similarity threshold (default 0.88)
- `CONV_PER_USER` — separate memory per user or shared global memory
- `CONV_TTL_DAYS` — expiry (default 90 days)

**Student safety:** When student profile/marks context is injected into a prompt, the response bypasses the semantic cache to avoid cross-user leakage if global memory is enabled.

### SQL Agent (`rag/tools/sql_agent.py`)

Handles structured queries (timetables, student marks) via Text-to-SQL:

```
User: "What classes does CCE-A have on Monday?"
    ↓
Step 1 — SQL Generation
  Inject DB schema into LLM prompt
  LLM outputs: {"sql": "SELECT * FROM timetables WHERE...", "explanation": "..."}

Step 2 — Execute (read-only)
  execute_readonly_query(sql) against institute_data.db

Step 2b — Self-correction
  If query fails → feed error back to LLM → retry once

Step 3 — Synthesize
  Format results as text table → LLM writes natural language answer
```

Security: The database connection is opened in SQLite URI read-only mode (`mode=ro`). Only SELECT queries can succeed.

### FAQ Retriever (`rag/faq_retriever.py`)

Maintains a separate ChromaDB collection (`ims_faq`) of structured Q+A pairs:

```
Admin adds FAQ:
  Question: "What is the admission process?"
  Answer: "Submit online application by March 31..."
    ↓ Embed question → store in ChromaDB with answer in metadata

User asks question → routed to FAQ:
  Embed user question → cosine search in FAQ collection
  Threshold (FAQ_MIN_SCORE = 0.45)
  Return matching answers as context chunks
```

FAQs appear in the chat as source-cited answers like regular document chunks.

### Voice-to-Text (`rag/voice_to_text.py`)

Whisper-based local audio transcription:

```
React mic button → POST /api/chat/audio with .webm audio blob
    ↓
transcribe_audio(file_path)
    → get_whisper_model() [cached with @lru_cache]
    → faster_whisper.WhisperModel (base.en, CPU, int8 quantization — default; float16 available for GPU)
    → segments joined → plain text
    ↓
Transcribed text fed into standard chat pipeline
```

Model stored at `models/whisper-base-en/` (local, no internet required after first download).

### LLM Providers (`rag/providers/`)

**`base.py`** — Abstract interface:
```python
class LLMProvider:
    name: str
    def generate(system_prompt, user_message, temperature, max_tokens) → str | None
    def generate_stream(...)  → Iterator[str] | None
    def is_available() → bool
    def get_status() → dict
```

**`ollama_provider.py`** — Local Ollama REST API:
- POST to `OLLAMA_BASE_URL/api/chat` with the configured model
- Checks `/api/tags` for availability
- Supports streaming via `/api/chat` with `stream=true`

**`groq_provider.py`** — Groq cloud API:
- Uses `groq` Python SDK
- Default model: `llama-3.3-70b-versatile`
- Requires `GROQ_API_KEY`

**`gemini_provider.py`** — Google Gemini API:
- Uses `google-generativeai` SDK
- Default model: `gemini-2.0-flash`
- Requires `GEMINI_API_KEY`

**`manager.py`** — Thread-safe singleton `ProviderManager`:

```
Mode: local_only  → chain = [ollama]
Mode: cloud_only  → chain = [primary_cloud, fallback_cloud]
Mode: hybrid      → chain = [primary, fallback, ollama]

generate() → tries each provider in order, returns first success
generate_stream() → yields chunks from first successful provider
```

### Observability (`rag/observability/`)

**`sqlite_tracer.py`** — Local SQLite-based distributed tracing:

```
Per request:
  start_observation() → creates ObservationTrace (root)
    ├─ trace.start_span("rag.retrieve") → ObservationSpan (step)
    │   span.end(output, metadata)       → records duration in SQLite
    ├─ trace.start_span("rag.generate_response")
    │   span.end(...)
    └─ trace.end(status="success")       → records total duration

Admin can view: traces + spans in Observability dashboard
```

**`langfuse_client.py`** — Optional Langfuse cloud integration:
- Only active when `LANGFUSE_ENABLED=true`
- Sends traces to `LANGFUSE_HOST` for external dashboards
- API-compatible with sqlite_tracer (same `start_span`/`end` interface)

**`trace_context.py`** — Thread-safe + async-safe context vars:
- `set_trace_id()`/`get_trace_id()` — propagate trace_id through pipeline
- `set_obs_trace()`/`get_obs_trace()` — propagate trace object

### Pipeline Trace (`rag/pipeline_trace.py`)

Terminal explainability for demos/jury presentations:
- Prints color-coded ASCII output to the server terminal showing every step
- ANSI colors: cyan headers, green/yellow/red similarity scores
- Shows: route, query expansion, retrieved chunks with scores, LLM model used, response time
- Zero-overhead when not used (only activates when `PipelineTrace` is instantiated)

### Middleware (`middleware/`)

**`rate_limiter.py`** — `slowapi`-based rate limiting:
- Key function: `X-User-ID` header (authenticated users) or IP address (anonymous)
- Tiers: global, per-user, chat (5/min), upload (10/min), auth (5/min)
- Returns HTTP 429 with `Retry-After: 60` on violation
- Rate limit config is stored in SQLite and can be changed by admin

**`request_tracking.py`** — Two middleware classes:
- `RequestTrackingMiddleware` — adds `X-Request-ID` to every request, logs request + response timing
- `ErrorContextMiddleware` — catches unhandled exceptions, attaches request_id for correlation

### Conversation History (`rag/conversation_history.py`)

Maintains a rolling window of recent Q+A pairs per user in memory for context injection:
- `get_history(user_id)` → returns last N query+response pairs
- `add_to_history(user_id, query, response)` → appends to in-memory dict
- Used by `_search_query_with_history()` in `api_server.py` to augment search queries with previous context

### Logging & Error Tracking (`log_config/`)

**`log_config/__init__.py`** — `setup_logging()`:
- Rotating file handler: `logs/astrobot.log`, 10 MB per file, 10 backups
- Console handler with configured `LOG_LEVEL`
- `get_logger(name)` factory used throughout codebase

**`log_config/sentry_config.py`** — `init_sentry()`:
- Optional Sentry integration (`SENTRY_DSN` required)
- Captures all unhandled exceptions and traces
- `SENTRY_TRACES_SAMPLE_RATE=0.1` (10% trace sampling)

### Streamlit Application (`app.py`)

Entry point for the Streamlit UI:

```
├─ Page config (wide layout, AstroBot icon)
├─ init_session_state() → sets auth defaults
├─ Sidebar
│   ├─ Login panel (if not authenticated)
│   │   └─ render_login_page() → auth.py
│   ├─ Navigation (if authenticated)
│   │   ├─ Chat → render_chat_page()
│   │   ├─ Knowledge (admin) → render_admin_page()
│   │   ├─ AI Settings (admin) → render_ai_settings_page()
│   │   ├─ Memory (admin) → render_memory_page()
│   │   └─ Observability (admin) → render_observability_page()
│   └─ Health sidebar (admin) → _check_system_health() [60s cache]
└─ Main content area renders selected page
```

Health check is cached `@st.cache_resource(ttl=60)` — only SQLite ping + ChromaDB directory check. Provider health is on-demand only.

### Chat View (`views/chat.py`)

Full RAG-powered chat interface:

```
User types question
    ↓
classify_query_route() → route
    ↓
if route.mode in (timetable, student_marks) or llm_router says sql_agent:
    execute_sql_agent(prompt) → structured DB answer
elif route.mode == general_chat:
    generate_response_direct(prompt) → no retrieval
else:
    retrieve_context(prompt, source_type, filters, complexity_score)
    format_context_for_llm(chunks)
    generate_response(query, context, user_id)
    ↓
Display response with sources
log_query() to SQLite
```

### Admin View (`views/admin.py`)

Four admin panels:

1. **Document Management** — Upload (parse+chunk+embed), delete, view stats + question suggestions
2. **AI Settings** — Change LLM mode/provider/model, temperature, max_tokens, system prompt, reset ProviderManager
3. **Memory** — View stats, delete entries, clear all, cleanup expired entries
4. **Observability** — View recent traces + spans, latency charts

### FastAPI REST Server (`api_server.py`)

30+ endpoints across categories:

| Category | Key Endpoints |
|----------|--------------|
| Auth | `POST /api/login`, `POST /api/register` |
| Chat | `POST /api/chat`, `POST /api/chat/stream`, `POST /api/chat/audio`, `POST /api/feedback` |
| Documents | `POST /api/documents/upload`, `GET /api/documents`, `DELETE /api/documents/{id}`, `POST /api/ingest-url` |
| FAQ | `POST /api/faq/bulk`, `GET /api/faq/stats`, `DELETE /api/faq` |
| Admin | `POST/GET/DELETE /api/admin/users`, `GET /api/admin/analytics`, `GET/POST /api/admin/rate-limits` |
| Institute | `POST /api/institute/timetable`, `POST /api/institute/students`, `POST /api/institute/marks` |
| Memory | `GET /api/memory/stats`, `POST /api/memory/cleanup`, `DELETE /api/memory`, `DELETE /api/memory/all` |
| Observability | `POST /api/observe/start`, `POST /api/observe/record_feedback`, `GET /api/traces` |
| Announcements | `GET /api/announcements`, `POST /api/admin/announcements` |
| System | `GET /api/health`, `GET /api/status` |

Startup warmup: on server start, a background thread pre-loads the embedding model + ChromaDB + ProviderManager so the first request isn't slow.

### Spring Boot Backend (`springboot-backend/`)

Java proxy layer between React frontend and Python FastAPI:

```
React → Spring Boot ChatController → PythonApiService (WebClient) → FastAPI
```

- **`PythonApiService.java`** — Async `WebClient` calls to FastAPI on `localhost:8000`
- **Controllers** — `ChatController`, `AuthController`, `DocumentController`
- **DTOs** — Java POJOs mirroring FastAPI request/response models
- **`WebConfig.java`** — WebClient bean, CORS settings

### React Frontend (`react-frontend/`)

Vite + React SPA:
- **`services/api.js`** — Centralized Axios client (points to FastAPI or Spring Boot)
- **`context/AuthContext.jsx`** — Global auth state (username, token, role)
- **Pages**: `LoginPage`, `ChatPage`, `admin/` (document upload, user management, analytics)
- **Components**: Chat bubble, source citation card, file upload drag-drop, announcement banner
- Microphone button → `POST /api/chat/audio` for voice-to-text

---

## 🗄️ Data Stores

### SQLite Main (`astrobot.db`)

All application data except structured institutional data. Uses WAL mode with foreign keys for concurrency and integrity. Passwords are hashed with PBKDF2-HMAC-SHA256 using per-user salts.

```
users              id (UUID), username, password_hash, password_salt, role, full_name, is_active
documents          id, filename, file_type, size, chunk_count, source_type, source_url,
                   uploaded_by, status, classification, tags, uploaded_at
query_logs         query, response, sources, route_mode, trace_id, response_time_ms, feedback
conversation_memory query_text, response_text, sources, user_id, usage_count, expires_at
traces / spans     distributed tracing data (service, operation, duration, status, error)
rate_limits        per-endpoint limit strings and enabled flags
announcements      title, content, author, is_active
question_suggestions doc_id → AI-suggested questions JSON
feedback           trace_id, user_id, rating (±1), comment
```

### SQLite Institute (`institute_data.db`)

Separate database for structured student data, opened read-only by the SQL Agent:

```
timetables         class_name, day, start_time, end_time, subject, room
students           roll_no, name, email, phone, department, semester, gpa
student_marks      student_id FK, subject_code, subject_name, semester,
                   internal_marks, external_marks, total_marks, grade
```

### ChromaDB Collections

| Collection | Purpose | Content |
|------------|---------|---------|
| `<doc_id>` (one per document) | Document chunk vectors | 384-dim embeddings + text + metadata |
| `ims_faq` | FAQ question→answer matching | FAQ question embeddings + answers in metadata |
| `conversation_memory` | Semantic Q&A cache | Query embeddings + response text in metadata |

---

## 📊 Data Flow

### Document Upload Flow

```
User uploads "course.pdf"
    ↓
POST /api/documents/upload → api_server.py
    ↓
save file to data/uploads/
    ↓
parse_document(file_path) → raw text
    ↓
chunk_document(text) → list of chunks [{text, metadata}]
    ↓
store_chunks(chunks, doc_id) → ChromaDB (384-dim vectors)
    ↓
add_document(filename, chunk_count, ...) → SQLite documents table
    ↓
store_document_question_suggestions() → LLM generates suggested Qs
    ↓
[Optional] invalidate_memory_by_source(doc_id) → clear stale cache
```

### Query Flow (Full RAG Path)

```
User types "What is the attendance policy?"
    ↓
POST /api/chat → api_server.py
    ↓
start_observation() → create trace in SQLite
    ↓
classify_query_route(query) → Route.DOCUMENT (matched "policy")
    ↓
retrieve_context(query, source_type="uploaded")
    ├─ Dense: embed query → ChromaDB search (top 20)
    ├─ BM25: tokenize query → keyword index scan (top 40)
    ├─ Merge: RRF → hybrid score → top 5 candidates
    └─ [HyDE if score < 0.58] [QueryExpansion if enabled]
    ↓
format_context_for_llm(chunks) → context string with source headers
    ↓
query_memory(query) → ChromaDB semantic search
    ├─ HIT: return cached response in <5ms
    └─ MISS: proceed
    ↓
generate_response(query, context, user_id)
    └─ ProviderManager.generate() → primary → fallback chain
    ↓
add_memory_entry(query, response, sources) → cache for next time
    ↓
log_query(user_id, query, response, sources, trace_id)
    ↓
trace.end() → record total duration
    ↓
Return ChatResponse {response, sources, citations, response_time_ms, trace_id}
```

### Student Marks Query Flow

```
User: "Show me marks for roll number 21CS001"
    ↓
classify_query_route() → Route.STUDENT_MARKS
    OR llm_router.get_tool_for_query() → "sql_agent"
    ↓
execute_sql_agent("Show me marks for roll number 21CS001")
    ↓
LLM generates: SELECT sm.*, s.name FROM student_marks sm
               JOIN students s ON sm.student_id = s.id
               WHERE LOWER(s.roll_no) LIKE LOWER('%21CS001%')
    ↓
execute_readonly_query(sql) → [{"name": "...", "subject_code": "...", ...}]
    ↓
LLM synthesizes → "Student 21CS001 scored 45 in internal for CS201..."
```

---

## ⚡ Performance Characteristics

### Query Latency (End-to-End)

| Step | Operation | Time |
|------|-----------|------|
| Memory cache hit | Semantic match → return cached | **< 5–10ms** |
| Embedding query | 384-dim vector generation | 10–20ms |
| Dense ChromaDB search | Top-20 candidates | 5–15ms |
| BM25 keyword search | Top-40 candidates | 2–5ms |
| RRF merge | Combine + score | 1–2ms |
| HyDE (if triggered) | LLM hypothesis + extra embed | +50–200ms |
| FlashRank reranker | Neural rerank (CPU ONNX) | 5–20ms |
| Context formatting | Format chunks + citations | 2–5ms |
| LLM generation — Ollama local | qwen3:0.6b, 512 tokens | 300–800ms |
| LLM generation — Groq cloud | llama-3.3-70b | 300–800ms |
| LLM generation — Gemini cloud | gemini-2.0-flash | 500–2000ms |
| SQL Agent | Schema → SQL → execute → synthesize | 600–2000ms |
| Database logging | SQLite write | 5–20ms |
| **Typical local (cache miss)** | Full pipeline | **~400–900ms** |

### Memory Usage

| Component | Size | Notes |
|-----------|------|-------|
| Python base + FastAPI | 250 MB | App code + libraries |
| Embedding model (all-MiniLM-L6-v2) | 400–500 MB | Lazy-loaded on first query |
| ChromaDB in-memory cache | 200–300 MB | Grows with vector count |
| Whisper model (base.en) | 145 MB | Lazy-loaded on first audio |
| FlashRank ONNX model | 50 MB | Lazy-loaded on first rerank |
| LLM model (local GGUF, e.g., Phi-3) | 2–4 GB | Ollama manages this |
| **TOTAL (no LLM)** | **~1.2 GB** | Typical startup |
| **TOTAL (with local Ollama LLM)** | **~3.5–5 GB** | Full system |

### Throughput

| Metric | Value | Notes |
|--------|-------|-------|
| Concurrent users (FastAPI) | 10–50 | LLM is the bottleneck |
| Single-threaded (Streamlit) | 1 active session | Normal for admin tools |
| Documents uploadable | 10,000+ | ChromaDB handles easily |
| Vectors storable | 1M+ | Practical limit ~10M |
| Database records | 1M+ | SQLite WAL handles well |
| Cache hit rate (repeat questions) | 40–70% | Typical institutional usage |

---

## 🎯 Key Design Decisions

### Why Hybrid Retrieval (BM25 + Dense)?

| Aspect | Dense only | Hybrid |
|--------|------------|--------|
| Exact acronym matches (e.g., "CGPA") | ❌ May miss | ✓ BM25 catches |
| Semantic paraphrases | ✓ | ✓ |
| Course codes (CS101) | ❌ | ✓ BM25 |
| Conceptual questions | ✓ | ✓ |

**Decision:** Hybrid at 70/30 (dense/BM25) weight = best of both worlds for institutional documents.

### Why RAG and not Fine-tuning?

| Aspect | RAG | Fine-tuning |
|--------|-----|------------|
| **Setup time** | Hours | Days/Weeks |
| **Update docs** | Instant (re-upload) | Retrain needed |
| **Private data** | Stays local | Uploaded to GPU cloud |
| **Cost** | Low | High |

**Decision:** RAG = right balance for institutional use with frequently updating documents.

### Why Two Separate SQLite Databases?

| Reason | Explanation |
|--------|-------------|
| **Security** | SQL Agent opens `institute_data.db` read-only; cannot corrupt main DB |
| **Schema isolation** | Student/marks data schema evolves independently |
| **Admin separation** | Admins can clear main DB without wiping student records |

**Decision:** `astrobot.db` (application) + `institute_data.db` (institutional data) = clean separation.

### Why Local Observability (not Langfuse by default)?

| Aspect | SQLite tracer | Langfuse cloud |
|--------|--------------|----------------|
| **Cloud dependency** | None | Requires account |
| **Privacy** | Traces stay local | Sent to Langfuse servers |
| **Setup** | Zero config | API keys needed |
| **Overhead** | ~3ms per request | ~10–50ms |

**Decision:** SQLite-based tracing by default; Langfuse opt-in (`LANGFUSE_ENABLED=true`).

### Why ChromaDB and not Elasticsearch?

| Aspect | ChromaDB | Elasticsearch |
|--------|----------|---------------|
| **Setup** | One Python import | Docker container |
| **Storage** | SQLite file | Server-based |
| **Scaling** | Single machine | Clusters |
| **Learning curve** | Easy | Steep |

**Decision:** ChromaDB = perfect for this project scale (up to 10M vectors).

### Why FastAPI and not Flask?

| Aspect | FastAPI | Flask |
|--------|---------|-------|
| **Async support** | Built-in | Extension needed |
| **Type safety** | Pydantic models | Manual |
| **Auto API docs** | `/docs` (Swagger) | Manual |
| **Streaming** | Native `StreamingResponse` | Third-party |

**Decision:** FastAPI = scales better, cleaner code, native streaming for LLM responses.

### Why Ollama Primary + Cloud Fallback?

| Aspect | Ollama (local) | Cloud (Groq/Gemini) |
|--------|----------------|---------------------|
| **Privacy** | Data stays on server | Sent to cloud |
| **Cost** | Free | Per-token cost |
| **Internet** | Not required | Required |
| **Latency** | 300–800ms | 300–2000ms |

**Decision:** Local-first for privacy + cost; cloud as fallback for reliability.

---

## 🔄 Common Workflows

### Workflow 1: Faculty Member Uploads Documents

```
1. Faculty logs in (Streamlit or React)
2. Admin view → Document Management → Upload
3. Selects 20 PDFs
4. System:
   - Parses text from each PDF
   - Chunks into ~500-char pieces
   - Embeds with all-MiniLM-L6-v2
   - Stores in ChromaDB
   - Records in SQLite with "processed" status
   - LLM generates 3 suggested questions per document
5. Faculty sees: "✓ 20 documents processed, 400 chunks indexed"
6. Students can now query these documents
```

### Workflow 2: Student Asks a Question

```
1. Student logs in → Chat
2. Types: "What are the attendance requirements?"
3. Behind the scenes:
   - Query Router: matched "attendance" → Route.DOCUMENT
   - Hybrid retrieval: dense + BM25 → top 5 chunks from regulations.pdf
   - Memory cache: no hit (first time)
   - LLM: generates answer grounded in retrieved context
   - Memory store: caches for next student who asks the same
4. Student sees:
   "Attendance must be at least 75% in each subject.
    [Source: Student Regulations 2024.pdf]"
5. Next student who asks the same question: <5ms cache hit
```

### Workflow 3: Student Asks for Timetable

```
1. Student types: "What classes does CCE-A have on Monday?"
2. Query Router: matched "class" + "Monday" → Route.TIMETABLE
3. SQL Agent:
   - Schema injected into LLM
   - LLM writes: SELECT subject, start_time, end_time, room
                 FROM timetables
                 WHERE LOWER(class_name) LIKE '%cce-a%'
                 AND LOWER(day) LIKE '%mon%'
   - Execute read-only → results
   - LLM: "CCE-A has Mathematics at 9:00 AM in Room 301..."
4. Student sees formatted timetable
```

**Student login mapping:** For the prototype, student logins are created from uploaded roll numbers. Username/password are set to the roll number, and student profile + marks are auto-loaded into the prompt when available.

### Workflow 4: Admin Troubleshooting

```
1. Admin logs in → Health sidebar
2. Checks:
   ✓ SQLite: OK (5 users, 20 documents)
   ✓ ChromaDB: Ready at chroma_db/
   ✓ LLM Mode: local_only
3. On-demand → "Check LLM Providers":
   ✓ Ollama: Running (qwen3:0.6b)
4. If slow responses (>1500ms):
   - Observability → recent traces → identify slow spans
   - AI Settings → switch to Groq for faster generation
5. Memory stats → high hit rate means caching is working well
```

### Workflow 5: Developer Adding a New LLM Provider

```
1. Create: rag/providers/claude_provider.py
2. Inherit: class ClaudeProvider(LLMProvider)
3. Implement:
   - generate(system_prompt, user_message, temp, max_tokens) → str | None
   - generate_stream(...) → Iterator[str] | None
   - is_available() → bool
   - get_status() → {"status": "ok", "message": "..."}
4. Register in rag/providers/manager.py:
   self._providers["claude"] = ClaudeProvider(CLAUDE_API_KEY, CLAUDE_MODEL)
5. Add to config.py: CLAUDE_API_KEY, CLAUDE_MODEL env vars
6. Test:
   python -c "from rag.providers.manager import get_manager; print(get_manager().get_all_statuses())"
7. Set in .env: LLM_PRIMARY_PROVIDER=claude
8. Done: Claude available in the fallback chain
```

---

## 🧠 Mental Model

**How to think about AstroBot:**

```
Simple view:
  Upload documents → Ask questions → Get cited answers

Advanced view:
  Query → Route → [SQL | Chat | Retrieve] → [Cache | LLM] → Answer + trace

Technical view:
  Documents → Parse → Chunk → Embed → ChromaDB
  Query → Route → Hybrid search (BM25+dense) → Rerank → Context
  Context + Query → Memory check → LLM → Cache → Response

System view:
  Presentation Layer (Streamlit + React + Spring Boot)
      ↓ HTTP
  Application Layer (FastAPI + RAG + Middleware)
      ↓ Local storage
  Data Layer (SQLite main + SQLite institute + ChromaDB + Files)
```

---

## ✅ You Now Understand

✅ What AstroBot does (RAG for institutional docs at RIT/IMS)
✅ Why RAG (accuracy, citations, privacy, instant updates)
✅ The 4-phase pipeline (ingest → route → retrieve → generate)
✅ Advanced retrieval (hybrid BM25+dense, HyDE, query expansion, reranker, full-page)
✅ Query routing (8 routes, keyword signals, sub-1ms heuristic)
✅ SQL Agent (text-to-SQL for timetables, students, marks)
✅ Conversation memory (semantic cache, 88% similarity threshold, TTL)
✅ Voice-to-text (local Whisper, CPU, <1s after first load)
✅ FAQ retrieval (separate ChromaDB collection, question-to-question matching)
✅ Two SQLite databases (application vs institutional data)
✅ Provider chain (local Ollama → cloud Groq/Gemini fallback)
✅ Observability (SQLite tracing + optional Langfuse cloud)
✅ Rate limiting (per-user + IP, slowapi, configurable from admin)
✅ Security (PBKDF2 passwords, read-only SQL Agent, parameterized queries)

---

## 📐 Configuration Reference

Key `.env` variables by functional area:

```
# LLM Mode
LLM_MODE=local_only          # local_only | cloud_only | hybrid
LLM_PRIMARY_PROVIDER=ollama  # ollama | groq | gemini
LLM_FALLBACK_PROVIDER=none   # none | ollama | groq | gemini
OLLAMA_MODEL=qwen3:0.6b
GROQ_API_KEY=...
GEMINI_API_KEY=...

# Retrieval
RETRIEVAL_MODE=hybrid        # dense | hybrid
HYBRID_DENSE_WEIGHT=0.7
HYDE_ENABLED=false           # true = hypothetical doc expansion on low scores
QUERY_EXPANSION_ENABLED=false

# Memory / Semantic Cache
CONV_ENABLED=true
CONV_MATCH_THRESHOLD=0.88    # higher = stricter cache matching
CONV_TTL_DAYS=90
CONV_PER_USER=false          # false = shared global memory

# Observability
LANGFUSE_ENABLED=false       # true = send traces to Langfuse cloud
SENTRY_DSN=                  # set to enable Sentry error tracking
LOG_LEVEL=INFO

# Rate Limits
RATE_LIMIT_CHAT=5/minute
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_AUTH=5/minute

# Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

---

## 🚀 Next Steps

- **Want to set up?** → [guides/QUICKSTART.md](../guides/QUICKSTART.md)
- **Want quick lookup?** → [guides/QUICKREF.md](../guides/QUICKREF.md)
- **Want SQL/marks data?** → [STUDENT_MARKS_INTEGRATION.md](../STUDENT_MARKS_INTEGRATION.md)
- **Want API details?** → [04-API_ENDPOINTS.md](../04-API_ENDPOINTS.md)
- **Want to code?** → [../COPILOT_GUIDE.md](../COPILOT_GUIDE.md)
- **Want development guide?** → [development/DEVELOPMENT_GUIDE.md](../development/DEVELOPMENT_GUIDE.md)

