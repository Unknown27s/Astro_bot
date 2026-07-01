# ═══════════════════════════════════════════════════════════════════════════
# IMS AstroBot — Start All Servers
# Launches Python API, React Frontend, and Spring Boot Backend
# ═══════════════════════════════════════════════════════════════════════════

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "🚀 Starting IMS AstroBot Servers..." -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python not found. Please install Python." -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Node.js not found. Please install Node.js." -ForegroundColor Red
    exit 1
}

# Resolve JAVA_HOME (required by Maven wrapper)
$resolvedJavaHome = $null

if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
    $resolvedJavaHome = $env:JAVA_HOME
}

if (-not $resolvedJavaHome) {
    $javaCommand = Get-Command java -ErrorAction SilentlyContinue
    if ($javaCommand) {
        $javaBinDir = Split-Path -Parent $javaCommand.Source
        $candidateJavaHome = (Resolve-Path (Join-Path $javaBinDir '..')).Path
        if (Test-Path (Join-Path $candidateJavaHome 'bin\java.exe')) {
            $resolvedJavaHome = $candidateJavaHome
        }
    }
}

if (-not $resolvedJavaHome) {
    Write-Host "❌ JAVA_HOME could not be resolved." -ForegroundColor Red
    Write-Host "   Install JDK 17+ and set JAVA_HOME to your JDK folder." -ForegroundColor Yellow
    exit 1
}

$env:JAVA_HOME = $resolvedJavaHome
Write-Host "✅ Java found: $($env:JAVA_HOME)" -ForegroundColor Green

$mvnwPath = Join-Path $scriptPath 'springboot-backend\mvnw.cmd'
if (-not (Test-Path $mvnwPath)) {
    Write-Host "❌ Maven wrapper not found: $mvnwPath" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Maven wrapper found" -ForegroundColor Green

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 1. Start Python API Server
Write-Host "1️⃣  Starting Python API Server..." -ForegroundColor Cyan
$pythonTerminal = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; python api_server.py" -PassThru
Write-Host "   ✅ Python API server started (PID: $($pythonTerminal.Id))" -ForegroundColor Green
Write-Host "   📍 Access at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 2

# 2. Start React Frontend Dev Server
Write-Host "2️⃣  Starting React Frontend (Vite Dev Server)..." -ForegroundColor Cyan
$reactTerminal = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath\react-frontend'; npm run dev" -PassThru
Write-Host "   ✅ React dev server started (PID: $($reactTerminal.Id))" -ForegroundColor Green
Write-Host "   📍 Access at: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 3

# 3. Start Spring Boot Backend
Write-Host "3️⃣  Starting Spring Boot Backend Server..." -ForegroundColor Cyan
$springCommand = "$env:JAVA_HOME = '$($env:JAVA_HOME)'; cd '$scriptPath\springboot-backend'; .\mvnw.cmd spring-boot:run"
$springTerminal = Start-Process powershell -ArgumentList "-NoExit", "-Command", $springCommand -PassThru
Write-Host "   ✅ Spring Boot server started (PID: $($springTerminal.Id))" -ForegroundColor Green
Write-Host "   📍 Access at: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""

Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 All Servers Running!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Server Endpoints:" -ForegroundColor White
Write-Host "   • Python FastAPI API:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "   • FastAPI Docs (Swagger): http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   • React Frontend:       http://localhost:5173" -ForegroundColor Cyan
Write-Host "   • Spring Boot Backend:  http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "🛑 To stop all servers:" -ForegroundColor Yellow
Write-Host "   • Close each terminal window, or" -ForegroundColor White
Write-Host "   • Run: stop-all-servers.ps1 (in the same directory)" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Magenta
Write-Host "   • Each server runs in its own terminal for easy log viewing" -ForegroundColor White
Write-Host "   • Check the terminals for startup errors or port conflicts" -ForegroundColor White
Write-Host "   • Make sure Ollama or your LLM provider is running if using local mode" -ForegroundColor White
Write-Host ""

# Keep this script window open
Read-Host "Press Enter to close this launcher window (servers will keep running)"
