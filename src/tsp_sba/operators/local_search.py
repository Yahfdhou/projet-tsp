"""Local search operators for TSP (2-opt)."""

from __future__ import annotations

import numpy as np

from tsp_sba.config import SBAParams
from tsp_sba.tsp.instance import TSPInstance


def two_opt(tour: np.ndarray, distance_matrix: np.ndarray) -> np.ndarray:
    """First-improvement 2-opt until local optimum."""
    n = len(tour)
    if n < 4:
        return tour.copy()

    best = tour.copy()
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            a, b = best[i], best[i + 1]
            for j in range(i + 2, n):
                c, d = best[j], best[(j + 1) % n]
                delta = (
                    distance_matrix[a, c]
                    + distance_matrix[b, d]
                    - distance_matrix[a, b]
                    - distance_matrix[c, d]
                )
                if delta < -1e-9:
                    best[i + 1 : j + 1] = best[i + 1 : j + 1][::-1]
                    improved = True
                    break
            if improved:
                break
    return best


def maybe_two_opt(
    tour: np.ndarray, instance: TSPInstance, params: SBAParams
) -> np.ndarray:
    """Apply 2-opt when enabled in params."""
    if not params.use_two_opt:
        return tour
    return two_opt(tour, instance.distance_matrix)
