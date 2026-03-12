# 🤖 IMS AstroBot

**Institutional AI Assistant — Powered by RAG + Local LLM**

IMS AstroBot is a Retrieval-Augmented Generation (RAG) chatbot built for institutional use. It combines a React-based admin dashboard with a RAG pipeline to let students and faculty ask questions about institutional documents. Administrators get real-time analytics, document management, and AI configuration tools.

**Latest Version:** 2.0.0 | **Status:** Production-Ready | **License:** MIT

---

## ✨ Key Features

### For Students & Faculty
- 💬 **Smart Q&A** — Ask natural language questions about institutional documents
- 📚 **Source Citations** — Every response includes exact document references
- ⚡ **Fast Search** — Semantic vector search via ChromaDB (sub-second retrieval)
- 🔐 **Role-Based Access** — Faculty and student roles with login authentication

### For Administrators  
- 📄 **Document Management** — Upload, index, search, and delete documents (PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML)
- 👥 **User Management** — Create users, enable/disable accounts, manage roles (admin/faculty/student)
- 📊 **Usage Analytics** — Dashboard with total queries, top users, response times, daily trends
- 📋 **Query Logs** — Inspect recent queries with full responses and source documents
- 🤖 **AI Settings** — Swap GGUF models, tune temperature/tokens, edit system prompts
- 🩺 **System Health** — Real-time status checks for SQLite, ChromaDB, LLM, embeddings, file storage

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Browser (React)                            │
│                  http://localhost:3000                        │
└────────────────┬─────────────────────────────────────────────┘
                 │ HTTP(S)
                 ▼
┌──────────────────────────────────────────────────────────────┐
│              Spring Boot API Gateway                          │
│         (Proxy/Load Balancer - Port 8080)                    │
│    ✓ Authentication  ✓ Error Handling  ✓ CORS               │
└─────────────────┬────────────────────────────────────────────┘
                  │ HTTP (Forward to FastAPI)
                  ▼
┌──────────────────────────────────────────────────────────────┐
│           Python FastAPI RAG Server                           │
│               Port 8000                                       │
│  ✓ Document Processing  ✓ RAG Pipeline  ✓ User/Admin APIs  │
└─────────┬───────────┬──────────────┬────────────┬────────────┘
          │           │              │            │
          ▼           ▼              ▼            ▼
      ┌────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐
      │ SQLite │  │ ChromaDB│  │  Ollama  │  │ Embedder │
      │   DB   │  │(Vector) │  │   API    │  │(sentence-│
      │        │  │         │  │          │  │transform)
      └────────┘  └─────────┘  └──────────┘  └──────────┘
