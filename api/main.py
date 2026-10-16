from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from api.config import settings
from api.db.session import engine
from api.routers import auth, datasets, jobs, users

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(datasets.router)
app.include_router(jobs.admin_router)
app.include_router(jobs.jobs_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe — no I/O, always fast."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/ready", tags=["meta"])
def ready() -> JSONResponse:
    """Readiness probe — returns 503 when the database is unreachable.

    Why separate from /health: liveness and readiness serve different purposes.
    A failed /ready tells the orchestrator not to route traffic; a failed /health
    tells it to restart the process.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse({"status": "ok"})
    except Exception:
        return JSONResponse({"status": "db_unavailable"}, status_code=503)
