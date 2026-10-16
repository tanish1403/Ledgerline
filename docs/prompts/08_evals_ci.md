# Prompt 08: Evaluation harness gated in CI

Tag the start: `git tag milestone-8-start`. Study guide row 5 (Ragas, RAG evaluation) first.

```
Milestone 8: measurable quality, enforced by CI. Milestones 4 and 7 must be done.

Goal: a change that makes the agent or RAG worse fails the build.

Build:
1. evals/golden/agent_tasks.jsonl: 30 or more tasks with known answers (for example "fit a Weibull to
   unit group A"), each with expected tool use and expected numbers. evals/golden/rag_questions.jsonl:
   50 or more questions with expected source document and page, plus 10 unanswerable ones.
2. evals/run.py computes: task success rate, validator pass rate, tool-call error rate,
   approval-bypass attempts (must be zero), retrieval recall@k and MRR, citation validity rate,
   "not found" correctness on unanswerable questions. It writes a JSON report to evals/reports/.
3. Two modes: `--mode replay` uses recorded model responses so it is deterministic and free (this runs
   in CI), and `--mode live` calls your real model through LLM_BASE_URL (run it locally).
4. evals/baseline.json holds accepted metrics. `evals/compare.py` exits non-zero if any metric drops by
   more than a tolerance, or if bypass attempts are not zero.
5. Prompt versioning: prompts live in agents/prompts/ with a version string recorded in every report.
6. Add an `evals` job to .github/workflows/ci.yml that runs replay mode and compare.
7. Optional: LLM-as-judge faithfulness check for RAG answers. If you add it, record judge bias risks in
   docs/evals.md. Ragas defaults to OpenAI, so point it at the local model or skip it.

Tests: compare.py fails on a regression and passes on equal metrics; the report schema is stable.

Acceptance criteria: `make test`, `make lint`, CI green including the evals job, docs/evals.md explains
the metrics and how to update the baseline deliberately, docs/PROGRESS.md updated.

Commit message: feat: golden-set evals with CI regression gate
```
