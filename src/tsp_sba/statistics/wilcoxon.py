"""Statistical analysis following the SBA paper experimental protocol."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class WilcoxonResult:
    statistic: float
    p_value: float
    significant_at_05: bool
    better_algorithm: str
    mean_a: float
    mean_b: float
    median_a: float
    median_b: float


def wilcoxon_signed_rank_test(
    samples_a: np.ndarray,
    samples_b: np.ndarray,
    algorithm_a: str,
    algorithm_b: str,
    alpha: float = 0.05,
) -> WilcoxonResult:
    """Wilcoxon signed-rank test for paired samples (30 runs as in paper).

    Tests whether one algorithm is significantly better than the other.
    """
    a = np.asarray(samples_a, dtype=np.float64)
    b = np.asarray(samples_b, dtype=np.float64)
    if len(a) != len(b):
        raise ValueError("Sample sizes must match for paired Wilcoxon test")

    # scipy tests difference a - b; negative statistic favors b
    try:
        stat, p_value = stats.wilcoxon(a, b, alternative="two-sided")
    except ValueError:
        stat, p_value = 0.0, 1.0

    mean_a, mean_b = float(np.mean(a)), float(np.mean(b))
    median_a, median_b = float(np.median(a)), float(np.median(b))

    if mean_a < mean_b:
        better = algorithm_a
    elif mean_b < mean_a:
        better = algorithm_b
    else:
        better = "tie"

    return WilcoxonResult(
        statistic=float(stat),
        p_value=float(p_value),
        significant_at_05=p_value < alpha,
        better_algorithm=better,
        mean_a=mean_a,
        mean_b=mean_b,
        median_a=median_a,
        median_b=median_b,
    )


def summarize_runs(costs: np.ndarray) -> dict[str, float]:
    """Descriptive statistics for multiple independent runs."""
    return {
        "mean": float(np.mean(costs)),
        "std": float(np.std(costs, ddof=1)) if len(costs) > 1 else 0.0,
        "min": float(np.min(costs)),
        "max": float(np.max(costs)),
        "median": float(np.median(costs)),
    }


def performance_improvement(mean_sba: float, mean_other: float) -> float:
    """Paper Eq. (14): P = 100 * (1 - MSBA / M_other) for minimization."""
    if mean_other == 0:
        return 0.0
    return 100.0 * (1.0 - mean_sba / mean_other)
