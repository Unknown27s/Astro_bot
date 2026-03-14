# AstroBot Quick Start Guide

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **Error Tracking**: sentry-sdk, python-json-logger
- **Rate Limiting**: slowapi
- **Database**: alembic
- **Monitoring**: prometheus-client
- **And all existing dependencies**

### 2. Verify Installation

```bash
# Test that API server imports successfully
python -c "import api_server; print('✅ API server ready')"

# Verify key modules
python -c "from log_config import setup_logging; print('✅ Logging configured')"
python -c "from middleware.rate_limiter import get_limiter; print('✅ Rate limiting ready')"
python -c "from database.db import init_db; print('✅ Database ready')"
```

### 3. Configure Environment (.env)

Create a `.env` file in the project root:

```env
# Error Tracking (Optional but recommended for production)
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_GLOBAL=100/minute
RATE_LIMIT_PER_USER=30/minute
RATE_LIMIT_CHAT=5/minute
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_AUTH=5/minute

# LLM Configuration
LLM_MODE=local_only
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:0.6b

# Database
SQLITE_DB_PATH=./data/astrobot.db

# API Settings
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 4. Run Locally

```bash
# Start FastAPI server
python api_server.py
```

The API will be available at:
- **API Base**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### 5. Test Key Features

**Health Check:**
```bash
curl http://localhost:8000/api/health | jq
```

**Test Rate Limiting:**
```bash
# This will succeed for 5 requests, then return 429
for i in {1..10}; do
  echo "Request $i:"
  curl -i http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' 2>/dev/null | grep "HTTP"
done
```

**Test Logging:**
```bash
# Check logs (JSON formatted)
tail -f logs/astrobot.log | jq
```

**Test Document Tagging:**
```bash
# Create a tag
curl -X POST http://localhost:8000/api/documents/tags \
  -H "Content-Type: application/json" \
  -d '{"name":"Important","description":"High priority","color":"#FF0000"}' | jq

# List tags
curl http://localhost:8000/api/documents/tags | jq
```

---

## Deployment with Load Balancing

### Prerequisites
- Docker & Docker Compose installed
- Ports 80, 8000-8002 available

### Steps

```bash
# Build Docker image
docker build -t astrobot-fastapi:latest .

# Start 3 FastAPI instances + Nginx load balancer
docker-compose -f deployment/docker-compose.lb.yml up -d

# Verify services are running
docker-compose -f deployment/docker-compose.lb.yml ps

# Check health through load balancer
curl http://localhost/api/health | jq

# Monitor logs
docker-compose -f deployment/docker-compose.lb.yml logs -f
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pythonjsonlogger'"
**Solution:** Run `pip install -r requirements.txt`

### Issue: "Unable to connect to Ollama"
**Solution:**
```bash
# Start Ollama (or skip if using cloud LLM)
ollama serve

# In another terminal, pull a model
ollama pull qwen3:0.6b
```

### Issue: "Database is locked"
**Solution:** Wait a moment. SQLite WAL mode handles concurrent access, but may need a moment to checkpoint.

### Issue: "Port 8000 already in use"
**Solution:** Either stop the process using port 8000, or specify a different port:
```bash
python api_server.py --port 8001
```

---

## Next Steps

1. ✅ **Immediate**: Install dependencies and verify import
2. ✅ **Today**: Test core features (rate limiting, logging, tagging)
3. ✅ **This Week**: Configure Sentry for production monitoring
4. ✅ **This Month**: Deploy with Docker load balancing
5. ✅ **Next Month**: Set up monitoring (Prometheus/Grafana)

---

## Documentation

- **`IMPLEMENTATION_SUMMARY.md`** - Complete implementation details
- **`deployment/LOAD_BALANCING.md`** - Load balancing & scaling guide
- **`.github/copilot-instructions.md`** - Architecture reference

---

**Ready? Run: `pip install -r requirements.txt` and then `python api_server.py`** 🚀
