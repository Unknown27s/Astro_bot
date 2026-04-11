# 🐛 Troubleshooting — Common Issues & Solutions

**When something goes wrong, find it here.**

---

## Connection Issues

### Issue: "No LLM provider available"

**Cause:** Ollama not running or credentials invalid

**Solution:**
```bash
# Start Ollama
ollama serve

# Or check status
ollama list  # Lists available models
```

**Verify:**
```python
from rag.providers.manager import get_manager
mgr = get_manager()
print(mgr.get_all_statuses())
```

---

### Issue: "Cannot connect to ChromaDB"

**Cause:** `chroma_db/` directory missing or corrupted

**Solution:**
```bash
# Delete corrupted database
rm -r data/chroma_db

# Restart servers (will recreate on first use)
.\start-all-servers.ps1

# Re-upload documents
```

---

### Issue: "SQLite database is locked"

**Cause:** Multiple processes writing simultaneously

**Solution:**
```bash
# Restart servers to reset locks
.\stop-all-servers.ps1
.\start-all-servers.ps1
```

**Prevention:** WAL mode is enabled (prevents most issues)

---

## Runtime Issues

### Issue: `ModuleNotFoundError: No module named 'tests.config'`

**Cause:** Python cannot resolve `tests` as an importable package in runtime context.

**Solution:**
```bash
# Ensure tests package marker exists
dir tests\__init__.py

# Install all project dependencies
pip install -r requirements.txt

# Re-run API
python api_server.py
```

**Notes:**
- Runtime modules currently import from `tests.config` in this codebase.
- If `tests/config.py` was modified, keep required exported names aligned with runtime imports.

---

### Issue: `Failed to load PostCSS config ... Cannot find module 'tailwindcss'`

**Cause:** Frontend dependencies are missing/out-of-sync in `react-frontend/node_modules`.

**Solution:**
```bash
cd react-frontend
npm install
npm ls tailwindcss
npm run dev
```

**Expected:** `tailwindcss@...` appears in dependency tree and Vite starts.

---

### Issue: `npm ERR! code EJSONPARSE` in `package.json`

**Cause:** Invalid JSON, often unresolved merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).

**Solution:**
```bash
cd react-frontend
npm run dev
```

If parse error mentions conflict markers:
1. Open `react-frontend/package.json`
2. Remove merge markers and keep valid JSON only
3. Run `npm install` again

---

### Issue: Embedding model timeout

**Cause:** First-time download of `all-MiniLM-L6-v2` (400+ MB)

**Solution:**
```bash
# Wait 1-2 minutes on first query
# Check internet connection
# Check disk space (>1 GB available)
```

**Speed up:** Pre-download model
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

---

### Issue: "Query taking 5+ seconds"

**Cause:** Could be ChromaDB large, cloud LLM slow, network

**Diagnosis:**
```python
# Check ChromaDB size
from ingestion.embedder import get_collection
col = get_collection()
print(f"Vectors: {col.count()}")  # If > 1M, may be slow

# Check LLM provider
from config import LLM_MODE, LLM_PRIMARY_PROVIDER
print(f"Mode: {LLM_MODE}, Provider: {LLM_PRIMARY_PROVIDER}")

# Cloud providers are inherently slower (network)
```

**Solution:**
```
- Switch to local_only (use Ollama)
- Reduce chunk count in query
- Optimize ChromaDB (smaller documents)
- Add caching layer
```

---

### Issue: Streamlit app crashes

**Cause:** Missing dependencies or import error

**Solution:**
```bash
# Check Python path
python -m streamlit version

# Reinstall dependencies
pip install -r requirements.txt

# Check .env syntax
echo %LLM_MODE%  # Windows
echo $LLM_MODE   # PowerShell

# Run with verbose output
streamlit run app.py --logger.level=debug
```

---

## Authentication Issues

### Issue: "Invalid credentials" (but credentials seem correct)

**Cause:** User doesn't exist or password hash mismatch

**Solution:**
```python
# Check users in database
from database.db import get_connection
conn = get_connection()
users = conn.execute("SELECT * FROM users").fetchall()
for u in users:
    print(f"Username: {u['username']}, Role: {u['role']}")
conn.close()

# Recreate default admin if missing
from database.db import init_db
init_db()  # Safe to call multiple times

# Test authentication
from database.db import authenticate_user
user = authenticate_user("admin", "admin123")
print(user)  # Should print user dict
```

