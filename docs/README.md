# 📚 AstroBot v2.0 Documentation

Welcome to the AstroBot documentation! This directory contains comprehensive guides for setup, development, and API usage.

---

## 📖 Documentation Index

### 🚀 [01 - Quick Start](./01-QUICKSTART.md)
**Getting started in 5 minutes**
- Installation steps
- Dependency verification
- Environment configuration
- Running locally
- Quick feature tests
- Troubleshooting

**Start here if you want to:** Get the app running quickly

---

### 🔧 [02 - Implementation Summary](./02-IMPLEMENTATION_SUMMARY.md)
**Complete implementation details**
- Executive summary of features
- Feature-by-feature breakdown:
  - **Phase 1**: Error Tracking & Structured Logging
  - **Phase 2**: Rate Limiting
  - **Phase 3**: Document Tagging/Classification
- Files created and modified
- Configuration options
- Testing checklist

**Start here if you want to:** Understand what was implemented and how

---

### 📡 [04 - API Endpoints](./04-API_ENDPOINTS.md)
**Complete REST API reference**
- Tag Management endpoints
- Document Tagging endpoints
- Classification endpoints
- Search & Filtering
- Rate Limits
- Error Responses

**Start here if you want to:** Integrate with the API

---

### ⏱️ [05 - Admin Rate Limiting](./05-ADMIN_RATE_LIMITING.md)
**Rate limit configuration guide**
- Per-endpoint rate limits
- Admin configuration
- Monitoring rate limits

---

### 🤝 [Contribution Guide](./contribution/CONTRIBUTING.md)
**How to add new features yourself**
- Architecture overview & data flow
- Adding new API endpoints (Python → Spring Boot → React)
- Adding new UI pages (React & Streamlit)
- Adding new LLM providers
- Adding new document parsers
- Database changes
- Testing checklist
- Common patterns & troubleshooting

Also see: [WORKFLOW.md](./contribution/WORKFLOW.md) - Quick checklist for feature development

---

### 📝 [Changelog](./CHANGELOG.md)
**Version history and changes**
- Bug fixes and improvements
- Files created/modified/deleted
- Project structure after cleanup

---

## 🎯 Choose Your Path

### 👤 I'm New - Just Want to Run the App
**Follow this path:**
1. Read: [01-QUICKSTART.md](./01-QUICKSTART.md) - 5 min
2. Run: `pip install -r requirements.txt && python api_server.py`
3. Test: `curl http://localhost:8000/api/health`

### 👨‍💻 I'm a Developer - Want to Understand Implementation
**Follow this path:**
1. Read: [START_HERE.md](./START_HERE.md) - Quick overview
2. Read: [COPILOT_GUIDE.md](./COPILOT_GUIDE.md) - Development workflow
3. Review: [02-IMPLEMENTATION_SUMMARY.md](./02-IMPLEMENTATION_SUMMARY.md)
4. Explore: [04-API_ENDPOINTS.md](./04-API_ENDPOINTS.md)
5. Check: [IMPROVEMENTS_NEEDED.md](./IMPROVEMENTS_NEEDED.md) - What needs work next

---

## 📁 Documentation Structure

```
docs/
├── 01-QUICKSTART.md          # Getting started guide
├── 02-IMPLEMENTATION_SUMMARY.md  # Implementation details
├── 04-API_ENDPOINTS.md       # REST API reference
├── 05-ADMIN_RATE_LIMITING.md # Rate limiting config
├── COPILOT_GUIDE.md          # AI agent/developer workflow
├── START_HERE.md             # Quick project overview
├── INDEX.md                  # Documentation index
├── IMPROVEMENTS_NEEDED.md    # Roadmap & next steps (NEW!)
├── README.md                 # This file
│
├── architecture/
│   ├── COMPLETE_UNDERSTANDING.md  # Full system docs
│   └── DATABASE_SCHEMA.md         # Database structure
│
├── development/
│   └── DEVELOPMENT_GUIDE.md       # Development workflow
│
├── guides/
│   ├── QUICKREF.md               # Quick reference commands
│   ├── QUICKSTART.md             # Setup guide
│   └── TROUBLESHOOTING.md        # Common issues & fixes
│
├── contribution/
│   ├── CONTRIBUTING.md           # How to add new features
│   └── WORKFLOW.md               # Quick development checklist
│
└── CHANGELOG.md                  # Version history
```

---

## 🔑 Key Features

✅ **RAG Pipeline** - Retrieval-Augmented Generation for document Q&A  
✅ **Error Tracking** - Sentry integration for monitoring  
✅ **Structured Logging** - JSON logs with request tracing  
✅ **Rate Limiting** - Per-user and endpoint-specific limits  
✅ **Document Tagging** - Flexible multi-tag system  
✅ **Document Classification** - Semantic document organization  
✅ **Advanced Search** - Filter by tags and classification  
✅ **Multi-Provider LLM** - Ollama, Grok, Gemini with fallback  

---

## 📊 Architecture Overview

```
React Frontend (3000) → Spring Boot (8080) → Python FastAPI (8001)
                                                    ↓
                                            ┌──────┴──────┐
                                            │             │
                                        ChromaDB      SQLite
                                        (vectors)    (relational)
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

**Last Updated:** March 2026  
**Version:** 2.0.0
