# Threat Model

This document outlines the security assets, actors, trust boundaries, risks, mitigations, and verifying test files for the Reliability Agent Platform.

---

## 1. Assets
- **Database (`reliability`, `reliability_test`)**: Relational tables holding user accounts, datasets, inspection logs, RAG document embeddings (`pgvector`), and approval queues.
- **Audit Log**: Tamper-evident hash-chained audit events tracking all critical API requests, agent tool executions, and approval decisions.
- **Secrets**: JWT signing secret (`JWT_SECRET`), PostgreSQL credentials, and LLM API keys (`LLM_API_KEY`).

---

## 2. Actors
- **Unauthenticated User**: External client without a valid JWT token.
- **Analyst**: Authenticated user with role `analyst`. Can upload datasets, run analysis agent loops, and request consequential actions.
- **Approver / Admin**: Authenticated user with role `approver` or `admin`. Can approve/reject pending consequential actions (subject to separation of duties).
- **LLM Agent**: Internal reasoning loop interacting with tools and processing untrusted model outputs.

---

## 3. Trust Boundaries
1. **API Perimeter**: HTTP requests entering FastAPI (`api/main.py`) requiring authentication and RBAC verification.
2. **LLM Boundary**: External OpenAI-compatible model endpoint (OmniRoute or Ollama) providing untrusted text outputs.
3. **Database & Tool Sandbox**: SQL query execution and file path resolution sandbox preventing unauthorized access or OS command execution.

---

## 4. Threat Analysis

| Threat / Attack Vector | Risk | Mitigation Control & File Path | Verifying Test File |
| --- | --- | --- | --- |
| **Prompt Injection** | Malicious instructions embedded in dataset texts or user queries manipulate the agent into unauthorized actions. | Strict Pydantic input/output validation, tool execution whitelist, and human approval gate (`agents/workflow.py`, `validators/recompute.py`). | `tests/test_approvals.py` |
| **Tool Abuse** | An agent or compromised account executing unauthorized tools (e.g. dropping tables or modifying system state). | Role-based tool permissions (`api/auth/rbac.py`) and explicit tool registry whitelisting (`tools/`). | `tests/test_audit.py` |
| **SQL Injection** | Attacker injects malicious SQL statements through model outputs or query parameters. | Parameterized SQLAlchemy queries (`api/db/`) and read-only execution constraints. | `tests/test_reliability.py` |
| **Path Traversal** | Accessing sensitive system files via relative paths (e.g., `../../etc/passwd`). | Strict path sandbox resolution rejecting `..` and absolute paths (`rag/ingest.py`). | `tests/test_rag.py` |
| **Privilege Escalation** | Low-privilege analyst performing administrative actions or approving their own requests. | Separation of duties enforcement requiring a different user ID for approval (`api/routers/approvals.py`). | `tests/test_approvals.py` |
| **Approval Bypass** | Bypassing the human approval gate for consequential actions. | LangGraph workflow interruption state machine (`agents/workflow.py`). | `tests/test_approvals.py` |
| **Audit Tampering** | Modifying or deleting audit log entries to cover tracks. | Append-only hash-chained event storage where each event hashes the previous event signature (`audit/chain.py`). | `tests/test_audit.py` |
| **Secret Leakage** | Exposing API keys or database passwords in logs or version control. | Environment variable isolation (`.env` git-ignored, `.env.example` committed) and Pydantic SecretStr. | `tests/test_observability.py` |
| **Data Exfiltration via LLM** | Sending sensitive internal data to external upstream LLM providers. | Optional local Ollama inference support and sanitized RAG chunking filters (`rag/`). | `tests/test_rag.py` |
