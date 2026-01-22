#!/bin/bash
# Test script for Docker configuration validation
# Task 21: Docker Compose Configuration

# Don't use set -e because arithmetic operations like ((PASSED++)) can return 1 when incrementing from 0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PASSED=0
FAILED=0

echo "=============================================="
echo "Docker Configuration Validation Tests"
echo "=============================================="
echo ""

# Test 1: Check docker-compose.yml exists
echo -n "Test 1: docker-compose.yml exists... "
if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 2: Check Dockerfile exists at project root
echo -n "Test 2: Dockerfile exists at project root... "
if [ -f "$PROJECT_ROOT/Dockerfile" ]; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 3: Check frontend/Dockerfile exists
echo -n "Test 3: frontend/Dockerfile exists... "
if [ -f "$PROJECT_ROOT/frontend/Dockerfile" ]; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 4: Check .dockerignore exists
echo -n "Test 4: .dockerignore exists... "
if [ -f "$PROJECT_ROOT/.dockerignore" ]; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 5: Validate docker-compose.yml syntax with docker compose config
echo -n "Test 5: docker-compose.yml syntax validation... "
if command -v docker &> /dev/null; then
    cd "$PROJECT_ROOT"
    if docker compose config > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAILED${NC}"
        echo "  Error: docker compose config failed"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}SKIPPED${NC} (docker not available)"
fi

# Test 6: Check docker-compose.yml contains required services
echo -n "Test 6: docker-compose.yml contains postgres service... "
if grep -q "postgres:" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

echo -n "Test 7: docker-compose.yml contains redis service... "
if grep -q "redis:" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

echo -n "Test 8: docker-compose.yml contains fastapi service... "
if grep -q "fastapi:" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

echo -n "Test 9: docker-compose.yml contains celery_worker service... "
if grep -q "celery_worker:" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

echo -n "Test 10: docker-compose.yml contains react service... "
if grep -q "react:" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 11: Check for health checks
echo -n "Test 11: docker-compose.yml contains health checks... "
if grep -q "healthcheck:" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 12: Check Dockerfile uses Python 3.11+
echo -n "Test 12: Dockerfile uses Python 3.11+... "
if grep -qE "python:3\.1[1-9]|python:3\.[2-9][0-9]" "$PROJECT_ROOT/Dockerfile"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 13: Check frontend Dockerfile uses Node 20
echo -n "Test 13: frontend/Dockerfile uses Node 20... "
if grep -qE "node:20" "$PROJECT_ROOT/frontend/Dockerfile"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 14: Check docker-compose contains DATABASE_URL
echo -n "Test 14: docker-compose.yml contains DATABASE_URL... "
if grep -q "DATABASE_URL" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 15: Check docker-compose contains REDIS_URL
echo -n "Test 15: docker-compose.yml contains REDIS_URL... "
if grep -q "REDIS_URL" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 16: Check docker-compose has depends_on for fastapi
echo -n "Test 16: fastapi service has depends_on configuration... "
if grep -A 20 "fastapi:" "$PROJECT_ROOT/docker-compose.yml" | grep -q "depends_on:"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 17: Check .dockerignore excludes node_modules
echo -n "Test 17: .dockerignore excludes node_modules... "
if grep -q "node_modules" "$PROJECT_ROOT/.dockerignore"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 18: Check .dockerignore excludes .venv
echo -n "Test 18: .dockerignore excludes .venv... "
if grep -q ".venv" "$PROJECT_ROOT/.dockerignore"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 19: Check .dockerignore excludes __pycache__
echo -n "Test 19: .dockerignore excludes __pycache__... "
if grep -q "__pycache__" "$PROJECT_ROOT/.dockerignore"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 20: Check docker-compose has volume mounts for hot reload
echo -n "Test 20: docker-compose.yml has volume mounts for hot reload... "
if grep -q "volumes:" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

# Test 21: Check celery_worker has proper command
echo -n "Test 21: celery_worker has celery command... "
if grep -A 15 "celery_worker:" "$PROJECT_ROOT/docker-compose.yml" | grep -qE "celery.*worker"; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
fi

echo ""
echo "=============================================="
echo "Test Summary"
echo "=============================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
