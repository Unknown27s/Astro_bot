# 🤖 COPILOT_GUIDE — Workflow for AI Agents

**This guide explains HOW to work on IMS AstroBot as an AI agent/Copilot.**

---

## 🎯 Your Role

As an AI agent/Copilot, you will:
- ✅ Implement features
- ✅ Fix bugs
- ✅ Optimize code
- ✅ Debug issues
- ✅ Add documentation
- ✅ Integrate new modules

You should act like an expert developer who knows this codebase intimately.

---

## 📋 Pre-Work Checklist

Before starting ANY task, verify:

```python
# 1. Check configuration is loaded
from config import LLM_MODE, OLLAMA_MODEL
print(f"LLM Mode: {LLM_MODE}, Model: {OLLAMA_MODEL}")

# 2. Check database is initialized
from database.db import init_db
init_db()  # Safe to call multiple times

# 3. Check provider availability
from rag.providers.manager import get_manager
mgr = get_manager()
statuses = mgr.get_all_statuses()
print(statuses)  # Should show available providers

# 4. Verify ChromaDB connection
from ingestion.embedder import get_collection
col = get_collection()
print(f"Documents stored: {col.count()}")
```

---

## 🔄 Common Task Workflows

### Workflow 1: User is asking a question

```
STEPS:
1. Retriever searches ChromaDB for relevant chunks
2. Retriever formats context from top-5 chunks
3. Generator sends context + question to LLM
4. LLM generates response (with fallback chain)
5. UI displays response with citations
6. Database logs the query

KEY FILES:
- rag/retriever.py         (step 1-2)
- rag/generator.py         (step 3-4)
- views/chat.py            (step 5)
- database/db.py           (step 6)

DEBUG:
from rag.retriever import retrieve_context, format_context_for_llm
from rag.generator import generate_response

chunks = retrieve_context("user question")
context = format_context_for_llm(chunks)
response = generate_response("user question", context)
print(response)
```

### Workflow 2: Admin uploads document

```
STEPS:
1. User selects file (PDF/DOCX/Excel/PPTX/HTML)
2. Parser extracts text
3. Chunker breaks text into pieces
4. Embedder converts chunks to vectors
5. ChromaDB stores vectors + metadata
6. SQLite records document

KEY FILES:
- ingestion/parser.py      (step 2)
- ingestion/chunker.py     (step 3)
- ingestion/embedder.py    (step 4-5)
- database/db.py           (step 6)

DEBUG:
from ingestion.parser import parse_pdf
from ingestion.chunker import chunk_document
from ingestion.embedder import add_document_to_chromadb

text = parse_pdf("file.pdf")
chunks = chunk_document(text, "file.pdf")
add_document_to_chromadb("doc_id", chunks)
```

### Workflow 3: LLM provider fails

```
SCENARIO: Grok API is down
EXPECTED: System falls back to Gemini, then Ollama

STEPS:
1. ProviderManager._get_chain() returns [Grok, Gemini, Ollama]
2. Try Grok → Exception → Continue
3. Try Gemini → Success → Return response
4. User never knows

KEY FILES:
- rag/providers/manager.py  (fallback logic)
- rag/generator.py          (handles None response)

DEBUG:
from rag.providers.manager import get_manager
mgr = get_manager()
statuses = mgr.get_all_statuses()
# Shows which providers are available
```

### Workflow 4: Performance issue

```
SCENARIO: Query taking 5+ seconds instead of ~350ms

DIAGNOSIS:
1. Check ChromaDB size
   from ingestion.embedder import get_collection
   col = get_collection()
   print(col.count())  # If > 1M, may be slow

2. Check LLM provider
   Query might be hitting slow cloud API
   Check config: LLM_MODE, LLM_PRIMARY_PROVIDER

3. Check network
   If cloud LLM, network latency

4. Check chunk size
   from config import CHUNK_SIZE
   If chunks are huge, embedding/search slow

OPTIMIZATION:
- Reduce CHUNK_SIZE in .env
- Switch to local_only mode
- Add caching
- Increase top_k carefully
```

---

## 🛠️ How to Approach a Task