---

### Issue: Session lost after page reload

**Cause:** Normal Streamlit behavior (session resets on reload)

**Solution:** This is expected. Session data is per-browser-session.

**Prevent:** Don't reload browser during session

---

## API Issues

### Issue: "API returns 503 Service Unavailable"

**Cause:** FastAPI server not running

**Solution:**
```bash
# Check if FastAPI is running
netstat -an | find ":8000"

# Start FastAPI
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

---

### Issue: CORS error from React frontend

**Cause:** FastAPI CORS not configured for origin

**Solution:** Currently set to `["*"]` (allow all)

**If restrictive:** Edit `api_server.py`
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your origin
    ...
)
```

---

## Data Issues

### Issue: PDF upload fails in Streamlit with error message

**Common Errors & Solutions:**

| Error | Cause | Solution |
|-------|-------|----------|
| "Parse failed for X: ..." | PDF malformed, encrypted, or no extractable text | Use a clean PDF with searchable text (not scans) |
| "No chunks generated from X" | Document too short (< 500 characters) | Ensure document has sufficient content |
| "Database error for X" | SQLite write failed or disk full | Check disk space, restart server |
| "Failed to index X in vector database" | ChromaDB error or corruption | Delete `data/chroma_db/`, restart, re-upload |
| "File too large (50.5MB). Max: 50MB" | Exceeds 50MB size limit | Split document into smaller files |

**Manual Troubleshooting:**

```python
# Test the upload pipeline step-by-step
from pathlib import Path
from ingestion.parser import parse_document
from ingestion.chunker import chunk_document
from ingestion.embedder import store_chunks

# Step 1: Test parsing
file_path = "path/to/test.pdf"
text, error = parse_document(file_path)
if not text:
    print(f"❌ Parse failed: {error}")
else:
    print(f"✅ Parsed {len(text)} characters")

# Step 2: Test chunking
chunks = chunk_document(text, source_name="test.pdf")
if not chunks:
    print("❌ No chunks generated (text too short?)")
else:
    print(f"✅ Generated {len(chunks)} chunks")

# Step 3: Test embedding/storage
try:
    stored = store_chunks(chunks, "test_doc_id")
    print(f"✅ Stored {stored} chunks in ChromaDB")
except Exception as e:
    print(f"❌ ChromaDB error: {e}")
```

**Prevention Tips:**
- ✅ Use clean PDFs with **searchable text** (not image scans)
- ✅ Keep files **under 50MB**
- ✅ Ensure document has **minimum 500 characters**
- ✅ Supported formats: `.pdf`, `.docx`, `.txt`, `.xlsx`, `.csv`, `.pptx`, `.html`
- ✅ Check file permissions and disk space

**Recent Fix:** The Streamlit upload handler now:
- ✅ Properly unpacks parse results (fixed silent failures)
- ✅ Shows detailed error messages for each failure step
- ✅ Validates file size before processing
- ✅ Handles database and ChromaDB errors gracefully
- ✅ Cleans up partial uploads on failure
- ✅ Counts/displays successful vs failed uploads

---

### Issue: Documents not searchable after upload

**Cause:** Document failed to parse or chunk

**Diagnosis:**
```python
# Check document status in database
from database.db import get_connection
conn = get_connection()
docs = conn.execute(
    "SELECT filename, status, chunk_count FROM documents"
).fetchall()
for d in docs:
    print(f"{d['filename']}: {d['status']} ({d['chunk_count']} chunks)")
conn.close()

# Check if status = 'failed'
```

**Solution:**
- If `status='failed'`: Delete and re-upload
- If `status='processed'` but `chunk_count=0`: Document might be empty

```python
# Delete and retry
from database.db import delete_document
delete_document(doc_id)

# Clear ChromaDB
import shutil
shutil.rmtree('data/chroma_db')

# Re-upload
```

---

### Issue: Irrelevant search results

**Cause:** Chunks too large/small, poor embedding, low relevance

