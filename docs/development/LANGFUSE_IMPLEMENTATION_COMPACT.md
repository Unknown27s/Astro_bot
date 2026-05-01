# Langfuse Full Implementation Plan - Compact

## PHASE 1: Trace ID Plumbing (3-4 hrs)

### 1.1 Python Backend - api_server.py

**Add imports** (top of file):
```python
import uuid
from typing import Optional
from fastapi import Header
```

**Modify `/api/chat` endpoint:**
```python
@app.post("/api/chat")
async def chat(
    request: Request,
    x_langfuse_trace_id: Optional[str] = Header(None),
    query: str = None,
    user_id: Optional[str] = None,
    **kwargs
):
    # Generate or use provided trace_id
    trace_id = x_langfuse_trace_id or str(uuid.uuid4())
    
    # Store in context for retriever/generator to use
    from rag.observability.trace_context import set_trace_id
    set_trace_id(trace_id)
    
    # ... existing chat logic ...
    
    # Make sure response includes trace_id
    return {
        "response": result["response"],
        "trace_id": trace_id,  # ADD THIS
        "citations": citations,
        # ... other fields ...
    }

@app.post("/api/chat/audio")
async def chat_audio(
    request: Request,
    x_langfuse_trace_id: Optional[str] = Header(None),
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    **kwargs
):
    trace_id = x_langfuse_trace_id or str(uuid.uuid4())
    
    from rag.observability.trace_context import set_trace_id
    set_trace_id(trace_id)
    
    # ... existing audio logic ...
    
    return {
        "transcribed_text": transcribed_text,
        "response": result["response"],
        "trace_id": trace_id,  # ADD THIS
        # ... other fields ...
    }
```

### 1.2 Create Python Context Module

**New file: `rag/observability/trace_context.py`**
```python
"""Thread-safe context for storing trace_id across RAG pipeline."""

import contextvars
from typing import Optional

# Context variable to store trace_id
_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id', default=None)

def set_trace_id(trace_id: str) -> None:
    """Set trace_id for current context."""
    _trace_id.set(trace_id)

def get_trace_id() -> Optional[str]:
    """Get trace_id from current context."""
    return _trace_id.get()

def clear_trace_id() -> None:
    """Clear trace_id from current context."""
    _trace_id.set(None)
```

### 1.3 Update Python Langfuse Client

**Modify: `rag/observability/langfuse_client.py` - `start_observation()` function**

Find this section (around line 206):
```python
def start_observation(
    name: str,
    user_id: Optional[str] = None,
    input_payload: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ObservationTrace:
```

Replace with:
```python
def start_observation(
    name: str,
    user_id: Optional[str] = None,
    input_payload: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
    trace_id: Optional[str] = None,  # NEW PARAM
) -> ObservationTrace:
    """Start a trace that can collect spans through the pipeline."""
    from rag.observability.trace_context import get_trace_id
    
    # Use provided trace_id or get from context or generate new
    if not trace_id:
        trace_id = get_trace_id()
    if not trace_id:
        trace_id = str(uuid.uuid4())
    
    # Rest remains same, but pass trace_id to Langfuse
    base_meta = dict(metadata or {})
    base_meta.setdefault("component", "astrobot")
    base_meta["trace_id"] = trace_id  # ADD THIS
    
    if user_id:
        base_meta.setdefault("user_hash", hash_user_identifier(user_id))
    
    # ... rest of function ...
    
    return ObservationTrace(
        trace_id=trace_id,
        name=name,
        trace_client=trace_client,
        start_time=time.time(),
        metadata=base_meta,
    )
```

### 1.4 Spring Boot - ChatController.java

**Modify: `springboot-backend/src/main/java/com/astrobot/controller/ChatController.java`**

