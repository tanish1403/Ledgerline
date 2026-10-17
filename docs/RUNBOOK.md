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

---

## 7. Launching and Operating the Streamlit Web Dashboard

The Streamlit dashboard (`ui/app.py`) provides an intuitive graphical interface for interacting with the reliability agent, visualizing statistical distributions, managing human approval gates, auditing cryptographic chains, and testing RAG retrieval.

### Local Execution
To launch the UI in local development mode:
```bash
make ui
# or: streamlit run ui/app.py --server.port 8501
```
The dashboard will open in your default browser at `http://localhost:8501`.

### Role Simulation
Use the role selector in the sidebar to simulate interactions under different RBAC roles:
- **Analyst (`analyst`)**: Can prompt the agent, explore Weibull/Kaplan-Meier survival curves, search technical documentation, and request unit maintenance holds.
- **Approver (`approver`)**: Has authorization to review, approve, or reject human-in-the-loop maintenance actions in adherence with separation-of-duties policies.
- **Admin (`admin`)**: Possesses complete access, including full audit chain verification and tamper-detection testing.

### Docker Stack Operation
When running the full stack with `docker compose up --build -d`, the UI container will automatically launch and bind to `http://127.0.0.1:8501`. Logs can be monitored via:
```bash
docker compose logs -f ui
```
