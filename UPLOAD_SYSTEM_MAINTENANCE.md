# 📚 AstroBot Upload System - Complete Maintenance Guide

**For Project Maintainers**

---

## Quick Reference: Files Involved in PDF Upload

### Upload Flow Files (In Order)

| Step | File | Lines | Function | Purpose |
|------|------|-------|----------|---------|
| 1️⃣ **User Upload** | `views/admin.py` | 38-151 | `_render_document_management()` | Streamlit UI for file selection |
| 1️⃣ **REST API** | `api_server.py` | 329-410 | `api_upload_document()` | FastAPI upload endpoint |
| 2️⃣ **Parse** | `ingestion/parser.py` | 138-154 | `parse_document()` | Extract text from PDF |
| 3️⃣ **Chunk** | `ingestion/chunker.py` | 1-150 | `chunk_document()` | Break text into pieces |
| 4️⃣ **Embed** | `ingestion/embedder.py` | 74-109 | `store_chunks()` | Store in ChromaDB |
| 5️⃣ **Database** | `database/db.py` | 312-322 | `add_document()` | Record metadata |

---

## File Details

### 1. Upload Handlers

#### `views/admin.py` (Lines 38-151)
**What it does:** Streamlit UI for uploading documents
**Key changes (recent):**
- ✅ Line 87: Fixed tuple unpacking → `text, parse_error = parse_document(...)`
- ✅ Line 67-70: Added file size validation (50MB max)
- ✅ Line 114-132: Added try-catch for database errors
- ✅ Line 135-143: Added try-catch for ChromaDB errors

**When to modify:** If you want to change the Streamlit upload UI

---

#### `api_server.py` (Lines 329-410)
**What it does:** FastAPI REST API endpoint for uploads
**Key changes (recent):**
- ✅ Line 370: Uses tuple unpacking (always did)
- ✅ Line 362-364: Added file size validation (50MB max)
- ✅ Line 384-396: Added try-catch for database errors
- ✅ Line 399-403: Added try-catch for ChromaDB errors

**When to modify:** If you want to change the REST API behavior

---

### 2. Document Parsing

#### `ingestion/parser.py` (Lines 1-200)
**What it does:** Extracts text from different file formats

| Format | Function | Library | Lines |
|--------|----------|---------|-------|
| PDF | `parse_pdf()` | PyPDF2 | 13-23 |
| DOCX | `parse_docx()` | python-docx | 26-42 |
| TXT | `parse_txt()` | built-in | 45-56 |
| XLSX | `parse_xlsx()` | openpyxl | 59-74 |
| CSV | `parse_csv()` | csv | 77-86 |
| PPTX | `parse_pptx()` | python-pptx | 89-105 |
| HTML | `parse_html()` | BeautifulSoup | 108-122 |

**Main entry point:** `parse_document()` (lines 138-154)
- Returns tuple: `(text, error)`
- Success: `("extracted text...", None)`
- Failure: `(None, "error message")`

**Why 422 errors happen:**
- PDF is encrypted
- PDF has no extractable text (scanned image)
- PDF is corrupted
- File format not supported

---

### 3. Text Chunking

#### `ingestion/chunker.py` (Lines 1-150)
**What it does:** Breaks text into searchable pieces

**Parameters (configurable in `config.py`):**
```python
CHUNK_SIZE = 500      # Characters per chunk
CHUNK_OVERLAP = 50    # Character overlap between chunks
```

**Strategy:**
1. Split by headings (context preservation)
2. Split by fixed size (500 chars)
3. Add overlap (50 chars) to avoid cutting mid-sentence

**Why "No chunks generated" error:**
- Text extracted = 0 characters
- Text too short (< 500 chars)
- Document is empty

---

### 4. Vector Storage

#### `ingestion/embedder.py` (Lines 1-200)
**What it does:**
- Converts text to vectors (embeddings)
- Stores in ChromaDB vector database

**Key functions:**
- `generate_embeddings()` - Convert text to numbers
- `store_chunks()` - Save to ChromaDB
- `get_collection()` - Access ChromaDB

**Configuration:**
```python
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # From config.py
CHROMA_PERSIST_DIR = "data/chroma_db"  # Database location
```

**ChromaDB Status:**
```
Location: data/chroma_db/
Size: 3.1 MB (as of last check)
Collection: "ims_documents"
```

---

### 5. Database Recording

#### `database/db.py` (Lines 312-322)
**What it does:** Records document metadata in SQLite

```python
def add_document(
    filename: str,           # Timestamp_Filename.pdf
    original_name: str,      # Original name from user
    file_type: str,          # .pdf extension
    file_size: int,          # Bytes
    chunk_count: int,        # Number of chunks
    uploaded_by: str,        # User ID
) -> str:
    # Returns: document ID
```

**Database location:** `data/astrobot.db`

---

## 🐛 Troubleshooting 422 Upload Errors

### Step 1: Check if PDF is Valid

```python
# Run this in Python shell
from pathlib import Path
from ingestion.parser import parse_document

pdf_path = "path/to/your/file.pdf"
text, error = parse_document(pdf_path)

if text:
    print(f"✅ SUCCESS: Extracted {len(text)} characters")
else:
    print(f"❌ FAILED: {error}")
```

