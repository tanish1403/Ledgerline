# Scripted Demo

This document outlines the scripted end-to-end user flow demonstration for the Reliability Agent Platform.

---

## Prerequisites
- Platform running locally (`make dev` or `docker compose up --build -d`).
- `curl` and `jq` installed.

---

## Demo Flow Steps

### Step 1: Log in as an Analyst
Authenticate and obtain a JWT access token for an analyst account.
```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@example.com", "password": "change-me"}' | jq -r .access_token)
echo "Analyst Token: $TOKEN"
```

### Step 2: Ask a Reliability Question & Trigger Agent
Submit an analysis prompt regarding turbofan datasets and Weibull failure analysis.
```bash
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/agent/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze unit 1 from C-MAPSS dataset and calculate Weibull shape parameter"}')
echo "$RESPONSE" | jq .
```

### Step 3: Hit the Approval Gate
Consequential actions (such as publishing production alerts or triggering model updates) pause execution and enter the approval queue.
```bash
APPROVAL_ID=$(curl -s -X GET "http://localhost:8000/api/v1/approvals/pending" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')
echo "Pending Approval ID: $APPROVAL_ID"
```

### Step 4: Approve as an Admin (Separation of Duties)
Log in as an admin/approver and approve the pending request.
```bash
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "change-me"}' | jq -r .access_token)

curl -s -X POST "http://localhost:8000/api/v1/approvals/$APPROVAL_ID/approve" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment": "Approved after manual verification."}' | jq .
```

### Step 5: Inspect Audit Trail & Trace
Verify the hash-chained audit log and OpenTelemetry trace metrics.
```bash
curl -s -X GET "http://localhost:8000/api/v1/audit/verify" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
```
