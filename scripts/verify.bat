@echo off
REM AstroBot Verification Script (Windows)
REM Run this after installing dependencies to verify everything is working

setlocal enabledelayedexpansion

echo.
echo ================================================
echo 0xf0 AstroBot Implementation Verification
echo ================================================
echo.

REM Function equivalent for checking Python modules
setlocal DisableDelayedExpansion
(
    python -m pip list > nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found or not in PATH
        exit /b 1
    )
)
setlocal EnableDelayedExpansion

echo 1 Checking Python Dependencies...
echo.

echo    Phase 1: Error Tracking
python -c "import sentry_sdk" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] sentry_sdk) else (echo [FAIL] sentry_sdk & exit /b 1)

python -c "import pythonjsonlogger" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] pythonjsonlogger) else (echo [FAIL] pythonjsonlogger & exit /b 1)

echo    Phase 2: Rate Limiting
python -c "import slowapi" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] slowapi) else (echo [FAIL] slowapi & exit /b 1)

echo    Core Dependencies
python -c "import fastapi" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] fastapi) else (echo [FAIL] fastapi & exit /b 1)

python -c "import chromadb" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] chromadb) else (echo [FAIL] chromadb & exit /b 1)

python -c "import sentence_transformers" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] sentence_transformers) else (echo [FAIL] sentence_transformers & exit /b 1)

echo.
echo 2 Checking Project Structure...
echo.

if exist "api_server.py" (echo [OK] api_server.py) else (echo [FAIL] api_server.py & exit /b 1)
if exist "config.py" (echo [OK] config.py) else (echo [FAIL] config.py & exit /b 1)
if exist "database\db.py" (echo [OK] database\db.py) else (echo [FAIL] database\db.py & exit /b 1)
if exist "requirements.txt" (echo [OK] requirements.txt) else (echo [FAIL] requirements.txt & exit /b 1)

echo.
echo 3 Checking Phase 1: Error Tracking
echo.

if exist "log_config" (echo [OK] log_config directory) else (echo [FAIL] log_config directory & exit /b 1)
if exist "log_config\__init__.py" (echo [OK] Logging module) else (echo [FAIL] Logging module & exit /b 1)
if exist "log_config\sentry_config.py" (echo [OK] Sentry configuration) else (echo [FAIL] Sentry configuration & exit /b 1)

echo.
echo 4 Checking Phase 2: Rate Limiting
echo.

if exist "middleware\rate_limiter.py" (echo [OK] Rate limiter middleware) else (echo [FAIL] Rate limiter middleware & exit /b 1)

echo.
echo 5 Checking Phase 3: Tagging/Classification
echo.

python -c "from database.db import create_tag, get_all_tags" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] Tag functions available) else (echo [FAIL] Tag functions & exit /b 1)

python -c "from database.db import set_document_classification" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] Classification functions available) else (echo [FAIL] Classification functions & exit /b 1)

echo.
echo 6 Checking Phase 4: Load Balancing
echo.

if exist "deployment\nginx.conf" (echo [OK] deployment\nginx.conf) else (echo [WARNING] deployment\nginx.conf)
if exist "deployment\docker-compose.lb.yml" (echo [OK] deployment\docker-compose.lb.yml) else (echo [WARNING] deployment\docker-compose.lb.yml)
if exist "Dockerfile" (echo [OK] Dockerfile) else (echo [WARNING] Dockerfile)

echo.
echo 7 Testing Python Imports...
echo.

python -c "from log_config import setup_logging" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] Logging imports work) else (echo [FAIL] Logging imports & exit /b 1)

python -c "from middleware.rate_limiter import get_limiter" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] Rate limiter imports work) else (echo [FAIL] Rate limiter imports & exit /b 1)

python -c "from database.db import init_db" > nul 2>&1
if !errorlevel! equ 0 (echo [OK] Database imports work) else (echo [FAIL] Database imports & exit /b 1)

echo.
echo ================================================
echo [SUCCESS] All Checks Passed!
echo ================================================
echo.
echo Next steps:
echo   1. Configure .env file
echo   2. Start API server: python api_server.py
echo   3. Test at: http://localhost:8000/api/health
echo.
echo Documentation:
echo   - QUICKSTART.md - Quick setup guide
echo   - IMPLEMENTATION_SUMMARY.md - Full details
echo   - deployment\LOAD_BALANCING.md - Scaling guide
echo.
