# Prompt 11: Docs, threat model, demo

Tag the start: `git tag milestone-11-start`.

```
Milestone 11: make the project understandable in ten minutes. Do not change behaviour in this milestone.

Build:
1. README.md rewrite: one-paragraph pitch, an architecture diagram (mermaid), a 10-minute quickstart that
   I test on a clean clone, a feature list that matches the code, a table of real metrics from evals/reports/
   and from the dashboard, and a "limits" section that says plainly what does not work yet.
2. docs/THREAT_MODEL.md: assets, actors, trust boundaries, and for each of these a risk, the control in
   the code (with file paths) and a test that proves it: prompt injection, tool abuse, SQL injection,
   path traversal, privilege escalation, approval bypass, audit tampering, secret leakage, data exfiltration
   through upstream model providers.
3. docs/RUNBOOK.md: how to start, stop, back up the database, rotate JWT secret, handle a stuck job, read
   a trace, and roll back a release.
4. scripts/demo.sh and docs/DEMO.md: a scripted demo of the example user flow (log in as an analyst, ask
   a question, hit the approval gate, approve as an admin, show the audit trail and the trace) with the
   exact commands and expected output.
5. A final `make verify` target that runs lint, tests, evals in replay mode and a docker build.

Acceptance criteria: a stranger can clone, run the quickstart and the demo without asking me anything;
every claim in the README is backed by a command or file; `make verify` passes; docs/PROGRESS.md complete.

Commit message: docs: readme, threat model, runbook and demo
```
