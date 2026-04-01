# 🤝 Contributing to IMS AstroBot

This guide explains how to add new features to AstroBot. Follow this step-by-step to understand where to make changes and how the code flows.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Reference: Where to Add Code](#quick-reference-where-to-add-code)
3. [Adding a New API Endpoint](#adding-a-new-api-endpoint)
4. [Adding a New UI Feature](#adding-a-new-ui-feature)
5. [Adding a New LLM Provider](#adding-a-new-llm-provider)
6. [Adding a New Document Parser](#adding-a-new-document-parser)
7. [Database Changes](#database-changes)
8. [Testing Your Changes](#testing-your-changes)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend (port 3000)     │   Streamlit UI (port 8501)   │
│  react-frontend/src/            │   app.py + views/            │
│  ↓                              │   ↓                          │
│  Vite Proxy → :8080             │   Direct Python calls        │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           │
┌─────────────────────────────────┐             │
│      SPRING BOOT LAYER          │             │
│      (port 8080)                │             │
├─────────────────────────────────┤             │
│  springboot-backend/            │             │
│  └── controller/ → REST APIs    │             │
│  └── service/    → Python proxy │             │
│  └── dto/        → Data objects │             │
│           │                     │             │
│           ▼                     │             │
│  PythonApiService.java          │             │
│  (HTTP calls to Python)         │             │
└─────────────────────────────────┘             │
                    │                           │
                    ▼                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PYTHON BACKEND LAYER                       │
│                         (port 8001)                             │
├─────────────────────────────────────────────────────────────────┤
│  api_server.py          → FastAPI REST endpoints                │
│  ├── auth/              → Authentication logic                  │
│  ├── database/db.py     → SQLite CRUD operations               │
│  ├── ingestion/         → Document parsing & chunking          │
│  │   ├── parser.py      → PDF, DOCX, Excel parsers             │
│  │   ├── chunker.py     → Text splitting logic                 │
│  │   └── embedder.py    → Embedding + ChromaDB storage         │
│  ├── rag/               → RAG pipeline                         │
│  │   ├── retriever.py   → Semantic search                      │
│  │   ├── generator.py   → LLM response generation              │
│  │   └── providers/     → LLM provider implementations         │
│  └── middleware/        → Rate limiting, logging               │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  data/astrobot.db       → SQLite (users, documents, logs)      │
│  data/chroma_db/        → ChromaDB (vector embeddings)         │
│  data/uploads/          → Uploaded document files              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Quick Reference: Where to Add Code

| Feature Type | Files to Modify |
|--------------|-----------------|
| **New REST API endpoint** | `api_server.py` → Spring Boot controller → React `api.js` |
| **New UI page (React)** | `react-frontend/src/pages/` + `App.jsx` routes |
| **New UI page (Streamlit)** | `views/` + `app.py` routing |
| **New LLM provider** | `rag/providers/` + `manager.py` |
| **New document type** | `ingestion/parser.py` |
| **New database table** | `database/db.py` |
| **New middleware** | `middleware/` + `api_server.py` |
| **Change chunking logic** | `ingestion/chunker.py` |
| **Change embedding model** | `config.py` + `ingestion/embedder.py` |

---

## 🔧 Adding a New API Endpoint

### Step 1: Add Python FastAPI Endpoint

**File: `api_server.py`**

```python
# Add your endpoint (group similar endpoints together)

@app.get("/api/your-feature")
async def get_your_feature():
    """
    Description of what this endpoint does.
    """
    try:
        # Your logic here
        result = do_something()
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in your-feature: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/your-feature")
async def create_your_feature(request: YourRequestModel):
    """
    Create a new feature item.
    """
    try:
        # Validate input
        if not request.name:
            raise HTTPException(status_code=400, detail="Name is required")
        
        # Your logic
        result = create_something(request.name)
        return {"status": "success", "id": result}
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error creating feature: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 2: Add Request/Response Models (if needed)

**File: `api_server.py`** (at the top with other models)

```python
class YourRequestModel(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[dict] = None

class YourResponseModel(BaseModel):
    id: str
    name: str
    created_at: str
```

### Step 3: Add Spring Boot Controller

**File: `springboot-backend/src/main/java/com/astrobot/controller/YourFeatureController.java`**

```java
package com.astrobot.controller;

import com.astrobot.service.PythonApiService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/your-feature")
public class YourFeatureController {

    @Autowired
    private PythonApiService pythonApiService;

    @GetMapping
    public Mono<ResponseEntity<Object>> getYourFeature() {
        return pythonApiService.getYourFeature()
            .map(ResponseEntity::ok)
            .onErrorReturn(ResponseEntity.internalServerError().build());
    }

    @PostMapping
    public Mono<ResponseEntity<Object>> createYourFeature(@RequestBody Map<String, Object> request) {
        return pythonApiService.createYourFeature(request)
            .map(ResponseEntity::ok)
            .onErrorReturn(ResponseEntity.internalServerError().build());
    }
}
```

### Step 4: Add PythonApiService Method

**File: `springboot-backend/src/main/java/com/astrobot/service/PythonApiService.java`**

```java
// Add these methods to the class

public Mono<Object> getYourFeature() {
    return webClient.get()
        .uri("/api/your-feature")
        .retrieve()
        .bodyToMono(Object.class)
        .timeout(Duration.ofSeconds(30))
        .doOnError(e -> logger.error("Error getting your-feature: {}", e.getMessage()));
}

public Mono<Object> createYourFeature(Map<String, Object> request) {
    return webClient.post()
        .uri("/api/your-feature")
        .bodyValue(request)
        .retrieve()
        .bodyToMono(Object.class)
        .timeout(Duration.ofSeconds(30))
        .doOnError(e -> logger.error("Error creating your-feature: {}", e.getMessage()));
}
```

### Step 5: Add React API Function

**File: `react-frontend/src/services/api.js`**

```javascript
// Add these functions

export const getYourFeature = async () => {
  const response = await api.get('/api/your-feature');
  return response.data;
};

export const createYourFeature = async (data) => {
  const response = await api.post('/api/your-feature', data);
  return response.data;
};
```

### Step 6: Test the Full Flow

```bash
# 1. Restart Python API
uvicorn api_server:app --reload --port 8001

# 2. Restart Spring Boot
cd springboot-backend && ./mvnw spring-boot:run

# 3. Test the endpoint directly
curl http://localhost:8001/api/your-feature

# 4. Test through Spring Boot
curl http://localhost:8080/api/your-feature

# 5. Test in React app (browser console)
# fetch('/api/your-feature').then(r => r.json()).then(console.log)
```

---

## 🖥️ Adding a New UI Feature

### React Frontend

#### 1. Create Page Component

**File: `react-frontend/src/pages/YourFeaturePage.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { getYourFeature, createYourFeature } from '../services/api';

const YourFeaturePage = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const result = await getYourFeature();
      setData(result.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (formData) => {
    try {
      await createYourFeature(formData);
      await loadData(); // Refresh data
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create');
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="your-feature-page">
      <h1>Your Feature</h1>
      {/* Your UI here */}
    </div>
  );
};

export default YourFeaturePage;
```

#### 2. Add Route

**File: `react-frontend/src/App.jsx`**

```jsx
import YourFeaturePage from './pages/YourFeaturePage';

// Add to routes
<Route path="/your-feature" element={<YourFeaturePage />} />
```

#### 3. Add Navigation Link

**File: `react-frontend/src/components/Sidebar.jsx`** (or similar)

```jsx
<NavLink to="/your-feature">Your Feature</NavLink>
```

### Streamlit UI

#### 1. Create View File

**File: `views/your_feature.py`**

```python
import streamlit as st
from database.db import get_connection

def render():
    """Render your feature page."""
    st.title("🆕 Your Feature")
    
    # Check authentication
    if "user_id" not in st.session_state:
        st.warning("Please login first")
        return
    
    # Your UI logic
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Main Content")
        # Add your content here
        
    with col2:
        st.subheader("Actions")
        if st.button("Create New"):
            # Handle create action
            pass
```

#### 2. Add to App Routing

**File: `app.py`**

```python
from views import your_feature

# In the page routing section
elif page == "Your Feature":
    your_feature.render()
```

---

## 🤖 Adding a New LLM Provider

### Step 1: Create Provider Class

**File: `rag/providers/your_provider.py`**

```python
"""
Your LLM Provider implementation.
"""
import requests
from typing import Optional
from .base import LLMProvider

class YourProvider(LLMProvider):
    """Your LLM API provider."""
    
    def __init__(self, api_key: str, model: str = "default-model"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.yourprovider.com/v1"
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.3, max_tokens: int = 512) -> str:
        """Generate response from your LLM."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"YourProvider error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if provider is configured and reachable."""
        if not self.api_key:
            return False
        try:
            # Simple health check or model list call
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_status(self) -> dict:
        """Return provider status."""
        available = self.is_available()
        return {
            "provider": "your_provider",
            "available": available,
            "model": self.model if available else None,
            "error": None if available else "API key not configured or service unavailable"
        }
```

### Step 2: Register in Manager

**File: `rag/providers/manager.py`**

```python
from .your_provider import YourProvider

class ProviderManager:
    def __init__(self):
        # ... existing code ...
        
        # Add your provider initialization
        if config.YOUR_PROVIDER_API_KEY:
            self.providers["your_provider"] = YourProvider(
                api_key=config.YOUR_PROVIDER_API_KEY,
                model=config.YOUR_PROVIDER_MODEL
            )
```

### Step 3: Add Config Variables

**File: `config.py`**

```python
# Your Provider settings
YOUR_PROVIDER_API_KEY = os.getenv("YOUR_PROVIDER_API_KEY", "")
YOUR_PROVIDER_MODEL = os.getenv("YOUR_PROVIDER_MODEL", "default-model")
```

**File: `.env`**

```env
YOUR_PROVIDER_API_KEY=your-api-key-here
YOUR_PROVIDER_MODEL=your-model-name
```

---

## 📄 Adding a New Document Parser

### Step 1: Add Parser Function

**File: `ingestion/parser.py`**

```python
def _parse_your_format(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse .yourformat files.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (extracted_text, error_message)
        - Success: (text, None)
        - Failure: (None, error_message)
    """
    try:
        # Import your library (lazy import to avoid startup delays)
        import your_parser_library
        
        # Parse the file
        with open(file_path, 'rb') as f:
            content = your_parser_library.read(f)
        
        # Extract text
        text = content.get_text()
        
        if not text or not text.strip():
            return None, "File appears to be empty or unreadable"
        
        return text.strip(), None
        
    except ImportError:
        return None, "Missing library: pip install your_parser_library"
    except Exception as e:
        return None, f"Failed to parse .yourformat: {str(e)}"
```

### Step 2: Register in parse_document()

**File: `ingestion/parser.py`**

```python
def parse_document(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Main parser dispatcher."""
    ext = Path(file_path).suffix.lower()
    
    parsers = {
        '.pdf': _parse_pdf,
        '.docx': _parse_docx,
        '.xlsx': _parse_excel,
        '.xls': _parse_excel,
        '.pptx': _parse_pptx,
        '.html': _parse_html,
        '.htm': _parse_html,
        '.txt': _parse_text,
        '.md': _parse_text,
        '.yourformat': _parse_your_format,  # Add your format here
    }
    
    parser = parsers.get(ext)
    if not parser:
        return None, f"Unsupported file type: {ext}"
    
    return parser(file_path)
```

### Step 3: Update Allowed Extensions

**File: `api_server.py`** (in upload endpoint)

```python
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.xls', '.pptx', '.html', '.htm', '.txt', '.md', '.yourformat'}
```

### Step 4: Add Required Library

**File: `requirements.txt`**

```
your_parser_library>=1.0.0
```

---

## 🗄️ Database Changes

### Adding a New Table

**File: `database/db.py`**

```python
def init_db():
    """Initialize database with all tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # ... existing tables ...
    
    # Your new table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS your_table (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            user_id TEXT,
            data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
```

### Adding CRUD Functions

```python
def create_your_item(name: str, user_id: str, data: dict = None) -> str:
    """Create a new item."""
    conn = get_connection()
    cursor = conn.cursor()
    
    item_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO your_table (id, name, user_id, data, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (item_id, name, user_id, json.dumps(data) if data else None, now))
    
    conn.commit()
    conn.close()
    return item_id


def get_your_items(user_id: str = None) -> list:
    """Get all items, optionally filtered by user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute('SELECT * FROM your_table WHERE user_id = ?', (user_id,))
    else:
        cursor.execute('SELECT * FROM your_table')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def delete_your_item(item_id: str) -> bool:
    """Delete an item by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM your_table WHERE id = ?', (item_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted
```

---

## 🧪 Testing Your Changes

### Manual Testing Checklist

```markdown
## Before Pushing
- [ ] Python API starts without errors
- [ ] Spring Boot compiles and starts
- [ ] React builds without warnings
- [ ] Endpoint works: curl http://localhost:8001/api/your-endpoint
- [ ] Endpoint works through proxy: curl http://localhost:8080/api/your-endpoint
- [ ] UI displays correctly in browser
- [ ] Error handling works (test with invalid input)
- [ ] No console errors in browser dev tools
```

### Quick Test Commands

```bash
# Test Python API directly
curl -X GET http://localhost:8001/api/your-endpoint
curl -X POST http://localhost:8001/api/your-endpoint -H "Content-Type: application/json" -d '{"name":"test"}'

# Test through Spring Boot
curl -X GET http://localhost:8080/api/your-endpoint

# Check Python API health
curl http://localhost:8001/api/health

# Check all services running
netstat -ano | findstr "8001 8080 3000"
```

### Browser Testing

```javascript
// In browser console (on React app)

// Test GET
fetch('/api/your-endpoint').then(r => r.json()).then(console.log)

// Test POST
fetch('/api/your-endpoint', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({name: 'test'})
}).then(r => r.json()).then(console.log)
```

---

## 🔁 Common Patterns

### Error Handling Pattern (Python)

```python
@app.post("/api/something")
async def do_something(request: RequestModel):
    try:
        # Validate
        if not request.required_field:
            raise HTTPException(status_code=400, detail="required_field is required")
        
        # Process
        result = process(request)
        
        # Return success
        return {"status": "success", "data": result}
        
    except HTTPException:
        raise  # Let HTTP exceptions pass through
    except Exception as e:
        logger.error(f"Error in do_something: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

### React Data Fetching Pattern

```jsx
const [data, setData] = useState([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

const loadData = async () => {
  try {
    setLoading(true);
    setError(null);
    const result = await apiFunction();
    setData(result.data || []);
  } catch (err) {
    setError(err.response?.data?.detail || 'Operation failed');
  } finally {
    setLoading(false);
  }
};

useEffect(() => { loadData(); }, []);
```

### Spring Boot Proxy Pattern

```java
public Mono<ResponseEntity<Object>> proxyEndpoint() {
    return pythonApiService.callPythonEndpoint()
        .map(ResponseEntity::ok)
        .onErrorResume(e -> {
            logger.error("Proxy error: {}", e.getMessage());
            return Mono.just(ResponseEntity.status(503).body(
                Map.of("error", "Python API unavailable")
            ));
        });
}
```

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| **422 Unprocessable Entity** | Check request body matches expected schema. Print `request.dict()` in Python to debug. |
| **500 Internal Server Error** | Check Python logs (`logs/` folder). Add `exc_info=True` to logger.error() calls. |
| **CORS Error** | Add origin to `api_server.py` CORS middleware and Spring Boot `WebConfig.java`. |
| **React not updating** | Clear browser cache. Check Vite proxy config in `vite.config.js`. |
| **Spring Boot can't reach Python** | Verify Python running on port 8001. Check `application.properties` for correct URL. |
| **Database locked** | Restart all servers. Enable WAL mode: `PRAGMA journal_mode=WAL;` |
| **ChromaDB errors** | Delete `data/chroma_db/` folder and re-upload documents. |

---

## 📂 File Reference

| Purpose | Primary File | Related Files |
|---------|--------------|---------------|
| API Endpoints | `api_server.py` | `middleware/*.py` |
| Database | `database/db.py` | `data/astrobot.db` |
| Document Parsing | `ingestion/parser.py` | `ingestion/chunker.py`, `ingestion/embedder.py` |
| LLM Providers | `rag/providers/*.py` | `rag/generator.py` |
| Semantic Search | `rag/retriever.py` | `data/chroma_db/` |
| Configuration | `config.py` | `.env` |
| React Pages | `react-frontend/src/pages/` | `react-frontend/src/services/api.js` |
| React Components | `react-frontend/src/components/` | |
| Spring Controllers | `springboot-backend/.../controller/` | `springboot-backend/.../service/` |
| Streamlit Views | `views/*.py` | `app.py` |

---

## 🚀 Quick Start Workflow

```bash
# 1. Make your code changes

# 2. Restart Python API (auto-reloads with --reload)
uvicorn api_server:app --reload --port 8001

# 3. Restart Spring Boot (if Java changes)
cd springboot-backend && ./mvnw spring-boot:run

# 4. React auto-reloads (npm run dev)

# 5. Test your changes
curl http://localhost:8001/api/your-endpoint

# 6. Check browser console for errors

# 7. Commit when working
git add .
git commit -m "Add your-feature: description"
```

---

**Questions?** Check the existing code for patterns. Most features follow similar structures.

Good luck! 🎉
