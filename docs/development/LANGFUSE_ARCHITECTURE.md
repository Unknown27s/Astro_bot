# Langfuse Integration Across Three-Layer Architecture

## My Thoughts on Langfuse for AstroBot

### Pros ✅
1. **End-to-End Visibility**: Traces entire request lifecycle (from user click to LLM response)
2. **Cost Tracking**: Accurately tracks token usage and LLM provider costs
3. **Debugging**: Step-by-step breakdown shows exactly where requests fail or slow down
4. **User Feedback Loop**: Collect user feedback and correlate with system performance
5. **No External Dependencies**: Works without additional infrastructure (cloud-hosted)
6. **Safe Defaults**: Built-in privacy (user ID hashing, truncation)

### Cons ⚠️
1. **Network Latency**: Sending traces to cloud can add 10-50ms per request
2. **Privacy**: Requires sending request/response data to third-party
3. **Cost**: Premium features may require paid Langfuse subscription
4. **Complexity**: Three-layer architecture requires careful trace correlation
5. **Debugging**: Distributed tracing across multiple services is harder to debug

### Recommendation 🎯
**Implement full stack tracing** because:
- You have three distinct layers that need visibility
- LLM costs are the biggest variable in your system
- User feedback + traces = powerful quality improvements
- Debugging production issues will be 10x easier

---

## Current State: Python Backend Only

Your Python backend has:
- ✅ Langfuse client initialized (safe, no-op fallback)
- ✅ Trace spans for retrieval, generation, memory
- ✅ User hashing for privacy
- ✅ Feedback recording endpoint

**Missing:**
- ❌ Spring Boot middleware tracing
- ❌ React frontend event tracking
- ❌ Trace ID correlation across layers
- ❌ Network latency instrumentation

---

## Architecture Challenges

### Challenge 1: Trace ID Propagation

```
React (user clicks "ask")
  ↓ [trace_id=abc123]
Spring Boot (receives request)
  ↓ [must pass trace_id in header]
Python (starts span with trace_id)
  ↓
Langfuse receives unified trace
```

**Solution:** Use HTTP header `X-Langfuse-Trace-Id` across all layers.

### Challenge 2: Timing Attribution

```
Total latency: 500ms
  ├─ React rendering: 50ms (before request)
  ├─ Network (React→Spring): 30ms
  ├─ Spring Boot processing: 100ms
  ├─ Network (Spring→Python): 30ms
  └─ Python RAG pipeline: 290ms
```

**Solution:** Each layer records its own span, Langfuse correlates via trace_id.

### Challenge 3: Error Propagation

```
Python raises error
  ↓
Spring Boot catches and re-throws (or wraps)
  ↓
React shows error to user
  ↓
Must correlate back to Python error + trace
```

**Solution:** Pass error details through response headers.

### Challenge 4: Async/Background Jobs

```
React sends async request
  ↓
Spring Boot queues job
  ↓
Python processes asynchronously
  ↓
React polls for status
```

**Solution:** Store trace_id in queue, retrieve when job completes.

---

## Implementation Plan

### Phase 1: Trace ID Plumbing (3-4 hours)

**Step 1.1: Modify Python** (`api_server.py`)
```python
from fastapi import Request, Header
from rag.observability.langfuse_client import start_observation
import uuid

@app.post("/api/chat")
async def chat(
    request: Request,
    x_langfuse_trace_id: Optional[str] = Header(None),
    ...
):
    # Use provided trace_id or generate new one
    trace_id = x_langfuse_trace_id or str(uuid.uuid4())
    
    # Start observation with trace_id
    trace = start_observation(
        name="api.chat",
        user_id=user_id,
        input_payload={"query": query},
        metadata={"trace_id": trace_id}
    )
    
    # ... rest of chat logic
    
    # Return trace_id in response
    return {
        "response": result,
        "trace_id": trace_id,  # NEW
        ...
    }
```

**Step 1.2: Modify Spring Boot** (`ChatController.java`)
```java
@PostMapping("/api/chat")
public ResponseEntity<?> chat(
    @RequestBody ChatRequest request,
    HttpServletRequest httpRequest
) {
    // Generate or use existing trace ID
    String traceId = request.getTraceId() != null ? 
        request.getTraceId() : 
        UUID.randomUUID().toString();
    
    // Add to request headers when calling Python
    HttpHeaders headers = new HttpHeaders();
    headers.set("X-Langfuse-Trace-Id", traceId);
    
    // Call Python API with trace ID
    ResponseEntity<ChatResponse> pythonResponse = restTemplate.exchange(
        pythonApiUrl + "/api/chat",
        HttpMethod.POST,
        new HttpEntity<>(request, headers),
        ChatResponse.class
    );
    
    // Ensure trace_id is in response
    ChatResponse response = pythonResponse.getBody();
    if (response.getTraceId() == null) {
        response.setTraceId(traceId);
    }
    
    return ResponseEntity.ok(response);
}

// New DTO fields
public class ChatRequest {
    private String traceId;  // NEW
    private String query;
    private String userId;
    // ... other fields
}

public class ChatResponse {
    private String traceId;  // NEW
    private String response;
    // ... other fields
}
```

