# 🤖 AstroBot — Open Source RAG Assistant

An open-source Retrieval-Augmented Generation (RAG) assistant for document-centric Q&A, search, and basic conversational workflows.

This repository packages a full-stack demo combining a Python FastAPI backend (RAG pipeline + embeddings), a Spring Boot proxy, and a React admin/chat frontend. It is intended as a community-maintained foundation for building document-aware assistants and experiments with local and cloud LLMs.

License: MIT

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
