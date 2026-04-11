#!/bin/bash

# run_all_tests.sh - Master script to run all project tests
# Usage: ./testing/scripts/run_all_tests.sh

set -e

echo "🧪 AstroBot Testing Suite - Complete Test Run"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_COVERAGE=60
FRONTEND_COVERAGE=60

# Test counters
PASSED=0
FAILED=0

# Function to run a test suite
run_tests() {
    local test_name=$1
    local test_command=$2

    echo -e "${YELLOW}Running: $test_name${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✓ $test_name passed${NC}\n"
        ((PASSED++))
    else
        echo -e "${RED}✗ $test_name failed${NC}\n"
        ((FAILED++))
    fi
}

# Step 1: Backend Unit Tests
echo -e "${YELLOW}=== BACKEND UNIT TESTS ===${NC}"
run_tests "Backend Auth Tests" "pytest testing/backend/test_auth.py -v --tb=short"
run_tests "Backend Chat Tests" "pytest testing/backend/test_chat.py -v --tb=short"
run_tests "Backend RAG Tests" "pytest testing/backend/test_rag_pipeline.py -v --tb=short"

# Step 2: Frontend Unit Tests
echo -e "${YELLOW}=== FRONTEND UNIT TESTS ===${NC}"
run_tests "Frontend Component Tests" "npm run test:frontend -- --testPathPattern=components --passWithNoTests"
run_tests "Frontend Page Tests" "npm run test:frontend -- --testPathPattern=pages --passWithNoTests"
run_tests "Frontend Hook Tests" "npm run test:frontend -- --testPathPattern=hooks --passWithNoTests"

# Step 3: Integration Tests
echo -e "${YELLOW}=== INTEGRATION TESTS ===${NC}"
run_tests "E2E Chat Flow" "pytest testing/integration/e2e_chat_flow.py -v --tb=short"

# Step 4: Code Coverage
echo -e "${YELLOW}=== CODE COVERAGE ===${NC}"
echo "Generating backend coverage report..."
pytest testing/backend/ \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=$BACKEND_COVERAGE \
    -q || echo -e "${RED}Coverage check failed${NC}"

echo ""
echo "Generating frontend coverage report..."
npm run test:frontend -- --coverage --passWithNoTests || echo -e "${RED}Frontend coverage check failed${NC}"

# Step 5: Linting and Code Quality
echo -e "${YELLOW}=== CODE QUALITY ===${NC}"
echo "Backend code quality checks..."
if command -v black &> /dev/null; then
    black --check testing/backend/ --quiet || echo "Black formatting issues found"
else
    echo "Black not installed, skipping format check"
fi

if command -v pylint &> /dev/null; then
    pylint testing/backend/ --exit-zero || echo "Pylint warnings found"
else
    echo "Pylint not installed, skipping lint check"
fi

echo "Frontend code quality checks..."
npm run lint:frontend -- --no-fix || echo "ESLint warnings found"

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}Test Run Complete${NC}"
echo "=============================================="
echo "Passed: $((PASSED))"
echo "Failed: $((FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
