# 🛠️ IMS AstroBot — Technology Stack & Future Improvements

This document describes every technology used in the IMS AstroBot project and provides concrete recommendations for future improvement.

---

## 📦 Application Stack

### 1. Frontend — React (Port 3000)

| Technology | Version | Purpose |
|---|---|---|
| **React** | 18.3 | UI component framework |
| **React Router** | v6.23 | Client-side routing (SPA navigation) |
| **Vite** | 5.2 | Build tool & dev server (HMR, fast bundling) |
| **Axios** | 1.7 | HTTP client — calls Spring Boot API Gateway |
| **Recharts** | 2.12 | Analytics charts in admin dashboard |
| **Lucide React** | 0.378 | Icon library |
| **React Hot Toast** | 2.4 | Toast notifications |

**Entry point:** `react-frontend/src/App.jsx`  
**Key pages:** `ChatPage`, `LoginPage`, `DocumentsPage`, `UsersPage`, `AnalyticsPage`, `SettingsPage`, `HealthPage`

---

### 2. API Gateway — Spring Boot (Port 8080)

| Technology | Version | Purpose |
|---|---|---|
| **Java** | 17 | Language runtime |
| **Spring Boot** | 3.2.4 | Web framework & application container |
| **Spring Web MVC** | (via Boot) | REST controller layer |
| **Spring WebFlux / WebClient** | (via Boot) | Async HTTP proxy to FastAPI |
| **Spring Validation** | (via Boot) | Request DTO validation |
| **Lombok** | latest | Boilerplate reduction (getters, builders) |
| **Maven** | (wrapper) | Build & dependency management |

**Role:** Sits between the React frontend and the Python FastAPI backend. Handles CORS, authentication forwarding, and error normalisation.

---

### 3. Python RAG Backend — FastAPI (Port 8000)

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Language runtime |
| **FastAPI** | ≥ 0.110 | High-performance REST API (async) |
| **Uvicorn** | ≥ 0.27 | ASGI server for FastAPI |
| **python-multipart** | ≥ 0.0.7 | File upload handling |
| **Streamlit** | ≥ 1.30 | Alternative standalone UI (port 8501) |
| **python-dotenv** | ≥ 1.0 | `.env` file loading |
| **requests** | ≥ 2.31 | HTTP calls to Ollama / Groq / Gemini |
| **pandas** | ≥ 2.1 | CSV/Excel data processing |

**Entry point:** `api_server.py`

---

### 4. AI / RAG Pipeline

| Technology | Version | Purpose |
|---|---|---|
| **sentence-transformers** | ≥ 2.2 | Embedding model (`all-MiniLM-L6-v2`) — converts text to vectors |
| **ChromaDB** | ≥ 0.4.22 | Persistent vector store — semantic similarity search |
| **Ollama** | (external) | Local LLM inference server (any GGUF-compatible model) |
| **Groq API** | (cloud) | Cloud LLM — `llama-3.3-70b-versatile` (default) |
| **Google Gemini API** | (cloud) | Cloud LLM — `gemini-2.0-flash` (default) |

**RAG flow:** Query → embed with `all-MiniLM-L6-v2` → retrieve top-5 chunks from ChromaDB → generate answer with active LLM provider → return response + source citations.

**LLM modes** (configured via `LLM_MODE` env var):
- `local_only` — Ollama only
- `cloud_only` — Groq → Gemini fallback
- `hybrid` — Groq → Gemini → Ollama last resort

---

### 5. Document Ingestion

| Technology | Version | Purpose |
|---|---|---|
| **PyPDF2** | ≥ 3.0 | PDF parsing |
| **python-docx** | ≥ 1.1 | DOCX parsing |
| **openpyxl** | ≥ 3.1 | XLSX / Excel parsing |
| **python-pptx** | ≥ 0.6.23 | PowerPoint parsing |
| **BeautifulSoup4** | ≥ 4.12 | HTML parsing |
| **lxml** | ≥ 5.0 | HTML/XML backend for BeautifulSoup4 |

**Supported formats:** `.pdf`, `.docx`, `.txt`, `.xlsx`, `.csv`, `.pptx`, `.html`, `.htm`  
**Pipeline:** Parse → chunk (500 chars, 50 overlap) → embed → store in ChromaDB

---

### 6. Database & Storage

| Technology | Purpose |
|---|---|
| **SQLite** | Relational store — users, documents metadata, query logs, analytics |
| **ChromaDB** (file-based) | Vector store — embedded document chunks |
| **Local filesystem** | Raw uploaded document files (`data/uploads/`) |
| **GGUF model files** | Local LLM weights stored in `models/` |

---

### 7. Authentication

| Technology | Purpose |
|---|---|
| **JWT (JSON Web Tokens)** | Stateless auth tokens generated and validated in `auth/auth.py` |
| **Role-based access control** | Three roles: `admin`, `faculty`, `student` |

---

### 8. Deployment & DevOps

