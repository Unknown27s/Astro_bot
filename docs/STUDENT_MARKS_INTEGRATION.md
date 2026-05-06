# Student Marks System Integration Guide

## Overview

The Student Marks System has been integrated with Spring Boot proxy layer and includes sample test data. This document explains how to set up and test the integration.

**Prototype login rule:** Student logins are created automatically from uploaded data. Username and password are both set to the student roll number, and the chat pipeline auto-loads that student's profile + marks into the prompt for faster answers.

## Project Structure

### Backend Components

1. **Python FastAPI** (`api_server.py`)
   - Endpoints: `POST /api/admin/upload/students`, `POST /api/admin/upload/marks`
   - Database: SQLite with `students` and `student_marks` tables
   - LLM Agent: `rag/tools/student_marks_agent.py` for query processing

2. **Spring Boot Proxy** (`springboot-backend/`)
   - Controllers: `StudentMarksController` - routes to Python FastAPI
   - Service: `PythonApiService` - adds `uploadStudents()`, `uploadMarks()` methods
   - DTOs: `StudentUploadResponse`, `MarksUploadResponse`

3. **React Frontend** (`react-frontend/`)
   - Component: `StudentMarksUpload.jsx` - dual upload forms
   - Integration: Ready to add to admin panel

## Sample Data Files

Located in `/data/sample_data/`:

### `students.csv`
10 sample students from 3 departments (CS, EC, ME) with:
- roll_no, name, email, phone, department, semester, gpa

```csv
roll_no,name,email,phone,department,semester,gpa
CS001,Rahul Kumar,rahul.kumar@imsuniversity.ac.in,9876543210,Computer Science,4,7.85
...
```

### `marks.csv`
40 sample marks records covering:
- Subject code, subject name, internal/external marks, grade
- Linked to students by roll_no

```csv
roll_no,subject_code,subject_name,semester,internal_marks,external_marks,grade
CS001,CS401,Data Structures & Algorithms,4,18,72,A
...
```

## Testing the Integration

### Step 1: Start All Services

```powershell
# Terminal 1: Activate Python env and start FastAPI
cd f:\Programming_project\Astrobot_v1\Astro_bot
.\venv\Scripts\Activate.ps1
uvicorn api_server:app --reload --port 8000

# Terminal 2: Start Spring Boot
cd springboot-backend
./mvnw spring-boot:run

# Terminal 3: (Optional) Start React frontend
cd react-frontend
npm run dev
```

### Step 2: Upload Sample Data

**Option A: Direct FastAPI (Testing)**
```powershell
# Upload students
curl -X POST "http://localhost:8000/api/admin/upload/students" `
  -F "file=@data/sample_data/students.csv" `
  -F "uploaded_by=admin"

# Upload marks
curl -X POST "http://localhost:8000/api/admin/upload/marks" `
  -F "file=@data/sample_data/marks.csv" `
  -F "uploaded_by=admin"
```

**Option B: Via Spring Boot (Production)**
```powershell
# Upload students
curl -X POST "http://localhost:8080/api/admin/upload/students" `
  -F "file=@data/sample_data/students.csv" `
  -F "uploaded_by=admin"

# Upload marks
curl -X POST "http://localhost:8080/api/admin/upload/marks" `
  -F "file=@data/sample_data/marks.csv" `
  -F "uploaded_by=admin"

# Upload unified data (optional)
curl -X POST "http://localhost:8080/api/admin/upload/unified" `
  -F "file=@data/sample_data/unified_student_data.csv" `
  -F "uploaded_by=admin"
```

**Option C: React Admin Panel (UI)**
1. Navigate to http://localhost:3000 (React) or http://localhost:8080 (Spring)
2. Login as admin (default: admin/admin123)
3. Go to Admin Panel → Student Data
4. Upload students.csv
5. Upload marks.csv

### Step 3: Query Student Marks

Send a chat query to test the student marks agent:

```bash
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "query": "Show my marks for semester 4",
  "user_id": "admin-id",
  "username": "admin"
}
```

Or via Spring Boot:
```bash
POST http://localhost:8080/api/chat
```

**Faculty/Admin override:** Prefix a query with `@Database` to force the SQL Agent (e.g., `@Database show marks for roll no CS001`). Students can type it, but it is ignored and treated as normal chat.

### Expected Response

```json
{
  "response": "Here are your marks for semester 4:\n\n**CS401** - Data Structures & Algorithms: 90/100 (Grade: A)\n**CS402** - Database Management Systems: 85/100 (Grade: A)\n**CS403** - Web Development: 94/100 (Grade: A+)\n**CS404** - Operating Systems: 81/100 (Grade: A)\n\nCurrent GPA: 7.85",
  "sources": [
    {
      "text": "CS001 marks data",
      "source": "student_marks",
      "score": 0.95
    }
  ],
  "citations": ["Internal student database"],
  "response_time_ms": 245
}
```

## API Endpoints Reference

