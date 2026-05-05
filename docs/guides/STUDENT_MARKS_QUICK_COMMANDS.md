# 🧪 Student Marks System - Quick Commands (Updated)

## ✅ Base URLs
- **Spring Boot (Proxy)**: `http://localhost:8080`
- **FastAPI (Direct)**: `http://localhost:8000`

---

## ✅ Upload Students (Spring Boot)
```bash
curl -X POST http://localhost:8080/api/admin/upload/students \
  -F "file=@students.csv" \
  -F "uploaded_by=admin"
```

## ✅ Upload Marks (Spring Boot)
```bash
curl -X POST http://localhost:8080/api/admin/upload/marks \
  -F "file=@marks.csv" \
  -F "uploaded_by=admin"
```

## ✅ Upload Unified CSV (Spring Boot)
```bash
curl -X POST http://localhost:8080/api/admin/upload/unified \
  -F "file=@students_and_marks.csv" \
  -F "uploaded_by=admin"
```

---

## ✅ Upload Students (FastAPI Direct)
```bash
curl -X POST http://localhost:8000/api/admin/students/upload \
  -F "file=@students.csv" \
  -F "uploaded_by=admin"
```

## ✅ Upload Marks (FastAPI Direct)
```bash
curl -X POST http://localhost:8000/api/admin/students/marks/upload \
  -F "file=@marks.csv" \
  -F "uploaded_by=admin"
```

## ✅ Upload Unified (FastAPI Direct)
```bash
curl -X POST http://localhost:8000/api/admin/students/marks/upload-unified \
  -F "file=@students_and_marks.csv" \
  -F "uploaded_by=admin"
```

---

## ✅ List Students (Spring Boot)
```bash
curl http://localhost:8080/api/admin/students
```

## ✅ List Timetables (Spring Boot)
```bash
curl http://localhost:8080/api/admin/timetables
```

---

## ✅ API Endpoints Summary (Spring Boot)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/admin/upload/students` | Upload student master list |
| POST | `/api/admin/upload/marks` | Upload student marks |
| POST | `/api/admin/upload/unified` | Upload combined students + marks |
| GET | `/api/admin/students` | List students |
| GET | `/api/admin/timetables` | List timetables |

---

## ✅ Legacy Endpoints (FastAPI Direct)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/admin/students/upload` | Upload students CSV |
| POST | `/api/admin/students/marks/upload` | Upload marks CSV |
| POST | `/api/admin/students/marks/upload-unified` | Upload unified CSV |

---

## ✅ Documentation References
- Student Marks Integration: `../STUDENT_MARKS_INTEGRATION.md`
- Spring Boot Summary: `../development/SPRING_BOOT_STUDENT_MARKS_SUMMARY.md`
- Verification Checklist: `../development/SPRING_BOOT_INTEGRATION_VERIFICATION.md`

---

**Last Updated:** May 2026
