"""Celery worker and background analysis task.

Configured with Redis broker and result backend.
"""

import time
from datetime import UTC, datetime

from celery import Celery

from api.config import settings
from api.db.models import Job, JobStatus
from api.db.session import SessionLocal

celery_app = Celery(
    "reliability_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=60,
    task_time_limit=120,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=2)
def run_analysis(self, job_id: int) -> dict:
    """Execute background reliability analysis job.

    Updates job state from queued -> running -> succeeded (or failed after retries).
    """
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return {"status": "not_found", "job_id": job_id}

        job.status = JobStatus.running
        db.commit()

        # Simulate work / placeholder analysis
        time.sleep(1)

        # Placeholder successful result
        job.status = JobStatus.succeeded
        job.result = {
            "analysis": "completed",
            "score": 0.98,
            "details": f"Successfully analysed dataset with params {job.params}",
        }
        job.finished_at = datetime.now(UTC)
        db.commit()
        return {"status": "succeeded", "job_id": job_id}

    except Exception as exc:
        db.rollback()
        job = db.get(Job, job_id)
        if job:
            if self.request.retries < self.max_retries:
                job.status = JobStatus.queued
                db.commit()
                raise self.retry(exc=exc) from exc
            else:
                job.status = JobStatus.failed
                job.error = str(exc)
                job.finished_at = datetime.now(UTC)
                db.commit()
        raise exc
    finally:
        db.close()
