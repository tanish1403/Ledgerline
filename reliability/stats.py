"""Pure reliability statistics and data analysis functions.

Provides Weibull fitting, Kaplan-Meier survival curves, outlier detection,
and summary statistics helpers using lifelines, numpy, and pandas.
"""

from typing import Any

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter, WeibullFitter


def weibull_fit(
    durations: list[float], event_observed: list[int]
) -> dict[str, Any]:
    """Fit Weibull distribution to survival data using lifelines."""
    df = pd.DataFrame(
        {"durations": durations, "event_observed": event_observed}
    )
    wf = WeibullFitter()
    wf.fit(df["durations"], event_observed=df["event_observed"])

    params = wf.summary
    # wf.summary typically contains columns like 'coef' for lambda (scale) and rho (shape)
    # In lifelines WeibullFitter: lambda_ is scale, rho_ is shape.
    scale = float(wf.lambda_)
    shape = float(wf.rho_)

    # Confidence intervals if available
    ci = wf.confidence_interval_
    ci_dict = {}
    if not ci.empty:
        ci_dict = ci.to_dict()

    return {
        "shape": shape,
        "scale": scale,
        "confidence_intervals": ci_dict,
        "AIC": float(wf.AIC_),
    }


def kaplan_meier(
    durations: list[float], event_observed: list[int]
) -> dict[str, list[Any]]:
    """Compute Kaplan-Meier non-parametric survival estimate."""
    df = pd.DataFrame(
        {"durations": durations, "event_observed": event_observed}
    )
    kmf = KaplanMeierFitter()
    kmf.fit(df["durations"], event_observed=df["event_observed"])

    timeline = kmf.timeline.tolist()
    survival_function = kmf.survival_function_.iloc[:, 0].tolist()

    return {
        "timeline": timeline,
        "survival_function": survival_function,
        "median_survival_time": float(kmf.median_survival_time_),
    }


def outliers(values: list[float], method: str = "mad") -> dict[str, Any]:
    """Detect outliers using robust z-score (MAD) or IQR method."""
    arr = np.array(values, dtype=float)
    if len(arr) == 0:
        return {"outliers": [], "indices": []}

    outlier_mask = np.zeros(len(arr), dtype=bool)

    if method == "mad":
        median = np.median(arr)
        mad = np.median(np.abs(arr - median))
        if mad == 0.0:
            # Fallback if all values identical
            modified_z = np.zeros_like(arr)
        else:
            modified_z = 0.6745 * (arr - median) / mad
        outlier_mask = np.abs(modified_z) > 3.5
    elif method == "iqr":
        q25, q75 = np.percentile(arr, [25, 75])
        iqr = q75 - q25
        lower = q25 - 1.5 * iqr
        upper = q75 + 1.5 * iqr
        outlier_mask = (arr < lower) | (arr > upper)
    else:
        raise ValueError(f"Unknown outlier detection method: {method}")

    indices = np.where(outlier_mask)[0].tolist()
    vals = arr[outlier_mask].tolist()

    return {
        "indices": indices,
        "outliers": vals,
        "count": len(indices),
        "method": method,
    }


def summary_stats(values: list[float]) -> dict[str, float]:
    """Compute summary statistics for a numeric list."""
    arr = np.array(values, dtype=float)
    if len(arr) == 0:
        return {
            "mean": 0.0,
            "std": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "median": float(np.median(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "p95": float(np.percentile(arr, 95)),
    }
