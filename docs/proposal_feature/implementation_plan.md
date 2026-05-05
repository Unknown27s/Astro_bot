# AstroBot: Startup Optimization, Tool-Calling Fix & Unified Upload

Three interconnected improvements to the AstroBot pipeline: diagnose slow startup, fix the pre-session LLM router overhead, and implement a single-sheet unified upload for student + marks data.

---

## Issue 1: Why the Python API Layer Takes So Long to Start

### Root Cause Analysis

The startup chain in [api_server.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/api_server.py) executes the following **synchronous, blocking imports** at module load time:

| Step | What Happens | Estimated Time |
|------|-------------|----------------|
| 1. `from log_config import ...` | Imports `tests.config` → imports `config` → `load_dotenv()`, parses all env vars | ~50ms |
| 2. `from log_config.sentry_config import init_sentry` | Imports `sentry_sdk` + FastAPI/Starlette integrations | ~200-500ms |
| 3. `init_sentry()` | Initializes Sentry SDK, sets up hooks | ~100ms |
| 4. `from database.db import ...` (14 functions) | Imports `sqlite3`, creates connection, compiles queries | ~100ms |
| 5. `init_db()` | Runs `CREATE TABLE IF NOT EXISTS` for all tables | ~50ms |
| 6. `from middleware.rate_limiter import ...` | Imports `slowapi`, creates `Limiter` instance | ~100ms |
| 7. `from rag.observability import ...` | Imports Langfuse client + observability system | ~200ms |
| 8. `from tests.config import ...` | Re-imports config (already cached, but chain is long) | ~20ms |
| 9. `init_institute_db()` | Creates institute_data.db tables | ~50ms |
| 10. `FastAPI()` + middleware setup | Creates app, adds CORS/error/tracking middleware | ~50ms |

**But the real killers are the lazy-imported heavy modules loaded on first request:**

| Module | Trigger | Time Cost |
|--------|---------|-----------|
| `sentence_transformers.SentenceTransformer` | First chat query → `retrieve_context` → `generate_embeddings` | **3-8 seconds** (model load) |
| `chromadb.PersistentClient` | First chat query → `get_collection()` | **1-3 seconds** |
| `rag.providers.manager.ProviderManager` | First call to `get_tool_for_query()` or `generate_response()` | **0.5-2s** (instantiates all 3 LLM providers) |
| `FlashRank` reranker (if enabled) | First retrieval | **1-2 seconds** |
| `pandas` (in `timetable_parser`) | First timetable upload | **1-2 seconds** |

### Total First-Request Latency: **~8-15 seconds**

The API server *appears* to start fast (uvicorn says "ready"), but the **first actual request** triggers all the lazy-loaded ML models, which is what feels "slow".

### Proposed Fix: Eager Background Warm-Up

Add a `@app.on_event("startup")` handler that warms up the heavy singletons in a background thread, so they're ready before the first user request arrives.

#### [MODIFY] [api_server.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/api_server.py)

Add a startup event after the middleware setup (~line 97) that pre-loads:
- The SentenceTransformer embedding model
- The ChromaDB client + collection
- The LLM ProviderManager singleton

```python
@app.on_event("startup")
async def warmup_models():
    """Pre-load heavy ML models so the first request isn't slow."""
    import threading

    def _warmup():
        import time
        start = time.time()
        logger.info("🔥 Warming up models in background...")

        # 1. Embedding model (heaviest — 3-8s)
        try:
            from ingestion.embedder import get_embedding_model, get_collection
            get_embedding_model()
            get_collection()
            logger.info("✅ Embedding model + ChromaDB ready")
        except Exception as e:
            logger.warning(f"⚠️ Embedding warmup failed: {e}")

        # 2. LLM Provider Manager
        try:
            from rag.providers.manager import get_manager
            get_manager()
            logger.info("✅ LLM Provider Manager ready")
        except Exception as e:
            logger.warning(f"⚠️ Provider warmup failed: {e}")

        elapsed = time.time() - start
        logger.info(f"🚀 Warmup complete in {elapsed:.1f}s")

    threading.Thread(target=_warmup, daemon=True).start()
```

