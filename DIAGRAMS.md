# IMS AstroBot — Visual Diagrams & Flows

## 1. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                               │
├──────────────────┬─────────────────┬────────────────┬───────────────┤
│  Streamlit UI    │   FastAPI       │  React Web UI  │  Spring Boot  │
│  (app.py)        │   REST API      │  (Vite)        │  Proxy        │
│  • Chat          │   (api_server)  │  • Modern UX   │  • JWT auth   │
│  • Admin dash    │   • JSON        │  • Responsive  │  • WebClient  │
│  • Settings      │     endpoints   │  • SPA         │  • caching    │
└──────────┬───────┴────────┬────────┴────────┬───────┴───────┬───────┘
           │                │                 │                │
           └────────────────┼─────────────────┴────────────────┘
                            │
        ┌───────────────────▼─────────────────────────┐
        │       APPLICATION LAYER                      │
        ├────────────────┬──────────────┬──────────────┤
        │  Auth Module   │   RAG Core   │ Admin Views  │
        │ (auth.py)      │  ┌───────┐   │ (admin.py)   │
        │ • Sessions     │  │Retriever   │ • Docs mgmt  │
        │ • SHA-256      │  │(search)    │ • Users mgmt │
        │   hashing      │  ├───────┤   │ • AI config  │
        │ • Role-based   │  │Generator   │ • Health     │
        │   access       │  │(LLM call)  │              │
        │                │  └───────┘   │              │
        └────────────────┼──────────────┼──────────────┘
                         │              │
        ┌────────────────┴──────────────┴──────────────┐
        │       PROCESSING LAYER                       │
        └────────────────┬──────────────┬──────────────┘
                         │              │
        ┌────────────────▼──────────────▼──────────────┐
        │        DATA & STORAGE LAYER                  │
        ├───────────────────┬──────────────────────────┤
        │  Ingestion Module │   Data Storage           │
        │  ┌───────────┐    │ ┌──────────────────────┐│
        │  │Parser     │    │ │ChromaDB              ││
        │  │(PDF,DOCX) │    │ │• Vectors (384-dim)   ││
        │  ├───────────┤    │ │• Metadata            ││
        │  │Chunker    │    │ │• Top-K search        ││
        │  │(hybrid)   │    │ └──────────────────────┘│
        │  ├───────────┤    │ ┌──────────────────────┐│
        │  │Embedder   │    │ │SQLite Database       ││
        │  │(sentence- │    │ │• users               ││
        │  │ transform)│    │ │• documents           ││
        │  └───────────┘    │ │• query_logs          ││
        │                   │ └──────────────────────┘│
        └───────────────────┴──────────────────────────┘
                         │
        ┌────────────────▼──────────────┐
        │   LLM PROVIDER LAYER          │
        ├──────────┬──────────┬─────────┤
        │  Ollama  │  Grok    │  Gemini │
        │ (Local)  │ (Cloud)  │ (Cloud) │
        │          │          │         │
        │ :11434   │ X-RPC    │  REST   │
        └──────────┴──────────┴─────────┘