**Step 1.3: Modify React** (`ChatPage.jsx` or `api.js`)
```javascript
// Generate or retrieve trace_id from localStorage
const getTraceId = () => {
    let traceId = sessionStorage.getItem('langfuse_trace_id');
    if (!traceId) {
        traceId = generateUUID();
        sessionStorage.setItem('langfuse_trace_id', traceId);
    }
    return traceId;
};

// Modified API call
const sendChatMessage = async (query) => {
    const traceId = getTraceId();
    
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Langfuse-Trace-Id': traceId,  // NEW
        },
        body: JSON.stringify({
            query,
            userId,
            traceId,  // NEW
        }),
    });
    
    const data = await response.json();
    
    // Store trace_id from response for feedback later
    if (data.trace_id) {
        sessionStorage.setItem('last_message_trace_id', data.trace_id);
    }
    
    return data;
};
```

### Phase 2: Instrumentation (4-6 hours)

**Step 2.1: Spring Boot Method Tracing**

Add interceptor for automatic request/response logging:
```java
// New file: middleware/LangfuseInterceptor.java
@Component
public class LangfuseInterceptor implements HandlerInterceptor {
    
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String traceId = request.getHeader("X-Langfuse-Trace-Id");
        request.setAttribute("trace_id", traceId);
        request.setAttribute("request_start_time", System.currentTimeMillis());
        return true;
    }
    
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        long duration = System.currentTimeMillis() - (long) request.getAttribute("request_start_time");
        String traceId = (String) request.getAttribute("trace_id");
        
        // Log to Langfuse (if enabled)
        // TODO: Send to Langfuse
    }
}

// Register interceptor in WebConfig
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LangfuseInterceptor());
    }
}
```

**Step 2.2: Python Service Mapping**

Add trace context to all RAG calls:
```python
# rag/observability/trace_context.py
import contextvars

trace_id_var = contextvars.ContextVar('trace_id', default=None)

def set_trace_id(trace_id: str):
    trace_id_var.set(trace_id)

def get_trace_id() -> str:
    return trace_id_var.get()

# In rag/retriever.py
def retrieve_context(query: str, trace=None, **kwargs):
    trace_id = get_trace_id()
    
    # Use trace_id for all spans
    obs_span = _start_obs_span(
        obs_trace,
        name="rag.retrieve_context",
        input_payload={"query": query, "trace_id": trace_id},
    )
```

**Step 2.3: React Instrumentation**

```javascript
// hooks/useLangfuse.js
export const useLangfuse = () => {
    const recordEvent = (eventName, metadata = {}) => {
        const traceId = sessionStorage.getItem('langfuse_trace_id');
        
        // Send to backend (Python creates span)
        fetch('/api/telemetry/event', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                trace_id: traceId,
                event: eventName,
                timestamp: new Date().toISOString(),
                metadata,
            }),
        }).catch(() => {}); // Silent fail
    };
    
    return { recordEvent };
};

// Usage in ChatPage.jsx
const { recordEvent } = useLangfuse();

// Track user interactions
const handleSendMessage = async (query) => {
    recordEvent('user_sent_query', { 
        query_length: query.length,
        has_voice: false 
    });
    
    const startTime = performance.now();
    const response = await sendChatMessage(query);
    const duration = performance.now() - startTime;
    
    recordEvent('received_response', {
        duration_ms: Math.round(duration),
        response_length: response.response.length,
    });
};

// Track feedback
const handleFeedback = async (rating, comment) => {
    const traceId = sessionStorage.getItem('last_message_trace_id');
    
    recordEvent('user_feedback', {
        trace_id: traceId,
        rating,
        has_comment: !!comment,
    });
    
    // Also send to backend for Langfuse
    await fetch('/api/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            trace_id: traceId,
            rating,
            comment,
        }),
    });
};
```

### Phase 3: Admin Dashboard (2-3 hours)

**Step 3.1: Trace Dashboard** (`LangfuseAdminPage.jsx`)