### Step 1: Understand the Task
```
Task: "Add support for markdown files"

Ask yourself:
• What module handles this? → parser.py
• What's the data flow? → Parser → Chunker → Embedder
• Where do I make changes? → ingestion/parser.py + config.py
• Will it affect performance? → Likely no
• Are there existing examples? → Yes, PDF parser
```

### Step 2: Check Configuration
```python
from config import SUPPORTED_EXTENSIONS
print(SUPPORTED_EXTENSIONS)
# {'.pdf', '.docx', '.txt', '.xlsx', ...}
# Add .md if not there
```

### Step 3: Implement Changes
```python
# In ingestion/parser.py
def parse_markdown(file_path: str) -> str:
    """Parse markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# Register in config.py
SUPPORTED_EXTENSIONS = {..., '.md'}
```

### Step 4: Test Immediately
```python
# Quick test
from ingestion.parser import parse_markdown
text = parse_markdown("test.md")
print(len(text))  # Should print number of chars
```

### Step 5: Add to Documentation
```
Update: docs/architecture/DATABASE_SCHEMA.md or relevant file
```

---

## 🐛 Debugging Approach

### Problem: "Function X returns None"

```python
# 1. Trace backward
# If generator.generate_response() returns None:
#    ├─ Check provider chain
#    ├─ Check if all providers failed
#    └─ Check is_llm_available()

from rag.generator import is_llm_available
print(is_llm_available())  # True or False

# 2. Test each provider
from rag.providers.manager import get_manager
mgr = get_manager()
statuses = mgr.get_all_statuses()
for provider, status in statuses.items():
    print(f"{provider}: {status['status']}")

# 3. Check config
from config import LLM_MODE, LLM_PRIMARY_PROVIDER
print(f"Mode: {LLM_MODE}, Primary: {LLM_PRIMARY_PROVIDER}")
```

### Problem: "No documents found"

```python
# 1. Check ChromaDB
from ingestion.embedder import get_collection
col = get_collection()
print(f"Total vectors: {col.count()}")  # Should be > 0

# 2. If 0, upload a document
# If > 0, check retrieval
from rag.retriever import retrieve_context
chunks = retrieve_context("test query", top_k=5)
print(chunks)  # Should be non-empty

# 3. If empty, similarity might be too low
# Check chunk quality:
for chunk in col.get():
    print(chunk['document'][:50])  # First 50 chars
```

### Problem: "Authentication failing"

```python
# 1. Check database
from database.db import authenticate_user
user = authenticate_user("admin", "admin123")
print(user)  # Should return {id, username, role, ...}

# 2. If None, check database exists
from database.db import get_connection
conn = get_connection()
users = conn.execute("SELECT * FROM users").fetchall()
print(users)  # Should have at least admin
conn.close()

# 3. If empty, reinitialize
from database.db import init_db
init_db()  # Creates default admin
```

---

## ✅ Code Quality Checklist

Before submitting code:

- [ ] Follows PEP 8 style
- [ ] Has type hints: `def func(arg: str) -> bool:`
- [ ] Has docstring with purpose, args, returns
- [ ] Uses parameterized SQL: `cursor.execute("... WHERE id = ?", (id,))`
- [ ] Handles exceptions explicitly (not silent fail)
- [ ] No hardcoded paths/API keys (use config.py)
- [ ] No circular imports
- [ ] Tested locally with quick check
- [ ] Updated docs if needed
- [ ] Follows conventions in development/CODE_CONVENTIONS.md

---

## 🎯 Pattern Reference

### Pattern 1: Add a Configuration Option

```python
# 1. In config.py
NEW_OPTION = os.getenv("NEW_OPTION", "default_value")

# 2. In .env
NEW_OPTION=custom_value

# 3. Use it
from config import NEW_OPTION
print(NEW_OPTION)
```

### Pattern 2: Call the RAG Pipeline

```python
from rag.retriever import retrieve_context, format_context_for_llm
from rag.generator import generate_response

query = "user question"
chunks = retrieve_context(query, top_k=5)
context = format_context_for_llm(chunks)
response = generate_response(query, context)
```

### Pattern 3: Database Operation

```python
from database.db import get_connection

conn = get_connection()
try:
    result = conn.execute(
        "SELECT * FROM users WHERE role = ?",
        ("admin",)
    ).fetchall()
    
    conn.commit()
finally:
    conn.close()
```

