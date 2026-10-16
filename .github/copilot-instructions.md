# Agent rules: reliability-agent-platform

You are helping build a self-hosted AI agent platform that analyzes engineering reliability data.
The owner will be asked about every line of this code in job interviews. Keep it simple, readable and
explainable. Prefer boring, well-known solutions over clever ones.

## Read first, every session
1. `docs/PLAN.md`: scope, architecture, milestones.
2. `docs/PROGRESS.md`: what is done. Update it when a milestone is finished.
3. `docs/prompts/NN_*.md`: the task for the current milestone. Work on ONE milestone at a time.

## Stack
Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, PostgreSQL 16 + pgvector, Redis, Celery,
LangGraph (milestone 6 only), OpenTelemetry, pytest, ruff, Docker Compose, Helm + kind, GitHub Actions.
The LLM is reached through an OpenAI-compatible endpoint (OmniRoute or Ollama) set in `.env`
(`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`). Never hard-code a provider, key or model name.

## Commands
- `make install`, `make dev`, `make test`, `make lint`, `make fmt`
- `make up` / `make down`: full stack with Docker Compose

## Workflow for every change
1. Restate the task and list the files you will touch. Keep each step to about 5 files or fewer.
2. Write or update tests first. Run them and confirm they fail for the right reason.
3. Implement the smallest change that makes them pass.
4. Run `make lint` and `make test`. Fix failures properly, never by weakening a test or a lint rule.
5. Show a short summary of the diff, then commit with a conventional message
   (`feat:`, `fix:`, `test:`, `docs:`, `chore:`). One logical change per commit.

## Safety rules (never break these)
- Never read, print or commit `.env` or any secret. Only `.env.example` is committed.
- Never run destructive commands without asking first: `rm -rf` outside the repo, `docker system prune`,
  `git push --force`, `DROP DATABASE`, deleting volumes.
- Never add a dependency without asking. Say what it is, why it is needed, and its licence.
- Never weaken authentication, RBAC, the approval gate, or the audit log to make a test pass.
- Model output is untrusted input. Validate it with Pydantic. Never `eval`/`exec` it, never pass it to a shell.
- SQL produced by a model runs read-only, on one statement, against an allow-list of tables, with a timeout.
- File paths produced by a model are resolved inside a sandbox directory. Reject `..` and absolute paths.
- Never call the network from tests. Use the `FakeLLM` test double.

## Code style
- Type hints everywhere. Small functions. A docstring says WHY, not what.
- No dead code, no commented-out code, no TODOs without an issue note in `docs/PROGRESS.md`.
- Tests are named `test_*`, live in `tests/`, and cover the failure path as well as the happy path.

## Honesty
- If you are unsure of a library API or a CLI flag, check the installed version (`pip show`, `--help`)
  or say you are unsure. Do not invent function names.
- If a task cannot be finished, say what is missing instead of faking it.
- Tell the owner when something you wrote is hard to explain, so they can ask you to simplify it.
