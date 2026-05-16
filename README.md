# 🤖 IMS AstroBot

**Institutional AI Assistant — Powered by RAG + Local LLM**

IMS AstroBot is a Retrieval-Augmented Generation (RAG) chatbot built for institutional use. It combines a React-based admin dashboard with a RAG pipeline to let students and faculty ask questions about institutional documents. Administrators get real-time analytics, document management, and AI configuration tools.

**Latest Version:** 2.0.0 | **Status:** Production-Ready | **License:** MIT

---

## ✨ Key Features

### For Students & Faculty
- 💬 **Smart Q&A** — Ask natural language questions about institutional documents
- ⚡ **Real-time Streaming** — Responses are delivered token-by-token via SSE for zero perceived latency
- 🎙️ **Voice-to-Text** — Ask questions via microphone (powered by OpenAI Whisper)
- 📚 **Source Citations** — Every response includes exact document references
- ⚡ **Fast Search** — Semantic vector search via ChromaDB (sub-second retrieval)
- 🔐 **Role-Based Access** — Faculty and student roles with login authentication

### For Administrators  
- 📄 **Document Management** — Upload, index, search, and delete documents (PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML)
- 👥 **User Management** — Create users, enable/disable accounts, manage roles (admin/faculty/student)
- 📊 **Usage Analytics** — Dashboard with total queries, top users, response times, daily trends
- 📋 **Query Logs** — Inspect recent queries with full responses and source documents
- 💾 **Conversation Memory** — Intelligent semantic caching for instant responses to similar questions (⚡50-100ms)
- 🤖 **AI Settings** — Swap GGUF models, tune temperature/tokens, edit system prompts
- 🩺 **System Health** — Real-time status checks for SQLite, ChromaDB, LLM, embeddings, file storage

---

## What this project provides

- A modular RAG pipeline (ingest → chunk → embed → retrieve → generate)
- Local/remote LLM provider integrations (Ollama, cloud providers)
- A React-based admin UI for document uploads, user management, and analytics
- FastAPI endpoints (REST + SSE) for chat and administration
- Examples for voice-to-text using Whisper and offline embedding setup

If you use this project in a product or research context, please follow the MIT license and attribution rules.

---

## Quick highlights — What we built

- Document ingestion for PDF, DOCX, CSV, XLSX, PPTX, HTML with structure-aware chunking
- Sentence-transformers embeddings stored in ChromaDB for fast semantic search
- Provider manager to route requests to a primary LLM with fallbacks
- Streaming responses (SSE) for low perceived latency in the chat UI
- Admin dashboard for uploads, user roles, and system health checks
- Conversation memory (semantic caching) to speed up repeated/frequent queries

---

## Getting started (quick)

Prerequisites: Python 3.10+, Node 16+, Java 17+ (for Spring Boot). See `requirements.txt` and `react-frontend/package.json` for exact versions.

1. Create a Python virtual environment and install dependencies

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the services (development)

```powershell
# Terminal 1 — FastAPI
python api_server.py

# Terminal 2 — Spring Boot
cd springboot-backend
.\mvnw.cmd spring-boot:run

# Terminal 3 — React
cd react-frontend
npm install
npm run dev
```

3. Open the frontend: http://localhost:3000 — admin credentials are defined in `.env` (change immediately).

---

## Contributing

This project is community-friendly. Contributions are welcome:

- Issues: open bug reports or feature requests
- Pull Requests: fork, branch, add tests/documentation, and submit a PR
- Code Style: follow existing project conventions (PEP8 for Python, typical React patterns)

Before larger changes, open an issue to discuss design and compatibility.

---

## Where to look in the repo

- Python API: `api_server.py`, `rag/`, `ingestion/`, `database/`
- React UI: `react-frontend/src/` (pages, components, services)
- Spring Boot proxy: `springboot-backend/src/main/java/`
- Docs: `docs/` (architecture and guides)

---

## Privacy & Data

This repository includes upload and storage code for documents and embeddings. Treat uploaded documents as potentially sensitive: do not store secrets in uploaded files and configure proper access controls when deploying.

---

If you'd like, I can also:

- Remove or anonymize institute-specific strings across the codebase (config, docs, test artifacts)
- Add a CONTRIBUTING.md and CODE_OF_CONDUCT.md
- Replace default credentials and example `.env` values with safer defaults

Tell me which of the above you'd like next.