```

## 2. RAG Pipeline Flow Diagram

```
DOCUMENT UPLOAD FLOW:
══════════════════════════════════════════════════════════════

    ┌─────────────────┐
    │ Admin uploads   │
    │ PDF/DOCX file   │
    └────────┬────────┘
             │ file_bytes
             ▼
    ┌─────────────────┐
    │  Save to disk   │
    │  data/uploads/  │
    └────────┬────────┘
             │ file_path
             ▼
    ┌──────────────────────────────┐
    │ 1. PARSER (ingestion/       │
    │    parser.py)                │
    │ ├─ PyPDF2 (PDF)             │
    │ ├─ python-docx (DOCX)       │
    │ ├─ openpyxl (Excel)         │
    │ └─ beautifulsoup4 (HTML)    │
    │                              │
    │ Raw text extracted           │
    └────────┬─────────────────────┘
             │ "Annual leave is 30 days. Medical leave..."
             ▼
    ┌──────────────────────────────┐
    │ 2. CHUNKER (ingestion/       │
    │    chunker.py)                │
    │                              │
    │ Strategy 1: Split by heading │
    │  "## Leave Policy"           │
    │  "## Medical Leave"          │
    │                              │
    │ Strategy 2: Fixed size       │
    │  500 chars/chunk             │
    │  50 char overlap             │
    │                              │
    │ Result: 4–6 chunks with      │
    │ {text, metadata}             │
    └────────┬─────────────────────┘
             │ chunks = [{text, metadata}, ...]
             ▼
    ┌──────────────────────────────┐
    │ 3. EMBEDDER (ingestion/      │
    │    embedder.py)               │
    │                              │
    │ Load model:                  │
    │ all-MiniLM-L6-v2             │
    │ (384 dimensions)             │
    │                              │
    │ Encode each chunk:           │
    │ text → 384-dim vector        │
    │                              │
    │ Store in ChromaDB:           │
    │ • embedding: [...]           │
    │ • metadata: {source, head}   │
    │ • document: original text    │
    └────────┬─────────────────────┘
             │ success
             ▼
    ┌──────────────────────────────┐
    │ 4. DATABASE (database/       │
    │    db.py)                     │
    │                              │
    │ INSERT documents table:      │
    │ • document_id                │
    │ • filename                   │
    │ • chunk_count = 5            │
    │ • status = 'processed'       │
    │ • uploaded_by = user_id      │
    │ • uploaded_at = ISO time     │
    └────────┬─────────────────────┘
             │
             ▼
         ✅ "Document ready"


QUERY PROCESSING FLOW:
══════════════════════════════════════════════════════════════

    ┌──────────────────────┐
    │ User asks question:  │
    │ "What is annual      │
    │  leave policy?"      │
    └──────────┬───────────┘
               │ query text
               ▼
    ┌──────────────────────────────┐
    │ RETRIEVER (rag/retriever.py) │
    │                              │
    │ Step 1: Embed question       │
    │  all-MiniLM-L6-v2            │
    │  "..." → [384-dim vector]    │
    │                              │
    │ Step 2: Search ChromaDB      │
    │  Vector similarity search    │
    │  Cosine distance             │
    │  Return top-5 chunks         │
    │                              │
    │ Step 3: Format context       │
    │  [Source: file > heading]    │
    │  Join with \n\n             │
    │                              │
    │ Result:                      │
    │ [{text, source, score}, ...] │
    │  score = 0–1 (similarity)    │
    └──────────┬───────────────────┘
               │ context_string
               ▼
    ┌──────────────────────────────┐
    │ GENERATOR (rag/generator.py) │
    │                              │
    │ Build prompt:                │
    │ system: "You are AstroBot.." │
    │ user: "Context:\n{ctx}       │
    │        Question: {query}"    │
    │                              │
    │ Parameters:                  │
    │ • temperature: 0.3           │
    │ • max_tokens: 512            │
    └──────────┬───────────────────┘
               │ (system_prompt, user_msg, temp, tokens)
               ▼
    ┌───────────────────────────────────────────┐
    │ PROVIDER MANAGER (rag/providers/manager.py)
    │                                            │
    │ Get provider chain from config:           │
    │ [Primary] → [Fallback] → [Ollama]        │
    │                                            │
    │ TRY PRIMARY:                              │
    │ ├─ Grok API call                         │
    │ ├─ if fails: next                        │
    │ └─ if success: return response           │
    │                                            │
    │ TRY FALLBACK:                             │
    │ ├─ Gemini API call                       │
    │ ├─ if fails: next                        │
    │ └─ if success: return response           │
    │                                            │
    │ TRY OLLAMA:                               │
    │ ├─ Ollama REST API                       │
    │ ├─ if fails: next                        │
    │ └─ if success: return response           │
    │                                            │
    │ ALL FAILED:                               │
    │ └─ return None (fallback_response)       │
    └───────────────────────────────────────────┘
               │ LLM response or None
               ▼
    ┌───────────────────────────────────────────┐
    │ Back to GENERATOR (fallback)              │
    │                                            │
    │ if response:                              │
    │   return response                         │
    │ else:                                     │
    │   # LLM failed, use context only         │
    │   return "Based on documents:\n{context}"│
    └───────────────────────────────────────────┘
               │ final response
               ▼
    ┌───────────────────────────────────────────┐
    │ UI renders response (views/chat.py)       │
    │                                            │
    │ Display:                                  │
    │ • Main response                           │
    │ • Source citations                        │
    │ • Time taken (ms)                         │
    │ • Relevance scores (%)                    │
    └───────────────────────────────────────────┘
               │
               ▼
    ┌───────────────────────────────────────────┐
    │ LOG TO DATABASE (database/db.py)          │
    │                                            │
    │ INSERT query_logs:                        │
    │ • user_id, username                       │
    │ • query_text                              │
    │ • response_text                           │
    │ • sources: JSON                           │
    │ • response_time_ms                        │
    │ • created_at: ISO time                    │
    └───────────────────────────────────────────┘
