# 📚 IMS AstroBot Documentation Hub

**Comprehensive documentation for IMS AstroBot v2.0 — RAG-powered institutional AI assistant**

---

## 🎯 Quick Navigation

### 🤖 **For AI Agents & Copilot**
→ Start with **[START_HERE.md](START_HERE.md)**  
→ Then read **[COPILOT_GUIDE.md](COPILOT_GUIDE.md)**  
→ Reference **[guides/QUICKREF.md](guides/QUICKREF.md)** while working

### 👨‍💻 **For Developers**
→ **[guides/QUICKREF.md](guides/QUICKREF.md)** — Quick reference  
→ **[architecture/COMPLETE_UNDERSTANDING.md](architecture/COMPLETE_UNDERSTANDING.md)** — Full system overview  
→ **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** — Deep dive  
→ **[development/DEVELOPMENT_GUIDE.md](development/DEVELOPMENT_GUIDE.md)** — How to add features

### 📊 **For Understanding Visually**
→ **[architecture/DIAGRAMS.md](architecture/DIAGRAMS.md)** — All flow diagrams

### 🚀 **For Getting Started**
→ **[guides/QUICKSTART.md](guides/QUICKSTART.md)** — 5-minute setup

### 📍 **For Navigation**
→ **[INDEX.md](INDEX.md)** — Complete documentation index

---

## 📁 Folder Structure

```
docs/
├── README.md                    ← You are here
├── START_HERE.md               ← Start for copilots
├── COPILOT_GUIDE.md            ← AI agent instructions
├── INDEX.md                    ← Documentation index
│
├── guides/
│   ├── QUICKREF.md             ← Commands & quick lookup
│   ├── QUICKSTART.md           ← 5-min setup
│   └── TROUBLESHOOTING.md      ← Common issues
│
├── architecture/
│   ├── COMPLETE_UNDERSTANDING.md   ← System overview
│   ├── ARCHITECTURE.md             ← Component details
│   ├── DIAGRAMS.md                 ← Flow diagrams
│   └── DATABASE_SCHEMA.md          ← DB documentation
│
└── development/
    ├── DEVELOPMENT_GUIDE.md     ← Adding features
    ├── CODE_CONVENTIONS.md      ← Coding standards
    ├── ADDING_PROVIDERS.md      ← New LLM providers
    └── PERFORMANCE_OPTIMIZATION.md
```

---

## 🎓 Learning Paths

### Path 1: AI Agent Onboarding (20 min)
1. [START_HERE.md](START_HERE.md) — Read first
2. [COPILOT_GUIDE.md](COPILOT_GUIDE.md) — Workflow instructions
3. [guides/QUICKREF.md](guides/QUICKREF.md) — Save for reference

### Path 2: Developer Onboarding (45 min)
1. [guides/QUICKSTART.md](guides/QUICKSTART.md) — Setup
2. [architecture/COMPLETE_UNDERSTANDING.md](architecture/COMPLETE_UNDERSTANDING.md) — Overview
3. [guides/QUICKREF.md](guides/QUICKREF.md) — Commands
4. [development/CODE_CONVENTIONS.md](development/CODE_CONVENTIONS.md) — Standards

### Path 3: RAG Deep Dive (60 min)
1. [architecture/COMPLETE_UNDERSTANDING.md](architecture/COMPLETE_UNDERSTANDING.md) § RAG Pipeline
2. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) § Component Details
3. [architecture/DIAGRAMS.md](architecture/DIAGRAMS.md) § Flows

### Path 4: Adding Features (45 min)
1. [development/DEVELOPMENT_GUIDE.md](development/DEVELOPMENT_GUIDE.md)
2. [guides/QUICKREF.md](guides/QUICKREF.md) § Common Workflows
3. [development/CODE_CONVENTIONS.md](development/CODE_CONVENTIONS.md)

---

## 📊 What This Documentation Covers

✅ **System Architecture** — 3-tier design, components, data flow  
✅ **RAG Pipeline** — How documents are stored and questions answered  
✅ **Performance Metrics** — Latency, memory, throughput, scaling  
✅ **Database Schema** — SQLite and ChromaDB structure  
✅ **API Documentation** — All FastAPI endpoints  
✅ **Security** — Authentication, data protection, best practices  
✅ **Development Guide** — How to add features, providers, parsers  
✅ **Troubleshooting** — Common issues and solutions  
✅ **Code Conventions** — Style, standards, patterns  
✅ **Deployment** — Production deployment guide  

