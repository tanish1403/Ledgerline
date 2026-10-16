# Prompt 02: Redis cache and background jobs

Tag the start: `git tag milestone-2-start`.

```
Milestone 2: caching and background jobs. Milestone 1 must be done.

Goal: slow work runs outside the request, and repeated reads are served from cache.

Build:
1. Redis cache for GET /datasets and GET /datasets/{id}, with a TTL from config, invalidated on any
   write. Expose cache hit and miss counters at GET /admin/cache-stats (admin only).
2. Celery worker (Redis broker) in api/worker.py with a `run_analysis(job_id)` task that sleeps and
   computes a placeholder result (real analysis arrives in milestone 4).
3. jobs table (id, type, status queued|running|succeeded|failed, params json, result json, error,
   created_by, created_at, finished_at) and a migration.
4. Endpoints: POST /jobs (analyst+) returns 202 and a job id; GET /jobs/{id} returns status, with
   ownership checks (a user sees only their own jobs, admin sees all).
5. Idempotency: POST /jobs accepts an `Idempotency-Key` header; the same key returns the same job.
6. Timeouts and retries: task time limit, bounded retries with backoff, final state `failed` with a reason.
7. Add a `worker` service to docker-compose.yml using the same image.

Tests:
- cache hit after first read, miss after a write, TTL respected (use a fake clock or short TTL)
- job lifecycle queued -> succeeded, and queued -> failed after retries (run the task eagerly in tests)
- idempotency key returns the same job; another user cannot read my job

Acceptance criteria: `make test`, `make lint`, CI green, `docker compose up` starts api and worker,
docs/PROGRESS.md updated.

Out of scope: agents, stats. Ask before adding dependencies. Show me the plan first.
Commit message: feat: redis cache and celery jobs with idempotency
```