```

## 3. Provider Fallback Chain Diagram

```
CONFIG: LLM_MODE=hybrid
        LLM_PRIMARY_PROVIDER=grok
        LLM_FALLBACK_PROVIDER=gemini

                      ┌──────────┐
                      │ Generate │
                      │ Request  │
                      └────┬─────┘
                           │
                ┌──────────▼──────────┐
                │ PROVIDER MANAGER    │
                │ _get_chain()        │
                │ Returns:            │
                │ [grok, gemini,      │
                │  ollama]            │
                └──────────┬──────────┘
                           │
        ┌──────────────────▼─────────────────┐
        │ TRY: GROK (Primary Cloud)          │
        ├────────────────────────────────────┤
        │ POST https://api.groq.com/...      │
        │ with GROK_API_KEY                  │
        └──────────┬──────────────────────────┘
                   │
           ┌───────▼─────────┐
           │ Response?       │
           └───┬─────────┬───┘
         YES ◀━┘         └━▶ NO
             │                │
        ✅ SUCCESS        ┌───▼────────────────────┐
             │            │ TRY: GEMINI (Fallback) │
             │            ├────────────────────────┤
             │            │ POST googleapis...     │
             │            │ with GEMINI_API_KEY   │
             │            └───┬───────────────────┘
             │                │
             │        ┌───────▼──────────┐
             │        │ Response?        │
             │        └───┬───────┬──────┘
             │        YES◀─┘       └─━NO
             │            │            │
             │       ✅ SUCCESS   ┌────▼────────────────────┐
             │            │       │ TRY: OLLAMA (Last Resort)
             │            │       ├─────────────────────────┤
             │            │       │ POST localhost:11434    │
             │            │       │ (local, always works)   │
             │            │       └────┬────────────────────┘
             │            │            │
             │            │    ┌───────▼──────────┐
             │            │    │ Response?        │
             │            │    └───┬───┬──────┬───┘
             │            │   YES ◀─┘   │     └━ NO
             │            │    ✅      │
             │            │    SUCCESS │
             │            │            │
             │            │      ┌─────▼──────────────────┐
             │            │      │ ALL FAILED             │
             │            │      │ Return _fallback_resp()
             │            │      │ = context-only answer  │
             │            │      └─────┬──────────────────┘
             │            │            │
             └────────────┴────────────┬┘
                                       │
                        ┌──────────────▼─────────────┐
                        │ RETURN RESPONSE            │
                        │ (from first successful     │
                        │  provider)                 │
                        └────────────────────────────┘