```

### Data Flow

1. **User asks question** → React → Spring Boot (8080) → FastAPI (8000)
2. **FastAPI embeds query** using `all-MiniLM-L6-v2` model
3. **ChromaDB retrieves** top-5 relevant document chunks via vector similarity
4. **Ollama generates** answer with retrieved context (local or cloud: Groq/Gemini)
5. **Response sent back** → Spring Boot → React with sources

---

## 📁 Project Structure

```
RAG_Astrobot/
│
├── 📄 Core Files
│   ├── api_server.py              # FastAPI REST API (port 8000)
│   ├── config.py                  # Configuration loader (.env)
│   ├── requirements.txt            # Python dependencies
│   └── .env                        # Environment variables
│
├── 🐍 Python Backend
│   ├── auth/
│   │   └── auth.py                # JWT token generation & validation
│   │
│   ├── database/
│   │   └── db.py                  # SQLite layer — users, documents, query logs
│   │
│   ├── ingestion/
│   │   ├── parser.py              # Multi-format document parsing
│   │   ├── chunker.py             # Text chunking (500 chars, 50 overlap)
│   │   └── embedder.py            # ChromaDB integration
│   │
│   ├── views/
│   │   ├── chat.py                # Chat endpoint logic
│   │   └── admin.py               # Admin operations
│   │
│   └── rag/
│       ├── provider/               # LLM providers (Ollama, Gemini, Groq)
│       ├── retriever.py           # Vector search & context formatting
│       └── generator.py           # Response generation
│
├── ☕ Java Backend (Spring Boot)
│   └── springboot-backend/
│       ├── pom.xml                # Maven configuration
│       ├── src/main/java/com/astrobot/
│       │   ├── AstroBotApplication.java
│       │   ├── controller/        # REST endpoints (proxy to FastAPI)
│       │   ├── dto/               # Data transfer objects
│       │   └── service/           # Business logic (proxying)
│       └── target/                # Compiled JAR files
│
├── ⚛️ React Frontend
│   └── react-frontend/
│       ├── vite.config.js         # Vite configuration with proxy
│       ├── package.json           # NPM dependencies
│       ├── index.html             # Entry point
│       ├── src/
│       │   ├── App.jsx            # Main app component
│       │   ├── main.jsx           # React entry
│       │   ├── pages/
│       │   │   ├── ChatPage.jsx    # Student/faculty chat
│       │   │   ├── LoginPage.jsx   # Login/register
│       │   │   └── admin/         # Admin dashboard pages
│       │   │       ├── DocumentsPage.jsx
│       │   │       ├── UsersPage.jsx
│       │   │       ├── AnalyticsPage.jsx
│       │   │       ├── SettingsPage.jsx
│       │   │       └── HealthPage.jsx
│       │   ├── components/        # Reusable React components
│       │   ├── services/
│       │   │   └── api.js         # Axios HTTP client
│       │   └── context/
│       │       └── AuthContext.jsx # Global auth state
│       └── dist/                   # Production build output
│
├── 📦 Data Storage
│   ├── data/
│   │   ├── chroma_db/             # ChromaDB persistent vector store
│   │   └── uploads/               # User-uploaded documents
│   ├── models/
│   │   └── *.gguf                 # GGUF model files
│   └── astrobot.db                # SQLite database file
│
├── 🐳 Deployment
│   ├── docker-compose.yml         # Dev deployment
│   ├── docker-compose.prod.yml    # Production deployment
│   ├── Dockerfile.api             # FastAPI container
│   ├── springboot-backend/Dockerfile
│   ├── react-frontend/Dockerfile
│   ├── deploy-lite.py             # Deployment script
│   └── quick-setup.sh             # Quick-start script
│
└── 🚀 Batch Scripts (Windows)
    ├── start-all-servers.bat      # Start all 3 services
    └── stop-all-servers.bat       # Stop all services
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- **Python 3.10+ & pip**
- **Node.js 16+ & npm**
- **Java 17+** (for Spring Boot)
- **Git**
- **Ollama** (https://ollama.ai) — *Optional for local LLM; cloud APIs work without it*
- **Ollama Model** (e.g., `ollama pull mistral`) — *Only needed if using local Ollama*

### Step 1: Clone Repository

```bash
git clone https://github.com/Unknown27s/Astro_bot.git
cd RAG_Astrobot
```

### Step 2: Create Python Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env  (or create manually if .env.example doesn't exist)
```

**Edit `.env` with:**
```ini
# ═══ LLM Configuration ═══
# Choose: local_only (Ollama), cloud_only (Groq/Gemini), or hybrid
LLM_MODE=cloud_only
LLM_PRIMARY_PROVIDER=groq
LLM_FALLBACK_PROVIDER=gemini

# Local Ollama (for LLM_MODE=local_only or hybrid)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Cloud APIs (for cloud_only or hybrid)
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

GEMINI_API_KEY=AIza_your_key_here
GEMINI_MODEL=gemini-3-flash-preview

# ═══ Generation Parameters ═══
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=512

# ═══ Database & Storage ═══
SQLITE_DB_PATH=data/astrobot.db
VECTOR_DB_PATH=data/chroma_db
UPLOAD_DIR=data/uploads

# ═══ Embeddings ═══
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# ═══ Admin Credentials (change after first login!) ═══
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### Step 5: Start All Servers

**Option A: Windows (Automated)**

Double-click `start-all-servers.bat` — Opens 3 terminal windows automatically. This will start:
- ✅ FastAPI on http://localhost:8000
- ✅ Spring Boot on http://localhost:8080  
- ✅ React on http://localhost:3000

Or run from command line:
```bash
start-all-servers.bat
```

**Option B: Manual (All Platforms)**

Open 3 separate terminal windows from project root:

**Terminal 1 — FastAPI (Python)**
```bash
# Windows
.venv\Scripts\activate
python api_server.py

# macOS/Linux
source .venv/bin/activate
python api_server.py
```
→ Running on http://localhost:8000

**Terminal 2 — Spring Boot (Java)**
```bash
cd springboot-backend

# Windows
.\mvnw.cmd spring-boot:run

# macOS/Linux
./mvnw spring-boot:run
```
→ Running on http://localhost:8080

**Terminal 3 — React (Node.js)**
```bash
cd react-frontend
npm install  # (first time only)
npm run dev
```
→ Running on http://localhost:3000

### Step 6: Open in Browser

Navigate to **http://localhost:3000** and login with:
- **Username:** `admin`
- **Password:** `admin123`

---

## 🔑 Default Credentials

| Role | Username | Password | Permissions |
|------|----------|----------|------------|
| **Admin** | `admin` | `admin123` | Full access — manage users, documents, settings, analytics |
| **Faculty** | *Register* | *Your choice* | Can ask questions, view documents |
| **Student** | *Register* | *Your choice* | Can ask questions, view documents |

**Change default credentials after first login!**

---

## 📊 Admin Dashboard

After login as admin, access these pages from the sidebar:

| Page | Purpose |
|------|---------|
| **👥 Users** | Create/delete users, enable/disable accounts |
| **📄 Documents** | Upload, list, delete institutional documents |
| **💬 Chat** | Test RAG pipeline with sample queries |
| **📊 Analytics** | View queries per user, response times, trends |
| **🤖 Settings** | Upload GGUF models, tune LLM parameters, edit prompts |
| **🩺 Health** | Check system status (DB, embeddings, LLM, file storage) |

---

## 🐳 Docker Deployment

### Build Docker Images

```bash
# Build all three services
docker-compose -f docker-compose.prod.yml build

# Or build individually
docker build -t astrobot-api -f Dockerfile.api .
docker build -t astrobot-spring -f springboot-backend/Dockerfile springboot-backend
docker build -t astrobot-react -f react-frontend/Dockerfile react-frontend
```

### Run with Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f api      # FastAPI
docker-compose logs -f spring   # Spring Boot
docker-compose logs -f web      # React
```

### Stop Services

```bash
docker-compose down
```

---

## 📋 Configuration Reference

### Environment Variables (`.env`)

```ini
# ═══════════════ LLM MODE ═════════════════
LLM_MODE=cloud_only                      # local_only|cloud_only|hybrid
LLM_PRIMARY_PROVIDER=groq                # ollama|groq|gemini
LLM_FALLBACK_PROVIDER=gemini

# ═══════════════ OLLAMA (LOCAL) ════════════
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# ═══════════════ GROQ (CLOUD) ══════════════
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# ═══════════════ GEMINI (CLOUD) ════════════
GEMINI_API_KEY=AIza_your_key_here
GEMINI_MODEL=gemini-3-flash-preview

# ═══════════════ GENERATION ════════════════
MODEL_TEMPERATURE=0.3                    # 0=focused, 1=balanced, 2=creative
MODEL_MAX_TOKENS=512                     # Max response length

# ═══════════════ DATABASE ══════════════════
SQLITE_DB_PATH=data/astrobot.db
DATABASE_URL=sqlite:///astrobot.db

# ═══════════════ VECTOR STORE ══════════════
VECTOR_DB_PATH=data/chroma_db

# ═══════════════ EMBEDDINGS ════════════════
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# ═══════════════ STORAGE ═══════════════════
UPLOAD_DIR=data/uploads

# ═══════════════ AUTH & SECURITY ═══════════
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET=your-secret-key-here
JWT_EXPIRATION=24                        # hours

# ═══════════════ SPRING BOOT ═══════════════
SPRING_BOOT_PORT=8080
PYTHON_API_URL=http://localhost:8000

# ═══════════════ CORS & NETWORKING ═══════
REACT_PORT=3000
VITE_API_URL=/api
```

---

## ⚙️ LLM Configuration

### Mode 1: Local Ollama (No API Keys Required)

**Benefits:** Free, private, runs locally

```bash
# 1. Install Ollama: https://ollama.ai
# 2. Start Ollama server
ollama serve

# 3. In another terminal, pull a model
ollama pull mistral       # Fast, good quality
ollama pull gemma2:2b     # Smaller, faster
ollama pull llama2        # Larger, slower but better

# 4. Update .env
LLM_MODE=local_only
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

Restart FastAPI server.

### Mode 2: Cloud APIs (Groq + Gemini)

**Benefits:** More powerful models, no local hardware needed

Get API keys:
- **Groq:** https://console.groq.com/keys (fast, free tier)
- **Gemini:** https://makersuite.google.com/app/apikey (flexible, free tier)

**Update `.env`:**
```ini
LLM_MODE=cloud_only
LLM_PRIMARY_PROVIDER=groq
LLM_FALLBACK_PROVIDER=gemini

GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile

GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-3-flash-preview
```

Restart FastAPI.

### Mode 3: Hybrid (Local + Cloud Fallback)

**Benefits:** First tries local (fast/free), falls back to cloud if needed

```ini
LLM_MODE=hybrid
LLM_PRIMARY_PROVIDER=ollama
LLM_FALLBACK_PROVIDER=groq

# Configure both local and cloud
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 8000, 8080, or 3000 already in use** | `netstat -ano \| findstr ":8000"` (Windows) or `lsof -i :8000` (macOS/Linux), then kill process |
| **"Module not found" error** | Run `pip install -r requirements.txt` in active venv |
| **React shows 404 on API calls** | Ensure Spring Boot (8080) is running; check Vite proxy in `react-frontend/vite.config.js` |
| **Java not found** | Install Java 17+: https://adoptium.net/ |
| **ChromaDB permission error on Windows** | Close other terminals using the directory; restart |
| **Model loading is slow** | First-time model download takes 5-10 min; subsequent loads are instant (cached) |
| **Ollama not connecting** | Ensure `ollama serve` is running on `http://localhost:11434`; check `OLLAMA_BASE_URL` in `.env` |

---

## 📞 Support & Debugging

### Check System Health

Visit **http://localhost:3000/admin/health** in React UI for real-time status.

### View Server Logs

**FastAPI (Terminal 1):**
```
Look for: "Application startup complete" = Server ready
```

**Spring Boot (Terminal 2):**
```
Look for: "Tomcat started on port 8080 (http)" = Server ready
```

**React (Terminal 3):**
```
Look for: "VITE v5.x ready in Xms" = Frontend ready
```

### Test FastAPI Directly

```bash
# Get all users (FastAPI docs)
curl http://localhost:8000/docs

# Or with Python
curl -X GET http://localhost:8000/api/users
```

### Debug Spring Boot Proxy

Check if Spring Boot is forwarding correctly:
```bash
curl http://localhost:8080/api/users
```

If you get 404, Spring Boot endpoints aren't mapped. Check `springboot-backend/src/main/java/com/astrobot/controller/*.java`.

---

## 📦 Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | React | 18+ |
| **Frontend Build** | Vite | 5+ |
| **API Gateway** | Spring Boot | 3.2+ |
| **RAG Engine** | FastAPI | 0.100+ |
| **Vector DB** | ChromaDB | Latest |
| **LLM Inference** | Ollama API | Latest |
| **Embeddings** | sentence-transformers | Latest |
| **Backend DB** | SQLite | 3.40+ |
| **LLM Models** | GGUF (.gguf files) | N/A |
| **Java Runtime** | OpenJDK | 17+ |
| **Node.js** | Node | 16+ |
| **Python** | Python | 3.10-3.12 |

---

## 📚 Supported Document Formats

| Format | Extension | Support |
|--------|-----------|---------|
| PDF | `.pdf` | ✅ Full |
| Word | `.docx` | ✅ Full |
| Plain Text | `.txt` | ✅ Full |
| Excel | `.xlsx` | ✅ Full |
| CSV | `.csv` | ✅ Full |
| PowerPoint | `.pptx` | ✅ Full |
| HTML | `.html, .htm` | ✅ Full |

---

## 📄 License

This project is licensed under the **MIT License** — see LICENSE file for details.

---

## ⚙️ Configuration Reference

All configuration is managed via `.env` and `config.py`. The AI Settings page in the admin dashboard allows real-time editing of most parameters.

### LLM Parameters

| Parameter | Range | Default | Effect |
|---|---|---|---|
| Temperature | 0.0 – 2.0 | 0.3 | Higher = more creative responses |
| Max Tokens | 64 – 4096 | 512 | Maximum response length |

### Chunking Parameters

| Parameter | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | 500 | Characters per chunk |
| `CHUNK_OVERLAP` | 50 | Overlapping characters between chunks |

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| **Ollama not connecting** | Ensure `ollama serve` is running on `http://localhost:11434`; check `OLLAMA_BASE_URL` in `.env` |
| **Ollama model not found** | Run `ollama pull <model-name>` (e.g., `ollama pull mistral`) |
| **No response from LLM** | Check `LLM_MODE` in `.env`; ensure Ollama running (local mode) or API keys valid (cloud mode) |
| Blank page on startup | Clear `__pycache__` folders: `Get-ChildItem -Recurse -Directory -Filter __pycache__ \| Remove-Item -Recurse -Force` |
| Slow first query | Normal — embedding model (~80 MB) loads on first use, subsequent queries are fast |
| "Fallback Mode" warning | No LLM provider available — configure a provider in `.env` and restart |

---

## 📄 License

This project is licensed under the **MIT License** — see LICENSE file for details.

---

<div align="center">
  <b>IMS AstroBot v2.0</b> — Powered by RAG + Ollama<br>
  Built with ❤️ using React, ChromaDB, FastAPI, and Spring Boot
</div>
