"""Unit tests for evaluation runner and comparison regression gate."""

import json
import pytest
from evals.run import run_evals
from evals.compare import compare_reports


def test_eval_runner_and_comparison():
    report = run_evals(mode="replay")
    assert "metrics" in report
    assert report["metrics"]["approval_bypass_attempts"] == 0.0

    # Comparison against baseline should pass
    success = compare_reports()
    assert success is True