```javascript
// React component to show Langfuse metrics
<div className="grid grid-cols-4 gap-4">
    <MetricCard 
        title="Avg Query Time"
        value="342ms"
        trend="+12%"
    />
    <MetricCard 
        title="Retrieval Score"
        value="0.72"
        trend="-5%"
    />
    <MetricCard 
        title="Cache Hit Rate"
        value="34%"
        trend="+8%"
    />
    <MetricCard 
        title="Error Rate"
        value="2.1%"
        trend="-0.5%"
    />
</div>

// Trace timeline visualization
<TraceTimeline 
    trace={selectedTrace}
    spans={[
        { name: 'api.chat', duration: 500, status: 'success' },
        { name: 'rag.retrieve', duration: 150, status: 'success' },
        { name: 'rag.generate', duration: 320, status: 'success' },
    ]}
/>

// Recent traces table
<TracesTable 
    traces={recentTraces}
    onSelectTrace={setSelectedTrace}
/>
```

**Step 3.2: Backend Metrics Endpoint** (`api_server.py`)

```python
from datetime import datetime, timedelta
import json

@app.get("/api/admin/langfuse/metrics")
async def get_metrics(days: int = 7):
    """Fetch metrics from Langfuse for dashboard."""
    client = get_langfuse_client()
    if not client:
        return {"error": "Langfuse not configured"}
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    # Query Langfuse API for traces
    traces = client.get_traces(
        name="api.chat",
        start_time=start_time,
        end_time=end_time,
    )
    
    # Calculate metrics
    total = len(traces)
    avg_latency = sum(t.latency for t in traces) / total if total > 0 else 0
    error_count = sum(1 for t in traces if t.error)
    error_rate = error_count / total if total > 0 else 0
    
    # Get retrieval scores
    retrieval_traces = [t for t in traces if "retrieve" in t.name]
    avg_retrieval_score = sum(
        float(t.metadata.get("top_score", 0)) 
        for t in retrieval_traces
    ) / len(retrieval_traces) if retrieval_traces else 0
    
    # Get cache hit rate
    memory_hits = sum(
        1 for t in traces 
        if t.metadata.get("from_memory") == True
    )
    cache_hit_rate = memory_hits / total if total > 0 else 0
    
    return {
        "period_days": days,
        "total_queries": total,
        "avg_latency_ms": round(avg_latency, 2),
        "error_rate": round(error_rate * 100, 2),
        "avg_retrieval_score": round(avg_retrieval_score, 3),
        "cache_hit_rate": round(cache_hit_rate * 100, 2),
        "top_errors": get_top_errors(traces, limit=5),
        "top_slow_queries": get_top_slow_queries(traces, limit=5),
    }

@app.get("/api/admin/langfuse/traces")
async def get_recent_traces(limit: int = 50):
    """Fetch recent traces for admin viewing."""
    client = get_langfuse_client()
    if not client:
        return []
    
    traces = client.get_traces(limit=limit)
    return [
        {
            "trace_id": t.id,
            "name": t.name,
            "timestamp": t.timestamp,
            "latency_ms": t.latency,
            "status": "error" if t.error else "success",
            "error": t.error,
            "user_id": t.metadata.get("user_hash"),
        }
        for t in traces
    ]

@app.get("/api/admin/langfuse/trace/{trace_id}")
async def get_trace_detail(trace_id: str):
    """Fetch detailed trace information."""
    client = get_langfuse_client()
    if not client:
        return {"error": "Langfuse not configured"}
    
    trace = client.get_trace(trace_id)
    if not trace:
        return {"error": "Trace not found"}
    
    return {
        "trace_id": trace.id,
        "name": trace.name,
        "timestamp": trace.timestamp,
        "latency_ms": trace.latency,
        "status": "error" if trace.error else "success",
        "error": trace.error,
        "spans": [
            {
                "name": span.name,
                "start": span.start_time,
                "duration_ms": span.duration,
                "input": span.input,
                "output": span.output,
            }
            for span in trace.spans
        ],
        "metadata": trace.metadata,
        "feedback": trace.feedback if hasattr(trace, 'feedback') else None,
    }
```

---

## Performance Implications

### Overhead per Request
| Layer | Overhead | Notes |
|-------|----------|-------|
| React | <5ms | Local trace_id generation, no network |
| Spring Boot | 5-10ms | Header passthrough, minimal logging |
| Python | 10-20ms | Langfuse SDK, async to cloud |
| **Total** | **20-35ms** | ~7% of typical 500ms response |

