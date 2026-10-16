"""Tests for Milestone 2: Redis cache, Celery jobs, idempotency, and RBAC."""

import pytest

from api.cache import redis_client
from api.worker import run_analysis
from tests.conftest import auth_header, get_token


@pytest.fixture(autouse=True)
def flush_redis():
    """Clear Redis cache before and after each test."""
    redis_client.flushall()
    yield
    redis_client.flushall()


# ===========================================================================
# Redis Cache & Cache Stats Tests
# ===========================================================================


def test_cache_hit_and_miss_lifecycle(client, analyst, existing_dataset):
    """Test cache miss on first read, cache hit on second read, and miss count increment."""
    token = get_token(client, "viewer@test.com", "viewerpass")
    headers = auth_header(token)

    # First read (miss)
    resp1 = client.get(f"/datasets/{existing_dataset.id}", headers=headers)
    assert resp1.status_code == 200

    # Second read (hit)
    resp2 = client.get(f"/datasets/{existing_dataset.id}", headers=headers)
    assert resp2.status_code == 200

    # Check admin cache stats
    admin_token = get_token(client, "admin@test.com", "adminpass")
    stats_resp = client.get("/admin/cache-stats", headers=auth_header(admin_token))
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1


def test_cache_invalidation_on_write(client, analyst, existing_dataset):
    """Test that writing (updating) a dataset invalidates the cache."""
    token = get_token(client, "viewer@test.com", "viewerpass")
    headers = auth_header(token)

    # Populate cache
    client.get(f"/datasets/{existing_dataset.id}", headers=headers)

    # Update dataset (should invalidate cache)
    analyst_token = get_token(client, "analyst@test.com", "analystpass")
    upd_resp = client.put(
        f"/datasets/{existing_dataset.id}",
        json={"name": "Updated Name", "description": "new desc"},
        headers=auth_header(analyst_token),
    )
    assert upd_resp.status_code == 200

    # Read again — should fetch from DB (new name)
    resp = client.get(f"/datasets/{existing_dataset.id}", headers=headers)
    assert resp.json()["name"] == "Updated Name"


# ===========================================================================
# Celery Job Lifecycle & Idempotency Tests
# ===========================================================================


def test_job_creation_and_eager_execution(client, analyst):
    """Test creating a job and running the celery task eagerly."""
    token = get_token(client, "analyst@test.com", "analystpass")
    headers = auth_header(token)

    resp = client.post(
        "/jobs",
        json={"type": "reliability_analysis", "params": {"dataset_id": 123}},
        headers=headers,
    )
    assert resp.status_code == 202
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "queued"

    # Run celery task eagerly in-process
    run_analysis(job_id)

    # Check job status finished successfully
    get_resp = client.get(f"/jobs/{job_id}", headers=headers)
    assert get_resp.status_code == 200
    completed = get_resp.json()
    assert completed["status"] == "succeeded"
    assert completed["result"]["score"] == 0.98


def test_job_idempotency(client, analyst):
    """Test that submitting with the same Idempotency-Key returns the same job."""
    token = get_token(client, "analyst@test.com", "analystpass")
    headers = auth_header(token)
    headers["Idempotency-Key"] = "unique-key-abc"

    resp1 = client.post(
        "/jobs",
        json={"type": "analysis", "params": {}},
        headers=headers,
    )
    assert resp1.status_code == 202
    job1_id = resp1.json()["id"]

    resp2 = client.post(
        "/jobs",
        json={"type": "analysis", "params": {}},
        headers=headers,
    )
    assert resp2.status_code == 202
    job2_id = resp2.json()["id"]

    assert job1_id == job2_id


def test_job_ownership_isolation(client, analyst, viewer, db):
    """Test that a regular user cannot view another user's job, but admin can."""
    analyst_token = get_token(client, "analyst@test.com", "analystpass")
    resp = client.post(
        "/jobs",
        json={"type": "analysis", "params": {}},
        headers=auth_header(analyst_token),
    )
    job_id = resp.json()["id"]

    # Viewer tries to read analyst's job -> 403 Forbidden
    viewer_token = get_token(client, "viewer@test.com", "viewerpass")
    view_resp = client.get(f"/jobs/{job_id}", headers=auth_header(viewer_token))
    assert view_resp.status_code == 403

    # Admin tries to read analyst's job -> 200 OK
    admin_token = get_token(client, "admin@test.com", "adminpass")
    admin_resp = client.get(f"/jobs/{job_id}", headers=auth_header(admin_token))
    assert admin_resp.status_code == 200
