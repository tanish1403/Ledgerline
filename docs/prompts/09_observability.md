# Prompt 09: Observability

Tag the start: `git tag milestone-9-start`. Study guide row 6 (OpenTelemetry, Grafana) first.

```
Milestone 9: traces, metrics and dashboards. Milestone 3 must be done.

Goal: follow one request across API, agent steps, tool calls, database and Redis, and see health at a glance.

Build:
1. OpenTelemetry setup in api/telemetry.py: auto-instrument FastAPI, SQLAlchemy and Redis, plus manual
   spans for each agent step and each tool call. Put the audit trace_id on those spans.
2. Custom metrics: tool_calls_total (by tool and status), tool_errors_total, agent_run_duration_seconds,
   llm_tokens_total (input and output), validation_failures_total, approvals_pending.
3. Structured JSON logs that include trace_id and span_id.
4. deploy/compose/observability.yml with an OpenTelemetry Collector, Prometheus, Grafana, and Jaeger
   (or Tempo). Collector config in observability/. Everything optional: the app must run when the
   collector is down.
5. A provisioned Grafana dashboard JSON committed to observability/grafana/: request latency percentiles,
   tool-call error rate, token usage, agent run duration, pending approvals.
6. One Prometheus alert rule: tool error rate above a threshold for 5 minutes.
7. Do not record prompts or tool outputs as span attributes unless redacted (they may contain private data).

Tests: a unit test that a tool call produces a span with the expected attributes (in-memory exporter);
metrics increment on success and on error; telemetry disabled by config does not break the app.

Acceptance criteria: `make test`, `make lint`, CI green, `docker compose -f docker-compose.yml -f
deploy/compose/observability.yml up` shows a trace for one agent run in Jaeger and the dashboard
populated. Add two screenshots to docs/img/. Update docs/PROGRESS.md.

Commit message: feat: opentelemetry traces, metrics and grafana dashboard
```
