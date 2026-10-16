# Progress

Tick a box only when its acceptance criteria in the milestone prompt are met and CI is green.
Write anything left undone under "Open items".

- [x] 0. Skeleton: health endpoint, Docker, Compose, CI, agent rules
- [x] 1. Auth, roles, datasets API
- [x] 2. Redis cache and background jobs
- [x] 3. Tool-calling agent
- [x] 4. Reliability stats and validators
- [x] 5. Audit log
- [ ] 6. Approval gate and rollback
- [ ] 7. RAG module
- [ ] 8. Evaluation harness in CI
- [ ] 9. Observability
- [ ] 10. Deployment and security scans
- [ ] 11. Docs, threat model, demo, resume

## Open items

(none)

## Decisions log

Record choices an interviewer might ask about: what you chose, what you rejected, why.

| Date       | Decision                                                   | Why                                                                                |
| ---------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 2026-10-16 | Password hashing: bcrypt over argon2-cffi                  | Pre-built wheels on Windows; simpler API; familiar to interviewers                 |
| 2026-10-16 | DB driver: psycopg[binary] (psycopg3) over psycopg2-binary | psycopg3 is the current release; binary wheel skips C compilation on all platforms |
| 2026-10-16 | JWT library: PyJWT over python-jose                        | Simpler, actively maintained, no hidden transitive crypto dependencies             |

- Milestone 5 completed: Tamper-evident hash-chained audit log, event redactor, audit verification endpoint, and documentation (`docs/audit.md`).
- Milestone 6 completed: Human approval gate with LangGraph interruption, inspection flagging tool, Alembic migration, separation of duties, rollback, audit logging, and documentation (`docs/approvals.md`).
- Milestone 7 completed: Hybrid RAG module with pgvector, sentence-transformers, verified citations, confidence flag, role-based chunk filtering, versioning, and documentation (`docs/rag.md`).



# Milestone 4 completed: Reliability statistics tools, C-MAPSS dataset models & loader, and deterministic claim validator.

| 2026-10-16 | Test DB isolation: SAVEPOINT rollback over pytest-postgresql | No extra dependency; works against CI's existing Postgres service container |
| 2026-10-16 | Alembic env.py pulls DATABASE_URL from settings | Keeps credentials out of alembic.ini and therefore out of version control |
| 2026-10-16 | Caching & Background Jobs: Redis caching + Celery tasks | Redis for caching GET /datasets with hit/miss counter stats and invalidation on write; Celery worker with `run_analysis` task, `jobs` table, idempotency key deduplication, and ownership checks |