---

## 🚀 Quick Start

```powershell
# Setup (5 minutes)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run all servers
.\start-all-servers.ps1

# Access
Streamlit:  http://localhost:8501
FastAPI:    http://localhost:8000  
Spring Boot: http://localhost:8080
```

See [guides/QUICKSTART.md](guides/QUICKSTART.md) for detailed setup.

---

## 🤖 For AI Agents / Copilot

### Before Working on This Project

**You MUST read these in order:**

1. **[START_HERE.md](START_HERE.md)** (5 min)
   - What is AstroBot
   - Key concepts
   - System overview

2. **[COPILOT_GUIDE.md](COPILOT_GUIDE.md)** (10 min)
   - RAG pipeline mechanics
   - Component interactions
   - Debugging workflow
   - Common patterns

3. **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** (15 min)
   - Deep dive into components
   - When to use each module
   - Common mistakes

**Then use as reference:**
- [guides/QUICKREF.md](guides/QUICKREF.md) — Commands & quick lookup
- [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md) — When stuck
- [development/CODE_CONVENTIONS.md](development/CODE_CONVENTIONS.md) — Coding standards

---

## 📞 Finding What You Need

| I need to understand... | Go to |
|------------------------|-------|
| **What is AstroBot?** | [START_HERE.md](START_HERE.md) |
| **System architecture** | [architecture/COMPLETE_UNDERSTANDING.md](architecture/COMPLETE_UNDERSTANDING.md) |
| **RAG pipeline** | [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) |
| **How to code** | [development/CODE_CONVENTIONS.md](development/CODE_CONVENTIONS.md) |
| **Quick commands** | [guides/QUICKREF.md](guides/QUICKREF.md) |
| **Visual flows** | [architecture/DIAGRAMS.md](architecture/DIAGRAMS.md) |
| **Debugging** | [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md) |
| **Adding features** | [development/DEVELOPMENT_GUIDE.md](development/DEVELOPMENT_GUIDE.md) |
| **New LLM provider** | [development/ADDING_PROVIDERS.md](development/ADDING_PROVIDERS.md) |
| **Database schema** | [architecture/DATABASE_SCHEMA.md](architecture/DATABASE_SCHEMA.md) |
| **Performance** | [development/PERFORMANCE_OPTIMIZATION.md](development/PERFORMANCE_OPTIMIZATION.md) |
| **All documentation** | [INDEX.md](INDEX.md) |

---

## 📈 Documentation Stats

- **Total documentation:** 40,000+ words
- **Code examples:** 50+
- **Diagrams:** 7+
- **Tables:** 20+
- **Files:** 12+

---

## ✨ Key Highlights

### For AI Agents
- ✅ Complete workflow documented
- ✅ Common patterns explained
- ✅ Error handling patterns shown
- ✅ RAG mechanics clearly described
- ✅ Component interactions illustrated
- ✅ "When to use" guidance provided

### For Developers
- ✅ Quick reference available
- ✅ Setup instructions clear
- ✅ Code conventions defined
- ✅ Troubleshooting guide included
- ✅ Performance guidance provided
- ✅ Development workflow documented

### For Architects
- ✅ System design explained
- ✅ Performance characteristics documented
- ✅ Scalability considerations listed
- ✅ Security measures described
- ✅ Component boundaries clear
- ✅ Data flow visualized

---

## 🎯 Next Steps

### If you're an AI Agent/Copilot:
→ Go to [START_HERE.md](START_HERE.md)  
→ Then [COPILOT_GUIDE.md](COPILOT_GUIDE.md)  
→ Then start working!

### If you're a Developer:
→ Go to [guides/QUICKSTART.md](guides/QUICKSTART.md)  
→ Then [guides/QUICKREF.md](guides/QUICKREF.md)  
→ Then start coding!

### If you need to understand everything:
→ Follow the "RAG Deep Dive" path above

---

## 📝 Version & Status

- **Project Version:** 2.0.0
- **Documentation Version:** 1.0
- **Last Updated:** March 2026
- **Status:** Complete ✅

---

**All documentation is current, complete, and ready for immediate use.**
