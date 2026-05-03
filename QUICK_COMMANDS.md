# Student Marks System - Quick Command Reference

## 🚀 Start Services (3 Terminals)

### Terminal 1: Python FastAPI
```powershell
cd f:\Programming_project\Astrobot_v1\Astro_bot
.\venv\Scripts\Activate.ps1
uvicorn api_server:app --reload --port 8000
```

### Terminal 2: Spring Boot
```powershell
cd f:\Programming_project\Astrobot_v1\Astro_bot\springboot-backend
./mvnw spring-boot:run
# Or if Maven installed globally:
mvn spring-boot:run
```

### Terminal 3: React Frontend (Optional)
```powershell
cd f:\Programming_project\Astrobot_v1\Astro_bot\react-frontend
npm run dev
```

---

## 🧪 Run Tests

### Full Test Suite (Spring Boot)
```powershell
cd f:\Programming_project\Astrobot_v1\Astro_bot
.\test-student-marks.ps1 -Mode springboot
```

### Full Test Suite (FastAPI)
```powershell
.\test-student-marks.ps1 -Mode fastapi
```

---

## 📤 Manual Upload Commands

### Upload Students (Spring Boot)
```powershell
curl -X POST "http://localhost:8080/api/admin/students/upload" `
  -F "file=@data/sample_data/students.csv" `
  -F "uploaded_by=admin"
```

### Upload Marks (Spring Boot)
```powershell
curl -X POST "http://localhost:8080/api/admin/students/marks/upload" `
  -F "file=@data/sample_data/marks.csv" `
  -F "uploaded_by=admin"
```

### Upload Students (FastAPI Direct)
```powershell
curl -X POST "http://localhost:8000/api/admin/upload/students" `
  -F "file=@data/sample_data/students.csv" `
  -F "uploaded_by=admin"
```

### Upload Marks (FastAPI Direct)
```powershell
curl -X POST "http://localhost:8000/api/admin/upload/marks" `
  -F "file=@data/sample_data/marks.csv" `
  -F "uploaded_by=admin"
```

---

## 💬 Query Examples

### Query via Spring Boot
```powershell
$query = @{
    query = "Show marks for CS001"
    user_id = "test-user"
    username = "test"
} | ConvertTo-Json

curl -X POST "http://localhost:8080/api/chat" `
  -H "Content-Type: application/json" `
  -d $query
```

### Query via FastAPI
```powershell
curl -X POST "http://localhost:8000/api/chat" `
  -H "Content-Type: application/json" `
  -d @{
    query = "What is my GPA?"
    user_id = "test"
    username = "test"
} | ConvertTo-Json
```

### Sample Queries
- "Show marks for CS001"
- "What are my grades for semester 4?"
- "List subjects for roll number EC001"
- "How many marks did CS002 score in CS402?"
- "What is the grade distribution for CS403?"

---

## 🗄️ Database Commands

### View Students Count
```powershell
sqlite3 ./data/astrobot.db "SELECT COUNT(*) FROM students;"
```

### View Marks Count
```powershell
sqlite3 ./data/astrobot.db "SELECT COUNT(*) FROM student_marks;"
```

### View All Students
```powershell
sqlite3 ./data/astrobot.db "SELECT roll_no, name, department, gpa FROM students;"
```

### View Marks for CS001
```powershell
sqlite3 ./data/astrobot.db "SELECT student_id, subject_code, subject_name, grade FROM student_marks WHERE student_id IN (SELECT id FROM students WHERE roll_no = 'CS001');"
```

### Clear Tables (Reset Data)
```powershell
sqlite3 ./data/astrobot.db @"
DELETE FROM student_marks;
DELETE FROM students;
VACUUM;
"@
```

---

## 🔍 Health Checks

