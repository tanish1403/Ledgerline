"""Approvals and inspection flags router with separation of duties, rollback, and audit logging."""

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.inspection_models import InspectionFlag
from api.db.models import Role, User
from api.db.session import get_db
from api.dependencies import require_role
from audit.chain import AuditChain

router = APIRouter(prefix="", tags=["approvals"])


@router.get("/approvals", response_model=list[dict[str, Any]])
def get_approvals(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(Role.admin)),
) -> list[dict[str, Any]]:
    """List pending inspection flags awaiting approval (Admin only)."""
    flags = db.scalars(
        select(InspectionFlag).order_by(InspectionFlag.created_at.desc())
    ).all()

    results = []
    for f in flags:
        results.append(
            {
                "id": f.id,
                "unit_ids": json.loads(f.unit_ids),
                "reason": f.reason,
                "status": f.status,
                "requested_by": f.requested_by,
                "decided_by": f.decided_by,
                "created_at": f.created_at,
                "decided_at": f.decided_at,
                "applied_at": f.applied_at,
                "rolled_back_at": f.rolled_back_at,
            }
        )
    return results


@router.post("/approvals/{id}/approve", response_model=dict[str, Any])
def approve_inspection(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(Role.admin)),
) -> dict[str, Any]:
    """Approve an inspection flag with separation of duties enforcement (Admin only)."""
    flag = db.get(InspectionFlag, id)
    if not flag:
        raise HTTPException(status_code=404, detail="Inspection flag not found.")

    if flag.status != "requested":
        raise HTTPException(
            status_code=400,
            detail=f"Inspection flag is already in status '{flag.status}'.",
        )

    if flag.requested_by == admin.username:
        raise HTTPException(
            status_code=403,
            detail="Separation of duties violation: Requester cannot approve their own inspection request.",
        )

    now = datetime.now(UTC).isoformat()
    flag.decided_by = admin.username
    flag.decided_at = now
    flag.applied_at = now
    flag.status = "applied"
    db.commit()

    chain = AuditChain(db)
    chain.append(
        event_type="inspection_flag_approved",
        actor_user_id=admin.username,
        actor_role=admin.role.value,
        resource=f"inspection_flag:{flag.id}",
        inputs={"flag_id": flag.id},
        outputs={"status": "applied", "decided_by": admin.username},
    )

    return {
        "id": flag.id,
        "status": flag.status,
        "decided_by": admin.username,
        "message": "Inspection flag approved and applied successfully.",
    }


@router.post("/approvals/{id}/reject", response_model=dict[str, Any])
def reject_inspection(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(Role.admin)),
) -> dict[str, Any]:
    """Reject an inspection flag with separation of duties enforcement (Admin only)."""
    flag = db.get(InspectionFlag, id)
    if not flag:
        raise HTTPException(status_code=404, detail="Inspection flag not found.")

    if flag.status != "requested":
        raise HTTPException(
            status_code=400,
            detail=f"Inspection flag is already in status '{flag.status}'.",
        )

    if flag.requested_by == admin.username:
        raise HTTPException(
            status_code=403,
            detail="Separation of duties violation: Requester cannot reject their own inspection request.",
        )

    now = datetime.now(UTC).isoformat()
    flag.status = "rejected"
    flag.decided_by = admin.username
    flag.decided_at = now
    db.commit()

    chain = AuditChain(db)
    chain.append(
        event_type="inspection_flag_rejected",
        actor_user_id=admin.username,
        actor_role=admin.role.value,
        resource=f"inspection_flag:{flag.id}",
        inputs={"flag_id": flag.id},
        outputs={"status": "rejected", "decided_by": admin.username},
    )

    return {
        "id": flag.id,
        "status": flag.status,
        "decided_by": admin.username,
        "message": "Inspection flag rejected successfully.",
    }


@router.post("/flags/{id}/rollback", response_model=dict[str, Any])
def rollback_inspection(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(Role.admin)),
) -> dict[str, Any]:
    """Roll back an applied inspection flag (Admin only)."""
    flag = db.get(InspectionFlag, id)
    if not flag:
        raise HTTPException(status_code=404, detail="Inspection flag not found.")

    if flag.status != "applied":
        raise HTTPException(
            status_code=400,
            detail=f"Only applied inspection flags can be rolled back (current: {flag.status}).",
        )

    now = datetime.now(UTC).isoformat()
    flag.status = "rolled_back"
    flag.rolled_back_at = now
    db.commit()

    chain = AuditChain(db)
    chain.append(
        event_type="inspection_flag_rolled_back",
        actor_user_id=admin.username,
        actor_role=admin.role.value,
        resource=f"inspection_flag:{flag.id}",
        inputs={"flag_id": flag.id},
        outputs={"status": "rolled_back", "rolled_back_by": admin.username},
    )

    return {
        "id": flag.id,
        "status": flag.status,
        "rolled_back_by": admin.username,
        "message": "Inspection flag rolled back successfully.",
    }