```

## 4. Database Schema Diagram

```
┌─────────────────────────────────────┐
│ USERS TABLE                         │
├─────────┬──────┬────────────────────┤
│ id*     │ TEXT │ UUID (PK)          │
│ username│ TEXT │ UNIQUE             │
│ pwd_hash│ TEXT │ SHA-256            │
│ role    │ TEXT │ admin/faculty/...  │
│ full_name TEXT │                    │
│ created_at TEXT│ ISO time           │
│ is_active INT  │ 0 or 1             │
└────┬────────────────────────────────┘
     │
     │ 1:N
     │
     ▼
┌─────────────────────────────────────┐
│ DOCUMENTS TABLE                     │
├──────────┬──────┬──────────────────┤
│ id*      │ TEXT │ UUID (PK)        │
│ filename │ TEXT │ leave-policy.pdf │
│ file_type TEXT │ .pdf, .docx, etc.│
│ file_size INT  │ bytes            │
│ chunk_cnt INT  │ # in ChromaDB    │
│ uploaded_by FK │ → users.id       │
│ uploaded_at TXT│ ISO time         │
│ status   TEXT  │ processed/failed │
└──────────────────────────────────────┘
     │
     │ N chunks per doc
     │ (stored in ChromaDB)
     │
     ▼
┌──────────────────────────────────────┐
│ ChromaDB COLLECTION (per collection)│
│ (separate from SQLite)              │
├──────────┬──────┬──────────────────┤
│ id       │      │ "doc_1_chunk_0"  │
│ embedding│ FLOAT│ [384-dim vector] │
│ metadata │ DICT │ {source, heading}
│ document │ TEXT │ chunk text       │
└──────────────────────────────────────┘
     │
     │ N:1
     │
     ▼
┌─────────────────────────────────────┐
│ QUERY_LOGS TABLE                    │
├──────────┬──────┬──────────────────┤
│ id*      │ TEXT │ UUID (PK)        │
│ user_id  │ FK   │ → users.id       │
│ username │ TEXT │ cached username  │
│ query    │ TEXT │ "What is...?"    │
│ response │ TEXT │ Long response    │
│ sources  │ JSON │ [{source, scv}]  │
│ time_ms  │ REAL │ 832.5            │
│ created  │ TEXT │ ISO time         │
└─────────────────────────────────────┘
```

## 5. Authentication Flow Diagram

```
STREAMLIT SESSION-BASED AUTHENTICATION:
════════════════════════════════════════════════════════

USER VISITS APP:
     │
     ▼
┌──────────────────────────────────────────┐
│ Check st.session_state.authenticated     │
└──────────────────────────────────────────┘
     │
     ├─ FALSE: Show Login page
     │         ├─ username input
     │         ├─ password input
     │         └─ "Login" button
     │
     └─ TRUE: Show Main app (role-based)
              ├─ Faculty/Student → chat.py
              ├─ Admin → admin.py
              └─ Logout button


LOGIN FLOW:
════════════════════════════════════════════════════

User submits credentials
     │
     ▼
┌──────────────────────────────────────────┐
│ auth.login(username, password)           │
│ (from auth/auth.py)                      │
└──────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────┐
│ db.authenticate_user(user, pwd)          │
│ (from database/db.py)                    │
│                                          │
│ 1. Query: SELECT * FROM users            │
│    WHERE username = ?                    │
│                                          │
│ 2. If found:                             │
│    hash = SHA256(password)               │
│    if hash == stored_hash:               │
│      return user dict                    │
│    else:                                 │
│      return None                         │
│                                          │
│ 3. If not found: return None             │
└──────────────────────────────────────────┘
     │
     ├─ RETURNED user dict
     │  │
     │  ▼
     │  Set st.session_state:
     │  • authenticated = True
     │  • user_id = user["id"]
     │  • username = user["username"]
     │  • role = user["role"]
     │  • user = full user dict
     │  │
     │  ▼
     │  ✅ Redirect to main app
     │
     └─ RETURNED None
        │
        ▼
        ❌ Show "Invalid credentials"
           (stay on login page)


LOGOUT FLOW:
════════════════════════════════════════════════════

