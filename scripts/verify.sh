#!/bin/bash
# AstroBot Verification Script
# Run this after installing dependencies to verify everything is working

set -e

echo "================================================"
echo "🔍 AstroBot Implementation Verification"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# Function to check if Python module exists
check_module() {
    python -c "import $1" 2>/dev/null
    check_status "Module '$1' installed"
}

echo "1️⃣  Checking Python Dependencies..."
echo ""

# Phase 1: Error Tracking & Logging
echo "   Phase 1: Error Tracking"
check_module "sentry_sdk"
check_module "pythonjsonlogger"

# Phase 2: Rate Limiting
echo "   Phase 2: Rate Limiting"
check_module "slowapi"

# Core dependencies
echo "   Core Dependencies"
check_module "fastapi"
check_module "uvicorn"
check_module "postgresql"
check_module "chromadb"
check_module "sentence_transformers"

echo ""
echo "2️⃣  Checking Project Structure..."
echo ""

# Check critical files
for file in api_server.py config.py database/db.py requirements.txt; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} Found: $file"
    else
        echo -e "${RED}❌${NC} Missing: $file"
        exit 1
    fi
done

echo ""
echo "3️⃣  Checking Phase 1: Error Tracking"
echo ""

if [ -d "log_config" ]; then
    echo -e "${GREEN}✅${NC} log_config/ directory exists"
else
    echo -e "${RED}❌${NC} log_config/ directory missing"
    exit 1
fi

if [ -f "log_config/__init__.py" ]; then
    echo -e "${GREEN}✅${NC} Logging module created"
else
    echo -e "${RED}❌${NC} Logging module missing"
    exit 1
fi

if [ -f "log_config/sentry_config.py" ]; then
    echo -e "${GREEN}✅${NC} Sentry configuration created"
else
    echo -e "${RED}❌${NC} Sentry configuration missing"
    exit 1
fi

echo ""
echo "4️⃣  Checking Phase 2: Rate Limiting"
echo ""

if [ -f "middleware/rate_limiter.py" ]; then
    echo -e "${GREEN}✅${NC} Rate limiter middleware created"
else
    echo -e "${RED}❌${NC} Rate limiter middleware missing"
    exit 1
fi

echo ""
echo "5️⃣  Checking Phase 3: Tagging/Classification"
echo ""

# Check database schema by attempting to import
python -c "from database.db import create_tag, get_all_tags, add_tag_to_document" 2>/dev/null
check_status "Tag functions available"

python -c "from database.db import set_document_classification, get_document_classification" 2>/dev/null
check_status "Classification functions available"

echo ""
echo "6️⃣  Checking Phase 4: Load Balancing"
echo ""

for file in deployment/nginx.conf deployment/docker-compose.lb.yml Dockerfile; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} Found: $file"
    else
        echo -e "${RED}❌${NC} Missing: $file"
    fi
done

echo ""
echo "7️⃣  Testing Python Imports..."
echo ""

python -c "from log_config import setup_logging, get_logger" 2>/dev/null
check_status "Logging imports work"

python -c "from middleware.rate_limiter import get_limiter" 2>/dev/null
check_status "Rate limiter imports work"

python -c "from database.db import init_db, create_tag" 2>/dev/null
check_status "Database imports work"

echo ""
echo "================================================"
echo -e "${GREEN}✅ All Checks Passed!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Configure .env file (copy from .env.example or create new)"
echo "  2. Start API server: python api_server.py"
echo "  3. Test at: http://localhost:8000/api/health"
echo ""
echo "Documentation:"
echo "  - QUICKSTART.md - Quick setup guide"
echo "  - IMPLEMENTATION_SUMMARY.md - Full implementation details"
echo "  - deployment/LOAD_BALANCING.md - Load balancing guide"
echo ""
