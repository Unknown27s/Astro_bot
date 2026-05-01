# RAG (Retrieval-Augmented Generation) System

## Overview

The RAG system is the core intelligence engine of AstroBot, combining document retrieval with LLM generation to answer institutional questions with context-aware, accurate responses.

**Architecture:** FastAPI service running on port 8001, coordinating:
- **Query Routing** — Classifies queries into institutional/general categories
- **Retrieval** — Hybrid semantic + keyword search against ChromaDB
- **Generation** — LLM-powered response generation with memory caching
- **Conversation Management** — Per-user conversation history for follow-ups

---

## Core Components

### 1. Query Router (`query_router.py`)

**Purpose:** Intelligently routes user queries to appropriate RAG pipelines.

**Routes:**
- `OFFICIAL_SITE` — Public campus information (admissions, facilities, placement)
- `DOCUMENT` — Uploaded documents (policies, handbooks, syllabi)
- `TIMETABLE` — Timetable/schedule queries (handled by separate agent)
- `FAQ` — FAQ-style questions with institutional backing
- `HYBRID` — Mix of official and document signals
- `GENERAL_CHAT` — Off-topic general conversation
- `UNCLEAR` — No clear routing signals

**Key Features:**
- Keyword-based signal groups with configurable base confidence (0.60–0.95)
- Per-hit confidence boost to reward multiple matching keywords
- Boundary-aware word matching (e.g., "hi" ≠ "this")
- Memory scope assignment (official_site / document / general_chat)
- Source type hints for retriever filtering

**Example:**
```python
from rag.query_router import classify_query_route

route = classify_query_route("What are the admission fees?")
# → Route.FAQ with "official_site" source and 0.72 confidence
```

**Configuration:** Edit keyword sets and confidence parameters in `_OFFICIAL_SITE`, `_DOCUMENT`, `_FAQ`, etc. Signal groups.

---

### 2. Retriever (`retriever.py`)

**Purpose:** Performs hybrid semantic + keyword search over ChromaDB vector store.

**Retrieval Methods:**
- **Dense (Semantic):** Embedding-based similarity search via ChromaDB
- **BM25 (Keyword):** Full-text ranking with term frequency + inverse document frequency
- **Hybrid:** Weighted fusion of dense and BM25 scores

**Key Optimizations:**

1. **BM25 Index Caching**
   - Built once per collection snapshot
   - Invalidated when new documents are ingested
   - Avoids per-query full corpus scans

2. **Embedding Caching**
   - LRU cache (512 entries) by query text
   - Replace with Redis/Memcached for production

3. **Score Fusion** (Fixed in recent update)
   - Normalizes BM25 scores across all candidates (not per-result-set)
   - Preserves IDF scale for accurate weighting
   - Hybrid score = `HYBRID_DENSE_WEIGHT * dense + (1 - HYBRID_DENSE_WEIGHT) * bm25`

4. **Deduplication & Metadata Enrichment**
   - Merges duplicate candidates from dense/BM25
   - Keeps max component scores
   - Consolidates metadata (heading, page_index, source_url)

5. **Page-Based Ranking**
   - Groups chunks by document page
   - Ranks pages by: best score (60%), average score (30%), coverage (10%)
   - Two-pass selection: one chunk per group, then fill remaining slots

6. **List Query Boosting**
   - Detects "What courses are available?" style queries
   - Boosts page_index, BM25, and heading signals
   - Useful for FAQ/catalog retrieval

7. **HyDE (Hypothetical Document Embeddings)**
   - When top score < HYDE_TRIGGER_SCORE, generates hypothetical answer
   - Re-retrieves against HyDE answer with blended scoring
   - Optional, configurable temperature/token budget

8. **Full-Page Expansion**
   - When FULL_PAGE_RAG_ENABLED, stitches chunks into full pages
   - Cleans PDF artifacts and truncates to max_chars
   - Better context for LLM, reduces token waste

**Key Constants:**
- `MIN_SCORE_THRESHOLD: 0.20` — Drops low-confidence chunks
- `_BM25_K1, _BM25_B` — BM25 algorithm tuning
- `_PAGE_RANK_*_WEIGHT` — Page ranking formula weights
- `_DENSE_MULTIPLIER_*, _BM25_MULTIPLIER_*` — Candidate fetch multipliers