This way:
- Uvicorn starts immediately (no blocking)
- Models load in the background within ~5-8s
- By the time a user actually opens the chat, everything is ready

---

## Issue 2: Pre-Session LLM Router Check — Fix & Optimize

### Problem Identified

The [llm_router.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/rag/llm_router.py) `get_tool_for_query()` makes an **LLM call on EVERY single query** just to decide whether to use the SQL agent or not. This adds **1-3 seconds of latency** to every chat request, even for simple greetings like "hello".

> [!WARNING]
> **This is redundant!** The [query_router.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/rag/query_router.py) already has keyword-based routing with `Route.TIMETABLE` and `Route.STUDENT_MARKS` that correctly identifies SQL-agent queries — and it runs in **<1ms** (pure regex/keyword matching).

### Current Flow (Wasteful)
```
User Query → query_router (keyword, <1ms) → llm_router (LLM call, 1-3s) → Decision
```

The `query_router` already detects timetable/marks queries, but then `llm_router` is called ANYWAY and sometimes **contradicts** the keyword router, causing confusion.

### Proposed Fix: Replace LLM Router with Heuristic Pre-Check

Instead of calling the LLM to decide tool routing, use the existing `query_router` result. The `classify_query_route()` already returns `Route.TIMETABLE` or `Route.STUDENT_MARKS` — those should directly trigger the SQL agent.

#### [MODIFY] [llm_router.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/rag/llm_router.py)

Replace the LLM-based routing with a fast heuristic check that uses the existing query_router signals, plus additional keyword patterns for edge cases the keyword router might miss:

```python
"""
Fast heuristic tool router for AstroBot.

Replaces the previous LLM-based router that added 1-3s latency per query.
Uses keyword signals (consistent with query_router.py) to decide whether 
a query needs the SQL agent.
"""

import logging

logger = logging.getLogger(__name__)

# Keywords that strongly indicate a database query
_SQL_KEYWORDS = frozenset({
    "timetable", "schedule", "class room", "period",
    "what class", "which class", "next class",
    "mark", "marks", "score", "scores", "grade", "grades",
    "result", "results", "cgpa", "gpa", "semester",
    "internal", "external", "marks sheet",
    "roll no", "roll number", "student id",
    "subject code", "topper", "average marks",
    "who scored", "who got", "highest marks", "lowest marks",
})

def get_tool_for_query(query: str) -> str:
    """
    Returns 'sql_agent' if the query needs database lookup, else 'none'.
    Pure keyword-based — runs in <1ms with zero LLM overhead.
    """
    text = " ".join(query.lower().split())
    
    for keyword in _SQL_KEYWORDS:
        if keyword in text:
            logger.info(f"Tool Router: sql_agent (matched: '{keyword}')")
            return "sql_agent"
    
    return "none"
```

#### [MODIFY] [api_server.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/api_server.py) — Chat Endpoints

Also fix a logic issue: currently the `selected_tool` check runs **before** the `route` check, but both the `route.mode` and `selected_tool` can independently detect SQL queries. This can cause conflicts. 

Change the logic so `query_router` result is checked first — if it says `TIMETABLE` or `STUDENT_MARKS`, go directly to SQL agent without calling `get_tool_for_query()`:

In both `/api/chat` and `/api/chat/stream`, change the routing logic to:

```python
# Use the route from query_router as primary signal
if route.mode in ("timetable", "student_marks"):
    selected_tool = "sql_agent"
else:
    selected_tool = get_tool_for_query(req.query)
```

#### [MODIFY] [views/chat.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/views/chat.py) — Same Fix for Streamlit

Apply the same routing logic fix to the Streamlit chat view.

---

## Issue 3: Unified Single-Sheet Upload (React UI + Backend + Sample Data)

### Problem

Currently the admin has to upload **two separate files** — one for student details, one for marks. This is inconvenient. The user wants a **single CSV/XLSX** that contains both student info and marks data on each row.

### Good News

