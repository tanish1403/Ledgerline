# Prompt 06: Human approval gate and rollback (LangGraph)

Tag the start: `git tag milestone-6-start`. Study guide row 8 (LangGraph course) first.

```
Milestone 6: human approval for consequential actions. Milestones 3 and 5 must be done.

Goal: the agent can ask for a consequential action, but a different human must approve it. State survives
restarts. Approved actions can be rolled back.

Build:
1. Consequential tool `flag_units_for_inspection` that writes to inspection_flags
   (id, unit_ids, reason, status requested|approved|rejected|applied|rolled_back, requested_by,
   decided_by, timestamps). Migration included.
2. LangGraph workflow in agents/workflow.py: analysis nodes, then an interrupt before the consequential
   node. Use the Postgres checkpointer so a paused run survives an API restart.
3. Endpoints: GET /approvals (admin), POST /approvals/{id}/approve and /reject (admin), and
   POST /flags/{id}/rollback (admin). Resume the paused graph on approve.
4. Separation of duties: the requester cannot approve their own request, even if they are an admin.
5. Rollback restores the previous state and is audited.
6. Every step writes to the audit log from milestone 5.

Tests:
- run pauses, shows up in /approvals, resumes after approve, and the action is applied exactly once
- reject leaves the data unchanged
- self-approval is refused; an analyst cannot approve; no approval means no action
- resume after simulated restart (new graph object, same checkpoint)
- double-approve is idempotent; rollback restores the old state
- bypass attempts: calling the consequential tool directly, replaying an old approval

Acceptance criteria: `make test`, `make lint`, CI green, docs/PROGRESS.md updated,
docs/approvals.md with a state diagram (mermaid).

Out of scope: UI. Ask before adding dependencies (langgraph and its Postgres checkpointer are expected).
Commit message: feat: human approval gate with rollback and separation of duties
```
