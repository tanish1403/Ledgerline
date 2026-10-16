"""Consequential inspection flagging tool with audit logging and approval workflow integration."""

import json
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from api.db.inspection_models import InspectionFlag
from api.db.session import SessionLocal
from audit.chain import AuditChain


class InspectionFlagArgs(BaseModel):
    unit_ids: list[int] = Field(..., description="List of engine unit IDs to flag for inspection.")
    reason: str = Field(..., description="Engineering justification for inspection.")


def flag_units_for_inspection(unit_ids: list[int], reason: str, actor_user_id: str = "agent") -> dict[str, Any]:
    """Create a consequential inspection flag in 'requested' state and record in audit log."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).isoformat()
        flag = InspectionFlag(
            unit_ids=json.dumps(unit_ids),
            reason=reason,
            status="requested",
            requested_by=actor_user_id,
            created_at=now,
        )
        db.add(flag)
        db.commit()
        db.refresh(flag)

        # Audit log entry
        chain = AuditChain(db)
        chain.append(
            event_type="inspection_flag_requested",
            actor_user_id=actor_user_id,
            actor_role="agent",
            resource=f"inspection_flag:{flag.id}",
            inputs={"unit_ids": unit_ids, "reason": reason},
            outputs={"flag_id": flag.id, "status": "requested"},
        )

        return {
            "flag_id": flag.id,
            "status": "requested",
            "message": "Inspection flag created and paused awaiting human approval.",
        }
    finally:
        db.close()
