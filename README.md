# 🤖 IMS AstroBot

**Institutional AI Assistant — Powered by RAG + Local LLM**

IMS AstroBot is a Retrieval-Augmented Generation (RAG) chatbot built for institutional use. It lets students and faculty ask natural language questions about uploaded institutional documents — regulations, policies, handbooks, circulars, and more — and get accurate, context-grounded answers.

---

## ✨ Features

### For Students & Faculty
- 💬 **Conversational Q&A** — Ask questions in natural language and get answers sourced from institutional documents
- 📚 **Source Citations** — Every response includes references to the source documents
- ⚡ **Fast Retrieval** — Semantic search via ChromaDB for instant context retrieval

### For Administrators
- 📄 **Document Management** — Upload, index, and manage institutional documents (PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML)
- 👥 **User Management** — Create, enable/disable, and delete user accounts with role-based access
- 📊 **Usage Analytics** — Track total queries, daily trends, top users, and response times
- 📋 **Query Logs** — View recent queries with responses, sources, and timing data
- 🤖 **AI Settings** — Upload/swap GGUF models, tune LLM parameters, edit system prompt, change embedding model
- 🩺 **System Health Dashboard** — Real-time status of SQLite, ChromaDB, LLM, embeddings, and uploads

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  Streamlit UI                    │
│         (app.py — role-based routing)            │
├─────────┬───────────┬───────────┬───────────────┤
│  Login  │  Admin    │  Student/ │   AI          │
│  Page   │  Dashboard│  Faculty  │   Settings    │
│         │           │  Chat     │               │
└────┬────┴─────┬─────┴─────┬─────┴───────┬───────┘
     │          │           │             │
     ▼          ▼           ▼             ▼
┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│  Auth   │ │ SQLite │ │   RAG    │ │  Config  │
│ (auth/) │ │(db.py) │ │ Pipeline │ │(.env)    │
└─────────┘ └────────┘ └────┬─────┘ └──────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
              ┌──────────┐    ┌─────────────┐
              │ ChromaDB │    │ GGUF Model  │
              │ (Vector  │    │ (llama.cpp) │
              │  Search) │    │             │
              └──────────┘    └─────────────┘
```

### RAG Pipeline

1. **Document Ingestion** — Upload → Parse (PyPDF2/python-docx/etc.) → Chunk (500 chars, 50 overlap) → Embed (`all-MiniLM-L6-v2`) → Store in ChromaDB
2. **Query Processing** — User question → Embed → Semantic search (top-5 chunks) → Format context
3. **Response Generation** — Context + question → Local GGUF LLM (Phi-3/etc.) → Answer with citations

---

## 📁 Project Structure

```
RAG_Astrobot/
├── app.py                  # Main entry point — login, routing, dashboards
├── config.py               # Central configuration (reads .env)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (model path, params, keys)
├── .streamlit/
│   └── config.toml         # Streamlit theme & settings
├── auth/
│   ├── __init__.py
│   └── auth.py             # Authentication — login, logout, register, sessions
├── views/
│   ├── __init__.py
│   ├── chat.py             # Chat interface with RAG pipeline
│   └── admin.py            # Document management + AI settings page
├── database/
│   ├── __init__.py
│   └── db.py               # SQLite CRUD — users, documents, query_logs
├── ingestion/
│   ├── __init__.py
│   ├── parser.py           # Document parsers (PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML)
│   ├── chunker.py          # Text chunking with overlap
│   └── embedder.py         # Sentence-transformers embeddings + ChromaDB storage
├── rag/
│   ├── __init__.py
│   ├── retriever.py        # Semantic search & context formatting
│   └── generator.py        # LLM generation (llama-cpp-python) with fallback
├── models/                 # Place GGUF model files here
│   └── (your-model.gguf)

    ├── uploads/            # Uploaded document files
    ├── chroma_db/          # ChromaDB persistent storage
    └── astrobot.db         # SQLite database
```

### Prerequisites

- **Python 3.10–3.12** (3.13+ may have compatibility issues with `llama-cpp-python`)
- **C++ Build Tools** — Required for `llama-cpp-python` (Visual Studio Build Tools on Windows)

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd RAG_Astrobot

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate
```
### 2. Install Dependencies

```bash
```

### 3. Configure Environment
Copy the example `.env` file and edit as needed:

```bash
cp .env.example .env
```

Key settings in `.env`:

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `models\phi-3-mini-4k-instruct-q4.gguf` | Path to GGUF model file |
| `MODEL_TEMPERATURE` | `0.3` | LLM temperature (0 = focused, 2 = creative) |
| `MODEL_MAX_TOKENS` | `512` | Max response length in tokens |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD` | `admin123` | Default admin password |

### 4. Download a GGUF Model

Download a quantized GGUF model and place it in the `models/` directory. Recommended:

- [Phi-3-mini-4k-instruct-Q4](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf) (~2.3 GB)
- [Mistral-7B-Instruct-Q4](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF) (~4.1 GB)


> **Note:** The app works in **fallback mode** without a model — it returns retrieved context directly instead of generating answers.

### 5. Run the App

You have two options: the **full-stack setup** (React + Spring Boot + Python API) or the **Streamlit standalone** UI.

---

#### Option A: Full-Stack (React + Spring Boot + FastAPI)

This runs three services. Open **three separate terminals** from the project root:

**Terminal 1 — Python FastAPI RAG Server (port 8000)**

```bash
# Activate virtual environment first
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Start the FastAPI server
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Spring Boot Backend (port 8080)**

