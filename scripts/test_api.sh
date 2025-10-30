#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-https://backend-skum.onrender.com}

echo "Testing BASE_URL=$BASE_URL"

echo "[health]"
curl -sS "$BASE_URL/api/health" | jq . || true

EMAIL="auto_$(date +%s)@example.com"
PASS="Password123!"

echo "[register]"
curl -sS -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | jq . || true

echo "[login_fst]"
curl -sS -c cookies.txt -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | jq . || true

echo "[forms_list_session]"
curl -sS -b cookies.txt "$BASE_URL/api/forms" | jq . || true

echo "[login_custom]"
TOKEN=$(curl -sS -X POST "$BASE_URL/api/auth/signin" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | jq -r .token)
echo "TOKEN=${TOKEN:0:10}..."

echo "[form_create]"
FORM_ID=$(curl -sS -b cookies.txt -X POST "$BASE_URL/api/forms" \
  -H "Content-Type: application/json" \
  -d '{"title":"Formulaire Auto","description":"Test POC","settings":{"theme":"blue"}}' | jq -r .data.form_id)
if [ "$FORM_ID" = "null" ] || [ -z "$FORM_ID" ]; then
  FORM_ID=$(curl -sS -X POST "$BASE_URL/api/forms" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"title":"Formulaire Auto","description":"Test POC","settings":{"theme":"blue"}}' | jq -r .data.form_id)
fi
echo "FORM_ID=$FORM_ID"

echo "[question_create]"
QID=$(curl -sS -b cookies.txt -X POST "$BASE_URL/api/forms/$FORM_ID/questions" \
  -H "Content-Type: application/json" \
  -d '{"type":"text","text":"Votre nom?","required":true,"order_index":0}' | jq -r .question_id || true)
if [ "$QID" = "null" ] || [ -z "$QID" ]; then
  QID=$(curl -sS -X POST "$BASE_URL/api/forms/$FORM_ID/questions" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"type":"text","text":"Votre nom?","required":true,"order_index":0}' | jq -r .question_id || true)
fi
echo "QID=$QID"

echo "[response_submit]"
curl -sS -b cookies.txt -X POST "$BASE_URL/api/forms/$FORM_ID/responses" \
  -H "Content-Type: application/json" \
  -d '{"answers":{}}' | jq . || true

echo "[analytics]"
curl -sS -b cookies.txt "$BASE_URL/api/forms/$FORM_ID/analytics" | jq . || true