User clicks "Logout"
     │
     ▼
┌──────────────────────────────────────────┐
│ auth.logout() (from auth/auth.py)        │
│                                          │
│ Clear st.session_state:                  │
│ • authenticated = False                  │
│ • user_id = None                         │
│ • username = None                        │
│ • role = None                            │
│ • user = None                            │
└──────────────────────────────────────────┘
     │
     ▼
  ✅ Redirect to login page
     (browser session ended)
```

## 6. Performance Timeline

```
USER ASKS QUESTION: "What is annual leave?"

TIMELINE (milliseconds):
════════════════════════════════════════════════════════

0 ms    ┌─ User submits query
        │
10 ms   ├─ Embed question (sentence-transformers)
        │  "..." → 384-dim vector
        │
25 ms   ├─ Search ChromaDB (cosine similarity)
        │  top-5 chunks retrieved
        │
30 ms   ├─ Format context for LLM
        │  Attach citations, join chunks
        │
35 ms   ├─ Send to LLM provider
        │  [START LLM CLOCK]
        │
335 ms  ├─ Ollama response received
        │  (local model, ~300ms generation)
        │  OR
        │  1035 ms if Gemini (1000ms network+gen)
        │
340 ms  ├─ Format response for UI
        │  Extract citations, format markdown
        │
345 ms  ├─ Log query to SQLite
        │  INSERT into query_logs
        │
350 ms  └─ Display to user
        │
        ✅ TOTAL: ~350 ms (Ollama) / ~1050 ms (Gemini)


MEMORY USAGE PROFILE:
═════════════════════════════════════════════════════

INITIALIZATION:
    Python        | 100 MB
    Streamlit     | 80 MB
    ─────────────────────
                  | 180 MB

FIRST QUERY (loads embedding model):
    + Model load  | +400 MB
    ─────────────────────
                  | 580 MB

ChromaDB (depends on doc count):
    + 100 docs    | +20 MB
    + 1000 docs   | +200 MB
    + 10000 docs  | +2000 MB (can exceed RAM)

LLM Model (if GGUF local):
    Phi-3 7B      | +2–3 GB
    Llama2 13B    | +7–8 GB

TOTAL POSSIBLE:
    Lean setup    | 580 MB (Ollama only)
    Full setup    | 3–4 GB (+ local GGUF)
    Large corpus  | 4–8+ GB (with 10K+ docs)
```

## 7. API Endpoint Call Chain

```
CLIENT REQUEST (JSON):
═════════════════════════════════════════════════════

POST /api/chat
{
  "query": "What is annual leave?",
  "user_id": "uuid-123",
  "username": "alice@inst.edu"
}

FASTAPI ENDPOINT:
▼
@app.post("/api/chat")
async def chat(request: ChatRequest):
    ├─ Validate input
    ├─ Check user auth (optional)
    │
    ├─ CALL RAG PIPELINE:
    │  ├─ retriever.retrieve_context(query)
    │  │  └─ Returns top-5 chunks
    │  │
    │  ├─ retriever.format_context_for_llm(chunks)
    │  │  └─ Returns formatted string
    │  │
    │  ├─ generator.generate_response(query, context)
    │  │  └─ Returns LLM response
    │  │
    │  └─ retriever.get_source_citations(chunks)
    │     └─ Returns citation string
    │
    ├─ Log query
    └─ Return response

RESPONSE (JSON):
═════════════════════════════════════════════════════

{
  "response": "Annual leave is 30 days per year...",
  "sources": [
    {
      "text": "Annual leave is 30 days...",
      "source": "leave-policy.pdf",
      "score": 0.94
    },
    ...
  ],
  "citations": "📄 leave-policy.pdf (94% match)\n📄 rules.docx (87% match)",
  "response_time_ms": 832.5
}

Spring Boot receives JSON and returns to React:
▼
React UI displays formatted response
```

---

These diagrams complement the detailed documentation and provide visual understanding of the AstroBot architecture and data flows.
