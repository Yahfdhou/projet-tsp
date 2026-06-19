"""Genetic operators adapted for permutation-based TSP representation."""

from __future__ import annotations

import numpy as np


def tournament_selection(
    population: np.ndarray,
    costs: np.ndarray,
    rng: np.random.Generator,
    tournament_size: int = 3,
) -> int:
    """Select one individual index via k-tournament (minimization)."""
    n = len(population)
    candidates = rng.choice(n, size=min(tournament_size, n), replace=False)
    best = candidates[np.argmin(costs[candidates])]
    return int(best)


def order_crossover(
    parent1: np.ndarray, parent2: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Order Crossover (OX) preserving permutation validity."""
    n = len(parent1)
    if n < 2:
        return parent1.copy()

    i, j = sorted(rng.choice(n, size=2, replace=False))
    child = np.full(n, -1, dtype=parent1.dtype)
    child[i : j + 1] = parent1[i : j + 1]
    segment = set(child[i : j + 1].tolist())

    fill_order = list(parent2[j + 1 :]) + list(parent2[: j + 1])
    fill_values = [c for c in fill_order if c not in segment]

    pos = (j + 1) % n
    for val in fill_values:
        child[pos] = val
        pos = (pos + 1) % n

    return child


def inversion_mutation(tour: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Inversion mutation: reverse a random subsequence."""
    n = len(tour)
    if n < 2:
        return tour.copy()
    i, j = sorted(rng.choice(n, size=2, replace=False))
    mutant = tour.copy()
    mutant[i : j + 1] = mutant[i : j + 1][::-1]
    return mutant


def copy_positions_assimilation(
    target: np.ndarray,
    source: np.ndarray,
    rng: np.random.Generator,
    num_positions: int,
) -> np.ndarray:
    """ICA assimilation adapted for TSP: copy segment from source into target.

    Replaces a contiguous block in target with values from source while
    repairing the permutation to maintain validity.
    """
    n = len(target)
    if num_positions < 1:
        num_positions = 1
    num_positions = min(num_positions, n)

    result = target.copy()
    start = int(rng.integers(0, n - num_positions + 1))
    segment = source[start : start + num_positions].tolist()

    # Remove segment cities from result, then insert at start
    for city in segment:
        idx = np.where(result == city)[0]
        if len(idx):
            result = np.delete(result, idx[0])

    result = np.insert(result, start, segment)
    return result.astype(target.dtype)


def compute_assimilation_positions(
    n_cities: int, coefficient: float, distance_ratio: float = 1.0
) -> int:
    """Number of cities to assimilate based on ICA beta coefficient."""
    base = max(2, int(round(coefficient * distance_ratio * n_cities * 0.05)))
    return min(base, n_cities // 2)


def assimilate_tsp(
    target: np.ndarray,
    source: np.ndarray,
    rng: np.random.Generator,
    use_crossover: bool,
) -> np.ndarray:
    """TSP assimilation: OX crossover or position-copy toward leader/imperialist."""
    if use_crossover:
        return order_crossover(target, source, rng)
    n_copy = compute_assimilation_positions(len(target), 2.0)
    return copy_positions_assimilation(target, source, rng, n_copy)
