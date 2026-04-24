# 📚 AstroBot Documentation

This directory documents the current AstroBot stack and keeps older phase-specific notes for reference.

The active system is centered on:
- FastAPI for the Python API layer
- React + Vite for the modern web frontend
- Spring Boot as the integration/proxy layer
- Streamlit for the legacy/admin UI that still ships with the repo
- ChromaDB + SentenceTransformers for retrieval
- Hybrid retrieval with dense vectors, BM25, and HyDE fallback
- Langfuse tracing, feedback capture, and trace monitoring
- Official-site ingestion with single-page fetch or multi-page site crawl

---

## Latest Stability Fixes (2026-04-24)

- Fixed startup import failures in FastAPI by restoring missing database helper functions used by API endpoints.
- Added persistence support for feedback logs, trace monitor events, and upload-derived suggested questions in SQLite.
- Fixed chat generation runtime crash caused by observability keyword arguments (`trace`, `obs_trace`, `route_mode`) not being accepted by generator functions.
- Updated files:
    - `database/db.py`
    - `rag/generator.py`

---

## 📖 Documentation Index

### Current docs
- [START_HERE.md](./START_HERE.md) - project overview and query flow
- [guides/QUICKREF.md](./guides/QUICKREF.md) - commands, config, and API shortcuts
- [architecture/QUERY_TO_VECTOR_SEARCH.md](./architecture/QUERY_TO_VECTOR_SEARCH.md) - retrieval pipeline
- [development/LANGFUSE_INTEGRATION_GUIDE.md](./development/LANGFUSE_INTEGRATION_GUIDE.md) - tracing, feedback, and monitor UI
- [UPLOAD_API_REFERENCE.md](./UPLOAD_API_REFERENCE.md) - upload response and suggested questions
- [Voice_to_Text_Implementation_Guide.md](./Voice_to_Text_Implementation_Guide.md) - Whisper voice input

### Development and contribution
- [COPILOT_GUIDE.md](./COPILOT_GUIDE.md) - workspace-specific agent guidance
- [contribution/CONTRIBUTING.md](./contribution/CONTRIBUTING.md) - how to add or change features
- [contribution/WORKFLOW.md](./contribution/WORKFLOW.md) - quick feature checklist

### Legacy docs
- [01-QUICKSTART.md](./01-QUICKSTART.md)
- [02-IMPLEMENTATION_SUMMARY.md](./02-IMPLEMENTATION_SUMMARY.md)
- [04-API_ENDPOINTS.md](./04-API_ENDPOINTS.md)
- [05-ADMIN_RATE_LIMITING.md](./05-ADMIN_RATE_LIMITING.md)

These older documents remain useful for history, but some details reflect earlier phases of the project.

---

## 🎯 Choose Your Path

### New contributor
1. Read: [START_HERE.md](./START_HERE.md)
2. Read: [guides/QUICKREF.md](./guides/QUICKREF.md)
3. Read: [architecture/COMPLETE_UNDERSTANDING.md](./architecture/COMPLETE_UNDERSTANDING.md)
4. Read: [development/CODE_CONVENTIONS.md](./development/CODE_CONVENTIONS.md)

### Feature work
1. Read: [COPILOT_GUIDE.md](./COPILOT_GUIDE.md)
2. Read: [contribution/CONTRIBUTING.md](./contribution/CONTRIBUTING.md)
3. Read: [contribution/WORKFLOW.md](./contribution/WORKFLOW.md)
4. Read: [development/LANGFUSE_INTEGRATION_GUIDE.md](./development/LANGFUSE_INTEGRATION_GUIDE.md)

### Retrieval and document pipeline
1. Read: [architecture/QUERY_TO_VECTOR_SEARCH.md](./architecture/QUERY_TO_VECTOR_SEARCH.md)
2. Read: [UPLOAD_API_REFERENCE.md](./UPLOAD_API_REFERENCE.md)
3. Read: [architecture/DATABASE_SCHEMA.md](./architecture/DATABASE_SCHEMA.md)
4. Read: [proposal_feature/official_site_ingestion_plan.md](./proposal_feature/official_site_ingestion_plan.md)

---

## 📁 Documentation Structure

```
docs/
├── README.md
├── INDEX.md
├── START_HERE.md
├── COPILOT_GUIDE.md
├── IMPROVEMENTS_NEEDED.md
├── UPLOAD_API_REFERENCE.md
├── Voice_to_Text_Implementation_Guide.md
│
├── architecture/
├── development/
├── guides/
└── contribution/
```

---

## 🔑 What This Project Covers

✅ Document ingestion and parsing
✅ Chunking and embeddings in ChromaDB
✅ Hybrid retrieval and fallback generation
✅ Role-based access for students, faculty, and admins
✅ Upload analytics, query logs, and feedback capture
✅ Trace monitoring and observability
✅ Official-site page ingestion and site crawl indexing
✅ Voice-to-text input using local Whisper

---

## 📊 Architecture Overview

```
React frontend → Spring Boot proxy → FastAPI backend
                                       ↓
                              ChromaDB + SQLite
```

---

## 🚨 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing dependencies | `pip install -r requirements.txt` |
| Port already in use | Check if another service is running |
| LLM not responding | Ensure Ollama is running: `ollama serve` |
| ChromaDB errors | Delete `data/chroma_db/`, re-upload docs |

See [guides/TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md) for more.

---

**Last Updated:** April 2026  
**Version:** 2.0.0
