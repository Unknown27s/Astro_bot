# 📚 IMS AstroBot — Documentation Index

**Complete reference guide to all project documentation.**

---

## 📖 Documentation Files

### 1. **`.github/copilot-instructions.md`** ← START HERE
   **Purpose:** Complete workspace instructions for AI agents and developers
   - System overview and three-tier architecture
   - Full project structure with file purposes
   - RAG pipeline mechanics (3 phases explained)
   - Component details (config, database, chunking, retrieval, generation)
   - Building & running instructions
   - Development conventions & common pitfalls
   - Performance metrics & scaling considerations
   - Security considerations
   - Common issues & debugging

   **When to use:** Daily reference for understanding the project

---

### 2. **`ARCHITECTURE.md`** (This document)
   **Purpose:** Deep dive into system architecture and RAG implementation
   - System overview with diagrams
   - RAG pipeline mechanics with detailed flow charts
   - Component details (Embedder, Retriever, Generator, Provider Manager, Database, Auth)
   - Performance metrics (latency breakdown, memory usage, throughput)
   - Data flow examples (upload, query, fallback)
   - Development guide (adding providers, custom parsers, analytics)

   **When to use:** Understanding HOW components work together, performance optimization

---

### 3. **`DIAGRAMS.md`**
   **Purpose:** Visual ASCII representations of system flows
   - System architecture diagram (3-tier with data flow)
   - RAG pipeline flow diagram (document upload → query → response)
   - Provider fallback chain diagram
   - Database schema diagram
   - Authentication flow diagram
   - Performance timeline (execution path with timing)
   - API endpoint call chain

   **When to use:** Visual learners, presenting to stakeholders, understanding data flow

---

