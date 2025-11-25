#!/bin/bash
# Deploy Legacy Adapter Service to VPS
#
# This script deploys the legacy adapter service to your secure VPS.
# Run this FROM YOUR VPS after copying the service files there.
#
# Usage:
#   ./deploy-vps.sh

set -e  # Exit on error

echo "🚀 Deploying Legacy Adapter Service to VPS..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.vps.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.vps.yml not found${NC}"
    echo "Please run this script from the legacy-adapter directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from .env.example..."

    if [ ! -f ".env.example" ]; then
        echo -e "${RED}❌ Error: .env.example not found${NC}"
        exit 1
    fi

    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual configuration${NC}"
    echo "Then run this script again."
    exit 1
fi

# Validate required environment variables
source .env

required_vars=("LEGACY_DB_HOST" "LEGACY_DB_USER" "LEGACY_DB_PASSWORD" "LEGACY_DB_NAME" "API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" == "your-"* ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}❌ Error: Missing or incomplete configuration${NC}"
    echo "Please set the following variables in .env:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo -e "${GREEN}✅ Configuration validated${NC}"

# Stop existing service if running
if docker compose -f docker-compose.vps.yml ps | grep -q "legacy_adapter"; then
    echo "🛑 Stopping existing service..."
    docker compose -f docker-compose.vps.yml down
fi

# Build and start the service
echo "🔨 Building Docker image..."
docker compose -f docker-compose.vps.yml build --no-cache

echo "🚀 Starting service..."
docker compose -f docker-compose.vps.yml up -d

# Wait for service to be healthy
echo "⏳ Waiting for service to be healthy..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is healthy!${NC}"
        break
    fi

    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Service failed to become healthy${NC}"
    echo "Checking logs..."
    docker compose -f docker-compose.vps.yml logs
    exit 1
fi

# Show service status
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.vps.yml ps

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Service is running at:"
echo "  - http://localhost:8001 (local)"
echo "  - http://$(hostname -I | awk '{print $1}'):8001 (network)"
echo ""
echo "Useful commands:"
echo "  docker compose -f docker-compose.vps.yml logs -f     # View logs"
echo "  docker compose -f docker-compose.vps.yml ps          # Check status"
echo "  docker compose -f docker-compose.vps.yml down        # Stop service"
echo "  docker compose -f docker-compose.vps.yml restart     # Restart service"
echo ""
echo "Next steps:"
echo "  1. Set up SSL with Caddy or Nginx (see DEPLOYMENT.md)"
echo "  2. Configure Windows firewall (run lockdown-mssql.ps1 on Windows machine)"
echo "  3. Update Django .env with LEGACY_ADAPTER_URL and API_KEY"