### Check FastAPI Health
```powershell
curl -X GET "http://localhost:8000/api/health" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Check Spring Boot Health
```powershell
curl -X GET "http://localhost:8080/actuator/health" | ConvertFrom-Json | ConvertTo-Json
```

### Check Python Logs
```powershell
# Check for errors in FastAPI
Get-Content -Path "logs/*.log" -Tail 20
```

### Check Spring Boot Logs
```powershell
# Logs appear in terminal window where mvn spring-boot:run is running
```

---

## 📊 API Endpoints Summary

### Spring Boot Proxy
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/admin/students/upload | Upload student CSV/XLSX |
| POST | /api/admin/students/marks/upload | Upload marks CSV/XLSX |
| POST | /api/chat | Query student marks |

### Python FastAPI (Direct)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/admin/upload/students | Upload student data |
| POST | /api/admin/upload/marks | Upload marks data |
| GET | /api/documents | List documents |
| POST | /api/chat | Chat with RAG |

---

## 🐛 Debugging Commands

### View Recent Errors
```powershell
# FastAPI errors
Get-Content "logs/*.log" -Tail 50 | Where-Object {$_ -match "error|Error|ERROR"}

# Spring Boot logs (in terminal)
# Scroll up in terminal running mvn spring-boot:run
```

### Test Database Connection
```powershell
# Test Python can reach DB
python3 -c "import sqlite3; db = sqlite3.connect('./data/astrobot.db'); print(db.cursor().execute('SELECT COUNT(*) FROM students').fetchone())"
```

### Test Spring Boot Connection to Python
```powershell
curl -X GET "http://localhost:8080/api/documents" | ConvertFrom-Json
```

---

## 📋 File Locations

| Component | File | Location |
|-----------|------|----------|
| Test Script | test-student-marks.ps1 | Root directory |
| Sample Data | students.csv, marks.csv | data/sample_data/ |
| Spring Controller | StudentMarksController.java | springboot-backend/src/main/java/com/astrobot/controller/ |
| Spring DTOs | StudentUploadResponse.java, MarksUploadResponse.java | springboot-backend/src/main/java/com/astrobot/dto/ |
| React Component | StudentMarksUpload.jsx | react-frontend/src/components/admin/ |
| Python DB | db.py | database/ |
| Python Agent | student_marks_agent.py | rag/tools/ |
| Python Parser | student_parser.py | ingestion/ |

---

## ✅ Verification Steps

1. **Verify Spring Boot Compilation**
   ```powershell
   cd springboot-backend
   ./mvnw clean compile
   ```

2. **Verify Python Syntax**
   ```powershell
   python3 -m py_compile database/student_db.py
   python3 -m py_compile ingestion/student_parser.py
   python3 -m py_compile rag/tools/student_marks_agent.py
   ```

3. **Verify Database Schema**
   ```powershell
   sqlite3 ./data/astrobot.db ".schema students"
   sqlite3 ./data/astrobot.db ".schema student_marks"
   ```

4. **Verify Files Exist**
   ```powershell
   Test-Path "data/sample_data/students.csv"
   Test-Path "data/sample_data/marks.csv"
   Test-Path "springboot-backend/src/main/java/com/astrobot/controller/StudentMarksController.java"
   ```

---

## 📞 Documentation References

- **Full Integration Guide**: `docs/STUDENT_MARKS_INTEGRATION.md`
- **Spring Boot Summary**: `SPRING_BOOT_STUDENT_MARKS_SUMMARY.md`
- **Verification Checklist**: `SPRING_BOOT_INTEGRATION_VERIFICATION.md`
- **This File**: `QUICK_COMMANDS.md`

---

## 🎯 Common Tasks

### Task: Upload and Test
```powershell
# 1. Make sure all 3 servers are running
# 2. Run test
.\test-student-marks.ps1 -Mode springboot
# 3. Check database
sqlite3 ./data/astrobot.db "SELECT COUNT(*) FROM students; SELECT COUNT(*) FROM student_marks;"
```

### Task: Reset Data
```powershell
sqlite3 ./data/astrobot.db "DELETE FROM student_marks; DELETE FROM students; VACUUM;"
```

### Task: Query Student Data
```powershell
$payload = @{query="Show marks for CS001"; user_id="test"; username="test"} | ConvertTo-Json
curl -X POST "http://localhost:8080/api/chat" -H "Content-Type: application/json" -d $payload
```

### Task: Redeploy
```powershell
# Kill all processes
# Clear database (optional)
# Restart services
# Re-run test
```

---

**Last Updated**: May 3, 2026  
**Status**: Ready for Production
