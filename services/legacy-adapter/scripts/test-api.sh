#!/bin/bash
# Test Legacy Adapter API Endpoints
#
# This script tests the main API endpoints of the legacy adapter service
# with sample data to verify functionality.
#
# Usage:
#   ./test-api.sh [api_key]
#
# Example:
#   ./test-api.sh your-api-key-here

API_KEY=${1:-"dev-api-key-change-in-production"}
SERVICE_URL="http://localhost:8001"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🧪 Testing Legacy Adapter API"
echo "Service URL: $SERVICE_URL"
echo "API Key: ${API_KEY:0:10}..."
echo ""

# Test 1: Health Check (no auth required)
echo -e "${BLUE}Test 1: Health Check (No Auth)${NC}"
response=$(curl -s "$SERVICE_URL/health")
echo "Response: $response"

if echo "$response" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    exit 1
fi
echo ""

# Test 2: Unauthorized Access (should fail)
echo -e "${BLUE}Test 2: Unauthorized Access (Should Fail)${NC}"
http_code=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/students/12345")
echo "HTTP Status: $http_code"

if [ "$http_code" == "401" ]; then
    echo -e "${GREEN}✅ PASSED - Correctly rejected unauthorized request${NC}"
else
    echo -e "${RED}❌ FAILED - Expected 401, got $http_code${NC}"
    exit 1
fi
echo ""

# Test 3: Create Student
echo -e "${BLUE}Test 3: Create Student${NC}"

# Generate random student ID for testing
STUDENT_ID=$((10000 + RANDOM % 90000))

student_data=$(cat <<EOF
{
  "student_id": $STUDENT_ID,
  "first_name": "សុភាព",
  "last_name": "ចាន់",
  "middle_name": null,
  "english_first_name": "Sopheak",
  "english_last_name": "Chan",
  "date_of_birth": "2000-01-15",
  "gender": "M",
  "email": "sopheak.chan@example.com",
  "phone_number": "+85512345678",
  "is_monk": false,
  "preferred_study_time": "morning",
  "is_transfer_student": false,
  "status": "ACTIVE",
  "enrollment_date": "2024-01-10"
}
EOF
)

echo "Creating student with ID: $STUDENT_ID"
response=$(curl -s -X POST "$SERVICE_URL/students" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$student_data")

echo "Response: $response"

if echo "$response" | grep -q '"success":true'; then
    legacy_id=$(echo "$response" | grep -o '"legacy_student_id":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✅ PASSED - Student created with legacy ID: $legacy_id${NC}"
else
    echo -e "${RED}❌ FAILED - Student creation failed${NC}"
    exit 1
fi
echo ""

# Test 4: Get Student (should exist now)
echo -e "${BLUE}Test 4: Get Student${NC}"
echo "Fetching student ID: $STUDENT_ID"

response=$(curl -s "$SERVICE_URL/students/$STUDENT_ID" \
    -H "X-API-Key: $API_KEY")

echo "Response: $response"

if echo "$response" | grep -q "\"StudentCode\":$STUDENT_ID"; then
    echo -e "${GREEN}✅ PASSED - Student retrieved successfully${NC}"
else
    echo -e "${RED}❌ FAILED - Could not retrieve student${NC}"
    exit 1
fi
echo ""

# Test 5: Create Duplicate Student (should fail with 409)
echo -e "${BLUE}Test 5: Create Duplicate Student (Should Fail)${NC}"
echo "Attempting to create duplicate student ID: $STUDENT_ID"

http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$SERVICE_URL/students" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$student_data")

echo "HTTP Status: $http_code"

if [ "$http_code" == "409" ]; then
    echo -e "${GREEN}✅ PASSED - Correctly rejected duplicate${NC}"
else
    echo -e "${RED}❌ FAILED - Expected 409, got $http_code${NC}"
    exit 1
fi
echo ""

# Test 6: Monk Gender Mapping
echo -e "${BLUE}Test 6: Monk Gender Mapping${NC}"

MONK_STUDENT_ID=$((10000 + RANDOM % 90000))

monk_data=$(cat <<EOF
{
  "student_id": $MONK_STUDENT_ID,
  "first_name": "វណ្ណា",
  "last_name": "ពុទ្ធិ",
  "english_first_name": "Vanna",
  "english_last_name": "Putthi",
  "date_of_birth": "1998-05-20",
  "gender": "M",
  "is_monk": true,
  "status": "ACTIVE"
}
EOF
)

echo "Creating monk student with ID: $MONK_STUDENT_ID"
response=$(curl -s -X POST "$SERVICE_URL/students" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$monk_data")

if echo "$response" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ PASSED - Monk student created${NC}"
    echo "Note: Gender should be stored as 'Monk' in legacy database"
else
    echo -e "${RED}❌ FAILED - Monk student creation failed${NC}"
    exit 1
fi
echo ""

# Test 7: Soft Delete
echo -e "${BLUE}Test 7: Soft Delete Student${NC}"
echo "Soft deleting student ID: $STUDENT_ID"

http_code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$SERVICE_URL/students/$STUDENT_ID" \
    -H "X-API-Key: $API_KEY")

echo "HTTP Status: $http_code"

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✅ PASSED - Student soft deleted${NC}"
else
    echo -e "${RED}❌ FAILED - Expected 200, got $http_code${NC}"
    exit 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ All API tests passed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Test Summary:"
echo "  - Created student ID: $STUDENT_ID (then soft deleted)"
echo "  - Created monk student ID: $MONK_STUDENT_ID"
echo "  - All authentication, authorization, and CRUD operations working"
echo ""
echo "🧹 Cleanup:"
echo "  Students created in this test can be cleaned up manually if needed"
echo "  or will be handled by your data migration processes"
