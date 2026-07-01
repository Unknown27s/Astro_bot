# AstroBot Multi-Server Startup Script
# Starts FastAPI, Spring Boot, and React in parallel terminals

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "IMS AstroBot Server Startup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Get-Location
Write-Host "Project Root: $projectRoot" -ForegroundColor Green

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host $pythonVersion -ForegroundColor Green

# Check Node
Write-Host "Checking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
Write-Host $nodeVersion -ForegroundColor Green

# Check Java
Write-Host "Checking Java..." -ForegroundColor Yellow
$javaVersion = java -version 2>&1 | Select-Object -First 1
Write-Host $javaVersion -ForegroundColor Green
Write-Host ""

# Ask user about server selection
Write-Host "Which servers do you want to start?" -ForegroundColor Cyan
Write-Host "1. FastAPI only (port 8000)"
Write-Host "2. React only (port 3000)"
Write-Host "3. Spring Boot only (port 8080)"
Write-Host "4. All three servers (recommended)"
Write-Host "5. Exit"
Write-Host ""

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "Starting FastAPI server on port 8000..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload"
    }
    "2" {
        Write-Host "Starting React frontend on port 3000..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\react-frontend'; npm install; npm run dev"
    }
    "3" {
        Write-Host "Starting Spring Boot on port 8080..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\springboot-backend'; .\mvnw.cmd spring-boot:run"
    }
    "4" {
        Write-Host "Starting all three servers..." -ForegroundColor Green
        Write-Host ""
        
        Write-Host "Terminal 1: FastAPI (8000)" -ForegroundColor Cyan
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; Write-Host 'FastAPI Server' -ForegroundColor Green; python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload"
        Start-Sleep -Seconds 2
        
        Write-Host "Terminal 2: React (3000)" -ForegroundColor Cyan
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\react-frontend'; Write-Host 'React Frontend' -ForegroundColor Green; npm run dev"
        Start-Sleep -Seconds 2
        
        Write-Host "Terminal 3: Spring Boot (8080)" -ForegroundColor Cyan
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\springboot-backend'; Write-Host 'Spring Boot API Gateway' -ForegroundColor Green; .\mvnw.cmd spring-boot:run"
        
        Write-Host ""
        Write-Host "====================================" -ForegroundColor Green
        Write-Host "All servers starting..." -ForegroundColor Green
        Write-Host "====================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access points:" -ForegroundColor Yellow
        Write-Host "  - React UI:  http://localhost:3000" -ForegroundColor Cyan
        Write-Host "  - FastAPI:   http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "  - Spring Boot: http://localhost:8080" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Default credentials:" -ForegroundColor Yellow
        Write-Host "  - Username: admin" -ForegroundColor Cyan
        Write-Host "  - Password: admin123" -ForegroundColor Cyan
    }
    "5" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "Servers are starting. Check the new terminal windows for output." -ForegroundColor Green
Write-Host "Press Ctrl+C in each terminal to stop the servers." -ForegroundColor Yellow
