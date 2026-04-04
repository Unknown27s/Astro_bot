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
6. [Rate Limits](#rate-limits)
7. [Error Responses](#error-responses)
8. [Examples](#examples)

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
  "response_time_ms": 1320.5
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