### Student Upload
```
POST /api/admin/upload/students
Host: localhost:8000 (FastAPI) or localhost:8080 (Spring Boot)

Form Data:
- file: CSV or XLSX file
- uploaded_by: Username (optional)

Response:
{
  "status": "success",
  "students_added": 10,
  "total_records": 10,
  "student_users_created": 10
}
```

### Marks Upload
```
POST /api/admin/upload/marks
Host: localhost:8000 (FastAPI) or localhost:8080 (Spring Boot)

Form Data:
- file: CSV or XLSX file
- uploaded_by: Username (optional)

Response:
{
  "status": "success",
  "marks_added": 40,
  "total_records": 40
}
```

### Query Student Marks
```
POST /api/chat
Host: localhost:8000 (FastAPI) or localhost:8080 (Spring Boot)

Body:
{
  "query": "What are my marks?",
  "user_id": "student-id",
  "username": "student"
}

Response: RAG-powered answer with source citations
```

## Database Schema

### students table
```sql
CREATE TABLE students (
  id TEXT PRIMARY KEY,
  roll_no TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  department TEXT,
  semester INTEGER,
  gpa REAL,
  uploaded_at TEXT NOT NULL
)
```

### student_marks table
```sql
CREATE TABLE student_marks (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  subject_code TEXT NOT NULL,
  subject_name TEXT NOT NULL,
  semester INTEGER,
  internal_marks REAL,
  external_marks REAL,
  total_marks REAL,
  grade TEXT,
  uploaded_at TEXT NOT NULL,
  FOREIGN KEY (student_id) REFERENCES students(id)
)
```

## Query Router Configuration

The system automatically routes queries containing marks-related keywords:
- "marks", "mark", "score", "grades", "grade", "result"
- "cgpa", "gpa", "semester", "internal", "external", "marks sheet", "percentage"

### Query Route Detection

```
User Query: "Show my marks"
  ↓
Query Router detects "marks" keyword
  ↓
Routes to Route.STUDENT_MARKS
  ↓
Calls student_marks_agent
  ↓
Agent extracts: roll_no, subject_code, semester
  ↓
Database query: SELECT * FROM student_marks WHERE roll_no = ?
  ↓
LLM synthesis → Natural language response
```

## Role-Based Access Control

Current implementation:
- **Admin**: Can upload data, view all student marks
- **Faculty**: Can upload marks, view all student marks
- **Student**: Can query their own marks (role check in agent)

Student logins are roll number-based in this prototype (username/password = roll_no), which allows auto-loading personal data in chat without asking for roll_no each time.

To implement student-owned data filtering:
1. Add `roll_no` field to `users` table
2. During login, store `user_roll_no` in session
3. In `student_marks_agent`, check:
   ```python
   if user_role == "student":
       roll_no = get_user_roll_no(user_id)  # Override query extraction
   ```

## Troubleshooting

### Issue: "File upload fails"
**Solution**: Ensure file is .csv or .xlsx, not .xls or other format

### Issue: "No student found"
**Solution**: Check that students.csv was imported first, before marks.csv

### Issue: "Query router doesn't detect marks questions"
**Solution**: Verify query_router.py has _STUDENT_MARKS signal group configured

### Issue: "Spring Boot can't reach Python API"
**Solution**: Ensure FastAPI is running on port 8000 and accessible at http://localhost:8000

## Next Steps

1. **Integrate StudentMarksUpload component into React admin panel**
   - Location: Add to `AdminLayout.jsx` or create `AdminStudentsPage.jsx`

2. **Implement user-student mapping**
   - Add roll_no to users table during signup
   - Enforce in student_marks_agent for role-based filtering

3. **Add more query types**
   - GPA calculation across semesters
   - Subject-wise performance analysis
   - Grade distribution reports

4. **Test end-to-end with sample data**
   - Upload students.csv → verify in SQLite
   - Upload marks.csv → verify foreign key relationships
   - Query "Show my marks" → verify agent extracts and returns data

## Files Modified/Created

**Modified:**
- `springboot-backend/src/main/java/com/astrobot/service/PythonApiService.java` - Added uploadStudents(), uploadMarks()
- `rag/query_router.py` - Added STUDENT_MARKS route
- `database/db.py` - Added students and student_marks tables
- `api_server.py` - Added /api/admin/upload/students and /api/admin/upload/marks endpoints

**Created:**
- `springboot-backend/src/main/java/com/astrobot/controller/StudentMarksController.java`
- `springboot-backend/src/main/java/com/astrobot/dto/StudentUploadResponse.java`
- `springboot-backend/src/main/java/com/astrobot/dto/MarksUploadResponse.java`
- `database/student_db.py` - CRUD functions
- `ingestion/student_parser.py` - CSV/XLSX parsers
- `rag/tools/student_marks_agent.py` - LLM agent
- `react-frontend/src/components/admin/StudentMarksUpload.jsx`
- `data/sample_data/students.csv` - Sample student records
- `data/sample_data/marks.csv` - Sample marks records
- `docs/STUDENT_MARKS_INTEGRATION.md` - This file

---

**Date Created**: May 3, 2026  
**Status**: Ready for testing and frontend integration
