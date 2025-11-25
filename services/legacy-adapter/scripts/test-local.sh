#!/bin/bash
# Test Legacy Adapter Service Locally (Mac M2)
#
# This script helps you test the adapter service on your Mac before
# deploying to VPS.
#
# Usage:
#   ./test-local.sh

set -e  # Exit on error

echo "🧪 Testing Legacy Adapter Service Locally..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to script's parent directory (legacy-adapter/)
cd "$(dirname "$0")/.."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from .env.example..."

    if [ ! -f ".env.example" ]; then
        echo -e "${RED}❌ Error: .env.example not found${NC}"
        exit 1
    fi

    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file with your MSSQL connection details${NC}"
    echo "Then run this script again."
    exit 1
fi

echo -e "${GREEN}✅ Found .env file${NC}"

# Build and start the service
echo ""
echo "🔨 Building Docker image (this may take a minute on first run)..."
docker compose -f docker-compose.dev.yml build

echo ""
echo "🚀 Starting service..."
docker compose -f docker-compose.dev.yml up -d

# Wait for service to be healthy
echo ""
echo "⏳ Waiting for service to be healthy..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is healthy!${NC}"
        break
    fi

    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done
echo ""

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Service failed to become healthy${NC}"
    echo "Checking logs..."
    docker compose -f docker-compose.dev.yml logs --tail=50
    exit 1
fi

# Run health check tests
echo ""
echo "🧪 Running health check tests..."
echo ""

# Test 1: Health endpoint
echo -e "${BLUE}Test 1: Health Check${NC}"
health_response=$(curl -s http://localhost:8001/health)
echo "Response: $health_response"

if echo "$health_response" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

echo ""

# Test 2: Test database connectivity
echo -e "${BLUE}Test 2: Database Connectivity${NC}"
if echo "$health_response" | grep -q '"database":"connected"'; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    echo "Check your MSSQL connection settings in .env"
    exit 1
fi

echo ""

# Test 3: API key authentication
echo -e "${BLUE}Test 3: API Key Authentication${NC}"

# Should fail without API key
unauthorized=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/students/123)
if [ "$unauthorized" == "401" ]; then
    echo -e "${GREEN}✅ Correctly rejects requests without API key${NC}"
else
    echo -e "${RED}❌ API key authentication not working (got HTTP $unauthorized)${NC}"
fi

echo ""

# Test 4: Docs availability (in DEBUG mode)
echo -e "${BLUE}Test 4: Documentation${NC}"
docs_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/docs)
if [ "$docs_status" == "200" ]; then
    echo -e "${GREEN}✅ API documentation available at http://localhost:8001/docs${NC}"
else
    echo -e "${YELLOW}⚠️  API docs not available (this is normal in production mode)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Service Info:"
echo "  - Local URL: http://localhost:8001"
echo "  - Health: http://localhost:8001/health"
echo "  - API Docs: http://localhost:8001/docs"
echo ""
echo "🔧 Useful Commands:"
echo "  docker compose -f docker-compose.dev.yml logs -f   # View logs"
echo "  docker compose -f docker-compose.dev.yml ps        # Check status"
echo "  docker compose -f docker-compose.dev.yml down      # Stop service"
echo "  docker compose -f docker-compose.dev.yml restart   # Restart"
echo ""
echo "📝 Next Steps:"
echo "  1. Test creating a student via API (see test-api.sh)"
echo "  2. Integrate with Django (see Django integration docs)"
echo "  3. Deploy to VPS when ready (see deploy-vps.sh)"
