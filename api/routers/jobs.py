"""Jobs router and admin cache stats router.

Provides:
- GET /admin/cache-stats (admin only)
- POST /jobs (analyst+) with idempotency key support
- GET /jobs/{id} with ownership enforcement
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from api.cache import get_cache_stats
from api.db.models import Job, JobStatus, Role, User
from api.db.session import get_db
from api.deps import require_role
from api.worker import run_analysis

admin_router = APIRouter(prefix="/admin", tags=["admin"])
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


class CacheStatsOut(BaseModel):
    hits: int
    misses: int


_admin_role = require_role(Role.admin)
_analyst_roles = require_role(Role.analyst, Role.admin)
_read_roles = require_role(Role.viewer, Role.analyst, Role.admin)


@admin_router.get("/cache-stats", response_model=CacheStatsOut)
def cache_stats_endpoint(
    _: User = Depends(_admin_role),  # noqa: B008
):
    """Return cache hit and miss statistics (admin only)."""
    return get_cache_stats()


class JobIn(BaseModel):
    type: str = Field(..., min_length=1, max_length=100)
    params: dict[str, Any] | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    status: JobStatus
    params: dict[str, Any] | None
    result: dict[str, Any] | None
    error: str | None
    idempotency_key: str | None
    created_by: int
    created_at: datetime
    finished_at: datetime | None


@jobs_router.post("", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    body: JobIn,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),  # noqa: B008
    user: User = Depends(_analyst_roles),  # noqa: B008
):
    """Create a background job (analyst+).

    Supports `Idempotency-Key` header: if the same key was used by the same user,
    returns the existing job instead of duplicating.
    """
    if idempotency_key:
        existing = (
            db.query(Job)
            .filter(Job.created_by == user.id, Job.idempotency_key == idempotency_key)
            .first()
        )
        if existing:
            return existing

    job = Job(
        type=body.type,
        params=body.params,
        status=JobStatus.queued,
        idempotency_key=idempotency_key,
        created_by=user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch Celery background task
    run_analysis.delay(job.id)

    return job


@jobs_router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),  # noqa: B008
    user: User = Depends(_read_roles),  # noqa: B008
):
    """Get job status and results.

    Ownership enforcement: regular users (viewer/analyst) see only their own jobs.
    Admins can view any job.
    """
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if user.role != Role.admin and job.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return job