Add to class level:
```java
@PostMapping("/api/chat")
public ResponseEntity<?> chat(
    @RequestBody ChatRequest request,
    @RequestHeader(value = "X-Langfuse-Trace-Id", required = false) String traceId,
    HttpServletRequest httpRequest
) {
    // Generate trace_id if not provided
    if (traceId == null || traceId.isEmpty()) {
        traceId = UUID.randomUUID().toString();
    }
    
    // Store in request scope
    final String finalTraceId = traceId;
    httpRequest.setAttribute("trace_id", finalTraceId);
    
    // Add to request headers when calling Python
    HttpHeaders headers = new HttpHeaders();
    headers.set("X-Langfuse-Trace-Id", finalTraceId);
    headers.set("Content-Type", "application/json");
    
    // Call Python with trace_id header
    try {
        ResponseEntity<ChatResponse> pythonResponse = restTemplate.exchange(
            pythonApiUrl + "/api/chat",
            HttpMethod.POST,
            new HttpEntity<>(request, headers),
            ChatResponse.class
        );
        
        ChatResponse response = pythonResponse.getBody();
        
        // Ensure trace_id in response
        if (response != null) {
            response.setTraceId(finalTraceId);
            return ResponseEntity.ok(response);
        }
        
        return ResponseEntity.status(500).body("No response from Python API");
    } catch (Exception e) {
        logger.error("Error calling Python API", e);
        ChatResponse errorResponse = new ChatResponse();
        errorResponse.setTraceId(finalTraceId);
        errorResponse.setError("Failed to get response: " + e.getMessage());
        return ResponseEntity.status(500).body(errorResponse);
    }
}

@PostMapping("/api/chat/audio")
public ResponseEntity<?> chatAudio(
    @RequestParam("file") MultipartFile file,
    @RequestParam(value = "user_id", required = false) String userId,
    @RequestHeader(value = "X-Langfuse-Trace-Id", required = false) String traceId,
    HttpServletRequest httpRequest
) {
    if (traceId == null || traceId.isEmpty()) {
        traceId = UUID.randomUUID().toString();
    }
    
    final String finalTraceId = traceId;
    httpRequest.setAttribute("trace_id", finalTraceId);
    
    HttpHeaders headers = new HttpHeaders();
    headers.set("X-Langfuse-Trace-Id", finalTraceId);
    headers.setContentType(MediaType.MULTIPART_FORM_DATA);
    
    try {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new HttpEntity<>(file.getBytes(), createFileHeaders(file.getOriginalFilename())));
        if (userId != null) {
            body.add("user_id", userId);
        }
        
        ResponseEntity<ChatResponse> pythonResponse = restTemplate.exchange(
            pythonApiUrl + "/api/chat/audio",
            HttpMethod.POST,
            new HttpEntity<>(body, headers),
            ChatResponse.class
        );
        
        ChatResponse response = pythonResponse.getBody();
        if (response != null) {
            response.setTraceId(finalTraceId);
            return ResponseEntity.ok(response);
        }
        
        return ResponseEntity.status(500).body("No response from Python API");
    } catch (Exception e) {
        logger.error("Error calling Python audio API", e);
        ChatResponse errorResponse = new ChatResponse();
        errorResponse.setTraceId(finalTraceId);
        errorResponse.setError("Failed to process audio: " + e.getMessage());
        return ResponseEntity.status(500).body(errorResponse);
    }
}
```

**Update DTOs:**
```java
// ChatRequest.java
public class ChatRequest {
    private String query;
    private String userId;
    private String traceId;  // ADD THIS
    
    // getters/setters
    public String getTraceId() { return traceId; }
    public void setTraceId(String traceId) { this.traceId = traceId; }
}

// ChatResponse.java
public class ChatResponse {
    private String response;
    private String traceId;  // ADD THIS
    private String error;
    
    // getters/setters
    public String getTraceId() { return traceId; }
    public void setTraceId(String traceId) { this.traceId = traceId; }
}
```

**Add import:**
```java
import java.util.UUID;
```

### 1.5 React Frontend - api.js

**Modify: `react-frontend/src/services/api.js`**

