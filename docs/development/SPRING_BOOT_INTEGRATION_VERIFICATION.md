# ✅ Spring Boot Integration Verification Checklist (Updated)

Use this document to verify that Spring Boot correctly proxies all React admin endpoints for student marks and timetables.

---

## ✅ 1. Controllers Present

✅ `AdminUploadController` exists:
```
springboot-backend/src/main/java/com/astrobot/controller/AdminUploadController.java
```

✅ `StudentMarksController` exists:
```
springboot-backend/src/main/java/com/astrobot/controller/StudentMarksController.java
```

✅ `TimetableController` exists:
```
springboot-backend/src/main/java/com/astrobot/controller/TimetableController.java
```

---

## ✅ 2. Required Endpoints Exposed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/upload/students` | POST | Upload students CSV |
| `/api/admin/upload/marks` | POST | Upload marks CSV |
| `/api/admin/upload/unified` | POST | Upload unified CSV |
| `/api/admin/students` | GET | List students |
| `/api/admin/timetables` | GET | List timetables |

---

## ✅ 3. PythonApiService Methods

Verify the following methods exist in:
```
springboot-backend/src/main/java/com/astrobot/service/PythonApiService.java
```

- `uploadStudents(...)`
- `uploadMarks(...)`
- `uploadUnified(...)`
- `getStudents()`
- `getTimetables()`

---

## ✅ 4. React Admin Matches These Routes

Ensure React uses the same endpoints:

- StudentMarksUpload.jsx → `/api/admin/upload/students`
- StudentMarksUpload.jsx → `/api/admin/upload/marks`
- StudentMarksUpload.jsx → `/api/admin/upload/unified`
- TimetableUpload.jsx → `/api/admin/upload/timetable`
- TimetablePage.jsx → `/api/admin/timetables`

---

## ✅ 5. Manual Curl Tests

```bash
# Upload students
curl -X POST http://localhost:8080/api/admin/upload/students \
  -F "file=@students.csv" \
  -F "uploaded_by=admin"

# Upload marks
curl -X POST http://localhost:8080/api/admin/upload/marks \
  -F "file=@marks.csv" \
  -F "uploaded_by=admin"

# Upload unified
curl -X POST http://localhost:8080/api/admin/upload/unified \
  -F "file=@students_and_marks.csv" \
  -F "uploaded_by=admin"

# List students
curl http://localhost:8080/api/admin/students

# List timetables
curl http://localhost:8080/api/admin/timetables
```

---

## ✅ 6. Expected Upload Response (Sample)

```json
{
  "success": true,
  "file": "students.csv",
  "rows": 182,
  "status": "uploaded"
}
```

---

**Last Updated:** May 2026
