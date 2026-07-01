# ═══════════════════════════════════════════════════════════════════════════
# IMS AstroBot — Stop All Servers
# Kills all running server processes
# ═══════════════════════════════════════════════════════════════════════════

Write-Host "🛑 Stopping all IMS AstroBot servers..." -ForegroundColor Red
Write-Host ""

# Kill Python API Server
Write-Host "Stopping Python API Server..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "api_server" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Kill Node/React Dev Server
Write-Host "Stopping React Dev Server..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Kill Maven/Spring Boot
Write-Host "Stopping Spring Boot Server..." -ForegroundColor Yellow
Get-Process java -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "spring-boot" -or $_.CommandLine -match "maven" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "✅ All servers stopped!" -ForegroundColor Green
Write-Host ""