```javascript
// Helper to manage trace_id
const getOrCreateTraceId = () => {
    let traceId = sessionStorage.getItem('langfuse_trace_id');
    if (!traceId) {
        traceId = generateUUID();
        sessionStorage.setItem('langfuse_trace_id', traceId);
    }
    return traceId;
};

const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
};

// Modified sendMessage function
export const sendMessage = async (query, userId = null) => {
    const traceId = getOrCreateTraceId();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Langfuse-Trace-Id': traceId,  // NEW
            },
            body: JSON.stringify({
                query,
                user_id: userId,
                trace_id: traceId,  // NEW
            }),
        });
        
        const data = await response.json();
        
        // Store trace_id from response
        if (data.trace_id) {
            sessionStorage.setItem('last_message_trace_id', data.trace_id);
        }
        
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
};

// Modified sendAudioMessage function
export const sendAudioMessage = async (audioBlob, userId = null) => {
    const traceId = getOrCreateTraceId();
    
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');
    if (userId) formData.append('user_id', userId);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/audio`, {
            method: 'POST',
            headers: {
                'X-Langfuse-Trace-Id': traceId,  // NEW
            },
            body: formData,
        });
        
        const data = await response.json();
        
        if (data.trace_id) {
            sessionStorage.setItem('last_message_trace_id', data.trace_id);
        }
        
        return data;
    } catch (error) {
        console.error('Error sending audio:', error);
        throw error;
    }
};

// New function to send feedback
export const sendFeedback = async (rating, comment = null) => {
    const traceId = sessionStorage.getItem('last_message_trace_id');
    if (!traceId) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Langfuse-Trace-Id': traceId,
            },
            body: JSON.stringify({
                trace_id: traceId,
                rating,
                comment,
            }),
        });
        
        return response.ok;
    } catch (error) {
        console.error('Error sending feedback:', error);
        return false;
    }
};
```

### 1.6 React - Add Feedback Button

**Modify: `react-frontend/src/components/chat/BotMessage.jsx`**

```jsx
import { sendFeedback } from '../../services/api';

export default function BotMessage({ content, sources, traceId }) {
    const [feedbackSent, setFeedbackSent] = useState(false);
    
    const handleThumbsUp = async () => {
        const success = await sendFeedback(1, 'thumbs_up');
        if (success) setFeedbackSent(true);
    };
    
    const handleThumbsDown = async () => {
        const success = await sendFeedback(-1, 'thumbs_down');
        if (success) setFeedbackSent(true);
    };
    
    return (
        <div className="bot-message">
            <div className="content">{content}</div>
            
            {sources && <div className="sources">{sources}</div>}
            
            {/* Feedback buttons */}
            <div className="feedback-buttons">
                <button 
                    onClick={handleThumbsUp}
                    disabled={feedbackSent}
                    title="This response was helpful"
                >
                    👍
                </button>
                <button 
                    onClick={handleThumbsDown}
                    disabled={feedbackSent}
                    title="This response was not helpful"
                >
                    👎
                </button>
            </div>
            
            {feedbackSent && <span className="text-xs text-gray-500">Feedback recorded</span>}
        </div>
    );
}
```

---

## PHASE 2: Spring Boot Instrumentation (2-3 hrs)

### 2.1 Create Langfuse Interceptor

**New file: `springboot-backend/src/main/java/com/astrobot/middleware/LangfuseInterceptor.java`**

```java
package com.astrobot.middleware;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@Component
public class LangfuseInterceptor implements HandlerInterceptor {
    
    private static final Logger logger = LoggerFactory.getLogger(LangfuseInterceptor.class);
    
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String traceId = request.getHeader("X-Langfuse-Trace-Id");
        long startTime = System.currentTimeMillis();
        
        request.setAttribute("trace_id", traceId);
        request.setAttribute("request_start_time", startTime);
        
