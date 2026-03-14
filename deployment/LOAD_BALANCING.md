# AstroBot Load Balancing Deployment Guide

## Overview

This guide explains how to deploy AstroBot with Nginx load balancing across multiple FastAPI instances for high availability and scalability.

## Architecture

```
┌─────────────────────────────┐
│      Client Requests        │
│   (React/ Spring Boot)      │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  Nginx Load Balancer        │
│  (Port 80/443)              │
│  - Health checks            │
│  - Round-robin/LeastConn    │
│  - SSL termination          │
└──────────────┬──────────────┘
      ┌────────┼────────┐
      │        │        │
┌─────▼─┐ ┌─────▼─┐ ┌──▼────┐
│FastAPI│ │FastAPI│ │FastAPI│
│   1   │ │   2   │ │   3   │
│ :8000 │ │ :8000 │ │ :8000 │
└───┬───┘ └───┬───┘ └──┬────┘
    │         │        │
    └─────────┼────────┘
              │
        ┌─────▼──────────┐
        │  Shared Data   │
        │ - SQLite DB    │
        │ - ChromaDB     │
        │ - Upload Files │
        │ - Logs         │
        └────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- Docker Compose version 3.8+
- At least 2GB free disk space for data/logs
- Ports 80, 443 available (or modify nginx.conf)

## Deployment Steps

### 1. Prepare Environment

```bash
cd /path/to/Astro_bot

# Create necessary directories
mkdir -p data logs deployment

# Create .env file (if not exists)
cp .env.example .env  # or create new

# Ensure deployment configs exist
ls deployment/nginx.conf
ls deployment/docker-compose.lb.yml
```

### 2. Build Docker Image

```bash
# Build FastAPI image
docker build -t astrobot-fastapi:latest .

# Verify image
docker images | grep astrobot-fastapi
```

### 3. Start Load Balanced Deployment

```bash
# Start all services (3x FastAPI + Nginx)
docker-compose -f deployment/docker-compose.lb.yml up -d

# Verify service health
docker-compose -f deployment/docker-compose.lb.yml ps

# Check Nginx logs
docker logs astrobot-nginx

# Check FastAPI logs
docker logs astrobot-fastapi-1
```

### 4. Verify Setup

```bash
# Health check
curl http://localhost/api/health

# Check that requests are load distributed
for i in {1..10}; do
  curl -s http://localhost/api/health | jq .
done

# Monitor load balancing
docker stats astrobot-nginx astrobot-fastapi-1 astrobot-fastapi-2 astrobot-fastapi-3
```

### 5. View Logs

```bash
# Nginx access logs
docker exec astrobot-nginx tail -f /var/log/nginx/astrobot_access.log

# Application logs in mounted volume
tail -f logs/astrobot.log

# Docker Compose logs
docker-compose -f deployment/docker-compose.lb.yml logs -f
```

## Configuration

### Rate Limiting Thresholds

Edit `config.py` to adjust rate limits:
```python
RATE_LIMIT_GLOBAL = "100/minute"      # Global across all users
RATE_LIMIT_PER_USER = "30/minute"     # Per authenticated user
RATE_LIMIT_CHAT = "5/minute"          # Chat endpoint
RATE_LIMIT_UPLOAD = "10/minute"       # Document upload
RATE_LIMIT_AUTH = "5/minute"          # Login/register
```

### Environment Variables

Configure in docker-compose.lb.yml environment sections:
```yaml
environment:
  - DATABASE_URL=sqlite:///./data/astrobot.db
  - LOG_LEVEL=INFO
  - SENTRY_DSN=your-sentry-dsn-here
  - SENTRY_ENVIRONMENT=production
  - LLM_MODE=hybrid
  - OLLAMA_BASE_URL=http://ollama:11434
  - RATE_LIMIT_CHAT=5/minute
```

### Adding More Instances

To scale from 3 to 5 FastAPI instances:

**1. Update docker-compose.lb.yml:**
```yaml
  fastapi-4:
    # Copy fastapi-3 block and change:
    # - container_name: astrobot-fastapi-4
    # - ports: "8003:8000"

  fastapi-5:
    # Copy fastapi-3 block and change:
    # - container_name: astrobot-fastapi-5
    # - ports: "8004:8000"
```

**2. Update deployment/nginx.conf:**
```nginx
upstream fastapi_backend {
    least_conn;
    server fastapi-1:8000 max_fails=3 fail_timeout=30s;
    server fastapi-2:8000 max_fails=3 fail_timeout=30s;
    server fastapi-3:8000 max_fails=3 fail_timeout=30s;
    server fastapi-4:8000 max_fails=3 fail_timeout=30s;  # Add
    server fastapi-5:8000 max_fails=3 fail_timeout=30s;  # Add
    keepalive 32;
}
```

**3. Restart services:**
```bash
docker-compose -f deployment/docker-compose.lb.yml up -d
docker exec astrobot-nginx nginx -s reload
```

## SSL/TLS (HTTPS)

### 1. Obtain Certificates

For Let's Encrypt:
```bash
# Using Certbot
certbot certonly --standalone -d your-domain.com

