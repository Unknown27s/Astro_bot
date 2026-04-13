# Document Upload API Reference

**Last Updated:** April 2026
**Status:** ✅ Admin-only with locked PDF detection
**Interfaces:** FastAPI, Streamlit, React Frontend

---

## 📌 Quick Summary

| Feature | Status | Details |
|---------|--------|---------|
| **Admin-Only** | ✅ Enforced | Only users with `role='admin'` can upload |
| **Locked PDF Detection** | ✅ Enabled | Rejects password-protected PDFs with clear error |
| **File Size Limit** | ✅ 50MB | HTTP 413 if exceeded |
| **Supported Formats** | ✅ 7 types | PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML |
| **Error Messages** | ✅ Detailed | User-friendly + technical details in logs |

---

## 🔐 Admin-Only Upload

### Requirement

Only users with **admin role** can upload documents. This is enforced at the API level.

**Files Checking Admin Role:**
- `api_server.py` (lines 329-354): FastAPI endpoint validation
- `views/admin.py`: Streamlit UI (sidebar only for logged-in admins)
- `react-frontend/src/pages/admin/DocumentsPage.jsx` (lines 20-60): React upload handler

### Validation Flow

```python
# 1. Check user exists
user = db.query("SELECT id, role FROM users WHERE id = ?", (uploaded_by,))

# 2. Check user is admin
if user["role"] != "admin":
    raise HTTPException(403, "Only administrators can upload documents")

# 3. Proceed with upload
```

**Error Codes:**
- `400`: `uploaded_by` missing or invalid
- `404`: User ID not found
- `403`: User exists but is not admin

---

## 🔒 Locked PDF Detection

### What It Does

Detects password-protected PDFs **before** attempting to parse them, preventing parse errors and confusing error messages.

**Detection Method:**
```python
from PyPDF2 import PdfReader

pdf_reader = PdfReader(file_path)
if pdf_reader.is_encrypted:
    # Reject the PDF
    raise HTTPException(422, "PDF is password-protected...")
```

### Files Implementing Detection

1. **`api_server.py` (lines 368-382)**
   - FastAPI endpoint
   - Checks after file save, before parsing
   - Returns HTTP 422 with message

2. **`views/admin.py` (lines 90-116)**
   - Streamlit UI
   - Detects before parse, shows error in UI
   - Cleans up file on rejection

3. **`react-frontend/src/pages/admin/DocumentsPage.jsx` (lines 43-50)**
   - React frontend
   - Handles HTTP 422 error response
   - Displays: `❌ PDF is password-protected or invalid format`

### Error Message

**To User:**
```
❌ {filename}: PDF is password-protected. Please remove the password and try again.
```

**In Logs:**
```
WARNING: Locked PDF rejected: document.pdf
```

---

## 📤 API Endpoint: POST /api/documents/upload

### Authorization

- **Required Role:** Admin
- **Required Field:** `uploaded_by` (user ID)

### Request Format

**Content-Type:** `multipart/form-data`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | File | ✅ Yes | Document file (PDF, DOCX, TXT, XLSX, CSV, PPTX, HTML) |
| `uploaded_by` | String | ✅ Yes | Admin user ID from database |

### Success Response

**Status:** 200 OK

```json
{
  "doc_id": "doc-1712150440",
  "filename": "course_handbook.pdf",
  "chunks_indexed": 45,
  "file_size": 1024000,
  "suggested_questions": [
    "Can you summarize key points from course handbook?",
    "What does the section 'Attendance Policy' explain?"
  ]
}
```

`suggested_questions` are generated from the uploaded document's headings and content and are used by `/api/suggestions` autocomplete.

### Error Responses

#### Missing or Invalid User

**Status:** 400 Bad Request
```json
{
  "detail": "uploaded_by (user ID) is required"
}
```

#### User Not Found

**Status:** 404 Not Found
```json
{
  "detail": "User ID admin-123 not found"
}
```

#### User is Not Admin

**Status:** 403 Forbidden
```json
{
  "detail": "Only administrators can upload documents"
}
```

#### Unsupported File Type

**Status:** 400 Bad Request
```json
{
  "detail": "Unsupported file type: .doc. Supported: .csv, .docx, .html, .pdf, .pptx, .txt, .xlsx"
}
```

#### File Too Large

**Status:** 413 Payload Too Large
```json
{
  "detail": "File too large (52.5MB). Maximum: 50MB"
}
```

