# Evaluation Framework & CI Regression Gate

The reliability agent platform maintains measurable quality through automated golden-set evaluations (`evals/`) executed in CI.

## Metrics Evaluated
1. **Task Success Rate**: Percentage of golden agent tasks successfully completed.
2. **Validator Pass Rate**: Rate at which generated calculations and statistical models pass validation checks.
3. **Tool-Call Error Rate**: Frequency of tool execution errors.
4. **Approval-Bypass Attempts**: Must be **0.0** (any attempt to bypass human approval gates fails the build instantly).
5. **Retrieval Recall & MRR**: Accuracy and ranking quality of hybrid retrieval (vector + FTS).
6. **Citation Validity Rate**: Percentage of RAG citations with verified verbatim quotes.
7. **Not Found Correctness**: Accuracy in returning `"not found"` on unanswerable questions.

## Execution Modes
- **Replay Mode (`--mode replay`)**: Uses recorded model responses and deterministic baselines. Fast, free, and executed in CI on every PR.
- **Live Mode (`--mode live`)**: Queries the real model configured via `LLM_BASE_URL`. Used locally for validation and tuning.

## Updating the Baseline Deliberately
When agent prompts, models, or retrieval algorithms are intentionally improved:
1. Run local evaluations in live mode: `python evals/run.py --mode live`
2. Inspect the generated report in `evals/reports/`.
3. Update `evals/baseline.json` with the new validated metrics after thorough review.
4. Commit both code changes and the updated `evals/baseline.json`.

## LLM-as-Judge Bias Risks
Using LLM-as-judge for RAG faithfulness introduces positional bias (favoring chunks appearing earlier in context), verbosity bias, and sycophancy. To mitigate this, our evaluation pipeline emphasizes deterministic checks (verbatim quote verification, exact tool matching, and numeric precision validation) over subjective LLM scoring.
