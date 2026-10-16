"""Audit log router for admin querying and verification."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import Role, User
from api.db.session import get_db
from api.dependencies import require_role
from audit.chain import AuditChain, AuditEvent


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[dict[str, Any]])
def get_audit_events(
    user_id: str | None = Query(None, description="Filter by actor user id"),
    event_type: str | None = Query(None, description="Filter by event type"),
    start_time: str | None = Query(None, description="Filter start ISO timestamp"),
    end_time: str | None = Query(None, description="Filter end ISO timestamp"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(Role.admin)),
) -> list[dict[str, Any]]:
    """Query audit events with filters (Admin only)."""
    stmt = select(AuditEvent).order_by(AuditEvent.id.asc())

    if user_id:
        stmt = stmt.where(AuditEvent.actor_user_id == user_id)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    if start_time:
        stmt = stmt.where(AuditEvent.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(AuditEvent.timestamp <= end_time)

    stmt = stmt.limit(limit)
    events = db.scalars(stmt).all()

    results = []
    for ev in events:
        results.append(
            {
                "id": ev.id,
                "timestamp": ev.timestamp,
                "actor_user_id": ev.actor_user_id,
                "actor_role": ev.actor_role,
                "event_type": ev.event_type,
                "resource": ev.resource,
                "inputs": ev.inputs,
                "outputs": ev.outputs,
                "trace_id": ev.trace_id,
                "prev_hash": ev.prev_hash,
                "hash": ev.hash,
            }
        )
    return results


@router.get("/verify", response_model=dict[str, Any])
def verify_audit_chain(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(Role.admin)),
) -> dict[str, Any]:
    """Walk the audit chain and report verification status (Admin only)."""
    chain = AuditChain(db)
    valid, broken_id, error = chain.verify()
    return {
        "valid": valid,
        "broken_id": broken_id,
        "error": error,
    }
