# 🚀 START_HERE — For AI Agents & Copilot

**Read this FIRST before working on IMS AstroBot**

---

## 📌 What is IMS AstroBot?

**IMS AstroBot** is a **Retrieval-Augmented Generation (RAG) chatbot** for institutional users.

### The Problem
Students/Faculty search through scattered documents (PDFs, handbooks, policies) to find answers. Information is often outdated, scattered, or unclear.

### The Solution
Users ask natural language questions → Bot finds relevant institutional documents → Bot generates answer grounded in those documents → Answer includes source citations.

### Example
```
User: "What is the annual leave policy?"
AstroBot: "Annual leave is 30 days per year, plus 10 sick days.
          Medical leave requires HR approval.
          See: leave-policy.pdf, HR handbook"
```

---

## 🎯 Three Core Ideas

### 1. RAG = Retrieval + Generation
```
Old way:   Question → LLM → Answer (may hallucinate)
RAG way:   Question → Find docs → LLM uses docs → Answer (factual, cited)
```

### 2. System is Resilient
```
Primary LLM fails? → Try backup → Try another → Use document context only
= Always returns something useful
```

### 3. Simple, Extensible Architecture
```
Parser → Chunker → Embedder → ChromaDB (storage)
                                    ↓
User Question → Retriever → Generator → Answer
                                    ↓
                            LLMProvider (Ollama, Grok, Gemini)
```

---

## 🏗️ System Architecture (30-second version)

```
FRONTEND
├─ Streamlit UI (http://localhost:8501)
├─ FastAPI REST (http://localhost:8000)
├─ React Web UI (http://localhost:5173)
└─ Spring Boot (http://localhost:8080)
        ↓
APPLICATION
├─ Authentication (SHA-256 password, session-based)
├─ RAG Pipeline (retrieve docs + generate answers)
└─ Admin Dashboard (manage docs, users, AI settings)
        ↓
DATA LAYER
├─ ChromaDB (vector database for semantic search)
├─ SQLite (relational DB: users, documents, query_logs)
├─ Embeddings (all-MiniLM-L6-v2, 384 dimensions)
└─ LLM Providers (Ollama local, Grok cloud, Gemini cloud)
```

---

## 🔄 Complete Query Flow (What happens when user asks a question)

```
1. USER ASKS QUESTION
   "What is the annual leave policy?"

2. RETRIEVER (~15 ms)
   ├─ Convert question to vector (384 dimensions)
   ├─ Search ChromaDB for similar document chunks
   ├─ Return top-5 most relevant chunks
   └─ Each chunk includes: text, source, relevance score

3. GENERATOR (~300-2000 ms)
   ├─ Format chunks as context
   ├─ Send to LLM: "Based on context: {docs}, answer: {question}"
   ├─ LLM reads context and generates answer
   └─ If LLM fails, use fallback (show context directly)

4. DISPLAY
   ├─ Show answer
   ├─ Show source citations
   └─ Log interaction to database

TOTAL TIME: ~350-2000 ms
```

---

## 📁 Project Structure (Key Files)

```
AstroBot/
├── config.py                      ← ALL SETTINGS HERE
├── .env                           ← Environment variables
│
├── database/db.py                 ← SQLite CRUD
├── auth/auth.py                   ← User authentication
│
├── ingestion/
│   ├── parser.py                 ← Parse PDF/DOCX/Excel/PPTX/HTML
│   ├── chunker.py                ← Break text into chunks
│   └── embedder.py               ← Convert to vectors, store
│
├── rag/
│   ├── retriever.py              ← Search + format context
│   ├── generator.py              ← Call LLM, handle fallback
│   └── providers/
│       ├── manager.py            ← Route to LLM (with fallback)
│       ├── ollama_provider.py    ← Local LLM
│       ├── groq_provider.py      ← Grok API
│       └── gemini_provider.py    ← Gemini API
│
├── views/
│   ├── chat.py                   ← User chat interface
│   └── admin.py                  ← Admin dashboard
│
├── app.py                        ← Streamlit entry point
├── api_server.py                 ← FastAPI REST API
│
└── data/
    ├── uploads/                  ← Uploaded documents
    ├── chroma_db/                ← Vector database
    └── astrobot.db               ← SQLite database
```

---

## 🔑 Key Concepts You MUST Know

### 1. Configuration
- **All settings in:** `config.py`
- **Secrets in:** `.env` (NOT in git)
- **Never hardcode:** paths, API keys, model names