### Pattern 4: Error Handling in RAG

```python
try:
    response = provider.generate(system_prompt, user_msg, temp, tokens)
    if response:
        return response
    else:
        continue  # Try next provider
except Exception as e:
    print(f"Provider failed: {e}")
    continue  # Try next provider

# All failed
return fallback_response()  # Use context-only
```

### Pattern 5: Provider Check

```python
from rag.providers.manager import get_manager

mgr = get_manager()
if mgr.is_any_available():
    # LLM available, safe to generate
    response = generate_response(query, context)
else:
    # All providers down, use context-only
    response = "Based on documents:\n" + context
```

---

## 📊 Data Flow Reference

### Document Flow
```
File Upload
    ↓ (views/admin.py)
File Saved to disk (data/uploads/)
    ↓ (ingestion/parser.py)
Text Extracted
    ↓ (ingestion/chunker.py)
Chunks with metadata
    ↓ (ingestion/embedder.py)
Vectors + ChromaDB
+
SQLite record
```

### Query Flow
```
User Input (views/chat.py)
    ↓
Embed question (ingestion/embedder.py)
    ↓
Search ChromaDB (rag/retriever.py)
    ↓
Top-5 chunks
    ↓
Format context (rag/retriever.py)
    ↓
Send to LLM (rag/providers/manager.py)
    ↓
Response
    ↓
Format for UI (views/chat.py)
    ↓
Log to DB (database/db.py)
    ↓
Display to User
```

---

## 🚀 When You're Done

### Before Declaring Task Complete:

1. ✅ **Tested locally:** Run at least one quick test
2. ✅ **Verified existing tests don't break:** If tests exist, run them
3. ✅ **Followed code conventions:** Style, type hints, docstrings
4. ✅ **Updated docs:** If behavior changed, update documentation
5. ✅ **Checked for side effects:** Will this break other modules?
6. ✅ **Logged appropriately:** Errors are logged, not silent
7. ✅ **No hardcoded values:** All settings in config.py

---

## 📞 Emergency Reference

If stuck and time is limited:

```python
# Check system health
from rag.providers.manager import get_manager
mgr = get_manager()
print(mgr.get_all_statuses())

# Quick RAG test
from rag.retriever import retrieve_context
from rag.generator import generate_response
response = generate_response("test", "context")
print(response)

# Database check
from database.db import get_connection
conn = get_connection()
print(conn.execute("SELECT COUNT(*) FROM documents").fetchone())
conn.close()

# Config check
from config import *
print(f"Mode: {LLM_MODE}, DB: {SQLITE_DB_PATH}")
```

---

## 🎓 Your Learning Path

1. **Read:** [START_HERE.md](START_HERE.md) (5 min)
2. **Understand:** [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) (20 min)
3. **Reference:** [guides/QUICKREF.md](guides/QUICKREF.md) (5 min)
4. **Code:** Use patterns from this guide (ongoing)
5. **Debug:** Use debugging approach above (as needed)

---

## ✨ Pro Tips

- Always check `config.py` first
- Test provider chain with `get_manager().get_all_statuses()`
- Use `reset_manager()` after config changes
- Parameterized SQL queries ALWAYS (`?` placeholders)
- Never silently fail — log errors
- Fallback is your friend (provides graceful degradation)
- Check if Ollama is running before assuming local_only works
- Remember: RAG pipeline is the heart of the system

---

## 🎯 Success Criteria

You've mastered this when you can:

- ✅ Explain RAG in < 30 seconds
- ✅ Trace a query through the entire system
- ✅ Add a new feature without breaking anything
- ✅ Debug any issue using provided approach
- ✅ Follow code conventions automatically
- ✅ Test changes before declaring done
- ✅ Know which file to modify for any task

---

**Now you're ready to work on AstroBot as an AI agent!**

Go build something awesome. 🚀

---

## Quick Links
- **Configuration:** [config.py](../../config.py)
- **Quick Commands:** [guides/QUICKREF.md](guides/QUICKREF.md)
- **Architecture Details:** [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- **Code Conventions:** [development/CODE_CONVENTIONS.md](development/CODE_CONVENTIONS.md)
- **Troubleshooting:** [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
