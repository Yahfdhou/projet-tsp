"""Algorithm result types."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class OptimizationResult:
    best_tour: np.ndarray
    best_cost: float
    history: list[float]
    algorithm: str
    instance_name: str
    run_id: int
    decades: int