**API:**
```python
from rag.retriever import retrieve_context, invalidate_bm25_index

chunks = retrieve_context(
    query="What are scholarship eligibility criteria?",
    top_k=5,
    source_type="official_site",  # optional filter
    doc_id="doc_123",               # optional single-doc retrieval
)
# Returns: [{"text": "...", "source": "...", "score": 0.85, ...}, ...]

# Call when documents are ingested:
invalidate_bm25_index()
```

**Configuration (tests/config.py):**
```python
RETRIEVAL_MODE = "hybrid"              # "dense" or "hybrid"
HYBRID_DENSE_WEIGHT = 0.5              # 0.0–1.0, controls score blend
TOP_K_RESULTS = 5                      # Results returned to generator

HYDE_ENABLED = False
HYDE_TRIGGER_SCORE = 0.4               # Trigger if top score < this
HYDE_TEMPERATURE = 0.5
HYDE_MAX_TOKENS = 100
HYDE_MAX_CHARS = 500
HYDE_SCORE_BLEND = 0.3

FULL_PAGE_RAG_ENABLED = False
FULL_PAGE_MAX_CHARS_PER_PAGE = 4000
```

---

### 3. Query Expansion (`query_expansion.py`)

**Purpose:** Generates semantically diverse query variants and merges results with Reciprocal Rank Fusion.

**Strategy:**
1. Call LLM once to generate N rewrite variants
2. Retrieve candidates for each variant + original
3. Merge with Reciprocal Rank Fusion (RRF) so no single variant dominates

**Why RRF?**
- Different query texts embed into different score ranges
- RRF is rank-based, scale-invariant, robust to score drift
- Efficient: O(variants × candidates) with small constants
- Handles duplicates cleanly (sums contributions)

**RRF Formula:**
```
rrf_score(candidate) = Σ 1.0 / (k + rank)
  where k is the RRF constant (default 60)
  and rank is the candidate's position in each ranked list
```

**API:**
```python
from rag.query_expansion import expand_and_retrieve

candidates = expand_and_retrieve(
    query="What are admission requirements?",
    retrieve_fn=_retrieve_candidates_for_text,
    retrieve_kwargs={...},
    trace=pipeline_trace,
)
# Returns RRF-merged list sorted by rrf_score descending
```

**Configuration (tests/config.py):**
```python
QUERY_EXPANSION_ENABLED = False              # Feature flag
QUERY_EXPANSION_N = 3                        # Rewrites per query
QUERY_EXPANSION_MAX_TOKENS = 150
QUERY_EXPANSION_RRF_K = 60                  # RRF constant
QUERY_EXPANSION_TEMPERATURE = 0.3
```

---

### 4. Generator (`generator.py`)

**Purpose:** Generates LLM responses with conversation memory caching and fallback handling.

**Generation Modes:**

1. **`generate_response(query, context, ...)`**
   - Takes retrieved context + query
   - Checks conversation memory first (semantic cache)
   - Generates via configured LLM provider
   - Falls back to context-only mode if all providers fail
   - Returns memory hit or stores new response

2. **`generate_response_direct(query, ...)`**
   - No retrieval context (general chat mode)
   - Useful for off-topic questions
   - Still checks memory, still stores responses

**Memory Caching:**
- Checks semantic memory before LLM call
- If hit: returns cached response + memory_id (fast)
- If miss: generates response via LLM + stores in memory

**Provider Fallback Chain:**
- Built by ProviderManager based on mode (local_only / cloud_only / hybrid)
- Tries primary → fallback → (hybrid only) Ollama
- Returns first successful response
- Falls back to context-only if all fail

**Fallback Responses:**
- If context has docs: returns formatted context as answer
- If no docs: suggests admin upload docs + configure LLM

**API:**
```python
from rag.generator import generate_response

result = generate_response(
    query="What is the scholarship deadline?",
    context=format_context_for_llm(chunks),
    user_id="student_123",
    sources=chunks,
)
# Returns: {"response": "...", "from_memory": False, "memory_id": "..."}

if result["from_memory"]:
    print("Cached response returned")
else:
    print(f"Generated response stored as {result['memory_id']}")
```

**Configuration (tests/config.py):**
```python
MODEL_TEMPERATURE = 0.7
MODEL_MAX_TOKENS = 500
SYSTEM_PROMPT = "You are a helpful institutional AI assistant..."
CONV_ENABLED = True                  # Enable memory caching
```

---

### 5. Conversation History (`conversation_history.py`)

**Purpose:** Maintains per-user conversation context for follow-up questions.

