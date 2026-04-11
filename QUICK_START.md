## AstroBot Quick Start Guide

### System Status: ✅ ALL GREEN

Your AstroBot environment has been fully configured and validated!

```
Python 3.12.7         : OK
Port 8000 (FastAPI)   : AVAILABLE
Port 8080 (Spring)    : AVAILABLE
Port 3000 (React)     : AVAILABLE
Dependencies          : ALL INSTALLED
.env Configuration    : COMPLETE
SQLite Database       : READY (1 admin user)
ChromaDB              : READY (195 vectors)
Ollama Provider       : READY
```

---

## Launch Options

### Option A: RECOMMENDED - Interactive Launcher
```powershell
cd "f:\Programming_project\Astrobot_v1\Astro_bot"
python launcher.py
```

This will:
1. Run system diagnostics
2. Show you all statuses
3. Let you choose which servers to start
4. Automatically open them

---

### Option B: Manual - Start Each Server

**Terminal 1 - FastAPI (API Server)**
```powershell
cd "f:\Programming_project\Astrobot_v1\Astro_bot"
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

✅ When you see: `Application startup complete`

**Terminal 2 - React Frontend (UI)**
```powershell
cd "f:\Programming_project\Astrobot_v1\Astro_bot\react-frontend"
npm run dev
```

✅ When you see: Server running at `http://localhost:3000`

**Terminal 3 - Spring Boot (API Gateway)**
```powershell
cd "f:\Programming_project\Astrobot_v1\Astro_bot\springboot-backend"
mvnw.cmd spring-boot:run
```

✅ When you see: `Tomcat started on port 8080`

---

## Access Your Application

Once all servers are running:

| URL | Purpose | Port |
|-----|---------|------|
| http://localhost:3000 | Main Application | 3000 |
| http://localhost:8000/docs | API Documentation | 8000 |
| http://localhost:8080 | Spring Boot Gateway | 8080 |

---

## Login Credentials

**Default Admin Account:**
```
Username: admin
Password: admin123
```

⚠️ **IMPORTANT:** Change these credentials immediately after your first login!

---

## What to Try First

1. **Login** with admin/admin123
2. **Go to Settings** (gear icon) and change admin password
3. **Go to Documents** → Upload a PDF or DOCX file
4. **Go to Chat** → Ask a question about the document
5. **View Analytics** to see the query you just made

---

## Troubleshooting

### Server already running on port?
```powershell
# Find what's using port 8000
netstat -ano | findstr ":8000"

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### Missing npm packages?
```powershell
cd react-frontend
npm install
npm run dev
```

### Python module errors?
```powershell
pip install -r requirements.txt -U
```

### Database errors?
```powershell
# Delete and recreate (WARNING: loses data)
Remove-Item data\astrobot.db -Force
Remove-Item data\chroma_db -Recurse -Force
```

### Ollama not connecting?
Make sure Ollama is running:
```powershell
# Check if Ollama is running
ollama list
# If not, start it
ollama serve
```

---

## Configuration Files

The system is configured through these files:

| File | Purpose |
|------|---------|
| `.env` | Environment variables (LLM mode, ports, database paths) |
| `config.py` | Python configuration loader |
| `springboot-backend/src/main/resources/application.properties` | Spring Boot settings |
| `react-frontend/vite.config.js` | React build configuration |

---

## Architecture Overview

```
┌─────────────────┐
│  React Browser  │ (http://localhost:3000)
│  Admin UI       │
└────────┬────────┘
         │ HTTP
┌────────▼────────┐
│  Spring Boot    │ (http://localhost:8080)
│  API Gateway    │
└────────┬────────┘
         │ HTTP
┌────────▼─────────────┐
│  FastAPI RAG Server  │ (http://localhost:8000)
│  • Document parsing  │
│  • Embeddings        │
│  • Vector search     │
│  • LLM generation    │
└──┬──────┬────────┬───┘
   │      │        │
   ▼      ▼        ▼
 SQLite ChromaDB Ollama
```

---

## Next Steps

1. Start the servers (Option A recommended)
2. Login to http://localhost:3000
3. Upload a document
4. Ask AstroBot a question
5. Explore the admin dashboard

**Enjoy using AstroBot!** 🤖

For detailed documentation, see:
- `STARTUP_FIXED.md` - All fixes applied
- `README.md` - Full project documentation
- `.github/copilot-instructions.md` - Development guide

