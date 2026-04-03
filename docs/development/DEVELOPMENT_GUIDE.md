# 🛠️ Development Guide

**How to add features and implement changes in AstroBot.**

*Audience: Backend/frontend developers | Time: 25 minutes*

---

## 📋 Table of Contents

1. [Development Workflow](#-development-workflow)
2. [Adding Backend Features](#-adding-backend-features)
3. [Adding Frontend Features](#-adding-frontend-features)
4. [Testing](#-testing)
5. [Debugging](#-debugging)
6. [Deployment](#-deployment)

---

## 🔄 Development Workflow

### Step 1: Understand the Request

**Before coding:** Read and understand what needs to be done

```
Request:  "Add ability for users to export query history as CSV"
          
What does this mean?
- Need to read query_logs from database
- Convert to CSV format
- Return as downloadable file
- Only show current user's queries
- Add to Streamlit sidebar or admin dashboard

Why? Track trends, audit trail, compliance
```

### Step 2: Plan the Implementation

**Create a mini-design:**

```
Flow:
1. User clicks "Export Queries" button
2. Backend queries: SELECT * FROM query_logs WHERE user_id = ?
3. Format results as CSV
4. Trigger browser download
5. File: "query_export_2024-03-20.csv"

Components needed:
- New function: export_queries_to_csv(user_id)
- New API endpoint: GET /api/queries/export
- New UI button: Streamlit/React button
- Security: Verify user can only export their own queries
```

### Step 3: Implement in Stages

**Work incrementally (test each stage):**

```
Stage 1: Backend function
└─ db.py: Add export_queries_to_csv()
└─ Test locally: python -c "..."

Stage 2: API endpoint  
└─ api_server.py: Add /api/queries/export
└─ Test: curl http://localhost:8000/api/queries/export

Stage 3: Frontend button
└─ views/admin.py (Streamlit) or ChatPage.jsx (React)
└─ Test: Click button, download works

Stage 4: Integration testing
└─ Test: End-to-end flow
└─ Test: Different file sizes
└─ Test: Permissions (can't export others' queries)
```

---

## 🐍 Adding Backend Features

### Scenario 1: Add New Database Table

**Example:** Track user feedback on responses

```
Goal: Store user ratings ("This answer was helpful" / "Not helpful")
```

#### Step 1: Define Schema

```python
# File: database/db.py

def init_db():
    """Create/update schema"""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        query_log_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        rating INTEGER NOT NULL,           -- 1=helpful, 0=not_helpful
        comment TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(query_log_id) REFERENCES query_logs(id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        CHECK(rating IN (0, 1))
    )
    """)
    connection.commit()
```

#### Step 2: Add CRUD Functions

```python
# File: database/db.py

def add_feedback(query_log_id, user_id, rating, comment=None):
    """Record user feedback"""
    feedback_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    query = """
    INSERT INTO feedback (id, query_log_id, user_id, rating, comment, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (feedback_id, query_log_id, user_id, rating, comment, created_at))
    connection.commit()
    return feedback_id

def get_feedback_stats():
    """Get feedback summary"""
    query = """
    SELECT 
        COUNT(*) as total_feedback,
        SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as helpful_count,
        SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) as unhelpful_count,
        ROUND(100.0 * SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as helpful_percentage
    FROM feedback
    """
    cursor.execute(query)
    result = cursor.fetchone()
    return {
        "total": result[0],
        "helpful": result[1],
        "unhelpful": result[2],
        "helpful_percentage": result[3]
    }
```

#### Step 3: Test Locally

```bash
# In Python REPL or script
from database.db import add_feedback, get_feedback_stats

# Add feedback
feedback_id = add_feedback("query_123", "user_456", 1, "Very helpful!")

# Get stats
stats = get_feedback_stats()
print(stats)
# {'total': 42, 'helpful': 35, 'unhelpful': 7, 'helpful_percentage': 83.33}
```

### Scenario 2: Add New API Endpoint

**Example:** Get analytics summary

```python
# File: api_server.py

from fastapi import APIRouter, Depends, HTTPException
from database.db import get_feedback_stats

@app.get("/api/analytics/feedback")
async def analytics_feedback(current_user = Depends(get_current_user)):
    """Get feedback analytics"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    stats = get_feedback_stats()
    return {
        "status": "success",
        "data": stats
    }
```

#### Testing

```bash
# Start FastAPI server
# In another terminal:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/analytics/feedback

# Response:
{
  "status": "success",
  "data": {
    "total": 42,
    "helpful": 35,
    "unhelpful": 7,
    "helpful_percentage": 83.33
  }
}
```

### Scenario 3: Add New RAG Feature

**Example:** Change embedding model

```python
# File: config.py

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# New option in .env:
# EMBEDDING_MODEL=all-mpnet-base-v2  (384 dims, slower but more accurate)
```

```python
# File: ingestion/embedder.py

def generate_embeddings(texts, model_name=None):
    """Generate embeddings with configurable model"""
    if model_name is None:
        model_name = config.EMBEDDING_MODEL
    
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    
    # Download model on first use
    embeddings = model.encode(texts)
    return embeddings
```

**When to use different models:**

| Model | Dims | Speed | Accuracy | Use case |
|-------|------|-------|----------|----------|
| `all-MiniLM-L6-v2` | 384 | ⚡ Fast | Good | Default, balanced |
| `all-mpnet-base-v2` | 768 | 🐌 Slow | Better | Higher accuracy needed |
| `all-distilroberta-v1` | 768 | Medium | Very good | Production |

---

## 🎨 Adding Frontend Features

### Scenario 1: Add New Streamlit Page

**Example:** Add "Feedback Analytics" page

```python
# File: views/feedback_analytics.py

import streamlit as st
from database.db import get_feedback_stats

def render():
    """Render feedback analytics page"""
    
    st.title("📊 Feedback Analytics")
    
    # Verify admin
    if st.session_state.get("role") != "admin":
        st.error("Admin only")
        return
    
    # Get stats
    stats = get_feedback_stats()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Feedback", stats["total"])
    with col2:
        st.metric("Helpful ✓", stats["helpful"])
    with col3:
        st.metric("Helpful %", f"{stats['helpful_percentage']:.1f}%")
    
    # Chart
    import pandas as pd
    data = pd.DataFrame({
        "Feedback": ["Helpful", "Not Helpful"],
        "Count": [stats["helpful"], stats["unhelpful"]]
    })
    st.bar_chart(data.set_index("Feedback"))
```

```python
# File: app.py (add to routing)

from views.feedback_analytics import render as render_feedback

page = st.sidebar.radio("Navigation", [..., "Feedback Analytics"])

if page == "Feedback Analytics":
    render_feedback()
```

### Scenario 2: Add React Component

**Example:** Feedback button below each response

```jsx
// File: react-frontend/src/components/FeedbackButton.jsx

import React, { useState } from 'react';
import { api } from '../services/api.js';

export function FeedbackButton({ queryLogId, onSubmit }) {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleFeedback = async (rating) => {
    setLoading(true);
    try {
      await api.post(`/api/feedback`, {
        query_log_id: queryLogId,
        rating: rating,  // 1 = helpful, 0 = not helpful
      });
      setSubmitted(true);
      if (onSubmit) onSubmit();
    } catch (error) {
      console.error('Feedback error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return <p className="text-green-600">✓ Thank you for your feedback!</p>;
  }

  return (
    <div className="flex gap-2 mt-2">
      <button
        onClick={() => handleFeedback(1)}
        disabled={loading}
        className="px-3 py-1 bg-green-500 text-white rounded"
      >
        👍 Helpful
      </button>
      <button
        onClick={() => handleFeedback(0)}
        disabled={loading}
        className="px-3 py-1 bg-red-500 text-white rounded"
      >
        👎 Not Helpful
      </button>
    </div>
  );
}
```

**Usage in ChatResponse:**

```jsx
<FeedbackButton queryLogId={response.id} />
```

---

## 🧪 Testing

### Unit Testing Example

```python
# File: tests/test_chunker.py

import pytest
from ingestion.chunker import chunk_document

def test_chunking_creates_overlap():
    """Test that chunks have proper overlap"""
    text = "a" * 600  # 600 characters
    chunks = chunk_document(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    
    # First chunk: chars 0-500
    assert len(chunks[0]["text"]) == 500
    
    # Second chunk: chars 450-950 (50-char overlap)
    assert len(chunks[1]["text"]) == 500
    assert chunks[0]["text"][450:] in chunks[1]["text"]  # Overlap present

def test_chunking_respects_sentence_boundaries():
    """Test that chunks break at sentence boundaries"""
    text = "Sentence one. Sentence two. Sentence three."
    chunks = chunk_document(text, 30, 5)
    
    # Should not break mid-sentence
    for chunk in chunks:
        assert "Sente" not in chunk["text"][-5:]  # No cut-off words

def test_heading_detection():
    """Test that headings are preserved"""
    text = "# Title\nContent here. ## Subtitle\nMore content."
    chunks = chunk_document(text, 100, 10)
    
    assert chunks[0]["metadata"]["heading"] == "Title"
    assert "Subtitle" in str(chunks)
```

**Run tests:**

```bash
pytest tests/test_chunker.py -v
```

### Integration Testing Example

```python
# File: tests/test_rag_pipeline.py

def test_full_rag_pipeline():
    """Test end-to-end: upload → search → answer"""
    
    # 1. Upload document
    doc_path = "tests/fixtures/sample.pdf"
    doc_id = upload_document(doc_path)
    assert doc_id is not None
    
    # 2. Wait for processing
    import time
    time.sleep(5)  # In production: use queue + callback
    
    # 3. Verify chunks stored
    chunk_count = get_chunk_count(doc_id)
    assert chunk_count > 0
    
    # 4. Query system
    query = "What is the main topic?"
    response = query_system(query)
    
    # 5. Verify response
    assert response["response"] is not None
    assert len(response["sources"]) > 0
    assert response["response_time_ms"] < 2000
```

---

## 🐛 Debugging

### Common Issues & Fixes

| Issue | Debug Steps | Fix |
|-------|------------|-----|
| **"LLM provider unavailable"** | Check if Ollama running: `curl http://localhost:11434/api/tags` | Start Ollama or switch provider |
| **Voice/Audio chat failures (FastAPI)** | Look for `ffmpeg` errors in python traceback | Verify `ffmpeg` is installed on host system and added to PATH |
| **ChromaDB search returns nothing** | Verify embeddings: `from ingestion.embedder import get_collection; print(get_collection().count())` | Re-upload document |
| **Slow responses (>2 seconds)** | Check `response_time_ms` in logs, profile LLM vs search | Switch to faster model |
| **SQL error "database is locked"** | Check concurrent writes | Use WAL mode: `PRAGMA journal_mode=WAL` |

### Adding Debug Logging

```python
# File: rag/generator.py

import logging

logger = logging.getLogger(__name__)

def generate_response(query, context):
    """With debug logging"""
    
    logger.debug(f"Query: {query}")
    logger.debug(f"Context length: {len(context)} chars")
    
    start_time = time.time()
    
    try:
        response = get_manager().generate(query, context)
        elapsed = time.time() - start_time
        logger.info(f"Response generated in {elapsed:.2f}s")
        logger.debug(f"Response: {response[:100]}...")
        
        return response
    
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}", exc_info=True)
        raise
```

**Enable debug logging:**

```python
# File: config.py

import logging
logging.basicConfig(level=logging.DEBUG)  # Shows all debug messages
```

---

## 🚀 Deployment

### Pre-Deployment Checklist

```
❏ Code review completed
❏ Tests pass locally
❏ No hardcoded secrets in code
❏ Dependencies documented in requirements.txt (including OS-level dependencies like FFmpeg)
❏ Database migrations tested
❏ Backup created
❏ Rollback plan documented
❏ Performance acceptable
❏ Security review completed
❏ Documentation updated
```

### Deployment Process

```
1. Create backup
   └─ Copy: data/astrobot.db → data/astrobot.db.backup

2. Stop services
   └─ ./stop-all-servers.ps1

3. Update code
   └─ git pull origin main

4. Update dependencies
   └─ pip install -r requirements.txt

5. Run migrations (if any)
   └─ python scripts/migrate.py

6. Start services
   └─ ./start-all-servers.ps1

7. Verify health
   └─ Check /api/health endpoint

8. Monitor logs
   └─ Watch for errors in first 5 minutes
```

### Rollback Procedure

```
If something goes wrong:

1. Stop services
   └─ ./stop-all-servers.ps1

2. Restore backup
   └─ cp data/astrobot.db.backup data/astrobot.db

3. Revert code
   └─ git reset --hard HEAD~1

4. Restart
   └─ ./start-all-servers.ps1
```

---

## 📝 Code Review Checklist

**When reviewing others' code, check:**

- [ ] Code follows [CODE_CONVENTIONS.md](CODE_CONVENTIONS.md)
- [ ] No hardcoded secrets/paths
- [ ] Proper error handling
- [ ] Security considerations addressed
- [ ] Tests included and passing
- [ ] Database queries parameterized
- [ ] Functions have docstrings
- [ ] Performance acceptable
- [ ] No breaking changes to API
- [ ] Documentation updated

---

## 🎓 Next Steps

- **Want coding standards?** → [CODE_CONVENTIONS.md](CODE_CONVENTIONS.md)
- **Want to add LLM?** → [ADDING_PROVIDERS.md](ADDING_PROVIDERS.md)
- **Want performance tips?** → [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)
- **Having issues?** → [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md)

