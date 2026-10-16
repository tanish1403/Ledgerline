# Reliability Agent Platform

A self-hosted AI agent platform for engineering reliability analysis. An LLM agent queries data through
authorized tools, reports numbers that are re-computed and checked by code, and cannot take consequential
actions without a human approving them. Everything is logged to an append-only audit trail.

Everything runs locally with open-source tools. No paid services.

> Status: skeleton. See `docs/PROGRESS.md` for what is built.

## Quick start

```bash
cp .env.example .env          # then edit the values
make install                  # creates .venv and installs dependencies
make test                     # health-check test should pass
make dev                      # http://localhost:8000/docs
```

Full stack (API + Postgres/pgvector + Redis):

```bash
docker compose up --build
curl http://localhost:8000/health
```

## Building this with an AI coding agent

1. Read `docs/SETUP.md` (VS Code + Cline + OmniRoute, plus Copilot and Antigravity notes).
2. Open `docs/prompts/00_kickoff.md` and paste it into the agent.
3. Then paste `docs/prompts/01_*.md`, `02_*.md` and so on, one at a time, reviewing every diff.

## Layout

| Folder | Purpose |
| --- | --- |
| `api/` | FastAPI app: auth, RBAC, routes |
| `agents/` | Agent loop and the approval workflow |
| `tools/` | Tools the agent may call, each with a typed schema |
| `validators/` | Deterministic re-computation of numbers the model reports |
| `audit/` | Append-only, hash-chained audit log |
| `rag/` | Document ingestion, retrieval, citations |
| `evals/` | Golden tasks and regression checks run in CI |
| `observability/` | OpenTelemetry, Prometheus and Grafana configuration |
| `deploy/` | Dockerfile, Helm chart, Kubernetes manifests |
| `docs/` | Plan, progress, setup guide, prompts, threat model |

## Milestones

See `docs/PLAN.md`. Eleven milestones, each with its own prompt in `docs/prompts/`.