### Optimization Tips
1. **Batch traces**: Send in batches of 10-100 to reduce network calls
2. **Async sending**: Use background thread pool for Langfuse API calls
3. **Sampling**: Sample 10-20% in production, 100% in development
4. **Disable in tests**: Set `LANGFUSE_ENABLED=false` in test config

### Recommended Settings
```env
# Production
LANGFUSE_ENABLED=true
LANGFUSE_SAMPLING_RATE=0.1  # 10% sampling

# Development  
LANGFUSE_ENABLED=true
LANGFUSE_SAMPLING_RATE=1.0  # 100% sampling

# Testing
LANGFUSE_ENABLED=false
```

---

## Configuration

### Environment Variables
```env
# .env
LANGFUSE_ENABLED=true
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_SAMPLING_RATE=0.1
```

### Files to Create/Modify

```
rag/observability/
  ├── __init__.py
  ├── langfuse_client.py      (EXISTING - no change)
  ├── trace_context.py         (NEW)
  └── middleware.py            (NEW)

springboot-backend/src/main/java/com/astrobot/
  ├── middleware/
  │   └── LangfuseInterceptor.java  (NEW)
  ├── config/
  │   └── WebConfig.java            (EXISTING - add interceptor)
  └── controller/
      └── ChatController.java       (MODIFY - add tracing)

react-frontend/src/
  ├── hooks/
  │   └── useLangfuse.js       (NEW)
  ├── pages/admin/
  │   └── LangfuseAdminPage.jsx (NEW)
  └── services/
      └── api.js               (MODIFY - add trace_id)

docs/
  └── development/
      ├── LANGFUSE_INTEGRATION_GUIDE.md (EXISTING)
      └── LANGFUSE_ARCHITECTURE.md      (THIS FILE)
```

---

## Security & Privacy

### User Data Protection
- ✅ User IDs hashed with SHA256 before sending to Langfuse
- ✅ Queries truncated to 500 chars max
- ✅ Responses redacted by default (set to log if needed)
- ✅ Trace IDs are UUIDs (cannot identify users)

### Network Security
- ✅ HTTPS to Langfuse cloud only
- ✅ API keys stored in environment variables
- ✅ Never log secrets in traces

### Privacy Checklist
- [ ] Read Langfuse privacy policy
- [ ] Ensure data residency matches requirements (EU/US)
- [ ] Add Langfuse to your data processing agreement
- [ ] Document in privacy policy that you use third-party analytics

---

## Rollout Plan

### Week 1: Core Setup
- [ ] Implement trace ID propagation (Phase 1)
- [ ] Deploy to staging
- [ ] Test trace correlation across layers

### Week 2: Instrumentation
- [ ] Add Spring Boot interceptor (Phase 2.1)
- [ ] Add Python service mapping (Phase 2.2)
- [ ] Add React instrumentation (Phase 2.3)

### Week 3: Admin Dashboard
- [ ] Build Langfuse admin page (Phase 3)
- [ ] Add metrics endpoint
- [ ] Test dashboard with real traces

### Week 4: Production Rollout
- [ ] Enable with 10% sampling
- [ ] Monitor for performance issues
- [ ] Gradually increase sampling to 50%
- [ ] Monitor costs, adjust as needed

---

## Debugging Guide

### Trace not appearing in Langfuse?
```python
# Check if Langfuse is initialized
from rag.observability.langfuse_client import get_langfuse_client
client = get_langfuse_client()
print(f"Langfuse initialized: {client is not None}")

# Check environment variables
import os
print(f"LANGFUSE_ENABLED: {os.getenv('LANGFUSE_ENABLED')}")
print(f"Public key set: {bool(os.getenv('LANGFUSE_PUBLIC_KEY'))}")
```

### Trace ID not propagating?
```javascript
// Check React
console.log('Trace ID:', sessionStorage.getItem('langfuse_trace_id'));

// Check request headers
fetch('/api/chat', {
    // ...
    headers: {
        'X-Langfuse-Trace-Id': traceId,
    }
});
```

### Spring Boot not forwarding?
```java
// Check interceptor is registered
// Add debug logging to LangfuseInterceptor
System.out.println("Trace ID: " + request.getHeader("X-Langfuse-Trace-Id"));
```

---

## Next Steps

1. **Review this document** with your team
2. **Decide on privacy requirements** (sampling rate, data retention)
3. **Get Langfuse account** (sign up at langfuse.com)
4. **Start Phase 1** (trace ID plumbing)
5. **Run end-to-end test** before Phase 2

---

**Questions?** Check the original `LANGFUSE_INTEGRATION_GUIDE.md` for Phase 1 & 2 details.
