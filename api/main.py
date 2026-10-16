from fastapi import FastAPI

from api.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe. Readiness checks (DB, Redis) are added in milestone 1 and 2."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
