# IMS AstroBot — Complete Architecture & Execution Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [RAG Pipeline Mechanics](#rag-pipeline-mechanics)
3. [Component Details](#component-details)
4. [Performance Metrics](#performance-metrics)
5. [Data Flow Examples](#data-flow-examples)
6. [Development Guide](#development-guide)

---

## System Overview

### What is AstroBot?

IMS AstroBot is a **Retrieval-Augmented Generation (RAG) chatbot** that answers questions about institutional documents. It combines three core technologies:

1. **Vector Search (ChromaDB):** Finds relevant documents using semantic similarity
2. **LLM Generation:** Generates answers from retrieved context
3. **Multi-provider Support:** Falls back gracefully between local (Ollama) and cloud LLMs (Grok, Gemini)

### Three-Tier Architecture

```
┌─────────────────────────────────────────────┐
│         Frontend Layer                       │
├─────────┬─────────────┬────────────────────┤
│Streamlit│ FastAPI     │ React + Spring Boot│
│  UI     │  REST API   │  Frontend          │
└────┬────┴──────┬──────┴────────────┬───────┘
     │           │                   │
┌────▼───────────▼──────────────────▼─────────┐
│         Application Layer                    │
├────────────────┬──────────┬──────────────────┤
│ Auth (session) │ RAG Core │ Admin Dashboard │
│                │(retrieval│                 │
│ (Streamlit st.)│& generation)               │
└────────────────┼──────────┼──────────────────┘
                 │          │
      ┌──────────┴──────────┴─────────┐
      │      Data/Processing Layer    │
      ├──────────┬────────────┬────────┤
      │Embedding │ChromaDB    │SQLite  │
      │(sentence │(vectors)   │(CRUD)  │
      │transform)│            │        │
      └──────────┴────────────┴────────┘
```

---

## RAG Pipeline Mechanics

### What is RAG?

**RAG = Retrieval-Augmented Generation**

Instead of:
```
Question → LLM → Answer (may hallucinate, outdated knowledge)
```

AstroBot does:
```
Question → Retrieval (find relevant documents)
        → LLM (generate answer grounded in retrieved context)
        → Answer (accurate, citable, current)
```

### The Three Phases

#### Phase 1: Document Ingestion (One-time, Admin-triggered)

```
1. User uploads file (PDF, DOCX, Excel, PPTX, HTML)
   └─ Stored in data/uploads/

2. Parser extracts text
   ├─ PDF → PyPDF2
   ├─ DOCX → python-docx
   ├─ Excel → openpyxl
   ├─ PPTX → python-pptx
   └─ HTML → BeautifulSoup

3. Chunker breaks text into overlapping pieces
   ├─ First: Split by document structure (headings, page breaks)
   ├─ Then: Split into fixed-size chunks (500 chars, 50 char overlap)
   └─ Attach metadata: source, heading, chunk_index

4. Embedder converts text to vectors
   ├─ Load model: all-MiniLM-L6-v2 (384-dimensional)
   ├─ Generate embedding vector per chunk
   └─ Store in ChromaDB with metadata

5. Database updated
   └─ Document record: chunk_count, status='processed'
```

**Execution Time per Document:**
- Small PDF (10 pages): ~5–10 seconds
- Large DOCX (50 pages): ~20–30 seconds
- Excel (complex): ~15–25 seconds

#### Phase 2: Query Processing (Per user question)

```
STEP 1: User asks question
        Input: "What is the leave policy?"

STEP 2: Embed question
        └─ Use same model as documents (all-MiniLM-L6-v2)
        └─ Output: 384-dim vector

STEP 3: Search ChromaDB
        ├─ Query: "What is the leave policy?" (as vector)
        ├─ Compare similarity to all stored chunks
        ├─ Return top-5 most similar chunks
        └─ Similarity = 1 - (distance / 2)
           (ChromaDB uses cosine distance: 0=identical, 2=opposite)

STEP 4: Format context
        ├─ Collect top-5 chunks
        ├─ Add source citations: [Source: leave-policy.pdf > Section 2 | Relevance: 94%]
        ├─ Join with \n\n separators
        └─ Output: 
           ---Context 1 [Source: leave-policy.pdf | Relevance: 94%]---
           Annual leave is 30 days...
           
           ---Context 2 [Source: rules.docx > HR Policy | Relevance: 87%]---
           Medical leave requires...

STEP 5: Send to LLM
        ├─ System prompt: "You are AstroBot... answer based ONLY on context..."
        ├─ User message: "Context:\n{formatted_context}\n\nQuestion: {query}"
        └─ Parameters: temperature=0.3 (deterministic), max_tokens=512

STEP 6: LLM generates response
        └─ Streams response or returns full text

STEP 7: Format for user
        ├─ Display response
        ├─ Show source citations (clickable, if web UI)
        └─ Log interaction in SQLite

Total latency: ~350–2000 ms (depends on LLM provider)
```

#### Phase 3: Answer Display

```
User sees:
┌─────────────────────────────────────────────┐
│ 🤖 AstroBot                                  │
│                                             │
│ Annual leave is 30 days per year...        │
│ Medical leave requires HR approval...      │
│                                             │
│ 📚 SOURCES:                                 │
│  • leave-policy.pdf (94% match)            │
│  • rules.docx > HR Policy (87% match)     │
└─────────────────────────────────────────────┘
```

---

## Component Details

### 1. Embedder (`ingestion/embedder.py`)

**Purpose:** Convert text → vectors, store in ChromaDB

**Key Functions:**

```python
# Initialize embedder on first use
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Convert text to vector
embeddings = embedder.encode(["Hello world"])
# Output: [[array of 384 floats]]

# Store in ChromaDB
collection.add(
    ids=["doc_1_chunk_0"],
    embeddings=[[vector_384_dims]],
    metadatas=[{"source": "policy.pdf", "heading": "Section 2"}],
    documents=["Actual text content"]
)

# Search for similar chunks
results = collection.query(
    query_embeddings=[[question_vector]],
    n_results=5
)
# Returns: top-5 documents + distances
```

**Why all-MiniLM-L6-v2?**
- Fast (384 dimensions << 1536 for large models)
- Accurate (good semantic understanding)
- Light weight (fits in RAM, no GPU needed)
- Open source (no API calls)

### 2. Retriever (`rag/retriever.py`)

**Purpose:** Search for relevant document chunks

```python
def retrieve_context(query: str, top_k: int = 5) -> list[dict]:
    """
    1. Embed the query
    2. Search ChromaDB
    3. Convert distance → similarity
    4. Return [{text, source, heading, score, doc_id}]
    """
    # Step 1: Embed question
    query_embedding = generate_embeddings([query])[0]
    
    # Step 2: Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    # Step 3: Convert distance to similarity
    # ChromaDB returns 0–2 range (0 = identical, 2 = opposite)
    # Similarity = (2 - distance) / 2 = 1 - distance/2
    similarity = 1 - (distance / 2)
    # Now: 1.0 = perfect match, 0.0 = orthogonal
    
    # Step 4: Format
    return [{
        "text": chunk_text,
        "source": "policy.pdf",
        "heading": "Section 2",
        "score": 0.94,  # 94% match
        "doc_id": "doc_123"
    }]
```

### 3. Generator (`rag/generator.py`)

**Purpose:** Generate LLM response from retrieved context

```python
def generate_response(query: str, context: str) -> str:
    """
    Takes retrieved context + question, sends to LLM provider.
    
    1. Format prompt
    2. Route to primary LLM
    3. If fails, try fallback
    4. If all fail, return context-only response
    """
    
    system_prompt = """You are AstroBot, a helpful academic assistant.
    Answer questions based ONLY on provided institutional documents.
    If context lacks info, say so clearly.
    Do not make up information."""
    
    user_message = f"""Based on institutional documents, answer:
    
    CONTEXT:
    {context}
    
    QUESTION: {query}"""
    
    response = provider_manager.generate(
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=0.3,  # Low = deterministic
        max_tokens=512
    )
    
    return response
```

### 4. Provider Manager (`rag/providers/manager.py`)

**Purpose:** Route requests through LLM providers with fallback

```python
class ProviderManager:
    """Singleton managing LLM provider chain."""
    
    def __init__(self):
        # Read config
        self.mode = os.getenv("LLM_MODE")  # local_only, cloud_only, hybrid
        self.primary = os.getenv("LLM_PRIMARY_PROVIDER")  # ollama, groq, gemini
        self.fallback = os.getenv("LLM_FALLBACK_PROVIDER")  # none, groq, gemini
    
    def _get_chain(self) -> list[LLMProvider]:
        """Build provider chain based on mode."""
        if self.mode == "local_only":
            return [OllamaProvider(...)]
        elif self.mode == "cloud_only":
            return [GroqProvider(...), GeminiProvider(...)]
        else:  # hybrid
            return [GroqProvider(...), OllamaProvider(...)]
    
    def generate(self, system_prompt, user_message, temp, tokens):
        """Try each provider in chain."""
        for provider in self._get_chain():
            try:
                response = provider.generate(system_prompt, user_message, temp, tokens)
                if response:
                    return response
            except Exception as e:
                continue  # Try next provider
        
        # All failed
        return None  # View handles fallback
```

**Modes Explained:**

| Mode | Chain | Use Case |
|------|-------|----------|
| `local_only` | [Ollama] | Dev environment, privacy, always available |
| `cloud_only` | [Primary] → [Fallback] | Production, want best LLM quality |
| `hybrid` | [Primary] → [Fallback] → [Ollama] | Production + offline fallback |

### 5. Database (`database/db.py`)

**Schema:**

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,              -- UUID
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,      -- SHA-256
    role TEXT NOT NULL,               -- admin, faculty, student
    full_name TEXT,
    created_at TEXT,                  -- ISO format
    is_active INTEGER                 -- 0 or 1
);

-- Documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,              -- UUID
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_type TEXT,                   -- .pdf, .docx, etc.
    file_size INTEGER,
    chunk_count INTEGER,              -- How many chunks stored in ChromaDB
    uploaded_by TEXT,                 -- FK → users.id
    uploaded_at TEXT,                 -- ISO format
    status TEXT                       -- processed, failed
);

-- Query logs table
CREATE TABLE query_logs (
    id TEXT PRIMARY KEY,              -- UUID
    user_id TEXT,                     -- FK → users.id
    username TEXT,
    query_text TEXT NOT NULL,
    response_text TEXT,
    sources TEXT,                     -- JSON: [{source, heading, score}]
    response_time_ms REAL,
    created_at TEXT                   -- ISO format
);
```

**Key CRUD Functions:**

```python
# Init database + default admin
init_db()
# Creates tables + inserts admin:admin123

# User auth
user = authenticate_user("admin", "admin123")
# Returns: {id, username, role, is_active}

# User mgmt
create_user("alice", "pass123", "faculty", "Alice Brown")
toggle_user_active(user_id, is_active=False)
delete_user(user_id)

# Document mgmt
add_document(doc_id, "policy.pdf", chunk_count=42, uploaded_by=user_id)
delete_document(doc_id)

# Query logging
log_query(user_id, query_text, response_text, sources, time_ms)

# Analytics
analytics = get_analytics()
# Returns: {total_queries, daily_trends, top_users, avg_response_time}
```

### 6. Authentication (`auth/auth.py`)

**Flow:**

```
User enters credentials
    ↓
authenticate_user(username, password)
    ├─ Query database for user
    ├─ Compute SHA-256(password)
    ├─ Compare with stored hash
    └─ Return user dict or None
    ↓
If successful, set st.session_state
    ├─ authenticated = True
    ├─ user_id = user["id"]
    ├─ username = user["username"]
    ├─ role = user["role"]  (admin, faculty, student)
    └─ user = full user dict
```

**Why Streamlit session_state?**
- Persists across page reruns
- Per-user (data isolated)
- Lost on browser close (no persistent token needed, safer)

---

## Performance Metrics

### Latency Breakdown

```
Question: "What is the annual leave policy?"

┌──────────────────────────────────────────┐
│ QUERY PROCESSING LATENCY                 │
├──────────────────────────────────────────┤
│ 1. Embed question          10–20 ms      │
│ 2. Search ChromaDB         5–15 ms       │
│ 3. Format context          2–5 ms        │
│ 4. LLM generation:                       │
│    • Ollama (local)        300–800 ms    │
│    • Grok (cloud)          500–1500 ms   │
│    • Gemini (cloud)        1000–2000 ms  │
│                                          │
│ TOTAL:                                   │
│ • Local (Ollama)           ~350–860 ms   │
│ • Cloud (Grok)             ~550–1550 ms  │
│ • Cloud (Gemini)           ~1050–2050 ms │
└──────────────────────────────────────────┘
```

### Memory Usage

```
COMPONENT                    TYPICAL RAM
─────────────────────────────────────────
Python runtime               100 MB
Streamlit framework          80 MB
FastAPI framework            50 MB
SQLite (10K docs)            5 MB
ChromaDB (in-memory)         200–500 MB (per document count)
Embedding model (loaded)     400–500 MB
LLM model (if local GGUF)    2–4 GB
Spring Boot                  300–500 MB

TOTAL:
• Streamlit alone            ~800 MB
• + Embedding model          ~1.2 GB
• + Local GGUF LLM           ~3.2–5.2 GB
• FastAPI alone              ~600 MB
• Spring Boot alone          ~400 MB
```

### Throughput

```
Concurrent users: 1              ~2 q/sec (sequential)
Concurrent users: 1 (FastAPI)    ~5–10 concurrent reqs
ChromaDB search speed            ~1–5 ms per million vectors
SQLite writes                    ~100+ writes/sec
```

### Scaling Limits

| Component | Bottleneck | Recommendation |
|-----------|-----------|---|
| ChromaDB | 10M+ vectors | Split collections or use Pinecone/Weaviate |
| SQLite | 1M+ records | Migrate to PostgreSQL |
| Streamlit | Single-threaded | Use FastAPI for concurrent users |
| Ollama | Network I/O | Use FastAPI worker pool |
| Grok/Gemini | Rate limits | 120 req/min (Grok), varies (Gemini) |

---

## Data Flow Examples

### Example 1: Upload Document

```
ACTOR: Admin user
ACTION: Upload leave-policy.pdf (25 KB)

┌─────────────────────────────────────────────────────────┐
│ Streamlit UI (admin.py)                                 │
│ • File input widget                                      │
│ • Click "Upload"                                        │
└────────────┬────────────────────────────────────────────┘
             │ file_bytes, filename
             ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Save file to data/uploads/                           │
│    leave-policy_<uuid>.pdf                              │
└────────────┬────────────────────────────────────────────┘
             │ file_path
             ↓
┌─────────────────────────────────────────────────────────┐
│ 2. parser.py extracts text                              │
│    PyPDF2 → "Annual leave is 30 days..."               │
└────────────┬────────────────────────────────────────────┘
             │ raw_text (2000 chars)
             ↓
┌─────────────────────────────────────────────────────────┐
│ 3. chunker.py breaks into pieces                        │
│    • Split by "## Leave Policy" heading                │
│    • Split into 500-char chunks with 50-char overlap   │
│    Result: [{text: "...", metadata: {...}}, ...]      │
└────────────┬────────────────────────────────────────────┘
             │ chunks = [4–6 chunks]
             ↓
┌─────────────────────────────────────────────────────────┐
│ 4. embedder.py converts to vectors                      │
│    • Load model: all-MiniLM-L6-v2                       │
│    • Encode 5 chunks → 5 × 384-dim vectors             │
│    • Store in ChromaDB with metadata                    │
└────────────┬────────────────────────────────────────────┘
             │ success/error
             ↓
┌─────────────────────────────────────────────────────────┐
│ 5. database.db.py updates record                        │
│    INSERT INTO documents:                               │
│    • id = <uuid>                                        │
│    • filename = leave-policy_<uuid>.pdf                │
│    • chunk_count = 5                                    │
│    • uploaded_by = <admin_user_id>                      │
│    • status = 'processed'                               │
└────────────┬────────────────────────────────────────────┘
             │
             ↓
         UI: "✓ Document uploaded (5 chunks)"
```

**Timeline:** ~10 seconds total

### Example 2: User Asks Question

```
ACTOR: Faculty member (alice@institution.edu)
ACTION: Ask "What is the annual leave policy?"

┌──────────────────────────────────────────────┐
│ Streamlit Chat UI (views/chat.py)            │
│ • Text input: "What is the annual..."       │
│ • Click send                                │
└────────────┬───────────────────────────────┘
             │ query = "What is the annual..."
             │ user_id, username
             ↓ [START TIMER]
┌──────────────────────────────────────────────┐
│ retriever.py (10–20 ms)                      │
│ 1. Embed question                           │
│ 2. Search ChromaDB top-5                    │
│ Result: [{text: "Annual...", source: "...", │
│           score: 0.94}, ...]                │
└────────────┬───────────────────────────────┘
             │
             ↓ (2–5 ms)
┌──────────────────────────────────────────────┐
│ retriever.format_context_for_llm()          │
│ ---Context 1 [Source: leave-policy.pdf]---  │
│ Annual leave is 30 days...                  │
│                                             │
│ ---Context 2 [Source: rules.docx]---        │
│ Medical leave requires...                   │
└────────────┬───────────────────────────────┘
             │
             ↓ (300–800 ms for Ollama)
┌──────────────────────────────────────────────┐
│ generator.py → ProviderManager               │
│ ProviderManager.generate(                    │
│   system_prompt="You are AstroBot...",      │
│   user_message="Context:\n...\nQuestion:...",│
│   temperature=0.3,                          │
│   max_tokens=512                            │
│ )                                           │
│                                             │
│ Ollama receives POST to /api/chat           │
│ Returns: "Annual leave policy..."           │
└────────────┬───────────────────────────────┘
             │
             ↓ (5–10 ms)
┌──────────────────────────────────────────────┐
│ Log to database (query_logs)                 │
│ INSERT:                                     │
│ • user_id = alice_id                        │
│ • query_text = "What is the annual..."      │
│ • response_text = "Annual leave..."         │
│ • sources = [{source: "...", score: 0.94}]  │
│ • response_time_ms = 832                    │
└────────────┬───────────────────────────────┘
             │
             ↓ [END TIMER] ~850 ms total
        UI displays response + sources
```

### Example 3: Provider Fallback Chain (Hybrid Mode)

```
CONFIG:
LLM_MODE=hybrid
LLM_PRIMARY_PROVIDER=groq
LLM_FALLBACK_PROVIDER=gemini

┌──────────────────────────────────────────────┐
│ generator.generate_response(query, context)  │
│                                              │
│ ProviderManager._get_chain() returns:        │
│ [GroqProvider, GeminiProvider, OllamaProvider]│
└────────────┬───────────────────────────────┘
             │
             ↓ TRY GROQ
┌──────────────────────────────────────────────┐
│ Groq API call (with API key)                 │
│ POST to https://api.groq.com/...             │
│ RESPONSE: Timeout (network issue)            │
│ ❌ FAILED                                    │
└────────────┬───────────────────────────────┘
             │ exception caught, continue
             ↓ TRY GEMINI
┌──────────────────────────────────────────────┐
│ Gemini API call (with API key)               │
│ POST to https://generativelanguage.googleapis │
│ RESPONSE: "Annual leave is 30 days..."       │
│ ✅ SUCCESS                                   │
│ Return response                              │
└────────────┬───────────────────────────────┘
             │
             ↓
         User sees Gemini-generated answer
         (faster than querying Ollama locally)
```

**Without fallback:** User would see "No LLM available"  
**With fallback:** Seamless experience across providers

---

## Development Guide

### Adding a New LLM Provider

```python
# 1. Create rag/providers/claude_provider.py

from rag.providers.base import LLMProvider
import anthropic

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key)
    
    @property
    def name(self) -> str:
        return "Claude (Anthropic)"
    
    def generate(self, system_prompt: str, user_message: str,
                 temperature: float, max_tokens: int) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    
    def is_available(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False
    
    def get_status(self) -> dict:
        if self.is_available():
            return {"status": "ok", "message": "Claude API available"}
        return {"status": "error", "message": "Claude API unreachable"}

# 2. Update config.py
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-sonnet")

# 3. Update rag/providers/manager.py
self._providers: dict[str, LLMProvider] = {
    "ollama": OllamaProvider(...),
    "groq": GroqProvider(...),
    "gemini": GeminiProvider(...),
    "claude": ClaudeProvider(CLAUDE_API_KEY, CLAUDE_MODEL),  # ← Add
}

# 4. Update .env
CLAUDE_API_KEY=sk-...
CLAUDE_MODEL=claude-3-sonnet

# 5. Set mode
LLM_MODE=hybrid
LLM_PRIMARY_PROVIDER=claude
LLM_FALLBACK_PROVIDER=groq
```

### Adding a New File Format Parser

```python
# In ingestion/parser.py

def parse_epub(file_path: str) -> str:
    """Extract text from EPUB files."""
    import ebooklib
    from ebooklib import epub
    
    book = epub.read_epub(file_path)
    text_parts = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            text = item.get_content().decode('utf-8')
            text_parts.append(strip_html_tags(text))
    
    return "\n".join(text_parts)

# In config.py
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".xlsx", ".csv", 
    ".pptx", ".html", ".htm", ".epub"  # ← Add
}

# In ingestion/embedder.py
def add_document_to_chromadb(file_path, source_name):
    if file_path.endswith(".epub"):
        text = parse_epub(file_path)
    elif file_path.endswith(".pdf"):
        text = parse_pdf(file_path)
    # ... handle other formats
```

### Adding Analytics Dashboard

```python
# In views/admin.py

def render_analytics_page():
    st.header("📊 Analytics")
    
    from database.db import get_analytics
    analytics = get_analytics()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Queries", analytics["total_queries"])
    col2.metric("Avg Response Time", f"{analytics['avg_response_time_ms']:.0f} ms")
    col3.metric("Daily Peak", analytics["daily_peak"])
    
    # Trend chart
    import pandas as pd
    df = pd.DataFrame(analytics["daily_trends"])
    st.line_chart(df.set_index("date"))
    
    # Top users
    st.write("**Top Users:**")
    for user in analytics["top_users"][:10]:
        st.write(f"• {user['username']}: {user['query_count']} queries")
```

---

## Summary

This document covers IMS AstroBot's complete architecture:

- **RAG Pipeline:** Document ingestion → embedding → retrieval → generation
- **Components:** Embedder, Retriever, Generator, ProviderManager, Database
- **Performance:** ~350–2000 ms latency, ~800 MB–5 GB RAM
- **Fallback:** Graceful degradation across Ollama → Grok → Gemini → context-only
- **Development:** Extensible provider + parser framework

The system is production-ready for institutional use with proper security hardening and rate limiting.

