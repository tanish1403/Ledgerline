"""Deterministic claim validation framework.

Re-runs each claim's computation via registered tools and compares the reported
value against the re-computed value within a tolerance.
"""

from typing import Any
from pydantic import BaseModel, Field

from tools.registry import registry


class Claim(BaseModel):
    """A single factual claim with a re-computation spec."""

    name: str = Field(..., description="Name of the claim.")
    value: float = Field(..., description="Numerical value claimed by the model.")
    computation: dict[str, Any] | None = Field(
        None, description="Computation spec containing tool name and arguments."
    )


class AgentAnswer(BaseModel):
    """Extended AgentAnswer including structured claims."""

    summary: str = Field(..., description="Executive summary.")
    claims: list[Claim] = Field(..., description="List of structured claims.")
    tool_calls_used: list[str] = Field(..., description="Tools used.")


class ClaimValidationResult(BaseModel):
    """Validation result for an individual claim."""

    name: str
    claimed_value: float
    recomputed_value: float | None = None
    passed: bool
    error: str | None = None


class ValidationReport(BaseModel):
    """Comprehensive validation report for all claims in an answer."""

    passed: bool
    claims: list[ClaimValidationResult]


def validate_claims(answer: AgentAnswer, tolerance: float = 0.05) -> ValidationReport:
    """Re-run computations for each claim and check agreement within tolerance."""
    claim_results: list[ClaimValidationResult] = []
    all_passed = True

    for claim in answer.claims:
        if not claim.computation:
            claim_results.append(
                ClaimValidationResult(
                    name=claim.name,
                    claimed_value=claim.value,
                    passed=False,
                    error="Claim has no computation spec.",
                )
            )
            all_passed = False
            continue

        tool_name = claim.computation.get("tool")
        args = claim.computation.get("arguments", {})

        if not tool_name or not registry.get(tool_name):
            claim_results.append(
                ClaimValidationResult(
                    name=claim.name,
                    claimed_value=claim.value,
                    passed=False,
                    error=f"Unregistered or missing tool '{tool_name}' in computation spec.",
                )
            )
            all_passed = False
            continue

        try:
            # Execute the tool computation directly via registry (internal role = admin for re-comp)
            from api.db.models import Role

            tool_res = registry.execute(tool_name, args, Role.admin)
            if isinstance(tool_res, dict) and "error" in tool_res:
                claim_results.append(
                    ClaimValidationResult(
                        name=claim.name,
                        claimed_value=claim.value,
                        passed=False,
                        error=f"Tool execution failed during validation: {tool_res['error']}",
                    )
                )
                all_passed = False
                continue

            # Extract numerical result based on tool output structure
            # e.g., weibull_fit returns {"result": {"shape": ..., "scale": ...}}
            # or outliers returns {"result": {"count": ...}}
            res_data = tool_res.get("result", tool_res)
            # Find the value matching claim name or pick first numeric metric
            recomputed_val = None
            if isinstance(res_data, dict):
                # Try matching claim name (e.g. 'shape', 'scale', 'count')
                for key in [claim.name.lower(), "shape", "scale", "count", "median_survival_time"]:
                    if key in res_data and isinstance(res_data[key], int | float):
                        recomputed_val = float(res_data[key])
                        break
                if recomputed_val is None and len(res_data) == 1:
                    val = list(res_data.values())[0]
                    if isinstance(val, int | float):
                        recomputed_val = float(val)
            elif isinstance(res_data, int | float):
                recomputed_val = float(res_data)

            if recomputed_val is None:
                claim_results.append(
                    ClaimValidationResult(
                        name=claim.name,
                        claimed_value=claim.value,
                        passed=False,
                        error="Could not extract numeric recomputed value from tool output.",
                    )
                )
                all_passed = False
                continue

            # Compare within tolerance
            diff = abs(claim.value - recomputed_val)
            rel_diff = diff / (abs(recomputed_val) + 1e-9)
            passed = rel_diff <= tolerance or diff <= 1e-3

            claim_results.append(
                ClaimValidationResult(
                    name=claim.name,
                    claimed_value=claim.value,
                    recomputed_value=recomputed_val,
                    passed=passed,
                    error=None if passed else f"Disagreement: claimed {claim.value}, recomputed {recomputed_val} (diff {diff:.4f}).",
                )
            )
            if not passed:
                all_passed = False

        except Exception as exc:
            claim_results.append(
                ClaimValidationResult(
                    name=claim.name,
                    claimed_value=claim.value,
                    passed=False,
                    error=f"Exception during re-computation: {str(exc)}",
                )
            )
            all_passed = False

    return ValidationReport(passed=all_passed, claims=claim_results)
