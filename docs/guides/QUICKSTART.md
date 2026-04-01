# 🚀 Quick Start — 5-Minute Setup

**Get AstroBot running in 5 minutes.**

---

## Prerequisites

- Python 3.9+
- Git
- Ollama (optional, for local LLM)

---

## Step 1: Clone & Setup Environment (2 min)

```powershell
# Navigate to project
cd d:\Harish Kumar\Project\Astro_botV2\Astro_bot

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

---

## Step 2: Install Dependencies (1 min)

```powershell
pip install -r requirements.txt
```

---

## Step 3: Create .env File (1 min)

```powershell
# Create .env with minimal config
@"
LLM_MODE=local_only
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:0.6b
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=512
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIR=./data/chroma_db
SQLITE_DB_PATH=./data/astrobot.db
"@ | Out-File -FilePath .env -Encoding UTF8
```

---

## Step 4: Start Servers (1 min)

```powershell
# Option 1: Start all servers at once
.\start-all-servers.ps1

# Option 2: Start individually
# Terminal 1:
streamlit run app.py

# Terminal 2:
uvicorn api_server:app --reload

# Terminal 3 (from springboot-backend/):
mvn spring-boot:run
```

---

## Step 5: Access Application (instant)

- **Streamlit UI:** http://localhost:8501
- **FastAPI Docs:** http://localhost:8000/docs
- **Spring Boot:** http://localhost:8080

---

## Step 6: Login (instant)

- **Username:** `admin`
- **Password:** `admin123`

---

## ✅ Done!

You now have:
- ✅ Streamlit UI running
- ✅ FastAPI server running
- ✅ Database initialized
- ✅ Ready to upload documents
- ✅ Ready to ask questions

---

## Troubleshooting

### Issue: "No module named streamlit"
```powershell
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Ollama not running"
```powershell
# Start Ollama (must be running for local_only mode)
ollama serve

# Or switch to cloud provider
# (Edit .env: LLM_MODE=cloud_only, add Grok/Gemini keys)
```

### Issue: "Port 8501 already in use"
```powershell
# Use different port
streamlit run app.py --server.port 8502
```

---

## Next Steps

1. **Upload Documents:** Admin dashboard → Upload PDF/DOCX
2. **Ask Questions:** Chat page → Type your question
3. **Monitor Health:** Admin dashboard → Health status
4. **Configure LLM:** Admin dashboard → AI Settings

---

**For more details, see:** [../README.md](../README.md)
