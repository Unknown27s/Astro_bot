# 🎓 Complete AstroBot System Understanding

**Comprehensive overview of every component, how they work, and why they're designed this way.**

*Read time: 20 minutes | Audience: Everyone (developers, architects, AI agents)*

---

## 📋 Table of Contents

1. [System Overview](#-system-overview)
2. [Three-Tier Architecture](#-three-tier-architecture)
3. [RAG Pipeline Explained](#-rag-pipeline-explained)
4. [Component Deep Dive](#-component-deep-dive)
5. [Data Flow](#-data-flow)
6. [Performance Characteristics](#-performance-characteristics)
7. [Key Design Decisions](#-key-design-decisions)
8. [Common Workflows](#-common-workflows)

---

## 🎯 System Overview

### What is AstroBot?

**AstroBot v2.0** is a **Retrieval-Augmented Generation (RAG) system** designed to answer questions about institutional documents through semantic search + AI.

**Simple flow:**
```
User uploads 50 PDFs about courses
    ↓
System extracts text → chunks → embeddings → stores in ChromaDB
    ↓
User asks: "Which courses are offered in Spring semester?"
    ↓
System searches for relevant course info → finds top 5 chunks
    ↓
System asks AI: "Based on these documents, which courses are offered in Spring?"
    ↓
AI generates answer with citations
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

---

## 🏗️ Three-Tier Architecture

```
┌─────────────────────────────────────────────────┐
│           PRESENTATION LAYER                     │
│  ┌─────────────────┬──────────┬─────────────┐  │
│  │  Streamlit UI   │ React    │ Spring Boot │  │
│  │  (Python)       │ Frontend │ REST API    │  │
│  └─────────────────┴──────────┴─────────────┘  │
│           (User-facing interfaces)              │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────▼──────────────────────────────┐
│           APPLICATION LAYER                     │
│  ┌─────────────────┬──────────┬─────────────┐  │
│  │  FastAPI REST   │ RAG      │ Auth &      │  │
│  │  API Server     │ Pipeline │ Database    │  │
│  │  (Python)       │          │ Layer       │  │
│  └─────────────────┴──────────┴─────────────┘  │
│    (Business logic, AI, security)               │
└──────────────────┬──────────────────────────────┘
                   │ Local Storage / APIs
┌──────────────────▼──────────────────────────────┐
│           DATA LAYER                            │
│  ┌─────────────────┬──────────┬─────────────┐  │
│  │  SQLite DB      │ ChromaDB │ File        │  │
│  │  (Users, logs)  │ (Vectors)│ Storage     │  │
│  └─────────────────┴──────────┴─────────────┘  │
│    (Persistent storage)                         │
└─────────────────────────────────────────────────┘
```

### Tier 1: Presentation (User Interfaces)

**What users see:**

| Interface | Purpose | Users |
|-----------|---------|-------|
| **Streamlit UI** | Chat + admin dashboard | Faculty, students, admins |
| **React Frontend** | Modern web UI | External users, students |
| **Spring Boot API** | REST endpoints | Mobile apps, integrations |

**What they do:**
- Render user interface
- Handle login/auth
- Send user queries to backend
- Display results + citations

### Tier 2: Application (Business Logic)

**Heart of the system:**

| Component | Purpose |
|-----------|---------|
| **FastAPI REST API** | Receives HTTP requests, routes to RAG |
| **RAG Pipeline** | Core intelligence (search + AI) |
| **Auth Layer** | Login, session management |
| **Database Layer** | CRUD operations |

**What it does:**
- Receives query from UI
- Finds relevant documents
- Gets AI response
- Returns with citations

### Tier 3: Data (Storage)

**Where information lives:**

| Storage | Purpose | Data |
|---------|---------|------|
| **SQLite** | Traditional database | Users, query logs |
| **ChromaDB** | Vector database | Document embeddings |
| **File System** | Document storage | Uploaded PDFs, documents |

---

## 🔄 RAG Pipeline Explained

### What is RAG?

**RAG = Retrieval-Augmented Generation**

```
Traditional LLM:     Question → LLM Brain → Answer (might be wrong)

RAG System:          Question → (1) Search documents → (2) Get AI to answer
                                      ↓
                                 Relevant docs
```

### The Three Phases

#### Phase 1: Document Ingestion (One-time, happens when admin uploads)

```
Admin uploads: "Syllabus 2024.pdf"
    ↓
[PARSER] Extract text from PDF
    ↓ Output: Raw text (10,000 characters)
[CHUNKER] Break into smaller pieces
    ├─ Split by headings (Chapter 1, 2, 3...)
    ├─ Create 500-character chunks
    └─ Add 50-character overlap
    ↓ Output: 20 chunks [{text, metadata}]
[EMBEDDER] Convert text to numbers
    ├─ Convert "Exam on May 15th" → [0.12, -0.45, 0.89...] (384 numbers)
    ├─ Store in ChromaDB
    └─ Save metadata (source file, heading)
    ↓ Output: Vector database updated
[DATABASE] Record document info
    └─ "Syllabus 2024.pdf: 20 chunks, processed, 2024-03-15"
```

**Result:** System now "knows" about syllabus

#### Phase 2: Query → Retrieval (Happens when user asks question)

```
User asks: "What's the midterm date?"
    ↓
[EMBEDDING] Convert question to numbers
    └─ "What's the midterm date?" → [0.15, -0.42, 0.85...] (384 numbers)
    ↓
[SEARCH] Find similar chunks in ChromaDB
    ├─ Compare question embedding to all 20 chunks
    ├─ Find most relevant (cosine similarity)
    └─ Return top 5 chunks with scores
    ↓ Output: [{chunk: "Midterm on April 20th", score: 0.92}, ...]
[FORMAT] Prepare context for AI
    └─ Build text passage with all 5 chunks
    ↓ Output: "Based on these documents: [Midterm on April 20th...]"
```

**Result:** System found relevant information

#### Phase 3: Generation (AI creates answer)

```
AI gets:
  - Question: "What's the midterm date?"
  - Context: "Based on documents: [Midterm on April 20th, in Room 102]"
    ↓
[LLM] AI reads context + question
    ├─ "The midterm is on April 20th in Room 102"
    ├─ (sourcing from provided context, not hallucinating)
    └─ "See [Syllabus 2024.pdf]"
    ↓ Output: "The midterm is on April 20th in Room 102. [Syllabus 2024.pdf]"
```

**Result:** User gets accurate, cited answer

---

## 🔧 Component Deep Dive

### Parser (`ingestion/parser.py`)

**Job:** Extract text from any document format

| Format | Tool | What it does |
|--------|------|-------------|
| PDF | PyPDF2 | Reads pages, extracts text |
| DOCX | python-docx | Reads paragraphs, tables |
| Excel | openpyxl | Reads sheets, cells |
| PPTX | python-pptx | Reads slides, notes |
| HTML | BeautifulSoup | Parses HTML, extracts text |

**Example:**
```python
Input:  "course_syllabus.pdf"
Output: "Course Code: CS101
         Title: Introduction to Programming
         Prerequisites: None
         Midterm: April 20th
         Final: May 15th"
```

**Key facts:**
- Handles 5+ formats
- Preserves document structure markers (headings, page breaks)
- Returns plain text + structure hints

### Chunker (`ingestion/chunker.py`)

**Job:** Break text into intelligent pieces

**Two-stage process:**

```
Stage 1: Structural Split
  Input:  "# Chapter 1\nContent...\n# Chapter 2\nMore..."
  Looks for: Headings (##), Page breaks ([Page 2]), Sheet names
  Output: [{heading: "Chapter 1", text: "Content..."}, {heading: "Chapter 2", ...}]

Stage 2: Fixed-size chunks
  Input:  Each "Chapter 1" section (maybe 2000 characters)
  Split:  Into 500-char chunks with 50-char overlap
  Output: [{heading: "Chapter 1", text: "First 500 chars"}, 
           {heading: "Chapter 1", text: "Chars 451-950"}, 
           {heading: "Chapter 1", text: "Chars 901-1400"}]
```

**Why 500 characters?**
- Small enough: Quick embedding + storage
- Large enough: Preserves context (1-2 sentences minimum)
- Common sweet spot: Used by most RAG systems

**Why 50-char overlap?**
- Prevents cutting off mid-sentence
- Maintains context between chunks
- When 2 chunks are returned as results, they read smoothly

**Result:** 10,000-char PDF → 20 smart chunks

### Embedder (`ingestion/embedder.py`)

**Job:** Convert text → vector numbers to enable semantic search

**How embedding works:**

```
Sentence 1: "The midterm exam is on April 20th"
  ↓ Embedding Model (all-MiniLM-L6-v2)
  ↓ Creates 384 numbers representing meaning
Vector 1:    [0.234, -0.156, 0.789, ..., 0.001]  (384 dimensions)

Sentence 2: "The midterm test happens on April 20th"
  ↓ Similar meaning = Similar vector
Vector 2:    [0.241, -0.152, 0.791, ..., 0.003]  (384 dimensions)

Sentence 3: "The final exam is on May 15th"
  ↓ Different meaning = Different vector
Vector 3:    [0.102, 0.456, 0.123, ..., 0.567]   (384 dimensions)

Distance between Vector 1 & 2:  0.01 (very close - similar meaning!)
Distance between Vector 1 & 3:  0.89 (far apart - different meaning)
```

**Why `all-MiniLM-L6-v2`?**

| Feature | Value |
|---------|-------|
| Speed | ⚡ Fast (~10ms per chunk) |
| Dimensions | 384 (good balance) |
| Accuracy | ✓ Good semantic understanding |
| GPU Required | ❌ No (CPU only) |
| Size | 80 MB (small) |

**Process:**

```
Upload Document
    ↓
[Parse] Extract text
    ↓
[Chunk] Break into pieces
    ↓
[For each chunk:]
    ├─ Convert text → 384-dim vector
    ├─ Store in ChromaDB with metadata
    └─ Link to document record
    ↓
[Update database]
    └─ Mark document as "processed"
```

### ChromaDB (Vector Storage)

**Job:** Store embeddings + enable fast similarity search

**How it works:**

```
When adding vectors:
  Original text: "Midterm is April 20th"
  Embedding: [0.234, -0.156, 0.789, ...]
  
ChromaDB stores:
  {
    id: "chunk_123",
    embedding: [0.234, -0.156, 0.789, ...],
    metadata: {source: "syllabus.pdf", heading: "Exams", chunk_index: 5},
    text: "Midterm is April 20th"
  }

When searching:
  Query: "When's the midterm?"
  Query embedding: [0.231, -0.158, 0.787, ...]  (similar to stored vector)
  
ChromaDB finds:
  1. Calculates distance from query to all stored vectors
  2. Sorts by distance (closest = most relevant)
  3. Returns top 5 results
```

**Key stats:**
- Persistent storage: `./data/chroma_db/`
- SQLite-backed (no server needed)
- Supports 1M+ vectors (billions possible)
- Cosine similarity search: Fast & accurate

### Retriever (`rag/retriever.py`)

**Job:** Get relevant documents + format for LLM

**Process:**

```
Input: "What courses are required?"

Step 1: Embed question
  Question embedding: [0.15, -0.42, 0.85, ...]

Step 2: Search ChromaDB
  Search all 100,000 stored vectors
  Find closest 5
  Results: [
    {text: "Course requirements...", source: "catalog.pdf", score: 0.94},
    {text: "Prerequisites include...", source: "syllabus.pdf", score: 0.86},
    ...
  ]

Step 3: Format context
  Output: "
[Source: catalog.pdf > Requirements | Relevance: 94%]
Course requirements include:
- CS101: Intro to Programming
- MATH101: Calculus I

[Source: syllabus.pdf | Relevance: 86%]
Prerequisites include:
- Basic computer literacy
- High school algebra
  "

```

**Key functions:**
- `retrieve_context()` — Search + get chunks
- `format_context_for_llm()` — Pretty-print for AI
- `get_source_citations()` — Extract references

### Generator (`rag/generator.py`)

**Job:** Use LLM to create answer from context

**Process:**

```
Input:
  - Query: "What courses are required?"
  - Context: "[Source: catalog.pdf]..."

Step 1: Build prompt
  System message: "You are a helpful assistant answering based on documents."
  User message: "Question: What courses are required?
                 Based on these documents: [catalog.pdf content]"

Step 2: Call LLM
  Via ProviderManager → Primary provider (Ollama) → Answer generated
  
Step 3: Return answer
  {
    response: "The required courses include CS101 and MATH101...",
    sources: [catalog.pdf, syllabus.pdf],
    response_time_ms: 450
  }
```

**LLM modes:**
- **Local-only**: Use Ollama GGUF (private, no API key)
- **Cloud-only**: Grok or Gemini (fast, needs API key)
- **Hybrid**: Try local first, fallback to cloud

### Whisper Transcription (`rag/voice_to_text.py`)

**Job:** Convert user's spoken voice (audio files) into plain text string.

**How it works:**
- Triggered when users use the microphone button in React and `/api/chat/audio` is called.
- Uses `faster-whisper` (running locally on CPU) with the `base.en` model for optimal speed-to-accuracy ratio.
- The model object is kept actively in Python memory using `@lru_cache` so sequential voice messages transcribe in < 1s.
- Securely processes browser-native `.webm` audio using the system-level `ffmpeg` multimedia framwork.
- Output text is seamlessly injected right into the standard `rag/retriever.py` and query flow.

### Provider Manager (`rag/providers/manager.py`)

**Job:** Route LLM calls through fallback chain

**Fallback logic:**

```
Try PRIMARY provider (e.g., Ollama)
  ├─ Success? Return response ✓
  ├─ Timeout/error? Try FALLBACK provider
  │   ├─ Success? Return response ✓
  │   ├─ Error? In HYBRID mode, try Ollama
  │   │   ├─ Success? Return response ✓
  │   │   ├─ Error? Return context-only: "Based on these documents: [...]"
```

**Providers:**

| Provider | Speed | Cost | Setup |
|----------|-------|------|-------|
| **Ollama** | Fast | Free | Local GGUF file |
| **Grok** | Very fast | $$ | API key |
| **Gemini** | Very fast | $$ | API key |

---

## 📊 Data Flow

### Document Upload Flow

```
┌─ User uploads "course.pdf"
│
├─ API receives file
│
├─ [PARSE] Extract text
│  └─ Result: "Course Code: CS101..."
│
├─ [CHUNK] Break into pieces
│  └─ Result: 20 chunks [{text, metadata}]
│
├─ [EMBED] Convert to vectors
│  └─ Result: 20 vectors [384 dimensions each]
│
├─ [STORE] Save to ChromaDB
│  └─ Result: Indexed in ChromaDB
│
└─ [UPDATE DB] Record metadata
   └─ Result: documents table updated
   
FINAL STATE: System can now answer questions about CS101!
```

### Query Flow

```
┌─ User types "When is midterm?" (or Speaks using Microphone)
│
├─ [TRANSCRIBE] (Optional) Convert audio webm blob to text using Whisper
│  └─ Result: Text string
│
├─ [EMBED QUERY] Convert text to vector
│  └─ Result: [0.15, -0.42, ...]
│
├─ [SEARCH CHROMADB] Find similar chunks
│  └─ Result: Top 5 chunks with scores
│
├─ [FORMAT CONTEXT] Create passage for LLM
│  └─ Result: "Based on: [chunk1], [chunk2]..."
│
├─ [GET AI RESPONSE] Call LLM
│  └─ Result: "The midterm is April 20th"
│
├─ [FORMAT ANSWER] Add citations
│  └─ Result: "The midterm is April 20th. [Source: syllabus.pdf]"
│
└─ [LOG QUERY] Store in database
   └─ Result: Query logged for analytics
```

---

## ⚡ Performance Characteristics

### Query Latency (End-to-End)

| Step | Operation | Time |
|------|-----------|------|
| Embedding query | Convert "What's the midterm?" to vector | 10-20ms |
| ChromaDB search | Find top-5 similar chunks | 5-15ms |
| Context formatting | Format chunks with citations | 2-5ms |
| LLM generation | **LOCAL (Ollama)** | 300-800ms |
| LLM generation | **CLOUD (Grok/Gemini)** | 500-2000ms |
| Database logging | Save query + response | 10-20ms |
| **TOTAL LOCAL** | End-to-end with local LLM | **~350-860ms** |
| **TOTAL CLOUD** | End-to-end with cloud LLM | **~550-2050ms** |

**What does 450ms feel like?**
- User perceives: "Fast response" ✓
- Acceptable for web: < 1 second ✓

### Memory Usage

| Component | Size | Notes |
|-----------|------|-------|
| Python base | 50 MB | Interpreter + stdlib |
| FastAPI + RAG | 200 MB | App code + libraries |
| Embedding model | 400 MB | Loaded lazily on first use |
| ChromaDB in-memory cache | 200 MB | Grows with usage |
| SQLite | 100 MB | Database file (variable) |
| **TOTAL (no LLM)** | **~950 MB** | Typical startup |
| LLM model (GGUF) | 2-4 GB | Depends on model size |
| **TOTAL (with local LLM)** | **~3-4.5 GB** | Full system |

**What does 3.5 GB mean?**
- Modern laptops: 8-16 GB RAM ✓
- Older servers: 4 GB MIN ⚠️
- Cloud VMs: 8 GB standard

### Throughput

| Metric | Value | Notes |
|--------|-------|-------|
| Concurrent users (FastAPI) | 10-50 | Limited by LLM |
| Single-threaded (Streamlit) | 1 user | One session at a time |
| Documents uploadable | 1000+ | ChromaDB handles easily |
| Vectors storable | 1M+ | Practical limit: 10M |
| Database records | 1M+ | SQLite handles well |

---

## 🎯 Key Design Decisions

### Why RAG and not Fine-tuning?

| Aspect | RAG | Fine-tuning |
|--------|-----|------------|
| **Setup time** | Hours | Days/Weeks |
| **Update docs** | Instant | Retrain needed |
| **Private data** | Stays local | Uploaded |
| **Accuracy** | High | Very high |
| **Cost** | Low | High |

**Decision:** RAG = Right balance for institutional use

### Why ChromaDB and not Elasticsearch?

| Aspect | ChromaDB | Elasticsearch |
|--------|----------|---------------|
| **Setup** | One line | Docker required |
| **Storage** | SQLite file | Server-based |
| **Scaling** | Single machine | Clusters |
| **Learning curve** | Easy | Steep |
| **Team size** | 1-50 | 50+ |

**Decision:** ChromaDB = Perfect for this project size

### Why FastAPI and not Flask?

| Aspect | FastAPI | Flask |
|--------|---------|-------|
| **Async support** | Built-in | Requires extension |
| **Concurrent requests** | 50+ | 10-20 |
| **Auto docs** | /docs endpoint | Manual |
| **Type hints** | Native | Not required |

**Decision:** FastAPI = Scales better, cleaner code

### Why Ollama and not directly calling OpenAI?

| Aspect | Ollama | OpenAI |
|--------|--------|--------|
| **Privacy** | Data stays local | Sent to cloud |
| **Cost** | Free | Per-token pricing |
| **Internet** | Optional | Required |
| **Latency** | 300-800ms | 500-2000ms |
| **Reliability** | Your machine | Their servers |

**Decision:** Ollama primary + cloud fallback = Best of both worlds

---

## 🔄 Common Workflows

### Workflow 1: Faculty Member Shares Course Documents

```
1. Faculty logs in → sees "Upload Documents"
2. Drags 20 PDFs into upload area
3. System processes: Parse → Chunk → Embed → Store
4. Faculty sees: "Processing... 20 documents"
5. After 2-3 minutes: "✓ Ready!"
6. Now students can ask course questions
```

### Workflow 2: Student Asks a Question

```
1. Student logs in → sees chat box
2. Asks: "What books are required for this course?"
3. Behind the scenes:
   - Question embedded [0.12, -0.45, ...]
   - ChromaDB searches: "Find chunks about books/required"
   - Returns: [syllabus.pdf, readings.txt, catalog.pdf]
   - LLM generates: "Required books are..."
   - AI adds sources: "[See syllabus.pdf p.3]"
4. Student sees: Answer + citation links
5. Student clicks source → sees original PDF
```

### Workflow 3: Admin Troubleshooting

```
1. Admin logs in → sees "Health Dashboard"
2. Checks:
   - ✓ SQLite: OK
   - ✓ ChromaDB: OK
   - ✓ Ollama: Running
   - ✓ Embeddings: 5000 vectors
3. If slow:
   - Checks: "Response time: 1200ms (slower than usual)"
   - Clicks: "Analyze" → sees LLM taking 900ms
   - Action: Switch to Grok for faster response
4. If documents missing:
   - Checks: ChromaDB vector count
   - Re-uploads documents
```

### Workflow 4: Developer Adding New Provider

```
1. Create: `rag/providers/claude_provider.py`
2. Inherit: `class ClaudeProvider(LLMProvider)`
3. Implement: `generate()`, `is_available()`, `get_status()`
4. Register: Add to `ProviderManager._get_chain()`
5. Test: `python -c "from rag.providers.manager import get_manager; print(get_manager().get_all_statuses())"`
6. Done!: Claude now available as fallback
```

---

## 🧠 Mental Model

**How to think about AstroBot:**

```
Simple view: Upload documents → Ask questions → Get answers with sources

Technical view:
  1. Documents → Parser → Text
  2. Text → Chunker → Pieces
  3. Pieces → Embedder → Numbers
  4. Numbers → ChromaDB → Searchable
  5. Question → Embedder → Numbers
  6. Numbers → ChromaDB → Similar pieces
  7. Similar pieces → LLM → Answer
  8. Answer → Formatter → Cited answer

Deep view:
  RAG = Search (semantically) + AI = Accurate, sourced answers

System view:
  Presentation Layer (3 UIs)
      ↓ HTTP
  Application Layer (FastAPI + RAG)
      ↓ Local APIs
  Data Layer (SQLite + ChromaDB + Files)
```

---

## ✅ You Now Understand

✅ What AstroBot does (RAG for institutional docs)  
✅ Why RAG (accuracy, sources, privacy)  
✅ How RAG works (4 phases, chunking, embeddings, search, LLM)  
✅ Each component's job (parser, chunker, embedder, retriever, generator)  
✅ How data flows (upload → search → answer)  
✅ Performance metrics (450ms typical, 3-4GB RAM)  
✅ Design decisions (why each technology was chosen)  
✅ Common workflows (upload, query, admin, develop)  

---

## 🚀 Next Steps

- **Want to set up?** → [guides/QUICKSTART.md](../guides/QUICKSTART.md)
- **Want quick lookup?** → [guides/QUICKREF.md](../guides/QUICKREF.md)
- **Want component details?** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Want visual flows?** → [DIAGRAMS.md](DIAGRAMS.md)
- **Want to code?** → [../COPILOT_GUIDE.md](../COPILOT_GUIDE.md)