### Step 2: Test Each Stage

```python
# Stage 1: Parse
text, error = parse_document("doc.pdf")
print(f"1. Parse: {'✅' if text else '❌ ' + error}")

# Stage 2: Chunk
from ingestion.chunker import chunk_document
chunks = chunk_document(text)
print(f"2. Chunk: {'✅' if chunks else '❌'} ({len(chunks)} chunks)")

# Stage 3: Store
from ingestion.embedder import store_chunks
stored = store_chunks(chunks, "test_id")
print(f"3. Store: ✅ ({stored} chunks)")

# Stage 4: Database
from database.db import add_document
doc_id = add_document("file.pdf", "file.pdf", ".pdf", 1024, len(chunks), "user1")
print(f"4. Database: ✅ ({doc_id})")
```

### Step 3: Check Recent Changes

```bash
# See what changed in upload-related files
git log --oneline -10 -- api_server.py views/admin.py ingestion/

# See git diff
git diff HEAD~5 api_server.py  # Last 5 commits
```

---

## 📊 Recent Changes Summary (2026-04-01)

### What We Fixed:
1. **Tuple Unpacking Bug** (views/admin.py:87)
   - Was: `text = parse_document(...)`  ❌
   - Now: `text, parse_error = parse_document(...)` ✅

2. **Error Handling** (views/admin.py, api_server.py)
   - Added try-catch for database insert
   - Added try-catch for ChromaDB storage
   - Shows detailed error messages to user

3. **File Size Validation**
   - Max 50MB per file
   - Validated before processing

4. **File Cleanup**
   - Removes partial files on parse failure
   - Removes on chunk failure
   - Removes if database insert fails

---

## 🔍 Common Issues & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `422 Unprocessable Entity` | PDF parse failed | Check if PDF is valid (searchable text, not scanned) |
| `No chunks generated` | Text too short | Ensure PDF has > 500 characters |
| `Failed to index in vector DB` | ChromaDB error | Delete `data/chroma_db/` and re-upload |
| `Database error` | SQLite issue | Check disk space, restart server |
| `File too large` | > 50MB | Split PDF into smaller files |

---

## 📁 Important Directories

```
Astro_bot/
├── data/
│   ├── uploads/           ← Where PDFs are saved
│   ├── chroma_db/         ← Vector database
│   └── astrobot.db        ← SQLite database
├── ingestion/
│   ├── parser.py          ← PDF/DOCX/etc parsing
│   ├── chunker.py         ← Text chunking
│   └── embedder.py        ← ChromaDB storage
├── views/
│   └── admin.py           ← Streamlit upload UI
├── api_server.py          ← FastAPI upload endpoint
└── config.py              ← Settings (CHUNK_SIZE, etc)
```

---

## 🚀 Testing the Upload System

### Manual Test (Python Shell)
```python
# Create test file
test_text = "This is a test document. " * 100  # > 500 chars
with open("test.txt", "w") as f:
    f.write(test_text)

# Test parse
from ingestion.parser import parse_document
text, error = parse_document("test.txt")
assert text, f"Parse failed: {error}"

# Test chunk
from ingestion.chunker import chunk_document
chunks = chunk_document(text)
assert chunks, "No chunks generated"

# Test storage
from ingestion.embedder import store_chunks
stored = store_chunks(chunks, "test_doc_id")
assert stored > 0, "Storage failed"

print("✅ All tests passed!")
```

### Web UI Test (Streamlit)
1. Login to http://localhost:8501 as admin
2. Go to "📄 Document Management"
3. Upload a PDF
4. Check for success message
5. Verify in "Knowledge Base" list

### REST API Test (FastAPI)
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.pdf" \
  -F "uploaded_by=user1"
```

---

## 📈 Performance Notes

Current bottlenecks:
- **PyPDF2**: 50-200ms for typical PDFs
- **Embedding**: 1-5s for first use (downloads model), 100-500ms after
- **ChromaDB**: <50ms per operation
- **SQLite**: <10ms per operation

Total upload time: 2-10 seconds depending on file size

---

## 🔐 Security Notes

✅ File validation:
- Extension check (only .pdf, .docx, etc)
- Size limit (50MB max)
- Malware scan: NOT implemented

⚠️ Considerations:
- Malicious PDFs could cause parser hang
- No sandboxing of parser process
- No file type verification beyond extension

---

## 🎯 Maintenance Checklist

Before deploying:
- [ ] Test with problematic PDF formats
- [ ] Verify 50MB limit is sufficient
- [ ] Check error messages are user-friendly
- [ ] Review git changes with `git diff`
- [ ] Test database constraints
- [ ] Verify ChromaDB persistence

---

## 📞 Quick Commands

```bash
# Check git history
git log --oneline -20 -- api_server.py views/admin.py ingestion/

# See recent changes
git diff HEAD~5 HEAD

# Reset to previous version if needed
git checkout HEAD~2 -- api_server.py

# Test dependencies
python3 -c "import PyPDF2; import docx; print('✅ OK')"

# Count uploaded files
ls -1 data/uploads/ | wc -l

# Check ChromaDB size
du -sh data/chroma_db/
```

---

**Last Updated:** 2026-04-01
**Version:** 2.0 with error handling and file validation
