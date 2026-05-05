# 🚀 AstroBot Upload System - Quick Reference Card

## ✅ Upload API is ACTIVE ✅

### ✅ FastAPI Endpoint (Direct)
```
POST /api/documents/upload
```

### ✅ Spring Boot Proxy (Recommended)
```
POST /api/admin/upload
```

---

## ✅ Upload Endpoint Details

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/upload` | Uploads document to backend for chunking + embedding |

**Required Payload (multipart/form-data)**
```bash
file=@document.pdf
uploaded_by=admin_user
```

---

## ✅ Upload File Types Supported

✅ PDF (.pdf)
✅ Word (.docx)
✅ Excel (.xlsx, .xls)
✅ CSV (.csv)
✅ PowerPoint (.pptx)
✅ HTML (.html)
✅ Plain Text (.txt)

---

## ✅ Common Use (Test Upload)

### Using PowerShell:
```powershell
Invoke-WebRequest -Uri http://localhost:8080/api/admin/upload \
  -Method POST \
  -Form @{
    file = Get-Item "C:\path\to\sample.pdf"
    uploaded_by = "admin"
  }
```

### Using curl:
```bash
curl -X POST http://localhost:8080/api/admin/upload \
  -F "file=@sample.pdf" \
  -F "uploaded_by=admin"
```

---

## ✅ Response Format
```json
{
  "success": true,
  "doc_id": "uuid",
  "filename": "document.pdf",
  "chunks": 42,
  "status": "processed"
}
```

---

## ✅ Troubleshooting Shortcut

If upload fails:
- Check Spring Boot logs
- Check FastAPI logs
- Use `debug_upload.py` to isolate backend

---

## ✅ Documentation Files (Updated)

| File | Purpose |
|------|---------|
| `../development/UPLOAD_SYSTEM_MAINTENANCE.md` | Complete maintenance guide + troubleshooting |
| `../guides/TROUBLESHOOTING.md` | User-friendly upload troubleshooting |
| `../guides/UPLOAD_QUICK_REFERENCE.md` | This quick reference card |

---

## ✅ Support Files Location

```
Astro_bot/
├── docs/
│   ├── development/UPLOAD_SYSTEM_MAINTENANCE.md
│   └── guides/UPLOAD_QUICK_REFERENCE.md
├── debug_upload.py
```

---

## ✅ Maintainer
**Project:** IMS AstroBot v2.0

**Last Modified:** May 2026

---

See full documentation in: [../README.md](../README.md)