#### Password-Protected PDF

**Status:** 422 Unprocessable Entity
```json
{
  "detail": "❌ PDF is password-protected. Please remove the password and try again."
}
```

#### PDF Parsing Failed

**Status:** 422 Unprocessable Entity
```json
{
  "detail": "Failed to extract text from document (file may be corrupted or scanned image)"
}
```

#### No Chunks Generated

**Status:** 422 Unprocessable Entity
```json
{
  "detail": "No chunks generated from document (text may be too short)"
}
```

#### Database Error

**Status:** 500 Internal Server Error
```json
{
  "detail": "Failed to record document in database: [error details]"
}
```

#### ChromaDB Error

**Status:** 500 Internal Server Error
```json
{
  "detail": "Failed to index document in vector database: [error details]"
}
```

---

## 🧪 Testing

### Using cURL

```bash
# Get admin user ID first
curl http://localhost:8000/api/admin/users | jq '.users[0].id'
# Example output: "user-admin-001"

# Upload document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf" \
  -F "uploaded_by=user-admin-001"
```

### Using Python

```python
import requests

with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/documents/upload",
        files={"file": f},
        data={"uploaded_by": "user-admin-001"}
    )
    print(response.json())
```

### Using React Frontend

```javascript
// components call uploadDocument(file, user?.id)
// See: react-frontend/src/services/api.js

const response = await uploadDocument(pdfFile, adminUserId);
// Handles all errors automatically
// Shows toast notifications to user
```

---

## 🔍 Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| **403 Forbidden** | Logged-in user is not admin | Use admin account to upload |
| **404 Not Found** | User ID doesn't exist in DB | Verify admin user ID in database |
| **422 Password-Protected** | PDF has encryption | Remove password using Adobe Reader, then reupload |
| **422 Parse Failed** | Scanned image, corrupted, or unsupported format | Check file integrity, try converting to text |
| **413 Too Large** | File exceeds 50MB limit | Compress or split the document |

---

## 📁 Implementation Details

### Upload Pipeline

```
1. Receive request (file + uploaded_by)
   ↓
2. Validate admin role ← NEW: Admin-only check
   ↓
3. Save file to disk
   ↓
4. Check if PDF is locked ← NEW: Locked PDF detection
   ↓
5. Parse document (extract text)
   ↓
6. Chunk text into smaller pieces
   ↓
7. Generate embeddings
   ↓
8. Store in ChromaDB
   ↓
9. Record in SQLite database
   ↓
10. Return success + doc_id
```

### Key Files

| File | Purpose | Key Functions |
|------|---------|----------------|
| `api_server.py:329-410` | FastAPI endpoint | `api_upload_document()` |
| `views/admin.py:42-150` | Streamlit upload UI | `_render_document_management()` |
| `ingestion/parser.py` | PDF/Document parsing | `parse_document()` |
| `ingestion/chunker.py` | Text chunking | `chunk_document()` |
| `ingestion/embedder.py` | Vector storage | `store_chunks()` |
| `database/db.py` | Document recording | `add_document()` |

---

## 🎯 Security Considerations

| Check | Status | Details |
|-------|--------|---------|
| **Role-based access** | ✅ Enforced | Only admins can upload |
| **File size limits** | ✅ Enforced | Max 50MB prevents memory exhaustion |
| **File type validation** | ✅ Enforced | Only MIME types in SUPPORTED_EXTENSIONS |
| **Rate limiting** | ✅ Enabled | 10 uploads per minute per IP |
| **File cleanup** | ✅ Implemented | Orphaned files removed on error |
| **Error messages** | ✅ Safe | No directory paths or system details leaked |

---

## 📅 Recent Changes (April 2026)

### Added
- ✅ Admin-only role check (HTTP 403 if not admin)
- ✅ Locked PDF detection using PyPDF2
- ✅ Enhanced error messages in React frontend
- ✅ Locked PDF detection in Streamlit UI

### Modified
- `api_server.py`: Added admin role validation + PDF encryption check
- `views/admin.py`: Added locked PDF detection
- `react-frontend/src/pages/admin/DocumentsPage.jsx`: Improved error handling

### Fixed
- Passwords-protected PDFs now rejected with clear message
- Non-admin users now get proper 403 response instead of silent failure

---

**Questions?** See `/docs/guides/TROUBLESHOOTING.md` or check logs in `data/logs/`