### 4. **`QUICKREF.md`**
   **Purpose:** Quick reference cheat sheet for developers
   - Quick start (< 5 minutes setup)
   - Key commands (SQLite, embeddings, RAG, providers, LLM status)
   - Configuration (.env file template)
   - Common workflows (upload, query, switch provider)
   - Debugging tips
   - Performance targets
   - Troubleshooting table
   - Key files map
   - API endpoints summary
   - Development principles (DO/DON'T)

   **When to use:** During development, when you need a specific command quickly

---

### 5. **`README.md`**
   **Purpose:** High-level project overview
   - Features highlight
   - Architecture diagram
   - RAG pipeline overview
   - Project structure
   - Quick start (setup, running)
   - Features (admin + student)

   **When to use:** Project introduction, onboarding new team members

---

## 🗺️ Learning Paths

### Path 1: Onboarding (New to project)
1. Read `README.md` (5 min) — What is AstroBot?
2. Review `DIAGRAMS.md` (10 min) — Visual understanding
3. Read `.github/copilot-instructions.md` (20 min) — Complete picture
4. Use `QUICKREF.md` (5 min) — Save for reference

**Total: ~40 minutes to understand the project**

### Path 2: RAG Deep Dive (Understanding retrievl + generation)
1. Read ARCHITECTURE.md § "RAG Pipeline Mechanics" (15 min)
2. Review `DIAGRAMS.md` § "RAG Pipeline Flow" (10 min)
3. Read `.github/copilot-instructions.md` § "Core Components" (20 min)
4. Review ARCHITECTURE.md § "Data Flow Examples" (15 min)

**Total: ~60 minutes to understand RAG fully**

### Path 3: Performance Optimization
1. Review `QUICKREF.md` § "Performance Targets" (5 min)
2. Read `ARCHITECTURE.md` § "Performance Metrics" (15 min)
3. Review `DIAGRAMS.md` § "Performance Timeline" (10 min)
4. Use debugging tips in `QUICKREF.md` (10 min)

**Total: ~40 minutes to understand performance**

### Path 4: Adding New Features
1. Start with `QUICKREF.md` § "Common Workflows" (10 min)
2. Review relevant section in `ARCHITECTURE.md` (20 min)
3. Check `QUICKREF.md` § "Development Principles" (5 min)
4. Consult `.github/copilot-instructions.md` § "Development Conventions" (10 min)

**Total: ~45 minutes to start coding new features**

---

## 🔍 Quick Search Reference

### I need to understand...

| Topic | Document | Section |
|-------|----------|---------|
| **What is AstroBot?** | README.md | "Quick Start" / "Features" |
| **System architecture** | ARCHITECTURE.md | "System Overview" |
| **RAG pipeline** | ARCHITECTURE.md | "RAG Pipeline Mechanics" |
| **Database schema** | DIAGRAMS.md | "Database Schema Diagram" |
| **Configuration** | QUICKREF.md | "Configuration" |
| **Performance metrics** | ARCHITECTURE.md | "Performance Metrics" |
| **LLM providers** | ARCHITECTURE.md § 6 | "LLM Provider Chain" |
| **How to upload docs** | ARCHITECTURE.md | "Data Flow Examples § 1" |
| **How questions are answered** | ARCHITECTURE.md | "Data Flow Examples § 2" |
| **Adding new LLM** | ARCHITECTURE.md | "Development Guide" |
| **Debugging** | QUICKREF.md | "Debugging" |
| **API endpoints** | QUICKREF.md | "API Endpoints" |
| **Common issues** | QUICKREF.md | "Troubleshooting" |
| **Development conventions** | .github/copilot-instructions.md | "Development Conventions" |
| **Security** | .github/copilot-instructions.md | "Security Considerations" |

---

## 📊 Component Reference

### Data Flow

```
Document Upload:
  User → UI → Parser → Chunker → Embedder → ChromaDB + SQLite

User Question:
  User → UI → Retriever → Generator → ProviderManager → LLM → UI
```

### Key Files

| Component | Primary File | Secondary Files |
|-----------|---|---|
| **Config** | `config.py` | `.env` |
| **Database** | `database/db.py` | — |
| **Authentication** | `auth/auth.py` | — |
| **Ingestion** | `ingestion/chunker.py` | `parser.py`, `embedder.py` |
| **Retrieval** | `rag/retriever.py` | — |
| **Generation** | `rag/generator.py` | — |
| **Providers** | `rag/providers/manager.py` | `base.py`, `ollama_provider.py`, `groq_provider.py`, `gemini_provider.py` |
| **Streamlit UI** | `app.py` | `views/chat.py`, `views/admin.py` |
| **FastAPI** | `api_server.py` | — |
| **Spring Boot** | `springboot-backend/pom.xml` | `AstroBotApplication.java`, controllers, services, DTOs |
| **React** | `react-frontend/src/App.jsx` | components, pages, services, context |

---

## ⚡ Command Reference

### Setup
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\start-all-servers.ps1
```

### Access
```
Streamlit: http://localhost:8501
FastAPI:   http://localhost:8000
Spring:    http://localhost:8080
React:     http://localhost:5173
```

### Common Python Operations
```python
# Database
from database.db import init_db, authenticate_user, log_query
init_db()

# Embeddings
from ingestion.embedder import generate_embeddings, get_collection

# RAG
from rag.retriever import retrieve_context
from rag.generator import generate_response

# Providers
from rag.providers.manager import get_manager, reset_manager
```

---

## 🎯 Document Purpose Summary

```
┌──────────────────────────────┬────────────┬──────────────────┐
│ Document                     │ Length     │ Best for         │
├──────────────────────────────┼────────────┼──────────────────┤
│ README.md                    │ Medium     │ Intro            │
│ .github/copilot-instr.md    │ Long       │ Complete ref     │
│ ARCHITECTURE.md              │ Very Long  │ Deep understanding
│ DIAGRAMS.md                  │ Medium     │ Visual learning  │
│ QUICKREF.md                  │ Short      │ Quick lookup     │
└──────────────────────────────┴────────────┴──────────────────┘
```

---

## 📝 Version Info

- **Project Version:** 2.0.0
- **Python:** 3.9+
- **Java:** 17+
- **Node.js:** 18+
- **Last Updated:** March 2026
- **Maintainer:** IMS Institutional AI Team

---

## 🚀 How to Use These Docs

1. **First time?** → Start with `README.md` then `.github/copilot-instructions.md`
2. **Have a question?** → Use the "Quick Search Reference" table above
3. **Need to code?** → Use `QUICKREF.md` for commands, `ARCHITECTURE.md` for understanding
4. **Presenting?** → Use `DIAGRAMS.md` for visuals
5. **Stuck?** → Check `QUICKREF.md` § "Troubleshooting"

---

## 📞 Document Navigation

- **High-level:** README.md
- **Complete reference:** .github/copilot-instructions.md
- **Deep dive:** ARCHITECTURE.md
- **Visual:** DIAGRAMS.md
- **Quick lookups:** QUICKREF.md
- **This file:** INDEX.md (you are here)

---

**All documentation is current and synchronized as of March 2026.**