The backend function `upsert_unified_data()` in [institute_db.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/database/institute_db.py#L111-L171) already exists and handles this perfectly — it upserts students and inserts/updates marks in one pass. But:
- ❌ There's no API endpoint that calls it
- ❌ There's no parser for unified CSV format
- ❌ The React UI doesn't have a unified upload option

### Proposed Changes

#### [MODIFY] [student_parser.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/ingestion/student_parser.py)

Add a new `parse_unified_csv()` function that parses a single sheet with both student and marks columns:

```python
def parse_unified_csv(content: bytes, file_ext: str) -> list[dict]:
    """Parse unified student+marks data from CSV/XLSX.
    Expected columns: roll_no, name, email, phone, department, semester,
                      subject_code, subject_name, subject_semester, 
                      internal_marks, external_marks, grade
    """
    # Same CSV/XLSX parsing logic as existing functions
```

---

#### [MODIFY] [api_server.py](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/api_server.py)

Add a new endpoint `POST /api/admin/upload/unified` that:
1. Accepts a single CSV/XLSX file
2. Parses it with `parse_unified_csv()`
3. Calls `upsert_unified_data()` from `institute_db.py`

```python
@app.post("/api/admin/upload/unified")
@limiter.limit("10/minute")
def api_upload_unified(request, file, uploaded_by):
    ...
```

---

#### [MODIFY] [api.js](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/react-frontend/src/services/api.js)

Add the `uploadUnifiedData()` API function.

---

#### [MODIFY] [StudentMarksUpload.jsx](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/react-frontend/src/components/admin/StudentMarksUpload.jsx)

Redesign the component to have **three tabs**:
1. **📊 Unified Upload** (default, highlighted) — single file with all data
2. **👤 Students Only** — existing student upload  
3. **📝 Marks Only** — existing marks upload

The unified upload tab will be the primary, recommended flow.

---

#### [MODIFY] [StudentDataPage.jsx](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/react-frontend/src/pages/admin/StudentDataPage.jsx)

Update the info cards and instructions to reflect the unified upload as the primary method. Update sample data links.

---

#### [NEW] [unified_student_data.csv](file:///d:/Harish%20Kumar/Project/Astro_botV2/Astro_bot/react-frontend/public/sample_data/unified_student_data.csv)

Create a sample CSV file with the unified format:

```csv
roll_no,name,email,phone,department,semester,subject_code,subject_name,subject_semester,internal_marks,external_marks,grade
CS001,Rahul Kumar,rahul.kumar@rit.ac.in,9876543210,Computer Science,4,CS401,Data Structures & Algorithms,4,18,72,A
CS001,Rahul Kumar,rahul.kumar@rit.ac.in,9876543210,Computer Science,4,CS402,Database Management Systems,4,17,68,A
...
```

Each row = one student + one subject's marks. Same student appears multiple times (once per subject). The `upsert_unified_data()` function already handles deduplication.

---

## Summary of All File Changes

| File | Change Type | What Changes |
|------|------------|--------------|
| `api_server.py` | MODIFY | Add startup warmup + fix routing logic + add `/api/admin/upload/unified` endpoint |
| `rag/llm_router.py` | MODIFY | Replace LLM-based routing with fast keyword heuristic |
| `views/chat.py` | MODIFY | Fix routing logic to use query_router result for SQL agent |
| `ingestion/student_parser.py` | MODIFY | Add `parse_unified_csv()` function |
| `react-frontend/.../StudentMarksUpload.jsx` | MODIFY | Add tabbed UI with unified upload as primary |
| `react-frontend/.../StudentDataPage.jsx` | MODIFY | Update info cards + instructions for unified upload |
| `react-frontend/src/services/api.js` | MODIFY | Add `uploadUnifiedData()` function |
| `react-frontend/public/sample_data/unified_student_data.csv` | NEW | Sample unified CSV file |

## Verification Plan

### Automated Tests
1. Start the Python API server and verify startup warmup logs appear
2. Measure first-request latency (should be <2s vs previous 8-15s)
3. Test the `/api/admin/upload/unified` endpoint with the sample CSV
4. Test chat queries like "show marks for CS001" to verify SQL agent routing works without LLM overhead

### Manual Verification
1. Open the React admin panel → Student Data page
2. Verify the new tabbed upload UI renders correctly
3. Download the unified sample CSV
4. Upload it via the unified upload tab
5. Verify students and marks appear in the preview table
6. Ask a question in chat like "What are Rahul's marks?" and verify SQL agent responds correctly