# Copy certificates
mkdir -p deployment/certs
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/certs/astrobot.crt
cp /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/certs/astrobot.key
chmod 644 deployment/certs/astrobot.crt
chmod 600 deployment/certs/astrobot.key
```

### 2. Update nginx.conf

Uncomment SSL sections in `deployment/nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/certs/astrobot.crt;
    ssl_certificate_key /etc/nginx/certs/astrobot.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### 3. Restart Nginx
```bash
docker-compose -f deployment/docker-compose.lb.yml down
docker-compose -f deployment/docker-compose.lb.yml up -d
```

## Monitoring

### Container Health

```bash
# Check all services
docker ps --filter "name=astrobot"

# Check specific service
docker exec astrobot-fastapi-1 curl -s http://localhost:8000/api/health | jq
```

### Request Distribution

Monitor which instance handles requests:
```bash
# Watch in real-time
watch -n 1 'curl -s http://localhost/api/health | jq'

# Check logs for instance identification
tail -f logs/astrobot.log | grep "request_id"
```

### Database Consistency

SQLite WAL (Write-Ahead Logging) mode ensures safety with multiple writers:
```bash
# Check WAL files
ls -la data/

# Verify database integrity
sqlite3 data/astrobot.db "PRAGMA integrity_check;"
```

## Troubleshooting

### Issue: 502 Bad Gateway from Nginx

**Cause:** FastAPI instance(s) not responding

**Solution:**
```bash
# Check downstream instances
docker exec astrobot-nginx curl http://fastapi-1:8000/api/health

# Restart failing instance
docker restart astrobot-fastapi-1

# Check logs
docker logs astrobot-fastapi-1
```

### Issue: Rate Limit Errors (429)

**Cause:** Exceeding configured rate limits

**Solution:**
1. Check rate limit settings in config.py
2. Increase thresholds if necessary
3. Consider implementing Redis for distributed rate limiting

### Issue: Uneven Request Distribution

**Cause:** Load balancing algorithm mismatch

**Solution:**
The config uses `least_conn` (least connections). For even distribution:
- Replace with `ip_hash` for session consistency
- Or add weights: `server fastapi-1:8000 weight=1;`

### Database Lock Errors

**Cause:** SQLite concurrency issues

**Solution:**
```bash
# WAL mode is already enabled, but check:
sqlite3 data/astrobot.db "PRAGMA journal_mode;"  # Should output: wal

# Check for stale locks
ls data/astrobot.db-*

# Force checkpoint
sqlite3 data/astrobot.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

## Performance Tuning

### Nginx Tuning

Edit `deployment/nginx.conf`:
```nginx
# Increase worker processes
worker_processes auto;

# Increase connections per worker
worker_connections 4096;

# Tune buffer sizes for your content size
proxy_buffer_size 256k;
proxy_buffers 8 256k;
```

### FastAPI Tuning

In `deployment/docker-compose.lb.yml`:
```yaml
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000",
     "--workers", "8",          # Increase from 4
     "--worker-class", "uvicorn.workers.UvicornWorker"]
```

### Database Optimization

```bash
# Analyze database for query optimization
sqlite3 data/astrobot.db "ANALYZE;"

# Vacuum to reclaim space
sqlite3 data/astrobot.db "VACUUM;"

# Check PRAGMA settings
sqlite3 data/astrobot.db "PRAGMA synchronous;" # Should be: 1 (NORMAL)
```

## Backup & Recovery

### Backup Data

```bash
# Backup all data
tar -czf astrobot_backup_$(date +%Y%m%d).tar.gz \
  data/ logs/ deployment/

# Backup database only
cp data/astrobot.db data/astrobot_backup_$(date +%Y%m%d).db
```

### Restore from Backup

```bash
# Restore all data
tar -xzf astrobot_backup_20240101.tar.gz

# Restart services
docker-compose -f deployment/docker-compose.lb.yml down
docker-compose -f deployment/docker-compose.lb.yml up -d
```

## Production Checklist

- [ ] SSL/TLS certificates installed
- [ ] Environment variables configured for production
- [ ] Sentry error tracking enabled
- [ ] Logging aggregation configured
- [ ] Rate limits tuned for expected load
- [ ] Database backups scheduled
- [ ] Monitoring/alerting setup (Prometheus/Grafana)
- [ ] Health check monitoring active
- [ ] Rollback plan documented
- [ ] Disaster recovery tested

## Support

For issues:
1. Check logs: `docker logs astrobot-*`
2. Verify health: `curl http://localhost/api/health`
3. Check Sentry for application errors
4. Review nginx logs for request issues
