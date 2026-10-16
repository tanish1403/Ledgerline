# Prompt 01: Auth, roles, datasets API

Paste in Plan mode first, then Act. Tag the start: `git tag milestone-1-start`.

```
Milestone 1: authenticated REST API on Postgres. Read AGENTS.md and docs/PLAN.md first.

Goal: users can log in, get a JWT, and call endpoints that depend on their role.

Build:
1. SQLAlchemy 2 models and Alembic migrations in api/db/ and api/migrations/:
   - users(id, email unique, hashed_password, role in viewer|analyst|admin, is_active, created_at)
   - datasets(id, name, description, owner_id -> users, created_at)
2. Password hashing with argon2 (or bcrypt). Never store or log plain passwords.
3. JWT with PyJWT. Secret and expiry come from api/config.py. Token carries user id and role.
4. Endpoints:
   - POST /auth/token (OAuth2 password form) -> access token
   - GET  /me
   - GET  /users (admin only)
   - CRUD /datasets: viewer can read, analyst can create and update, admin can delete
5. A reusable dependency `require_role(*roles)` used by every protected route.
6. scripts/create_admin.py that creates the first admin from environment variables.
7. Readiness: GET /ready checks the database and returns 503 if it is down. Keep GET /health simple.

Tests (pytest, against a separate Postgres test database, each test in a rolled-back transaction):
- login success, wrong password, inactive user, expired token, tampered token
- every role against every dataset endpoint (a table-driven test)
- viewer cannot create, analyst cannot delete, no token gets 401, wrong role gets 403

Acceptance criteria:
- `make test` and `make lint` pass, and CI is green (CI already provides Postgres).
- `alembic upgrade head` works on an empty database.
- Passwords never appear in logs or responses.
- docs/PROGRESS.md updated.

Out of scope: Redis, agents, audit log. Ask before adding dependencies. Show me the plan first.
Commit message: feat: authenticated datasets API with roles
```
