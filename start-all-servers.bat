@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM IMS AstroBot — Start All Servers (Batch version for Windows)
REM Launches Python API, React Frontend, and Spring Boot Backend
REM ═══════════════════════════════════════════════════════════════════════════

cls
color 0B
echo.
echo ══════════════════════════════════════════════════════════════════════════
echo                    IMS ASTROBOT - START ALL SERVERS
echo ══════════════════════════════════════════════════════════════════════════
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ERROR: Python not found. Please install Python.
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js not found. React server may not start.
) else (
    echo [OK] Node.js found
)
echo.

REM Check Java
echo Checking Java...
java -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Java not found. Spring Boot may not start.
) else (
    echo [OK] Java found
)
echo.

echo ══════════════════════════════════════════════════════════════════════════
echo Starting servers...
echo ══════════════════════════════════════════════════════════════════════════
echo.

REM 1. Start Python API Server
echo 1. Starting Python FastAPI Server...
start "AstroBot - Python API Server" cmd /k "python api_server.py"
echo    - Running on http://localhost:8000/docs
echo    - New terminal window opened
echo.
timeout /t 2 /nobreak

REM 2. Start React Frontend
echo 2. Starting React Frontend (Vite)...
start "AstroBot - React Frontend" cmd /k "cd react-frontend && npm run dev"
echo    - Running on http://localhost:5173
echo    - New terminal window opened
echo.
timeout /t 3 /nobreak

REM 3. Start Spring Boot
echo 3. Starting Spring Boot Backend...
start "AstroBot - Spring Boot" cmd /k "cd springboot-backend && .\mvnw.cmd spring-boot:run"
echo    - Running on http://localhost:8080
echo    - New terminal window opened
echo.

cls
color 0A
echo.
echo ══════════════════════════════════════════════════════════════════════════
echo                     ALL SERVERS STARTED SUCCESSFULLY!
echo ══════════════════════════════════════════════════════════════════════════
echo.
echo SERVICES RUNNING:
echo.
echo   1. Python FastAPI API
echo      URL: http://localhost:8000
echo      Docs: http://localhost:8000/docs
echo.
echo   2. React Frontend
echo      URL: http://localhost:5173
echo.
echo   3. Spring Boot Backend
echo      URL: http://localhost:8080
echo.
echo ══════════════════════════════════════════════════════════════════════════
echo.
echo NOTES:
echo   - Each server runs in its own terminal window
echo   - Check terminals for errors or logs
echo   - To stop servers, close each terminal window individually
echo   - Or run: stop-all-servers.bat
echo.
echo ══════════════════════════════════════════════════════════════════════════
echo.
pause