**Diagnosis:**
```python
# Check chunk size
from config import CHUNK_SIZE, CHUNK_OVERLAP
print(f"Chunk: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP}")

# Check top-5 results
from rag.retriever import retrieve_context
chunks = retrieve_context("test query", top_k=5)
for i, chunk in enumerate(chunks):
    print(f"\n{i+1}. Relevance: {chunk['score']:.0%}")
    print(f"   Source: {chunk['source']}")
    print(f"   Text: {chunk['text'][:100]}...")
```

**Solution:**
```
- Reduce CHUNK_SIZE to 300 (more specific chunks)
- Increase TOP_K_RESULTS to 10 (get more candidates)
- Upload more documents
- Check document quality (clear formatting helps)
```

---

## Configuration Issues

### Issue: "Changes to .env not taking effect"

**Cause:** Application loaded config before .env changed

**Solution:**
```python
# Restart application
.\stop-all-servers.ps1
.\start-all-servers.ps1

# Or programmatically reset
from rag.providers.manager import reset_manager
reset_manager()
```

---

### Issue: "Can't find model in Ollama"

**Cause:** Model not pulled, wrong name

**Solution:**
```bash
# List available models
ollama list

# Pull missing model
ollama pull qwen3:0.6b

# Check .env
# OLLAMA_MODEL=qwen3:0.6b  (exact name must match)
```

---

## Performance Issues

### Issue: "Responses very slow (>2 seconds)"

**Typical breakdown:**
- Local (Ollama): 350-860 ms ✓
- Grok: 550-1550 ms ✓
- Gemini: 1050-2050 ms ✓

**If slower:**

```python
# Profile the pipeline
import time
from rag.retriever import retrieve_context
from rag.generator import generate_response

query = "test question"

t1 = time.time()
chunks = retrieve_context(query)
print(f"Retrieval: {(time.time()-t1)*1000:.0f} ms")

t1 = time.time()
response = generate_response(query, "test context")
print(f"Generation: {(time.time()-t1)*1000:.0f} ms")
```

**Optimization:**
- Local LLM faster than cloud
- Reduce top_k results
- Smaller document corpus
- Add caching

---

## Memory Issues

### Issue: "Out of memory" errors

**Typical memory usage:**
- Python base: 100 MB
- Streamlit: 80 MB
- Embedding model: 400-500 MB
- ChromaDB: 200-500 MB (per doc count)
- Local LLM: 2-4 GB

**If OOM:**
```python
# Check current usage
import psutil
print(f"Memory: {psutil.virtual_memory().percent}%")

# Reduce ChromaDB size
# (Delete old documents, re-organize)

# Use cloud LLM instead of local
# (Reduces 2-4 GB)
```

---

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'streamlit'` | Missing dep | `pip install -r requirements.txt` |
| `ConnectionRefusedError: [Errno 111]` | Service not running | Start the server |
| `UnicodeDecodeError` | File encoding issue | Check file encoding |
| `TypeError: 'NoneType' object is not iterable` | Function returned None | Check error handling |
| `ValueError: Vector dimension mismatch` | Embedding model changed | Delete ChromaDB, re-embed |
| `sqlite3.OperationalError: database is locked` | Concurrent writes | Restart servers |

---

## Quick Debug Checklist

Before reporting an issue:

1. [ ] Restarted servers
2. [ ] Checked Ollama is running (if local mode)
3. [ ] Verified .env configuration
4. [ ] Checked database exists (`data/astrobot.db`)
5. [ ] Ran `init_db()` to reset database
6. [ ] Checked error logs
7. [ ] Tried with minimal example

---

## Getting Help

**When stuck:**

1. Check this file for your issue
2. Review [QUICKREF.md](QUICKREF.md) for quick commands
3. Read [../COPILOT_GUIDE.md](../COPILOT_GUIDE.md) § Debugging
4. Check `.env` configuration
5. Review [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)

---

**Still stuck?** Check status of all services:

```python
from rag.providers.manager import get_manager
from database.db import get_connection
from ingestion.embedder import get_collection
from config import *

print(f"LLM Mode: {LLM_MODE}")
print(f"Providers: {get_manager().get_all_statuses()}")
print(f"ChromaDB vectors: {get_collection().count()}")

conn = get_connection()
users = conn.execute("SELECT COUNT(*) FROM users").fetchone()
docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
print(f"Users: {users[0]}, Documents: {docs[0]}")
conn.close()
```

