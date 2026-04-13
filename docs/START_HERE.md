# 🚀 START_HERE — Project Overview

Read this first if you want the current shape of AstroBot in one place.

---

## 📌 What AstroBot Is

AstroBot is a document-grounded institutional assistant built around retrieval-augmented generation.

Users ask questions about institutional documents, and the system retrieves relevant chunks before generating a cited answer.

Current focus areas:
- document upload and parsing
- chunking and embeddings into ChromaDB
- hybrid retrieval with dense search, BM25, and HyDE fallback
- feedback capture and trace monitoring
- voice input through Whisper
- role-based access for admin, faculty, and student users

---

## 🎯 Core Ideas

### 1. Retrieval first, generation second
```
Question -> Retrieve relevant chunks -> LLM answers with context -> Citations shown to the user
```

### 2. Resilience matters
```
Primary provider fails -> fallback provider -> local provider -> context-only response
```

### 3. The project is multi-layered
```
Parser -> Chunker -> Embedder -> ChromaDB
    ↓
User question -> Retriever -> Generator -> Response
```

---

## 🏗️ System View

```
React frontend (admin + chat)
  ↓
Spring Boot proxy layer
  ↓
FastAPI backend
  ├─ Auth and user APIs
  ├─ Document ingestion and retrieval
  ├─ Feedback and trace monitoring
  └─ Voice-to-text + analytics
  ↓
Data layer
  ├─ ChromaDB for embeddings
  ├─ SQLite for metadata and logs
  └─ Local models and provider integrations
```

The repo still includes a Streamlit interface, but the current development focus is the FastAPI + React + Spring Boot stack.

---

## 🔄 Query Flow

1. User asks a question.
2. The question is embedded.
3. Retrieval combines dense similarity, BM25, and HyDE fallback when needed.
4. The generator builds the answer from retrieved context.
5. The response includes citations and is logged for analytics and tracing.

---

## 📁 Key Files

```
config.py           - runtime configuration
api_server.py       - FastAPI entry point
ingestion/parser.py - document parsing
ingestion/embedder.py - embeddings and storage
rag/retriever.py    - retrieval logic
rag/generator.py    - answer generation
database/db.py      - SQLite tables and analytics
views/              - Streamlit UI pages
react-frontend/     - modern web UI
springboot-backend/ - proxy and integration layer
```

---

## 🔑 What to Check Before Editing

- `config.py` for runtime flags and provider settings
- `database/db.py` for persisted tables and analytics
- `rag/retriever.py` for retrieval behavior
- `api_server.py` for exposed API endpoints
- `react-frontend/src/services/api.js` for frontend API wiring

---

## 🚀 Quick Setup

1. Install Python dependencies with `pip install -r requirements.txt`.
2. Configure `.env`.
3. Start the API and frontend stack.
4. Verify `http://localhost:8000/api/health`.

---

## 🧪 Useful Checks

- Test embeddings with `ingestion.embedder.generate_embeddings()`
- Test retrieval with `rag.retriever.retrieve_context()`
- Test provider availability with `rag.providers.manager.get_manager()`
- Test DB access with `database.db.authenticate_user()`


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