**Features:**
- Thread-safe in-memory storage (per session)
- Automatic trimming to last N Q&A pairs
- Timeout-based cleanup (30 min idle)
- Formats history for LLM prompts

**Use Case:** User asks "Tell me more about scholarships" → system includes prior scholarship context.

**API:**
```python
from rag.conversation_history import add_turn, get_history, format_history_for_prompt

# After each exchange:
add_turn(user_id="student_123", query="Q", response="A")

# When generating next response:
history_str = format_history_for_prompt("student_123")
# Returns: "PREVIOUS CONVERSATION:\n  User [1]: ...\n  AstroBot [1]: ...\n"

# Clear on logout:
clear_history("student_123")
```

**Configuration:**
```python
MAX_HISTORY_TURNS = 5                 # Keep last 5 Q&A pairs
HISTORY_TIMEOUT_SECONDS = 1800        # 30 min idle timeout
```

---

### 6. Provider Manager (`providers/manager.py`)

**Purpose:** Routes LLM requests through configured providers with fallback chain.

**Providers Supported:**
- **Ollama** (local, free) — On-device inference via ollama/llama2, etc.
- **Groq** (cloud, fast) — Groq LLM API with fast inference
- **Gemini** (cloud, capable) — Google Gemini API

**Modes:**
- `local_only` → Ollama only
- `cloud_only` → Primary cloud → fallback cloud
- `hybrid` → Primary → fallback → Ollama (always last resort)

**Configuration (tests/config.py):**
```python
LLM_MODE = "hybrid"                      # or "local_only", "cloud_only"
LLM_PRIMARY_PROVIDER = "ollama"          # "ollama", "groq", "gemini"
LLM_FALLBACK_PROVIDER = "groq"           # or "none"

# Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama2"

# Groq
GROQ_API_KEY = "..."
GROQ_MODEL = "mixtral-8x7b-32768"

# Gemini
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-pro"
```

**API:**
```python
from rag.providers.manager import get_manager, reset_manager

mgr = get_manager()
response = mgr.generate(
    system_prompt="...",
    user_message="...",
    temperature=0.7,
    max_tokens=500,
)

# After config changes:
reset_manager()  # Re-reads config on next get_manager() call
```

---

## Data Flow

```
User Query
    ↓
[Query Router] — Routes to institutional/general/FAQ/etc.
    ↓
[Query Expansion] — Optional semantic variants
    ↓
[Retriever] — Hybrid search (dense + BM25)
    │  ├→ Dense candidates (ChromaDB embeddings)
    │  ├→ BM25 candidates (keyword index)
    │  └→ Merge & rank by page
    ↓
[Conversation History] — Include prior turns if exists
    ↓
[Generator] — LLM response with memory caching
    │  ├→ Check memory first
    │  ├→ Try provider chain (primary → fallback → Ollama)
    │  └→ Store in memory on success
    ↓
Response to User
```

---

## Integration Points

### Document Ingestion
```python
# When new document uploaded:
from ingestion.embedder import embed_and_store
from rag.retriever import invalidate_bm25_index

embed_and_store(pdf_bytes, metadata={...})
invalidate_bm25_index()  # ← Critical: clear BM25 cache
```

### FastAPI Endpoints
```python
# Typical RAG endpoint integration (api_server.py):
@app.post("/api/chat")
async def chat(query: str, user_id: str):
    route = classify_query_route(query)
    
    if route.mode == Route.GENERAL_CHAT:
        result = generate_response_direct(query, user_id=user_id)
    else:
        chunks = retrieve_context(query, top_k=5)
        context = format_context_for_llm(chunks)
        result = generate_response(query, context, user_id=user_id, sources=chunks)
    
    citations = get_source_citations(chunks) if chunks else ""
    return {"response": result["response"], "citations": citations}
```

### Conversation History
```python
# After each response:
from rag.conversation_history import add_turn

add_turn(user_id="student_123", query=original_query, response=result["response"])
```

### Observability / Tracing
```python
# Optional integration with Langfuse or OpenTelemetry:
from rag.observability.langfuse_client import get_langfuse_trace

trace = get_langfuse_trace()
chunks = retrieve_context(query, trace=trace)
# trace automatically captures retrieval stats, timings, etc.
```

---

## Features & Capabilities

### 1. Intelligent Query Routing
Routes queries based on keyword signals, not rigid patterns. Flexible, maintainable, extensible.