```bash
cd springboot-backend

# Windows (using Maven wrapper):
.\mvnw.cmd spring-boot:run

# macOS/Linux:
./mvnw spring-boot:run

# Or if Maven is installed globally:
mvn spring-boot:run
```

> Requires **Java 17+**. The Spring Boot backend proxies REST calls to the Python API at `http://localhost:8000`.

**Terminal 3 — React Frontend (port 3000)**

```bash
cd react-frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

Open **http://localhost:3000** in your browser.

**Build React for Production:**

```bash
cd react-frontend
npm run build    # outputs to dist/
npm run preview  # preview the production build
```

---

#### Option B: Streamlit Standalone UI (port 8501)

```bash
# Activate virtual environment first
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

### Port Summary

| Service | Port | Command |
|---|---|---|
| Python FastAPI (RAG engine) | `8000` | `uvicorn api_server:app --port 8000 --reload` |
| Spring Boot Backend | `8080` | `.\mvnw.cmd spring-boot:run` |
| React Frontend | `3000` | `npm run dev` (from `react-frontend/`) |
| Streamlit UI (standalone) | `8501` | `streamlit run app.py` |

---

## 🔐 Default Login

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |

Students and faculty can register via the login page.

---

## 📖 Usage

### Admin Workflow

1. **Login** → Select "Admin Login" in the sidebar → Enter credentials
2. **Upload Documents** → Navigate to "📄 Documents" → Upload PDF/DOCX/TXT files → Click "Process & Upload"
3. **Monitor** → Check "📊 Analytics" for query stats, "👥 Users" for account management
4. **Configure AI** → "🤖 AI Settings" to tune model parameters, upload new GGUF models, edit system prompt
5. **Test** → Use "💬 Test Chat" to verify the RAG pipeline

### Student/Faculty Workflow

1. **Login/Register** → Select "Student/Faculty" in the sidebar → Login or create an account
2. **Ask Questions** → Type questions in the chat input about institutional documents
3. **View Sources** → Expand "📚 Sources" under each response to see cited documents

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Frontend (Modern)** | React 18 + Vite |
| **Frontend (Legacy)** | Streamlit |
| **API Gateway** | Spring Boot 3.2 (Java 17) |
| **RAG Engine** | FastAPI + Uvicorn |
| **LLM Providers** | Ollama (local), Gemini, Groq |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) |
| **Vector Database** | ChromaDB (persistent, cosine similarity) |
| **Relational Database** | SQLite |
| **Document Parsing** | PyPDF2, python-docx, openpyxl, python-pptx, BeautifulSoup4 |
| **Configuration** | python-dotenv (`.env` file) |

---

## 📂 Supported Document Formats

| Format | Extension | Parser |
|---|---|---|
| PDF | `.pdf` | PyPDF2 |
| Word | `.docx` | python-docx |
| Plain Text | `.txt` | Built-in |
| Excel | `.xlsx` | openpyxl |
| CSV | `.csv` | Built-in csv |
| PowerPoint | `.pptx` | python-pptx |
| HTML | `.html`, `.htm` | BeautifulSoup4 |

---

## ⚙️ Configuration Reference

All configuration is managed via `.env` and `config.py`. The AI Settings page in the admin dashboard allows real-time editing of most parameters.

### LLM Parameters

| Parameter | Range | Default | Effect |
|---|---|---|---|
| Temperature | 0.0 – 2.0 | 0.3 | Higher = more creative responses |
| Max Tokens | 64 – 4096 | 512 | Maximum response length |
| Context Size | 512 – 16384 | 4096 | Token context window |
| CPU Threads | 1 – 16 | 4 | Parallel inference threads |

### Chunking Parameters

| Parameter | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | 500 | Characters per chunk |
| `CHUNK_OVERLAP` | 50 | Overlapping characters between chunks |

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| `llama-cpp-python` won't install | Install C++ Build Tools: `winget install Microsoft.VisualStudio.2022.BuildTools` |
| Model not loading | Check `MODEL_PATH` in `.env` matches the actual filename in `models/` |
| Blank page on startup | Clear `__pycache__` folders: `Get-ChildItem -Recurse -Directory -Filter __pycache__ \| Remove-Item -Recurse -Force` |
| Slow first query | Normal — embedding model (~80 MB) loads on first use, subsequent queries are fast |
| "Fallback Mode" warning | No GGUF model found — download one to `models/` or use without LLM generation |

---

## 📄 License

This project was built for the IMS Institutional Hackathon.

---

<div align="center">
  <b>IMS AstroBot v1.0</b> — Powered by RAG + llama.cpp<br>
  Built with ❤️ using Streamlit, ChromaDB, and sentence-transformers
</div>