        logger.debug("Request started - Trace ID: {}, Path: {}", traceId, request.getRequestURI());
        return true;
    }
    
    @Override
    public void afterCompletion(
        HttpServletRequest request, 
        HttpServletResponse response, 
        Object handler, 
        Exception ex
    ) {
        String traceId = (String) request.getAttribute("trace_id");
        long startTime = (long) request.getAttribute("request_start_time");
        long duration = System.currentTimeMillis() - startTime;
        
        int statusCode = response.getStatus();
        
        logger.info("Request completed - Trace ID: {}, Path: {}, Duration: {}ms, Status: {}", 
            traceId, request.getRequestURI(), duration, statusCode);
        
        if (ex != null) {
            logger.error("Request error - Trace ID: {}, Exception: {}", traceId, ex.getMessage(), ex);
        }
    }
}
```

### 2.2 Register Interceptor

**Modify: `springboot-backend/src/main/java/com/astrobot/config/WebConfig.java`**

```java
package com.astrobot.config;

import com.astrobot.middleware.LangfuseInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    
    @Autowired
    private LangfuseInterceptor langfuseInterceptor;
    
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(langfuseInterceptor)
            .addPathPatterns("/api/**");  // Apply to all API endpoints
    }
}
```

---

## PHASE 3: Python Enhanced Tracing (2 hrs)

### 3.1 Update Retriever to Use Context

**Modify: `rag/retriever.py` - in `retrieve_context()` function**

Find where `start_observation` is called (around line 787):

```python
# ADD THIS IMPORT at top
from rag.observability.trace_context import get_trace_id

# FIND THIS (around line 787-791):
obs_span = _start_obs_span(
    obs_trace,
    name="rag.retrieve_context",
    input_payload={"query": query, "top_k": top_k, "source_type": source_type, "doc_id": doc_id},
)

# REPLACE WITH THIS:
trace_id = get_trace_id()  # GET TRACE_ID FROM CONTEXT
obs_span = _start_obs_span(
    obs_trace,
    name="rag.retrieve_context",
    input_payload={"query": query, "top_k": top_k, "source_type": source_type, "doc_id": doc_id},
    metadata={"trace_id": trace_id} if trace_id else None,
)
```

### 3.2 Update Generator to Use Context

**Modify: `rag/generator.py` - in `generate_response()` function**

Find start (around line 88):

```python
# ADD THIS IMPORT at top
from rag.observability.trace_context import get_trace_id

# In generate_response() function, add after start_time assignment:
trace_id = get_trace_id()  # ADD THIS LINE

# When calling _check_memory, pass trace_id in metadata:
memory_result = _check_memory(query, user_id)
```

---

## PHASE 4: Admin Dashboard (3-4 hrs)

### 4.1 Python Metrics Endpoint

**Add to: `api_server.py`**

```python
@app.get("/api/admin/langfuse/metrics")
async def get_langfuse_metrics(days: int = 7):
    """Fetch Langfuse metrics for dashboard."""
    from datetime import datetime, timedelta
    from rag.observability.langfuse_client import get_langfuse_client
    
    client = get_langfuse_client()
    if not client:
        return {"error": "Langfuse not configured", "metrics": None}
    
    try:
        # For now, return placeholder - integrate with Langfuse SDK later
        return {
            "period_days": days,
            "total_queries": 0,
            "avg_latency_ms": 0,
            "error_rate": 0,
            "avg_retrieval_score": 0,
            "cache_hit_rate": 0,
        }
    except Exception as e:
        logger.error(f"Error fetching Langfuse metrics: {e}")
        return {"error": str(e)}

