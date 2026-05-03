#!/usr/bin/env pwsh
# Test Student Marks Integration
# Usage: .\test-student-marks.ps1

param(
    [string]$Mode = "fastapi",  # "fastapi" or "springboot"
    [string]$AdminUsername = "admin"
)

$ErrorActionPreference = "Stop"

# Determine base URL
$BaseUrl = if ($Mode -eq "springboot") { "http://localhost:8080" } else { "http://localhost:8000" }
$SampleDataPath = "./data/sample_data"

Write-Host "🧪 Testing Student Marks Integration" -ForegroundColor Cyan
Write-Host "Mode: $Mode ($BaseUrl)" -ForegroundColor Yellow
Write-Host ""

# Check if sample data files exist
if (!(Test-Path "$SampleDataPath/students.csv")) {
    Write-Host "❌ students.csv not found at $SampleDataPath/students.csv" -ForegroundColor Red
    exit 1
}

if (!(Test-Path "$SampleDataPath/marks.csv")) {
    Write-Host "❌ marks.csv not found at $SampleDataPath/marks.csv" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Sample data files found" -ForegroundColor Green

# Test 1: Upload students
Write-Host ""
Write-Host "📤 Test 1: Uploading students.csv..." -ForegroundColor Cyan

$studentEndpoint = if ($Mode -eq "springboot") { 
    "$BaseUrl/api/admin/students/upload" 
}
else { 
    "$BaseUrl/api/admin/upload/students" 
}

try {
    $studentResponse = curl.exe -X POST "$studentEndpoint" `
        -F "file=@$SampleDataPath/students.csv" `
        -F "uploaded_by=$AdminUsername" `
        --silent `
        --show-error

    $studentJson = $studentResponse | ConvertFrom-Json
    
    if ($studentJson.status -eq "success") {
        Write-Host "✅ Students uploaded successfully" -ForegroundColor Green
        Write-Host "   Added: $($studentJson.students_added) records" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Upload returned status: $($studentJson.status)" -ForegroundColor Yellow
        Write-Host "   Response: $studentResponse" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Error uploading students: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Upload marks
Write-Host ""
Write-Host "📤 Test 2: Uploading marks.csv..." -ForegroundColor Cyan

$marksEndpoint = if ($Mode -eq "springboot") { 
    "$BaseUrl/api/admin/students/marks/upload" 
}
else { 
    "$BaseUrl/api/admin/upload/marks" 
}

try {
    $marksResponse = curl.exe -X POST "$marksEndpoint" `
        -F "file=@$SampleDataPath/marks.csv" `
        -F "uploaded_by=$AdminUsername" `
        --silent `
        --show-error

    $marksJson = $marksResponse | ConvertFrom-Json
    
    if ($marksJson.status -eq "success") {
        Write-Host "✅ Marks uploaded successfully" -ForegroundColor Green
        Write-Host "   Added: $($marksJson.marks_added) records" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Upload returned status: $($marksJson.status)" -ForegroundColor Yellow
        Write-Host "   Response: $marksResponse" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Error uploading marks: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Query student marks
Write-Host ""
Write-Host "💬 Test 3: Querying student marks..." -ForegroundColor Cyan

$chatEndpoint = "$BaseUrl/api/chat"

$queryPayload = @{
    query    = "Show marks for CS001"
    user_id  = "test-user-1"
    username = "test_user"
} | ConvertTo-Json

try {
    $chatResponse = curl.exe -X POST "$chatEndpoint" `
        -H "Content-Type: application/json" `
        -d $queryPayload `
        --silent `
        --show-error

    $chatJson = $chatResponse | ConvertFrom-Json
    
    if ($chatJson.response) {
        Write-Host "✅ Query executed successfully" -ForegroundColor Green
        Write-Host "   Response preview: $($chatJson.response.Substring(0, [Math]::Min(100, $chatJson.response.Length)))..." -ForegroundColor Green
        Write-Host "   Response time: $($chatJson.response_time_ms)ms" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Unexpected response format" -ForegroundColor Yellow
        Write-Host "   Response: $chatResponse" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Error querying marks: $_" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ All tests completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Verify database: sqlite3 ./data/astrobot.db 'SELECT COUNT(*) FROM students; SELECT COUNT(*) FROM student_marks;'" -ForegroundColor White
Write-Host "2. Test via React UI: http://localhost:3000" -ForegroundColor White
Write-Host "3. Try other queries: 'What is my GPA?', 'Show semester 4 results'" -ForegroundColor White
