@echo off
REM ═════════════════════════════════════════════════════════════════════════
REM IMS AstroBot — Stop All Servers (Batch version)
REM Kills running server processes
REM ═════════════════════════════════════════════════════════════════════════

cls
color 0C
echo.
echo Stopping all IMS AstroBot servers...
echo.

REM Kill Python processes
echo Stopping Python API Server...
taskkill /F /IM python.exe /T >nul 2>&1

REM Kill Node processes
echo Stopping React Dev Server...
taskkill /F /IM node.exe /T >nul 2>&1

REM Kill Java processes (Spring Boot)
echo Stopping Spring Boot Server...
taskkill /F /IM java.exe /T >nul 2>&1

echo.
color 0A
echo All servers stopped!
echo.
pause
