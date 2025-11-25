#!/bin/bash
# Monitor Legacy Adapter Service
#
# This script continuously monitors the health of the legacy adapter service
# and sends alerts if it becomes unhealthy.
#
# Usage:
#   ./monitor.sh [interval_seconds]
#
# Example:
#   ./monitor.sh 30  # Check every 30 seconds

INTERVAL=${1:-60}  # Default: check every 60 seconds
SERVICE_URL="http://localhost:8001"
HEALTH_ENDPOINT="$SERVICE_URL/health"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Monitoring Legacy Adapter Service"
echo "Service URL: $SERVICE_URL"
echo "Check interval: ${INTERVAL}s"
echo "Press Ctrl+C to stop"
echo ""

# Counter for consecutive failures
failures=0
MAX_FAILURES=3

while true; do
    # Get current timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Check health endpoint
    response=$(curl -sf "$HEALTH_ENDPOINT" 2>&1)
    curl_exit_code=$?

    if [ $curl_exit_code -eq 0 ]; then
        # Success - parse response
        status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        database=$(echo "$response" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)

        if [ "$status" == "healthy" ] && [ "$database" == "connected" ]; then
            echo -e "[$timestamp] ${GREEN}✅ Healthy${NC} - Database: $database"
            failures=0
        else
            echo -e "[$timestamp] ${YELLOW}⚠️  Degraded${NC} - Status: $status, Database: $database"
            failures=$((failures + 1))
        fi
    else
        # Failure - service not responding
        echo -e "[$timestamp] ${RED}❌ Unhealthy${NC} - Cannot reach service (curl exit code: $curl_exit_code)"
        failures=$((failures + 1))
    fi

    # Check if we've exceeded failure threshold
    if [ $failures -ge $MAX_FAILURES ]; then
        echo ""
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}🚨 ALERT: Service unhealthy for $failures consecutive checks!${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Troubleshooting steps:"
        echo "  1. Check if service is running: docker compose ps"
        echo "  2. View logs: docker compose logs -f"
        echo "  3. Restart service: docker compose restart"
        echo ""

        # Reset counter after alert
        failures=0
    fi

    # Wait for next check
    sleep "$INTERVAL"
done