@app.post("/api/feedback")
async def submit_feedback(
    trace_id: str,
    rating: float,
    comment: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Record user feedback for a trace."""
    from rag.observability.langfuse_client import record_feedback
    
    success = record_feedback(trace_id, rating, comment)
    
    return {
        "success": success,
        "trace_id": trace_id,
        "rating": rating,
    }

@app.post("/api/telemetry/event")
async def record_telemetry_event(
    trace_id: str,
    event: str,
    timestamp: str,
    metadata: Optional[dict] = None,
):
    """Record frontend telemetry event."""
    logger.info(f"Telemetry: {event} (trace={trace_id}) - {metadata}")
    return {"success": True}
```

### 4.2 React Admin Page

**New file: `react-frontend/src/pages/admin/LangfuseAdminPage.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { fetchLangfuseMetrics } from '../../services/api';

export default function LangfuseAdminPage() {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState(7);
    
    useEffect(() => {
        const loadMetrics = async () => {
            setLoading(true);
            const data = await fetchLangfuseMetrics(days);
            setMetrics(data);
            setLoading(false);
        };
        loadMetrics();
    }, [days]);
    
    if (loading) return <div>Loading...</div>;
    if (!metrics) return <div>No data available</div>;
    
    return (
        <div className="p-6">
            <h1 className="text-3xl font-bold mb-6">Langfuse Observability</h1>
            
            {/* Period selector */}
            <div className="mb-6 flex gap-4">
                {[7, 14, 30].map(d => (
                    <button
                        key={d}
                        onClick={() => setDays(d)}
                        className={`px-4 py-2 rounded ${
                            days === d ? 'bg-blue-600 text-white' : 'bg-gray-200'
                        }`}
                    >
                        Last {d} days
                    </button>
                ))}
            </div>
            
            {/* Metrics grid */}
            <div className="grid grid-cols-4 gap-4 mb-6">
                <MetricCard 
                    title="Total Queries"
                    value={metrics.total_queries}
                />
                <MetricCard 
                    title="Avg Latency"
                    value={`${metrics.avg_latency_ms}ms`}
                />
                <MetricCard 
                    title="Cache Hit Rate"
                    value={`${(metrics.cache_hit_rate * 100).toFixed(1)}%`}
                />
                <MetricCard 
                    title="Error Rate"
                    value={`${(metrics.error_rate * 100).toFixed(2)}%`}
                />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
                <MetricCard 
                    title="Avg Retrieval Score"
                    value={metrics.avg_retrieval_score.toFixed(3)}
                />
                <MetricCard 
                    title="Period"
                    value={`${days} days`}
                />
            </div>
        </div>
    );
}

function MetricCard({ title, value }) {
    return (
        <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-gray-600 text-sm font-semibold">{title}</h3>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
    );
}
```

**Add to: `react-frontend/src/services/api.js`**

```javascript
export const fetchLangfuseMetrics = async (days = 7) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/langfuse/metrics?days=${days}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            },
        });
        return await response.json();
    } catch (error) {
        console.error('Error fetching Langfuse metrics:', error);
        return null;
    }
};
```

---

## Testing

### Test Python Backend
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-Langfuse-Trace-Id: test-trace-123" \
  -H "Content-Type: application/json" \
  -d '{"query":"What are fees?","user_id":"student1"}'

# Check response includes trace_id
```

### Test Spring Boot
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "X-Langfuse-Trace-Id: test-trace-456" \
  -H "Content-Type: application/json" \
  -d '{"query":"What are admission criteria?","userId":"student1"}'
```

### Test React
```javascript
// In browser console
sessionStorage.getItem('langfuse_trace_id');
// Should show UUID
```

---

## Activation Checklist

- [ ] Copy `trace_context.py` to `rag/observability/`
- [ ] Update `api_server.py` (both endpoints)
- [ ] Update `langfuse_client.py` 
- [ ] Update Spring Boot ChatController.java
- [ ] Update Spring Boot DTOs
- [ ] Create WebConfig.java
- [ ] Create LangfuseInterceptor.java
- [ ] Update React `api.js`
- [ ] Update `BotMessage.jsx` (feedback buttons)
- [ ] Add Langfuse credentials to `.env`:
  ```env
  LANGFUSE_ENABLED=true
  LANGFUSE_PUBLIC_KEY=pk_...
  LANGFUSE_SECRET_KEY=sk_...
  ```
- [ ] Restart all 3 services (React, Spring Boot, Python)
- [ ] Test endpoints with curl
- [ ] Check Langfuse dashboard for traces
- [ ] Deploy Phase 4 (admin dashboard)

---

**Total Time: 8-12 hours end-to-end**
