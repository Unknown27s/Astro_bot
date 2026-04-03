# 📝 Changelog

All notable changes to IMS AstroBot are documented in this file.

---

## [2.1.0] - 2026-04-03

### ✨ New Features

#### Voice-to-Text (Microphone Input)
- **`rag/voice_to_text.py`**: Added local OpenAI Whisper inference using `faster-whisper`. Base model is lazy-loaded and cached in memory.
- **`api_server.py`**: Added `/api/chat/audio` endpoint to accept webm blobs and route them through Whisper then into the standard RAG pipeline.
- **`springboot-backend/src/main/java/com/astrobot/controller/ChatController.java` & `PythonApiService.java`**: Added `/audio` POST route that proxies `multipart/form-data` natively with Spring WebClient.
- **`react-frontend/src/pages/ChatPage.jsx`**: Added a Microphone button that uses Web Audio API (`MediaRecorder`) to capture mic data, manage recording states, and dispatch voice queries.
- **Requirements**: Added `faster-whisper` to `requirements.txt` and `ffmpeg` system dependency.

---

## [2.0.3] - 2026-04-01

### 🐛 Bug Fixes

#### Spring Boot Proxy Configuration
- **`springboot-backend/src/main/resources/application.properties` (line 6)**: Fixed Python FastAPI proxy URL
  - Changed from `astrobot.python-api-url=http://localhost:8001` (incorrect)
  - To `astrobot.python-api-url=http://localhost:8000` (correct, matches FastAPI actual port)
  - **Impact**: Resolves 500 errors on `/api/documents`, `/api/analytics`, `/api/analytics/logs` endpoints
  - **Root cause**: Spring Boot was attempting to proxy to non-existent FastAPI port, causing all downstream client calls to fail

#### FastAPI Document Upload Request Parameter
- **`api_server.py` (line 334)**: Fixed multipart form-data upload validation
  - Changed from `request: Request = Depends()`
  - To `request: Request` (removed `Depends()` wrapper)
  - Moved `request` parameter to first position (before `file` and `uploaded_by`)
  - **Impact**: Resolves 422 "Unprocessable Entity" error with message `{"detail":[{"type":"missing","loc":["body","scope"],"msg":"Field required"}]}`
  - **Root cause**: FastAPI Pydantic validation was incorrectly expecting a `scope` field in request body when `Depends()` was used on `Request` type with multipart form data

### 📋 Verification Steps

After restart:
1. **Spring Boot**: Kill running process on port 8080, rebuild/restart (config will reload)
2. **Admin Dashboard**: File upload should now succeed without 422 errors
3. **Analytics**: Admin → Analytics page should load document count, query logs without 500 errors

---

## [2.0.2] - 2026-04-01

### ✨ New Features

#### Admin-Only Document Upload
- **`api_server.py` (lines 329-354)**: Added admin role validation to `/api/documents/upload`
  - Returns HTTP 403 if user is not admin
  - Returns HTTP 404 if user not found in database
  - Requires `uploaded_by` field with admin user ID
- **`views/admin.py`**: Streamlit UI already restricted to admins via sidebar
- **`react-frontend/src/pages/admin/DocumentsPage.jsx`**: Enhanced error handling for 403 responses

#### Locked PDF Detection
- **`api_server.py` (lines 368-382)**: Detects password-protected PDFs using PyPDF2
  - Checks `PdfReader.is_encrypted` before parsing
  - Returns HTTP 422 with user-friendly message
  - Clean error: "PDF is password-protected. Please remove the password and try again."
- **`views/admin.py` (lines 90-116)**: Same detection in Streamlit UI
  - Prevents confusing parse errors
  - Shows clear message to user
  - Cleans up orphaned file

#### Enhanced API Error Responses
- **`react-frontend/src/pages/admin/DocumentsPage.jsx` (lines 20-60)**: Improved error message extraction
  - Handles both string and array error formats from Pydantic
  - Shows HTTP status code specific messages (403, 404, 413, 422)
  - User-friendly icons (❌) in all error messages

### 📝 Documentation

#### New
- **`docs/UPLOAD_API_REFERENCE.md`**: Comprehensive upload endpoint documentation
  - Admin-only requirement explained
  - Locked PDF detection details
  - All error codes and responses
  - cURL, Python, and React examples

#### Updated
- **`docs/guides/QUICKREF.md`**: Added detailed `/api/documents/upload` endpoint documentation
  - Admin role requirement
  - All error responses
  - cURL example

### 🐛 Bug Fixes

#### Previously Failing Scenarios
- Non-admin users uploading via API: Now returns 403 instead of silent failure
- Password-protected PDFs: Now returns 422 instead of parse error
- Missing `uploaded_by`: Now returns 400 with clear message

---

## [2.0.1] - 2026-03-31

### 🔧 Bug Fixes

#### Document Upload (422 Error Fix)
- **`ingestion/parser.py`**: Changed `parse_document()` to return `(text, error_message)` tuple for better error reporting
- **`api_server.py`**: Enhanced upload endpoint with specific error messages:
  - Empty file detection
  - Parse failure details
  - Supported file types shown in error message