### 2. Hybrid Retrieval
Combines semantic search (captures meaning) + keyword search (captures exact terms). Better coverage than either alone.

### 3. Conversation Memory (Semantic Cache)
Repeated questions return instant cached responses. Reduces LLM latency + cost.

### 4. Query Expansion
Generates diverse paraphrases, retrieves for each, merges with RRF. Improves recall on paraphrased questions.

### 5. Full-Page Context
Expands chunk hits into full pages. Richer context for LLM without token waste.

### 6. HyDE Retrieval
Generates hypothetical answers, re-retrieves against them. Improves retrieval on complex questions.

### 7. LLM Provider Fallback
Seamlessly switches providers (Ollama → Groq → Gemini). Always-on service, even if primary fails.

### 8. Follow-up Context
Maintains per-user conversation history. LLM can handle "Tell me more", "And the fees?", etc.

### 9. Observability
Optional integration with Langfuse for retrieval metrics, latency tracking, debugging.

---

## Configuration (tests/config.py)

Key settings:

```python
# Routing
ENABLE_GENERAL_CHAT_ROUTING = True          # Enable general chat route

# Retrieval
RETRIEVAL_MODE = "hybrid"                   # "dense" or "hybrid"
HYBRID_DENSE_WEIGHT = 0.5                   # Score blend
TOP_K_RESULTS = 5

FULL_PAGE_RAG_ENABLED = False
FULL_PAGE_MAX_CHARS_PER_PAGE = 4000

HYDE_ENABLED = False
HYDE_TRIGGER_SCORE = 0.4

# Query Expansion
QUERY_EXPANSION_ENABLED = False
QUERY_EXPANSION_N = 3

# Generation
MODEL_TEMPERATURE = 0.7
MODEL_MAX_TOKENS = 500
CONV_ENABLED = True

# LLM Provider
LLM_MODE = "hybrid"
LLM_PRIMARY_PROVIDER = "ollama"
LLM_FALLBACK_PROVIDER = "groq"
```

---

## Recent Fixes & Improvements (April 8–9, 2026)

1. **Score Fusion Fix**
   - BM25 scores now normalized across ALL candidates, not per-result-set
   - IDF scale preserved, hybrid scores accurate

2. **Retrieval Pipeline Trace Hooks**
   - `trace.event()` and `trace.record_search()` now properly called
   - Full integration with Langfuse/OpenTelemetry

3. **Magic Literal Cleanup**
   - All hardcoded constants extracted to module top
   - Easier to tune, self-documenting

4. **Candidate Deduplication**
   - `_merge_candidates()` split into deduplicate/fuse/label
   - No mid-loop mutation bugs
   - Clear separation of concerns

5. **Query Expansion Integration**
   - RRF-based merging of expansion variants
   - Scales well, avoids variant dominance

---

## Testing & Debugging

### Debug Retrieval
```python
from rag.retriever import retrieve_context

chunks = retrieve_context("What is the placement rate?", top_k=10)
for c in chunks:
    print(f"Score: {c['score']:.3f} | Method: {c['retrieval_method']} | Source: {c['source']}")
```

### Debug Routing
```python
from rag.query_router import classify_query_route

route = classify_query_route("Tell me a joke")
print(f"Route: {route.mode} | Confidence: {route.confidence} | Reason: {route.reason}")
```

### Debug Memory
```python
from rag.memory import query_memory
from rag.conversation_history import get_history_stats

# Check semantic cache hit
result = query_memory("What are fees?", user_id="student_123")
print(f"Cache hit: {result is not None}")

# Check conversation history stats
stats = get_history_stats()
print(f"Active sessions: {stats['active_sessions']}")
```

---

## Performance Notes

- **Retrieval:** 50–150ms (hybrid search + page ranking)
- **Generation:** 500–2000ms (LLM call depends on provider)
- **Memory hit:** <5ms (instant cached lookup)
- **BM25 Index:** Built once, cached in-memory (500K chunks ~ 20MB)
- **Embedding Cache:** LRU 512 entries (drop to Redis for multi-instance)

---

## Future Enhancements

- [ ] Redis embedding cache for distributed deployments
- [ ] Async retrieval for high-traffic scenarios
- [ ] Fine-tuned embeddings for domain-specific queries
- [ ] User feedback loop for retrieval ranking (RLHF)
- [ ] Document clustering for better page ranking
- [ ] Multi-language support
