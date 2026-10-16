# Prompt 04: Reliability statistics and validators

Tag the start: `git tag milestone-4-start`. Get the data first: see `scripts/README_data.md`.

```
Milestone 4: reliability statistics tools and deterministic validators. Milestone 3 must be done.

Goal: when the model states a number, code re-computes it and rejects the answer if it disagrees.

Build:
1. A `reliability/` package (pure functions, no web code, easy to test):
   - weibull_fit(durations, event_observed) using lifelines; returns shape, scale and confidence intervals
   - kaplan_meier(durations, event_observed)
   - outliers(values, method) with a robust z-score and an IQR option
   - summary stats helper
2. scripts/load_cmapss.py loads the turbofan files from data/cmapss/ into Postgres tables
   (engine_cycles, engine_life). Do not commit data.
3. Register tools: weibull_fit, kaplan_meier, outliers. They take a dataset name or unit group, query
   Postgres themselves, and return a result with a `computation` spec (tool name plus arguments).
4. Extend AgentAnswer: each claim is {name, value, computation}, where computation says how to re-compute it.
5. validators/recompute.py re-runs each claim's computation with the same pure function and compares
   within a tolerance. Return a ValidationReport. If any claim fails, the agent gets the report and
   one chance to correct, otherwise the answer is returned flagged `validated: false`.

Tests:
- known Weibull parameters recovered from simulated data within tolerance (fixed random seed)
- censored data handled
- validator accepts a correct claim, rejects a wrong number, rejects a claim with no computation
- validator cannot be bypassed by a claim that references an unregistered tool

Acceptance criteria: `make test`, `make lint`, CI green (tests use simulated data, not the real files),
docs/PROGRESS.md updated, and docs/validation.md explaining the idea in half a page.

Out of scope: approvals, RAG. Ask before adding dependencies (lifelines, numpy, pandas are expected).
Commit message: feat: reliability tools with deterministic claim validation
```