- **`DocumentsPage.jsx`**: Now displays actual error message from server instead of generic "Failed"

#### Document Delete (500 Error Fix)
- **`api_server.py`**: Added try-except blocks around ChromaDB and file deletion
- Errors are logged instead of crashing the endpoint
- Returns proper 500 error with details if deletion fails

#### Spring Boot Integration Fixes
- **`DocumentController.java`**: Made `uploaded_by` parameter optional (`required = false`)
- **`PythonApiService.java`**: Only includes `uploaded_by` in form data when not null/empty
- **`PythonApiService.java`**: Fixed stats endpoint path from `/api/knowledge-base/stats` to `/api/documents/stats`

#### Missing Endpoint Fix
- **NEW: `SuggestionsController.java`**: Created controller to proxy `/api/suggestions` calls
- **`PythonApiService.java`**: Added `getSuggestions()` method
- React → Spring Boot → Python suggestions flow now works

#### Error Handling Improvements
- **`AnalyticsController.java`**: Returns HTTP 503 (Service Unavailable) when Python API is down (was incorrectly returning 200 OK)
- **`api_server.py`**: Added `/api/documents/stats` as alias for `/api/knowledge-base/stats`

### 🗑️ Removed Files

#### Root Directory Cleanup
Removed 26 unnecessary files from project root:
- Duplicate MD files (moved to `docs/`)
- Deployment files (Docker, nginx) - not needed for development
- Temporary output files

**Removed:**
- `ADMIN_RATE_LIMITING_QUICKSTART.md`
- `ARCHITECTURE.md`
- `COMPLETE_UNDERSTANDING.md`
- `DIAGRAMS.md`
- `DOCUMENTATION_COMPLETE.md`
- `DOCUMENTATION_SUMMARY.md`
- `IMPLEMENTATION_SUMMARY.md`
- `INDEX.md`
- `PORT_CONFIGURATION.md`
- `PORT_MIGRATION_FIX.md`
- `QUICKREF.md`
- `QUICKSTART.md`
- `SERVER-STARTUP.md`
- `# Code Citations.md`
- `deploy-lite.py`
- `docker-compose.prod.yml`
- `docker-compose.yml`
- `Dockerfile`
- `Dockerfile.api`
- `quick-setup.sh`
- `.dockerignore`
- `test_output.txt`
- `verify_output.txt`
- `verify_fix.py`
- `pip_list.txt`
- `deployment/` folder

#### Docs Cleanup
- Removed `03-LOAD_BALANCING.md` (deployment not needed)

### 📝 Documentation Updates
- **`docs/README.md`**: Updated to remove deployment references, added architecture overview
- **`docs/CHANGELOG.md`**: Created this changelog

---

## [2.0.0] - 2026-03-14

### ✨ Features
- **Phase 1**: Error Tracking & Structured Logging (Sentry integration)
- **Phase 2**: Rate Limiting (slowapi middleware)
- **Phase 3**: Document Tagging/Classification (13 new endpoints)
- **Phase 4**: Load Balancing (nginx + Docker) - *Removed in 2.0.1*

### 🏗️ Architecture
- React Frontend (Vite) on port 3000
- Spring Boot Backend on port 8080
- Python FastAPI on port 8001
- ChromaDB for vector storage
- SQLite for relational data
- Multi-provider LLM (Ollama, Grok, Gemini)

---

## File Structure After Cleanup

```
AstroBot/
├── api_server.py           # FastAPI REST API
├── app.py                  # Streamlit entry point
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
├── README.md               # Project README
├── .env                    # Environment variables
│
├── auth/                   # Authentication
├── database/               # SQLite CRUD
├── ingestion/              # Document parsing & embedding
├── log_config/             # Logging setup
├── middleware/             # Rate limiting
├── rag/                    # RAG pipeline & LLM providers
├── views/                  # Streamlit UI pages
│
├── react-frontend/         # React UI (Vite)
├── springboot-backend/     # Spring Boot proxy
│
├── docs/                   # Documentation
│   ├── 01-QUICKSTART.md
│   ├── 02-IMPLEMENTATION_SUMMARY.md
│   ├── 04-API_ENDPOINTS.md
│   ├── 05-ADMIN_RATE_LIMITING.md
│   ├── COPILOT_GUIDE.md
│   ├── START_HERE.md
│   ├── README.md
│   ├── CHANGELOG.md        # This file
│   ├── architecture/
│   ├── development/
│   └── guides/
│
├── data/                   # Runtime data
│   ├── uploads/
│   ├── chroma_db/
│   └── astrobot.db
│
├── logs/                   # Log files
├── tests/                  # Test files
│
├── start-all-servers.ps1   # Start servers (PowerShell)
├── start-all-servers.bat   # Start servers (Windows)
├── stop-all-servers.ps1    # Stop servers (PowerShell)
├── stop-all-servers.bat    # Stop servers (Windows)
├── verify.bat              # Verify installation
└── verify.sh               # Verify installation (Unix)
```

---

**Maintained by:** IMS AstroBot Team