| Technology | Purpose |
|---|---|
| **Docker** | Containerisation — separate `Dockerfile` for each service |
| **Docker Compose** | Multi-container orchestration (`docker-compose.yml` / `docker-compose.prod.yml`) |
| **Windows Batch / PowerShell scripts** | `start-all-servers.bat/ps1` — one-click startup on Windows |
| **Bash shell script** | `quick-setup.sh` — automated first-time setup on macOS/Linux |

---

## 🚀 Future Improvement Recommendations

### Short-term (Low effort, high impact)

1. **Add a test suite**  
   The project currently has no automated tests. Adding unit tests for the RAG pipeline (`rag/retriever.py`, `rag/generator.py`), document ingestion, and authentication would dramatically improve reliability.  
   *Tools: `pytest` for Python, `vitest` or `react-testing-library` for React.*

2. **Streaming LLM responses**  
   Replace request-response chat with streaming (`text/event-stream` / SSE) so users see the answer token-by-token in real time. FastAPI supports `StreamingResponse` natively; React can consume it with the `EventSource` API or `fetch` streaming.

3. **Stronger default credentials & secret management**  
   The default `admin` / `admin123` credentials and plain-text `.env` storage are unsafe for production. Enforce password change on first login and document integration with secret managers (AWS Secrets Manager, Vault).

4. **Input validation & sanitisation**  
   Add server-side validation for all user inputs (query length, file size, file type MIME checks beyond extension checking) to guard against prompt injection and malicious uploads.

5. **Conversation history / multi-turn chat**  
   Store and pass prior chat turns as context to the LLM, so the bot can answer follow-up questions without the user having to repeat themselves.

---

### Medium-term (Moderate effort)

6. **Upgrade from SQLite to PostgreSQL**  
   SQLite works well for a single-server deployment but has write-concurrency limits. Replacing it with PostgreSQL (or MySQL) enables multi-instance deployments and better analytics queries.  
   *Use SQLAlchemy ORM + Alembic migrations to make this swap straightforward.*

7. **Add a caching layer (Redis)**  
   Cache frequently asked queries and their answers in Redis with a TTL. This cuts LLM costs and latency for repeated questions without touching the vector store or LLM at all.

8. **Proper JWT refresh token flow**  
   Implement short-lived access tokens (15 min) and long-lived refresh tokens stored in HttpOnly cookies to replace the current single-token approach.

9. **Enhanced RAG: hybrid search + reranking**  
   Combine dense vector search (current) with sparse keyword search (BM25) for more robust retrieval, then apply a cross-encoder reranker (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`) to reorder the top-K results before generation.

10. **OpenAI API support**  
    Add `openai` as a fourth LLM provider alongside Ollama/Groq/Gemini, selectable via `LLM_PRIMARY_PROVIDER=openai` in `.env`.

11. **CI/CD pipeline**  
    Add GitHub Actions workflows for:  
    - Python linting (`ruff`, `black --check`)  
    - Running the test suite on every PR  
    - Building and pushing Docker images to a container registry on merge to `main`

---

### Long-term (Higher effort, architectural)

12. **Migrate to LangChain or LlamaIndex**  
    Replacing the hand-rolled RAG pipeline with LangChain or LlamaIndex provides battle-tested retrieval chains, agent support, more chunking strategies, and a growing ecosystem of integrations.

13. **Kubernetes / horizontal scaling**  
    The three-service Docker Compose stack maps cleanly to a Kubernetes deployment. Adding a Horizontal Pod Autoscaler on the FastAPI service would let the RAG backend scale out under load.

14. **Observability stack**  
    Integrate Prometheus metrics into FastAPI, scrape with a Prometheus server, and visualise with Grafana. Add structured JSON logging (e.g. via `structlog`) and ship logs to an ELK stack or Loki.

15. **Multilingual support**  
    Switch the embedding model to a multilingual variant (e.g. `paraphrase-multilingual-MiniLM-L12-v2`) and allow users to configure their preferred language for both queries and responses.

16. **User feedback & RLHF data collection**  
    Add 👍 / 👎 feedback buttons on each chat response. Store ratings alongside the query, retrieved context, and response in the database. This data can later feed fine-tuning or evaluation pipelines.

17. **Document versioning**  
    Track document versions so that when a PDF is re-uploaded, old embeddings are invalidated and re-indexed automatically, and query logs record which version a response was based on.

---

## 📊 Stack Summary Table

| Layer | Technology | Language |
|---|---|---|
| Frontend | React 18 + Vite 5 | JavaScript |
| API Gateway | Spring Boot 3.2 | Java 17 |
| REST Backend | FastAPI | Python 3.10+ |
| Alternative UI | Streamlit | Python 3.10+ |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Python |
| Vector Store | ChromaDB | Python |
| Local LLM | Ollama (any GGUF model) | External service |
| Cloud LLM | Groq API / Google Gemini API | External API |
| Relational DB | SQLite | SQL |
| Auth | JWT | Python |
| Containerisation | Docker + Docker Compose | YAML / Dockerfile |
