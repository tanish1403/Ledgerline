# Prompt 05: Append-only audit log

Tag the start: `git tag milestone-5-start`.

```
Milestone 5: tamper-evident audit log. Milestones 1 and 3 must be done.

Goal: answer "who did what, with which tool, using which inputs, and what happened" after the fact.

Build:
1. audit_events table: id, timestamp, actor_user_id, actor_role, event_type, resource, inputs json,
   outputs json, trace_id, prev_hash, hash. Migration included.
2. Hash chain: hash = sha256(prev_hash + canonical JSON of the event). Write audit/chain.py with
   `append(event)` and `verify()`.
3. Append-only at the database level: a trigger that raises an error on UPDATE and DELETE, and no
   application code path that edits rows. Concurrent appends must not fork the chain (lock or serialize).
4. Record: logins and failures, every agent run, every tool call (inputs and outputs, with secrets and
   passwords redacted), validation results, and later approvals.
5. GET /audit (admin only, filters by user, type, time) and GET /audit/verify (admin only) that walks the
   chain and reports the first broken link.

Tests:
- events are chained and verify() passes
- editing a row directly in the database makes verify() fail at that row
- UPDATE and DELETE are rejected by the trigger
- redaction removes passwords and tokens from stored inputs
- two concurrent appends keep a single linear chain

Acceptance criteria: `make test`, `make lint`, CI green, docs/PROGRESS.md updated, docs/audit.md with the
event schema and what the chain does and does not protect against (a database superuser can still
rewrite everything, so say so).

Commit message: feat: hash-chained append-only audit log
```
