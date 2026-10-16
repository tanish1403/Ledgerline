# Operations Runbook

This runbook covers routine operations, maintenance, and incident response procedures for the Reliability Agent Platform.

---

## 1. Starting and Stopping the Stack

### Local Development
- **Start API Server**:
  ```bash
  make dev
  ```
- **Stop API Server**: Press `Ctrl+C` in the terminal.

### Docker Compose Production/Staging Stack
- **Start All Services** (API, Postgres + pgvector, Redis, Celery worker):
  ```bash
  make up
  ```
- **Stop All Services**:
  ```bash
  make down
  ```
- **View Container Logs**:
  ```bash
  make logs
  # or specifically:
  docker compose logs -f api
  ```

---

## 2. Database Backup and Restore

### Backup PostgreSQL Database
```bash
docker compose exec db pg_dump -U postgres reliability > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore PostgreSQL Database
```bash
docker compose exec -T db psql -U postgres reliability < backup_YYYYMMDD_HHMMSS.sql
```

---

## 3. Rotating JWT Secrets

1. Generate a new cryptographic secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
2. Update `JWT_SECRET` in your `.env` file (or Kubernetes secret store / Helm values).
3. Restart the API service:
   ```bash
   docker compose restart api
   ```
   *(Note: Rotating the JWT secret will invalidate existing active user sessions, forcing users to re-authenticate).*

---

## 4. Handling Stuck Background Jobs

If a Celery background analysis job hangs or fails to complete:
1. Check Celery worker logs:
   ```bash
   docker compose logs worker
   ```
2. Purge stuck queue tasks (if necessary):
   ```bash
   docker compose exec redis celery -A api.celery_app inspect active
   docker compose exec redis celery -A api.celery_app purge
   ```
3. Restart the Celery worker container:
   ```bash
   docker compose restart worker
   ```

---

## 5. Reading Traces and Observability

The platform exports OpenTelemetry traces, metrics, and logs to the observability stack.
- **Prometheus UI**: `http://localhost:9090`
- **Grafana Dashboards**: `http://localhost:3000` (pre-provisioned with reliability agent telemetry dashboards).
- **Inspect Structured Logs**: Look for `trace_id` and `span_id` fields in JSON container logs.

---

## 6. Rolling Back a Release

If a deployment introduces regressions:
1. **Docker Compose Rollback**:
   Checkout the previous stable git tag and rebuild:
   ```bash
   git checkout <stable-tag>
   docker compose up --build -d
   ```
2. **Kubernetes / Helm Rollback**:
   ```bash
   helm rollback reliability-release 1
   ```
