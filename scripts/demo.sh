#!/usr/bin/env bash
set -e

echo "=== Reliability Agent Platform Scripted Demo ==="

BASE_URL="http://localhost:8000"

echo "[1/5] Logging in as Analyst..."
ANALYST_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@example.com", "password": "change-me"}' | jq -r .access_token)

if [ "$ANALYST_TOKEN" = "null" ] || [ -z "$ANALYST_TOKEN" ]; then
  echo "Failed to obtain analyst token. Ensure server is running and default users are seeded."
  exit 1
fi
echo "Analyst authenticated successfully."

echo "[2/5] Running Agent Analysis..."
AGENT_RESP=$(curl -s -X POST "$BASE_URL/api/v1/agent/run" \
  -H "Authorization: Bearer $ANALYST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze unit 1 and calculate Weibull fit"}')
echo "Agent response received."

echo "[3/5] Fetching Pending Approval Queue..."
APPROVAL_ID=$(curl -s -X GET "$BASE_URL/api/v1/approvals/pending" \
  -H "Authorization: Bearer $ANALYST_TOKEN" | jq -r '.[0].id // empty')

if [ -n "$APPROVAL_ID" ] && [ "$APPROVAL_ID" != "null" ]; then
  echo "Found pending approval ID: $APPROVAL_ID"
  
  echo "[4/5] Logging in as Admin & Approving Request..."
  ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "change-me"}' | jq -r .access_token)

  curl -s -X POST "$BASE_URL/api/v1/approvals/$APPROVAL_ID/approve" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"comment": "Approved by demo script."}'
  echo "Approval granted."
else
  echo "No pending approvals found (or test mode)."
fi

echo "[5/5] Verifying Audit Trail Integrity..."
VERIFY_RESP=$(curl -s -X GET "$BASE_URL/api/v1/audit/verify" \
  -H "Authorization: Bearer $ANALYST_TOKEN")
echo "Audit verification response: $VERIFY_RESP"

echo "=== Demo completed successfully! ==="
