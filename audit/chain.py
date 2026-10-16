"""Audit event model and tamper-evident hash chain implementation."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Float, Integer, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from api.db.models import Base


class AuditEvent(Base):
    """Tamper-evident audit event record in database."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(100), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(200), nullable=True)
    inputs: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    outputs: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    trace_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)


def redactor(data: Any) -> Any:
    """Recursively redact sensitive keys like password, token, api_key, secret."""
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if any(secret_key in k.lower() for secret_key in ["password", "token", "secret", "api_key", "key"]):
                new_dict[k] = "[REDACTED]"
            else:
                new_dict[k] = redactor(v)
        return new_dict
    elif isinstance(data, list):
        return [redactor(item) for item in data]
    return data


def canonical_json(event_dict: dict[str, Any]) -> str:
    """Produce canonical JSON string with sorted keys and no extra whitespace."""
    return json.dumps(event_dict, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(prev_hash: str, event_dict: dict[str, Any]) -> str:
    """Compute sha256 hash of prev_hash + canonical JSON of event."""
    # Exclude 'hash' itself from event_dict when hashing
    clean_dict = {k: v for k, v in event_dict.items() if k != "hash"}
    payload = prev_hash + canonical_json(clean_dict)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditChain:
    """Manages appending and verifying hash-chained audit events."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def append(
        self,
        event_type: str,
        actor_user_id: str | None = None,
        actor_role: str | None = None,
        resource: str | None = None,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> AuditEvent:
        """Append a new audit event with hash chaining, serialized to prevent forks."""
        # Use database table locking / transaction serialization to prevent concurrent forks
        self.db.execute(select(AuditEvent).with_for_update())

        # Get latest event
        last_event = self.db.scalars(
            select(AuditEvent).order_by(AuditEvent.id.desc())
        ).first()

        prev_hash = last_event.hash if last_event else "0" * 64
        timestamp = datetime.now(timezone.utc).isoformat()

        redacted_inputs = redactor(inputs) if inputs else None
        redacted_outputs = redactor(outputs) if outputs else None

        event_data = {
            "timestamp": timestamp,
            "actor_user_id": actor_user_id,
            "actor_role": actor_role,
            "event_type": event_type,
            "resource": resource,
            "inputs": json.dumps(redacted_inputs) if redacted_inputs is not None else None,
            "outputs": json.dumps(redacted_outputs) if redacted_outputs is not None else None,
            "trace_id": trace_id,
            "prev_hash": prev_hash,
        }

        h = compute_hash(prev_hash, event_data)
        event_data["hash"] = h

        audit_event = AuditEvent(**event_data)
        self.db.add(audit_event)
        self.db.commit()
        self.db.refresh(audit_event)
        return audit_event

    def verify(self) -> tuple[bool, int | None, str | None]:
        """Walk the audit chain and verify all links. Returns (valid, broken_id, error_message)."""
        events = self.db.scalars(select(AuditEvent).order_by(AuditEvent.id.asc())).all()

        expected_prev = "0" * 64
        for ev in events:
            if ev.prev_hash != expected_prev:
                return False, ev.id, f"Prev hash mismatch at event {ev.id}: expected {expected_prev}, got {ev.prev_hash}"

            # Recompute hash
            ev_dict = {
                "timestamp": ev.timestamp,
                "actor_user_id": ev.actor_user_id,
                "actor_role": ev.actor_role,
                "event_type": ev.event_type,
                "resource": ev.resource,
                "inputs": ev.inputs,
                "outputs": ev.outputs,
                "trace_id": ev.trace_id,
                "prev_hash": ev.prev_hash,
            }
            computed = compute_hash(ev.prev_hash, ev_dict)
            if computed != ev.hash:
                return False, ev.id, f"Hash mismatch at event {ev.id}: expected {computed}, got {ev.hash}"

            expected_prev = ev.hash

        return True, None, None