### 2. RAG is the Core
```
Parse → Chunk → Embed → Store
                         (admin action)
                            ↓
                       Search → Format → Generate
                         (user query)
```

### 3. Fallback Chain Ensures Resilience
```
Try Primary Provider (e.g., Grok)
  ↓ if fails
Try Fallback Provider (e.g., Gemini)
  ↓ if fails
Try Ollama (local, always works)
  ↓ if fails
Return context-only (show document chunks)
  = User always gets SOMETHING
```

### 4. Database Has Three Tables
```
users: id, username, password_hash, role
documents: id, filename, chunk_count, status
query_logs: id, user_id, query_text, response_text
```

### 5. ChromaDB Stores Vectors
```
Per chunk: {
  embedding: [384 floats],
  metadata: {source, heading, chunk_index},
  document: "actual text"
}
Search: similarity = 1 - (distance / 2)
```

---

## 🚀 Quick Setup (< 5 minutes)

```powershell
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env
echo "LLM_MODE=local_only" > .env
echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env
echo "OLLAMA_MODEL=qwen3:0.6b" >> .env

# 4. Start all servers
.\start-all-servers.ps1

# 5. Access
# Streamlit: http://localhost:8501
# Login: admin / admin123
```

---

## 💡 Before You Start Coding

### ✅ DO:
- Check `config.py` first for all settings
- Use parameterized SQL queries (`?` placeholders)
- Log errors explicitly (don't silently fail)
- Test provider chain: `get_manager().get_all_statuses()`
- Use `st.session_state` for Streamlit state
- Call `reset_manager()` after `.env` changes

### ❌ DON'T:
- Hardcode paths, API keys, model names
- Assume Ollama is always running (check `is_available()`)
- Load all documents into memory (use ChromaDB)
- Skip error handling in RAG pipeline
- Embed credentials in code
- Forget parameterized SQL queries

---

## 🧪 Testing Your Changes

### Quick Test Commands

```python
# Test embeddings work
from ingestion.embedder import generate_embeddings
v = generate_embeddings(["test"])
print(len(v[0]))  # Should be: 384

# Test ChromaDB
from ingestion.embedder import get_collection
collection = get_collection()
print(collection.count())  # Total vectors

# Test Ollama
from rag.providers.ollama_provider import OllamaProvider
llm = OllamaProvider("http://localhost:11434", "qwen3:0.6b")
print(llm.is_available())  # True or False

# Test database
from database.db import authenticate_user
user = authenticate_user("admin", "admin123")
print(user)  # {id, username, role, ...}
```

---

## 📊 Performance You Should Know

| Operation | Time |
|-----------|------|
| Question embedding | 10–20 ms |
| ChromaDB search | 5–15 ms |
| Ollama response | 300–800 ms |
| Grok response | 500–1500 ms |
| Gemini response | 1000–2000 ms |
| **Total (local)** | **~350–860 ms** |
| **Total (cloud)** | **~550–2050 ms** |

**Memory:** 800 MB base + 400 MB embeddings + 2–4 GB if local LLM

---

## 🐛 Common Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| "No LLM available" | Start Ollama: `ollama serve` |
| Embedding timeout | Wait 1–2 min (first download) |
| ChromaDB error | Delete `data/chroma_db/`, re-upload docs |
| SQLite locked | Restart servers |
| Streamlit crash | Missing import? Check `.env` |

---

## 📚 What to Read Next

1. **For workflow:** Read [COPILOT_GUIDE.md](COPILOT_GUIDE.md)
2. **For commands:** Read [guides/QUICKREF.md](guides/QUICKREF.md)
3. **For details:** Read [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
4. **For visuals:** Read [architecture/DIAGRAMS.md](architecture/DIAGRAMS.md)

---

## 🎯 You're Ready When You Can Answer:

- ✅ What is RAG and why do we use it?
- ✅ What are the three phases of the pipeline?
- ✅ Where is the configuration stored?
- ✅ What happens when a user asks a question?
- ✅ How does the fallback chain work?
- ✅ What are the three database tables?
- ✅ How does ChromaDB search work?
- ✅ What should you NOT do when coding?

**If you can answer these, proceed to [COPILOT_GUIDE.md](COPILOT_GUIDE.md)**

---

**Status:** Ready to work on AstroBot ✅

Next: [COPILOT_GUIDE.md](COPILOT_GUIDE.md)
