# 🎯 AstroBot Upload - Quick Reference Card

## Your 422 Error Explained

```
User uploads PDF → FastAPI receives file → Parser tries to extract text
                                                       ↓
                                    ❌ Text extraction fails
                                    ❌ Returns error message
                                                       ↓
                                    HTTP 422 response sent
```

**Error comes from:** `api_server.py` line 375

---

## What We Fixed ✅

| Issue | File | Line | Before | After |
|-------|------|------|--------|-------|
| Tuple unpacking | `views/admin.py` | 87 | `text = parse_document(...)` | `text, parse_error = parse_document(...)` |
| No DB error handling | `views/admin.py` | 115 | No try-catch | Added try-catch |
| No ChromaDB error handling | `views/admin.py` | 135 | No try-catch | Added try-catch |
| No file size check | Both files | Line 67-70 | None | Added 50MB max |
| Poor error messages | Both files | Various | Silent failures | Detailed messages |

---

## Files You Need to Know

### When uploading happens:

```
1. User clicks "Upload" → views/admin.py (Streamlit UI)
                  OR
                 → api_server.py:329 (FastAPI REST)
                          ↓
2. File saved to disk (data/uploads/)
                          ↓
3. Text extracted → ingestion/parser.py:138 parse_document()
   - parse_pdf()  [PyPDF2]
   - parse_docx() [python-docx]
   - etc...
                          ↓
4. Text chunked → ingestion/chunker.py chunk_document()
                          ↓
5. Embeddings created → ingestion/embedder.py store_chunks()
   - Stored in data/chroma_db/
                          ↓
6. Metadata saved → database/db.py add_document()
   - Saved in data/astrobot.db
```

---

## Debugging Command

Run this to test your system:

```bash
cd Astro_bot/
python3 debug_upload.py
```

Returns:
- ✅ All checks pass = System OK, your PDFs might be problematic
- ❌ Some fail = System issue found, will show which one

---

## Test Your PDF

```python
from ingestion.parser import parse_document

text, error = parse_document("your_pdf_file.pdf")

print(f"Text extracted: {len(text) if text else 0} characters")
print(f"Error: {error}")
```

**If error:** That's what caused your 422!

---

## Key Directories

| Path | Purpose | Status |
|------|---------|--------|
| `data/uploads/` | Uploaded PDF files | Exists (has 2 PDFs) |
| `data/chroma_db/` | Vector database | Exists (3.1 MB) |
| `data/astrobot.db` | SQLite database | Exists |

---

## What Causes 422 Error

### Most Common:
1. **PDF is encrypted** → Add password OR use different PDF
2. **PDF is scanned image** → Open in Photoshop/OCR tool first
3. **PDF is corrupted** → Try opening in Adobe Reader
4. **Very old PDF format** → Convert to newer format

### Less Common:
5. Disk space full
6. File permissions issue
7. PyPDF2 bug with specific PDF version
8. Memory exhausted

---

## Recent Code Changes Summary

### `views/admin.py` - Streamlit Upload
```python
# Line 87 - BEFORE (WRONG):
text = parse_document(str(file_path))
if not text:  # Always False! Tuple is truthy!

# Line 87 - AFTER (CORRECT):
text, parse_error = parse_document(str(file_path))
if not text:  # Now checks actual text
    st.error(f"Parse failed: {parse_error}")
```

### `views/admin.py` - Error Handling
```python
# Added (line 114-132):
try:
    doc_id = add_document(...)
except Exception as e:
    st.error(f"Database error: {e}")
    os.remove(file_path)  # Clean up
    continue

# Added (line 135-143):
try:
    stored = store_chunks(chunks, doc_id)
except Exception as e:
    st.error(f"ChromaDB error: {e}")
    continue
```

### `api_server.py` - Same Changes Applied
- Line 370: Tuple unpacking (already had)
- Line 362-364: File size validation (added)
- Line 384-396: Database error handling (added)
- Line 399-403: ChromaDB error handling (added)

---

## Documentation Files Created

| File | Purpose |
|------|---------|
| `UPLOAD_SYSTEM_MAINTENANCE.md` | Complete reference guide |
| `README_UPLOAD_FIXES.md` | Summary of what we fixed |
| `debug_upload.py` | Diagnostic script |
| `docs/guides/TROUBLESHOOTING.md` | Updated with PDF upload section |

---

## How to Check Git History

```bash
# See all changes to upload files
git log --oneline -20 -- api_server.py views/admin.py

# See exactly what changed
git diff HEAD~1 api_server.py

# Revert if needed
git checkout HEAD~1 -- api_server.py
```

---

## Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Streamlit UI | ✅ Fixed | Proper error handling |
| FastAPI endpoint | ✅ Enhanced | File size validation added |
| PDF Parser | ✅ Working | Returns (text, error) tuple |
| Chunker | ✅ Working | 500 char chunks, 50 char overlap |
| ChromaDB | ✅ Active | 3.1 MB, ready for uploads |
| SQLite | ✅ Active | Recording documents |

---

## Next Action Items

- [ ] **Test** with a simple PDF (not scannecd)
- [ ] **Run** debug script if test fails
- [ ] **Check** error message from parser
- [ ] **Review** git history for recent changes
- [ ] **Backup** current version if modifying

---

## Support Files Location

```
Astro_bot/
├── UPLOAD_SYSTEM_MAINTENANCE.md  ← Read this first
├── README_UPLOAD_FIXES.md         ← What changed
├── debug_upload.py                ← Run this to diagnose
└── docs/guides/TROUBLESHOOTING.md ← User guide
```

---

**Version:** 2.0 (Apr 2026)
**Status:** Production Ready
**Last Modified:** 2026-04-01
