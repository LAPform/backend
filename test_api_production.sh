#!/bin/bash

# Script de test complet de l'API FormForge sur Render
# URL: https://backend-skum.onrender.com

API_URL="https://backend-skum.onrender.com"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="Test123!@#"
TEST_NAME="Test User"

# Couleurs pour l'output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les résultats
print_test() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}TEST: $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  INFO: $1${NC}"
}

# Fonction pour extraire le token
extract_token() {
    echo "$1" | grep -o '"authentication_token":"[^"]*"' | cut -d'"' -f4
}

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          TEST COMPLET API FORMFORGE - PRODUCTION          ║"
echo "║                 backend-skum.onrender.com                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Variables pour stocker les résultats
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# TEST 1: Health Check
print_test "1. Health Check - /api/health"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY"

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API is healthy"
    PASSED_TESTS=$((PASSED_TESTS + 1))

    # Vérifier la version
    VERSION=$(echo "$BODY" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    SECURITY=$(echo "$BODY" | grep -o '"security":"[^"]*"' | cut -d'"' -f4)
    echo "Version: $VERSION"
    echo "Security: $SECURITY"
else
    print_error "API health check failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 2: Signup (Inscription)
print_test "2. User Signup - POST /api/auth/signup"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

print_info "Creating user: $TEST_EMAIL"

SIGNUP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"name\": \"$TEST_NAME\"
  }")

HTTP_CODE=$(echo "$SIGNUP_RESPONSE" | tail -n1)
BODY=$(echo "$SIGNUP_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY"

if [ "$HTTP_CODE" = "201" ]; then
    print_success "User created successfully"
    PASSED_TESTS=$((PASSED_TESTS + 1))

    # Extraire le token
    SIGNUP_TOKEN=$(extract_token "$BODY")
    if [ -n "$SIGNUP_TOKEN" ]; then
        print_success "Token received: ${SIGNUP_TOKEN:0:20}..."
        TOKEN="$SIGNUP_TOKEN"
    else
        print_error "No token in signup response"
    fi
else
    print_error "User creation failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 3: Signin (Connexion)
print_test "3. User Signin - POST /api/auth/signin"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

print_info "Logging in with: $TEST_EMAIL"

SIGNIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/signin" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

HTTP_CODE=$(echo "$SIGNIN_RESPONSE" | tail -n1)
BODY=$(echo "$SIGNIN_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY"

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Login successful"
    PASSED_TESTS=$((PASSED_TESTS + 1))

    # Extraire le token
    SIGNIN_TOKEN=$(extract_token "$BODY")
    if [ -n "$SIGNIN_TOKEN" ]; then
        print_success "Token received: ${SIGNIN_TOKEN:0:20}..."
        TOKEN="$SIGNIN_TOKEN"
    else
        print_error "No token in signin response"
    fi
else
    print_error "Login failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 4: Get Current User (endpoint protégé)
print_test "4. Get Current User - GET /api/auth/me"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -n "$TOKEN" ]; then
    print_info "Using token: ${TOKEN:0:20}..."

    ME_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/auth/me" \
      -H "Authentication-Token: $TOKEN")

    HTTP_CODE=$(echo "$ME_RESPONSE" | tail -n1)
    BODY=$(echo "$ME_RESPONSE" | head -n-1)

    echo "HTTP Status: $HTTP_CODE"
    echo "Response: $BODY"

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "User info retrieved successfully"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "Failed to retrieve user info"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    print_error "No token available, skipping test"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 5: Create Form (endpoint protégé)
print_test "5. Create Form - POST /api/forms"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -n "$TOKEN" ]; then
    FORM_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/forms" \
      -H "Content-Type: application/json" \
      -H "Authentication-Token: $TOKEN" \
      -d "{
        \"title\": \"Test Form $(date +%s)\",
        \"description\": \"Test form created by automated test script\"
      }")

    HTTP_CODE=$(echo "$FORM_RESPONSE" | tail -n1)
    BODY=$(echo "$FORM_RESPONSE" | head -n-1)

    echo "HTTP Status: $HTTP_CODE"
    echo "Response: $BODY"

    if [ "$HTTP_CODE" = "201" ]; then
        print_success "Form created successfully"
        PASSED_TESTS=$((PASSED_TESTS + 1))

        # Extraire le form_id
        FORM_ID=$(echo "$BODY" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        print_info "Form ID: $FORM_ID"
    else
        print_error "Form creation failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    print_error "No token available, skipping test"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 6: List Forms (endpoint protégé)
print_test "6. List Forms - GET /api/forms"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -n "$TOKEN" ]; then
    FORMS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/forms" \
      -H "Authentication-Token: $TOKEN")

    HTTP_CODE=$(echo "$FORMS_RESPONSE" | tail -n1)
    BODY=$(echo "$FORMS_RESPONSE" | head -n-1)

    echo "HTTP Status: $HTTP_CODE"
    echo "Response: $BODY" | head -c 500
    echo "..."

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Forms retrieved successfully"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "Failed to retrieve forms"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    print_error "No token available, skipping test"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 7: Test sans token (doit échouer)
print_test "7. Security Test - Access protected endpoint without token"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/forms")
HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | tail -n1)
BODY=$(echo "$UNAUTH_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY"

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    print_success "Security working: Unauthorized access blocked"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    print_error "Security issue: Endpoint accessible without token"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 8: Test CORS headers
print_test "8. CORS Headers Test"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

CORS_RESPONSE=$(curl -s -I -X OPTIONS "$API_URL/api/health" \
  -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: GET")

echo "$CORS_RESPONSE"

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    print_success "CORS headers present"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    print_error "CORS headers missing or misconfigured"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 9: Test changement de mot de passe
print_test "9. Change Password - POST /api/auth/change-password"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -n "$TOKEN" ]; then
    NEW_PASSWORD="NewTest123!@#"

    CHANGE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/change-password" \
      -H "Content-Type: application/json" \
      -H "Authentication-Token: $TOKEN" \
      -d "{
        \"current_password\": \"$TEST_PASSWORD\",
        \"new_password\": \"$NEW_PASSWORD\"
      }")

    HTTP_CODE=$(echo "$CHANGE_RESPONSE" | tail -n1)
    BODY=$(echo "$CHANGE_RESPONSE" | head -n-1)

    echo "HTTP Status: $HTTP_CODE"
    echo "Response: $BODY"

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Password changed successfully"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "Password change failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    print_error "No token available, skipping test"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TEST 10: Logout
print_test "10. Logout - POST /api/auth/logout"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -n "$TOKEN" ]; then
    LOGOUT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/logout" \
      -H "Authentication-Token: $TOKEN")

    HTTP_CODE=$(echo "$LOGOUT_RESPONSE" | tail -n1)
    BODY=$(echo "$LOGOUT_RESPONSE" | head -n-1)

    echo "HTTP Status: $HTTP_CODE"
    echo "Response: $BODY"

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Logout successful"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "Logout failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    print_error "No token available, skipping test"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# RÉSULTATS FINAUX
echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    RÉSULTATS DES TESTS                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "Total tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Tests réussis: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Tests échoués: ${RED}$FAILED_TESTS${NC}"

SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
echo -e "Taux de réussite: ${GREEN}${SUCCESS_RATE}%${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✅ TOUS LES TESTS SONT PASSÉS ! L'API FONCTIONNE PARFAITEMENT !${NC}\n"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  CERTAINS TESTS ONT ÉCHOUÉ. VÉRIFIER LES LOGS CI-DESSUS.${NC}\n"
    exit 1
fi
