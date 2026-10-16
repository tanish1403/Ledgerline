"""Comprehensive documentation for audit logging and hash-chain guarantees."""

# Tamper-Evident Audit Log

The reliability agent platform maintains a hash-chained, append-only audit log of all critical security, agent, and reliability operations.

## Event Schema (`audit_events`)

- `id`: Primary key identifier.
- `timestamp`: ISO 8601 UTC timestamp of the event.
- `actor_user_id`: Identifier of the user or agent performing the action.
- `actor_role`: RBAC role of the actor (`viewer`, `analyst`, `admin`).
- `event_type`: Type of event (`login`, `login_failure`, `agent_run`, `tool_call`, `validation`, `approval`).
- `resource`: Target resource or object being acted upon.
- `inputs`: JSON string of operation inputs (with passwords, tokens, and secrets automatically redacted).
- `outputs`: JSON string of operation outputs or results.
- `trace_id`: Correlation ID linking related operations across requests or agent steps.
- `prev_hash`: SHA-256 hash of the preceding event (or 64 zeros for the genesis event).
- `hash`: SHA-256 hash of `prev_hash` + canonical JSON representation of the current event.

## Hash Chain Verification (`/audit/verify`)

The audit log enforces cryptographic integrity through a hash chain:
$$H_i = \text{SHA256}(H_{i-1} + \text{canonical\_json}(Event_i))$$

If any record in the database is modified or deleted, verification walking from the genesis event will detect a hash mismatch or broken link at that exact event ID.

## What it protects against vs. Limitations

- **Protected against:** Silent tampering or retroactive modification of historical audit records by application users or compromised services.
- **Limitations:** A database superuser (`postgres` or direct database administrator access) can still rewrite rows and recompute or bypass database triggers and hash chains. The audit chain provides tamper-evidence, not absolute hardware-level immutability against database-level root administrators.
