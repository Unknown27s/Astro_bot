# 🚀 AstroBot Server Startup Guide

This directory contains scripts to start and stop all three AstroBot servers with a single click.

## 📋 Available Scripts

### **Windows Batch Files (Easiest)**
- **`start-all-servers.bat`** ← Use this!
- **`stop-all-servers.bat`**

Simply double-click `start-all-servers.bat` to launch everything.

### **PowerShell Scripts (Alternative)**
- **`start-all-servers.ps1`**
- **`stop-all-servers.ps1`**

Run from PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\start-all-servers.ps1
```

---

## 🎯 What Gets Started

When you run the startup script, it launches **3 separate servers** in their own terminal windows:

| # | Server | Port | URL |
|---|--------|------|-----|
| 1 | **Python FastAPI** (RAG Engine) | 8000 | http://localhost:8000 |
| 2 | **React Frontend** (Vite Dev) | 5173 | http://localhost:5173 |
| 3 | **Spring Boot Backend** | 8080 | http://localhost:8080 |

---

## ✅ Prerequisites

Before running the startup script, ensure you have installed:

- ✅ **Python 3.8+** — Run `python --version`
- ✅ **Node.js 16+** — Run `node --version`
- ✅ **Java 17+** — Run `java -version`
- ✅ **Maven 3.8+** — Run `mvn --version`
- ✅ **pip dependencies** — Run `pip install -r requirements.txt`
- ✅ **npm dependencies** — Run `npm install` in `react-frontend/`

---

## 🚀 Quick Start

### Option 1: Batch File (Windows - Recommended)
1. Navigate to this folder
2. Double-click `start-all-servers.bat`
3. Wait for all servers to start
4. Open http://localhost:5173 in your browser

### Option 2: PowerShell
```powershell
.\start-all-servers.ps1
```

### Option 3: Manual Start (in separate terminals)
```powershell
# Terminal 1: Python API
python api_server.py

# Terminal 2: React Frontend
cd react-frontend
npm run dev

# Terminal 3: Spring Boot
cd springboot-backend
mvn spring-boot:run
```

---

## 📍 Access Points

Once all servers are running:

| Service | URL | Purpose |
|---------|-----|---------|
| React UI | http://localhost:5173 | Main web interface |
| FastAPI Docs | http://localhost:8000/docs | API documentation |
| Spring Boot | http://localhost:8080 | Backend proxy server |

---

## 🛑 Stopping Servers

### Option 1: Close Terminal Windows
Simply close each of the 3 terminal windows that were opened.

### Option 2: Run Stop Script
```batch
start-all-servers.bat
```

### Option 3: Kill Processes (PowerShell)
```powershell
Get-Process python, node, java | Stop-Process -Force
```

---

## 🔧 Troubleshooting

### **Port Already in Use**
If you see "Address already in use" errors:

```powershell
# Find process using a port
netstat -ano | findstr :8000

# Kill it (replace PID with the actual number)
taskkill /PID <PID> /F
```

### **Python Dependencies Missing**
```powershell
pip install -r requirements.txt
```

### **Node Dependencies Missing**
```powershell
cd react-frontend
npm install
```

### **Maven Build Fails**
Make sure Java 17+ is installed:
```powershell
java -version
```

---

## 📝 Notes

- All servers must be running for the app to work fully
- Each server runs in **its own terminal** for independent logs
- Don't close the launcher window immediately — let servers start first
- Check individual terminal windows for detailed error messages
- Make sure your `.env` file is configured with API keys if using cloud providers

---

## 📚 Project Structure

```
Astro_bot/
├── start-all-servers.bat  ← Start everything (Batch)
├── stop-all-servers.bat   ← Stop all (Batch)
├── start-all-servers.ps1  ← Start everything (PowerShell)
├── stop-all-servers.ps1   ← Stop all (PowerShell)
├── api_server.py          ← Python FastAPI (Port 8000)
├── react-frontend/        ← React Vite app (Port 5173)
├── springboot-backend/    ← Spring Boot (Port 8080)
└── ...
```

---

**Questions?** Check individual server logs in their terminal windows for detailed error information.
