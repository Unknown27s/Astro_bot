# AstroBot v2.2 API Endpoints Reference

**Last Updated:** April 2026
**Total Endpoints:** 16
**Rate Limiting:** Enabled on all endpoints

---

## Table of Contents

1. [Tag Management](#tag-management)
2. [Document Tagging](#document-tagging)
3. [Classification](#classification)
4. [Search & Filtering](#search--filtering)
5. [Announcements](#announcements)
6. [Voice Chat](#voice-chat)
7. [Suggestions](#suggestions)
8. [Feedback](#feedback)
9. [Memory](#memory)
10. [Monitor](#monitor)
11. [Rate Limits](#rate-limits)
12. [Error Responses](#error-responses)
13. [Examples](#examples)

---

## Tag Management

### Create Tag

**Endpoint:** `POST /api/documents/tags`

**Rate Limit:** 30 requests/minute

**Request:**
```json
{
  "name": "Important",
  "description": "High priority documents",
  "color": "#FF0000"
}
```

**Response:** 201 Created
```json
{
  "id": "tag-123",
  "name": "Important",
  "description": "High priority documents",
  "color": "#FF0000",
  "created_by": "user-456",
  "created_at": "2026-03-14T10:30:00Z"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/documents/tags \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Important",
    "description": "High priority documents",
    "color": "#FF0000"
  }'
```

---

### List Tags

**Endpoint:** `GET /api/documents/tags`

**Rate Limit:** 60 requests/minute

**Response:** 200 OK
```json
{
  "tags": [
    {
      "id": "tag-123",
      "name": "Important",
      "description": "High priority documents",
      "color": "#FF0000",
      "usage_count": 5,
      "created_by": "user-456",
      "created_at": "2026-03-14T10:30:00Z"
    },
    {
      "id": "tag-789",
      "name": "Review",
      "description": "Needs review",
      "color": "#0000FF",
      "usage_count": 3,
      "created_by": "user-456",
      "created_at": "2026-03-14T11:00:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/documents/tags | jq
```

---

### Update Tag

**Endpoint:** `PUT /api/documents/tags/{tag_id}`

**Rate Limit:** 30 requests/minute

**URL Parameters:**
- `tag_id` (string, required): ID of tag to update

**Request:**
```json
{
  "name": "Critical",
  "description": "Critical priority documents",
  "color": "#FF0000"
}
```

**Response:** 200 OK
```json
{
  "id": "tag-123",
  "name": "Critical",
  "description": "Critical priority documents",
  "color": "#FF0000",
  "created_by": "user-456",
  "created_at": "2026-03-14T10:30:00Z"
}
```

**cURL Example:**
```bash
curl -X PUT http://localhost:8000/api/documents/tags/tag-123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Critical",
    "description": "Critical priority documents"
  }'
```

---

### Delete Tag

**Endpoint:** `DELETE /api/documents/tags/{tag_id}`

**Rate Limit:** 30 requests/minute

**URL Parameters:**
- `tag_id` (string, required): ID of tag to delete

**Response:** 204 No Content

**Note:** Deleting a tag automatically removes it from all documents (cascading delete)

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/documents/tags/tag-123
```

---

## Document Tagging

### Add Tag to Document

**Endpoint:** `POST /api/documents/{doc_id}/tags/{tag_id}`

**Rate Limit:** 30 requests/minute

**URL Parameters:**
- `doc_id` (string, required): Document ID
- `tag_id` (string, required): Tag ID to add

**Response:** 201 Created
```json
{
  "id": "doc-tag-999",
  "document_id": "doc-456",
  "tag_id": "tag-123",
  "tag_name": "Important",
  "added_by": "user-789",
  "added_at": "2026-03-14T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/documents/doc-456/tags/tag-123
```

---

### Get Document Tags

**Endpoint:** `GET /api/documents/{doc_id}/tags`

**Rate Limit:** 60 requests/minute

**URL Parameters:**
- `doc_id` (string, required): Document ID

**Response:** 200 OK
```json
{
  "document_id": "doc-456",
  "tags": [
    {
      "id": "tag-123",
      "name": "Important",
      "color": "#FF0000",
      "description": "High priority documents",
      "added_at": "2026-03-14T12:00:00Z"
    },
    {
      "id": "tag-789",
      "name": "Review",
      "color": "#0000FF",
      "description": "Needs review",
      "added_at": "2026-03-14T12:05:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/documents/doc-456/tags | jq
```

---

### Remove Tag from Document

**Endpoint:** `DELETE /api/documents/{doc_id}/tags/{tag_id}`

**Rate Limit:** 30 requests/minute

**URL Parameters:**
- `doc_id` (string, required): Document ID
- `tag_id` (string, required): Tag ID to remove

**Response:** 204 No Content

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/documents/doc-456/tags/tag-123
```

---

## Classification

### Set Document Classification

**Endpoint:** `POST /api/documents/{doc_id}/classify`

**Rate Limit:** 30 requests/minute

**URL Parameters:**
- `doc_id` (string, required): Document ID

**Request:**
```json
{
  "classification": "Policy",
  "confidence": 0.95,
  "notes": "Annual policy document for 2026"
}
```

**Response:** 201 Created / 200 OK
```json
{
  "id": "class-999",
  "document_id": "doc-456",
  "classification": "Policy",
  "confidence": 0.95,
  "auto_classified": false,
  "classified_by": "user-789",
  "classified_at": "2026-03-14T13:00:00Z",
  "notes": "Annual policy document for 2026"
}
```

**Available Classifications:**
- Policy
- Procedure
- Guidelines
- Announcement
- Other

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/documents/doc-456/classify \
  -H "Content-Type: application/json" \
  -d '{
    "classification": "Policy",
    "confidence": 0.95,
    "notes": "Annual policy document for 2026"
  }'
```

---

### Get Document Classification

**Endpoint:** `GET /api/documents/{doc_id}/classify`

**Rate Limit:** 60 requests/minute

**URL Parameters:**
- `doc_id` (string, required): Document ID

**Response:** 200 OK
```json
{
  "id": "class-999",
  "document_id": "doc-456",
  "classification": "Policy",
  "confidence": 0.95,
  "auto_classified": false,
  "classified_by": "user-789",
  "classified_at": "2026-03-14T13:00:00Z",
  "notes": "Annual policy document for 2026"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/documents/doc-456/classify | jq
```

---

## Search & Filtering

### Search by Tags and Classification

**Endpoint:** `GET /api/documents/search`

**Rate Limit:** 60 requests/minute

**Query Parameters:**
- `tags` (string, optional): Comma-separated tag names (e.g., `Important,Review`)
- `classification` (string, optional): Classification type (e.g., `Policy`)
- `limit` (integer, optional, default=50): Maximum results to return
- `offset` (integer, optional, default=0): Pagination offset

**Response:** 200 OK
```json
{
  "documents": [
    {
      "id": "doc-456",
      "filename": "policy_2026.pdf",
      "original_name": "2026-Q1-Policy.pdf",
      "uploaded_at": "2026-03-14T10:30:00Z",
      "tags": [
        {
          "id": "tag-123",
          "name": "Important",
          "color": "#FF0000"
        }
      ],
      "classification": {
        "type": "Policy",
        "confidence": 0.95,
        "classified_at": "2026-03-14T13:00:00Z"
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**cURL Example:**
```bash
# Filter by tags
curl "http://localhost:8000/api/documents/search?tags=Important,Review" | jq

# Filter by classification
curl "http://localhost:8000/api/documents/search?classification=Policy" | jq

# Filter by both tags and classification
curl "http://localhost:8000/api/documents/search?tags=Important&classification=Policy" | jq

# Pagination
curl "http://localhost:8000/api/documents/search?limit=10&offset=20" | jq
```

---

### List All Documents (Enhanced)

**Endpoint:** `GET /api/documents`

**Rate Limit:** 60 requests/minute

**Response:** 200 OK (now includes tags and classification)
```json
{
  "documents": [
    {
      "id": "doc-456",
      "filename": "policy_2026.pdf",
      "original_name": "2026-Q1-Policy.pdf",
      "uploaded_at": "2026-03-14T10:30:00Z",
      "tags": [
        {
          "id": "tag-123",
          "name": "Important",
          "color": "#FF0000",
          "description": "High priority documents"
        },
        {
          "id": "tag-789",
          "name": "Review",
          "color": "#0000FF",
          "description": "Needs review"
        }
      ],
      "classification": {
        "type": "Policy",
        "confidence": 0.95,
        "auto_classified": false,
        "classified_at": "2026-03-14T13:00:00Z"
      }
    }
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/documents | jq
```

---

## Chat Routing

### Send Chat Query

**Endpoint:** `POST /api/chat`

**Access:** All authenticated users

**Routing behavior:** The backend now classifies the query before retrieval. Public campus questions prefer official-site chunks, document/policy/technical questions prefer uploaded-document RAG, and mixed/unclear questions fall back to hybrid retrieval.

**Response:** `200 OK`
```json
{
  "response": "...",
  "sources": [
    {
      "source": "Campus Website",
      "heading": "Admissions",
      "score": 0.91
    }
  ],
  "citations": "📄 **Campus Website** — Admissions (91% match)",
  "response_time_ms": 842.4,
  "route_mode": "official_site"
}
```

**Route values:**
- `official_site` for public campus information
- `document` for uploaded policies/documents
- `hybrid` for mixed queries
- `unclear` when the router cannot confidently choose one source

**Note:** `@Announcement` still bypasses normal routing and formats the message for the announcements feed.

---

## Announcements

> **Role Access:** `GET` is public (all authenticated users). Posting is via the `/api/chat` endpoint with the `@Announcement` prefix — Admin and Faculty roles only.

### Get Announcements Feed

**Endpoint:** `GET /api/announcements`

**Access:** All authenticated users (Students, Faculty, Admin)

**Query Parameters:**
- `limit` (integer, optional, default=50): Max number of announcements to return (newest first)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid-1234",
    "user_id": "user-uuid",
    "author_name": "Dr. Smith",
    "content": "📢 **Important Notice**\n\nThe campus library will be closed this Friday...",
    "created_at": "2026-04-04T14:30:00"
  }
]
```

**cURL Example:**
```bash
curl http://localhost:8000/api/announcements | jq
```

### Post an Announcement (via Chat)

**Endpoint:** `POST /api/chat`

**Access:** Admin and Faculty only (returns HTTP 403 for students)

**How it works:** Send a regular chat request with the query starting with `@Announcement`. The AI will automatically format the message and save it to the announcements feed.

**Request:**
```json
{
  "query": "@Announcement Tomorrow is a public holiday. All classes are cancelled.",
  "user_id": "admin-uuid",
  "username": "dr.smith"
}
```

**Response:** `200 OK`
```json
{
  "response": "✅ Announcement generated and posted successfully!\n\n---\n\n📢 **Important Notice**\n\nWe wish to inform all students that...",
  "sources": [],
  "citations": "",
  "response_time_ms": 1320.5,
  "route_mode": "announcement"
}
```

**Error — Student attempts to post:**
```json
{
  "detail": "Only faculty and admins can post announcements"
}
```
*HTTP 403 Forbidden*

---

### Delete Announcement

**Endpoint:** `DELETE /api/announcements/{id}`

**Rate Limit:** 30 requests/minute (using general write endpoint limits)

**Headers:**
- `X-User-ID` (string, required): The ID of the requesting user.
- `X-User-Role` (string, required): The role of the requesting user (`admin`, `faculty`, `student`).

**Response:** 200 OK
```json
{
  "message": "Announcement deleted",
  "id": "ann-12345"
}
```

**Response (Unauthorized or Not Found):** 404 Not Found
*Note: The API deliberately obscures whether an announcement doesn't exist vs the user not having permission to prevent ID harvesting.*
```json
{
  "detail": "Announcement not found or you don't have permission to delete it"
}
```

### Frontend Role Hint Behavior

- Typing suggestion for `@Announcement` is shown only to `admin` and `faculty` users in the React chat UI.
- Students do not see the `@Announcement` command hint and receive HTTP 403 if they try to post one manually.

---

## Voice Chat

### Send Voice Query

**Endpoint:** `POST /api/chat/audio`

**Access:** All authenticated users

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `audio` (file, required): Browser-recorded audio blob (`webm` recommended)
- `user_id` (string, required)
- `username` (string, required)

**Response:** `200 OK`
```json
{
  "response": "Attendance policy requires 75% minimum attendance...",
  "sources": [],
  "citations": "",
  "response_time_ms": 1042.1,
  "transcribed_text": "What is the attendance policy",
  "route_mode": "document"
}
```

---

## Suggestions

### Get Typing Suggestions

**Endpoint:** `GET /api/suggestions`

**Access:** All authenticated users

**Query Parameters:**
- `q` (string, optional): Current typed input
- `user_id` (string, optional): Used for personalized recent history suggestions

**Response:** `200 OK`
```json
{
  "recent": [
    "What are the exam rules?"
  ],
  "popular": [
    "What is the fee structure?"
  ],
  "document_based": [
    "What does the section 'Attendance Policy' explain?"
  ],
  "preset": [
    "What are the admission requirements?"
  ]
}
```

**Notes:**
- `document_based` suggestions are generated from uploaded document text/headings and refreshed as new documents are indexed.

---

## Official Site Ingestion

### Fetch and Index a Public Page

**Endpoint:** `POST /api/documents/ingest-url`

**Access:** Admin

**Request:**
```json
{
  "url": "https://www.example.edu/about",
  "title": "About the College",
  "uploaded_by": "user-456"
}
```

**Notes:**
- This endpoint fetches one public HTML page, cleans boilerplate, chunks the text, and indexes it locally.
- The stored chunks are tagged with `source_type=official_site`.
- The endpoint is proxied through Spring Boot to FastAPI.

**Response:** `200 OK`
```json
{
  "doc_id": "c6f8f946-b74f-4f8a-8d1a-7b4eaf43a03b",
  "url": "https://www.example.edu/about",
  "domain": "example.edu",
  "title": "About the College",
  "chunks_indexed": 18,
  "file_size": 14820,
  "source_type": "official_site",
  "suggested_questions": [
    "Can you summarize key points from About the College?",
    "What does the section 'Admissions' explain?"
  ]
}
```

---

## Feedback

### Submit Chat Feedback

**Endpoint:** `POST /api/feedback`

**Access:** All authenticated users

**Request:**
```json
{
  "trace_id": "6a1fd2f0-8d86-4a26-b6f8-97b0ef8d34e8",
  "rating": 1,
  "user_id": "user-123",
  "comment": "Helpful answer"
}
```

**Notes:**
- `rating` must be `1` (helpful) or `-1` (not helpful)
- Feedback is persisted in SQLite for admin analytics
- If Langfuse is enabled, the same feedback is also exported as `user_feedback`

**Response:** `200 OK`
```json
{
  "accepted": true,
  "trace_id": "6a1fd2f0-8d86-4a26-b6f8-97b0ef8d34e8",
  "feedback_id": "f5892c2b-2b57-4f97-96b2-fc2d2c8f01cb",
  "langfuse_recorded": true
}
```

### Analytics Feedback Fields

`GET /api/analytics` includes these feedback fields:

- `total_feedback`
- `helpful_feedback`
- `not_helpful_feedback`
- `helpful_feedback_rate`
- `daily_feedback` (array with `day`, `helpful`, `not_helpful`, `total`)

---

## Memory

### Get Memory Stats

**Endpoint:** `GET /api/memory/stats`

**Access:** Admin

**Response:** `200 OK`
```json
{
  "enabled": true,
  "stats": {
    "total_entries": 42,
    "avg_usage": 1.8,
    "by_user": [
      {
        "username": "admin",
        "entries": 12,
        "avg_usage": 2.1
      }
    ]
  }
}
```

### Delete One Memory Entry

**Endpoint:** `DELETE /api/memory/{memory_id}`

**Access:** Admin

**Behavior:** Deletes the memory entry from both storage layers (ChromaDB semantic cache + SQLite metadata) to avoid stale cache hits after deletion.

**Response:** `200 OK`
```json
{
  "deleted": true,
  "id": "9ffaf3f8-dfdf-4f69-a4f3-7f56da36c9af"
}
```

### Cleanup Expired Memory

**Endpoint:** `POST /api/memory/cleanup`

**Access:** Admin

**Behavior:** Removes expired/old cache entries from both cache and metadata layers.

### Clear All Memory

**Endpoint:** `POST /api/memory/clear`

**Access:** Admin

**Behavior:** Clears full conversation memory from ChromaDB and SQLite, then recreates the memory collection.

---

## Monitor

### Trace Timeline

**Endpoint:** `GET /api/monitor/traces`

**Access:** Admin (frontend admin panel usage)

**Query Parameters:**
- `limit` (int, optional, default `120`, max `500`)
- `status` (optional: `ok`, `http_error`, `error`)
- `endpoint` (optional, exact endpoint path)
- `provider` (optional, exact provider name)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "4dcf4e74-99f8-4f0e-a8d8-2e1f308df3fe",
      "trace_id": "5cf95f16-c63b-4f61-9d2a-933956c95d73",
      "endpoint": "/api/chat",
      "status": "ok",
      "query_preview": "What is the attendance policy?",
      "response_time_ms": 842.4,
      "retrieval_top_score": 0.81,
      "retrieval_mode": "hybrid",
      "hyde_applied": true,
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "fallback_chain": [
        {"name": "groq", "success": true}
      ],
      "created_at": "2026-04-12T12:43:12.129244"
    }
  ],
  "count": 1
}
```

### Monitor Overview

**Endpoint:** `GET /api/monitor/overview`

**Access:** Admin (frontend admin panel usage)

**Query Parameters:**
- `minutes` (int, optional, default `60`, min `5`, max `1440`)
- `include_providers` (bool, optional, default `false`)

**Purpose:**
- Consolidates trace failure trends, health components, and optional provider statuses.
- Returns alert objects to quickly detect which subsystem is degraded or failing.

**Response:** `200 OK`
```json
{
  "status": "degraded",
  "window_minutes": 60,
  "trace_summary": {
    "total_requests": 120,
    "failed_requests": 5,
    "failure_rate": 4.17,
    "avg_latency_ms": 932.6,
    "by_endpoint": [
      {
        "endpoint": "/api/chat",
        "total": 110,
        "failed": 3,
        "avg_latency": 901.1
      }
    ]
  },
  "alerts": [
    {
      "type": "component",
      "name": "embeddings",
      "status": "warning",
      "message": "all-MiniLM-L6-v2 (lazy load)"
    }
  ]
}
```

---

## Rate Limits

### Rate Limiting Configuration

| Endpoint Category | Limit | Purpose |
|-------------------|-------|---------|
| Read Operations | 60/minute | List tags, list documents, retrieve single items |
| Write Operations | 30/minute | Create/update/delete tags, tagging operations |
| Auth Endpoints | 5/minute | Login/register (brute-force protection) |
| Chat/Query | 5/minute | LLM queries (expensive operations) |
| Upload | 10/minute | Document uploads (resource intensive) |
| Global | 100/minute | All requests combined per minute |

### Checking Rate Limit Status

All responses include rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1710417600
```

**cURL Example to View Headers:**
```bash
curl -i http://localhost:8000/api/documents/tags
```

---

## Error Responses

### 429 Too Many Requests (Rate Limited)

**Response:**
```json
{
  "detail": "Rate limit exceeded: 30 requests per 1 minute"
}
```

**Headers:**
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710417672
Retry-After: 45
```

### 404 Not Found

**Response:**
```json
{
  "detail": "Document not found"
}
```

### 400 Bad Request

**Response:**
```json
{
  "detail": "Invalid tag name: name must be unique"
}
```

### 500 Internal Server Error

**Response:**
```json
{
  "detail": "Internal server error",
  "error_id": "req-123456789"
}
```

Check logs: `tail -f logs/astrobot.log | jq '.error_id'`

---

## Examples

### Complete Workflow Example

```bash
# 1. Create tags
curl -X POST http://localhost:8000/api/documents/tags \
  -H "Content-Type: application/json" \
  -d '{"name": "Important", "color": "#FF0000"}'

curl -X POST http://localhost:8000/api/documents/tags \
  -H "Content-Type: application/json" \
  -d '{"name": "Q1-Review", "color": "#0000FF"}'

# 2. Upload a document (existing endpoint)
# This returns: {"id": "doc-456", ...}

# 3. Add tags to the uploaded document
curl -X POST "http://localhost:8000/api/documents/doc-456/tags/tag-123"
curl -X POST "http://localhost:8000/api/documents/doc-456/tags/tag-789"

# 4. Set classification
curl -X POST http://localhost:8000/api/documents/doc-456/classify \
  -H "Content-Type: application/json" \
  -d '{"classification": "Policy", "confidence": 0.95}'

# 5. Search for tagged documents
curl "http://localhost:8000/api/documents/search?tags=Important"

# 6. Get all tags with usage counts
curl http://localhost:8000/api/documents/tags | jq '.tags[] | {name, usage_count}'
```

### Pagination Example

```bash
# Get first 10 results
curl "http://localhost:8000/api/documents?limit=10&offset=0"

# Get next 10 results
curl "http://localhost:8000/api/documents?limit=10&offset=10"

# Get results sorted by specific fields (if implemented)
curl "http://localhost:8000/api/documents?sort=uploaded_at&order=desc"
```

### Error Handling Example

```bash
# Try to create duplicate tag (will fail)
curl -X POST http://localhost:8000/api/documents/tags \
  -H "Content-Type: application/json" \
  -d '{"name": "Important"}'
# Response: 400 Bad Request - "Tag name already exists"

# Check remaining rate limit
curl -i http://localhost:8000/api/documents/tags 2>/dev/null | grep "X-RateLimit"
# Output:
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 55
# X-RateLimit-Reset: 1710417672

# Wait and retry if rate limited
RETRY_AFTER=$(curl -i http://localhost:8000/api/documents/tags 2>/dev/null | grep "Retry-After" | cut -d' ' -f2)
echo "Retry after $RETRY_AFTER seconds"
```

---

## Integration with Existing Endpoints

### Enhanced Chat Query with Tag Filtering

The chat endpoint now supports filtering documents by tags before querying:

```bash
# Query only "Important" tagged documents
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the policy on vacation?",
    "tags": ["Important"],
    "classification": "Policy"
  }'
```

---

## Testing Commands

```bash
# Run the verification script to ensure all endpoints work
bash verify.sh

# Or test manually with the complete workflow
bash docs/test-api.sh  # (if test script exists)
```

---

## Documentation Links

- **Implementation Details:** [02-IMPLEMENTATION_SUMMARY.md](02-IMPLEMENTATION_SUMMARY.md)
- **Quick Start:** [01-QUICKSTART.md](01-QUICKSTART.md)
- **Load Balancing:** [03-LOAD_BALANCING.md](03-LOAD_BALANCING.md)
- **Troubleshooting:** [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md)

---

**Last Updated:** March 14, 2026
**API Version:** 2.0
