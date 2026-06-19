"""TSPLIB instance loader and TSP tour utilities."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class TSPInstance:
    """A symmetric TSP instance from TSPLIB format."""

    name: str
    dimension: int
    coordinates: np.ndarray  # shape (n, 2)
    edge_weight_type: str = "EUC_2D"

    def __post_init__(self) -> None:
        self._distance_matrix: np.ndarray | None = None

    @property
    def n_cities(self) -> int:
        return self.dimension

    @property
    def distance_matrix(self) -> np.ndarray:
        if self._distance_matrix is None:
            self._distance_matrix = compute_distance_matrix(self)
        return self._distance_matrix

    def tour_length(self, tour: np.ndarray) -> float:
        return tour_length(tour, self.distance_matrix)

    def random_tour(self, rng: np.random.Generator) -> np.ndarray:
        return rng.permutation(self.dimension)

    def nearest_neighbor_tour(self, start: int = 0) -> np.ndarray:
        """Constructive heuristic for initialization warm-start."""
        n = self.dimension
        unvisited = set(range(n))
        tour = [start]
        unvisited.remove(start)
        current = start
        dist = self.distance_matrix
        while unvisited:
            nxt = min(unvisited, key=lambda c: dist[current, c])
            tour.append(nxt)
            unvisited.remove(nxt)
            current = nxt
        return np.array(tour, dtype=np.int32)


def euclidean_distance(p1: np.ndarray, p2: np.ndarray) -> int:
    """TSPLIB EUC_2D: round Euclidean distance."""
    return int(round(math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)))


def compute_distance_matrix(instance: TSPInstance) -> np.ndarray:
    """Precompute full distance matrix for fast evaluation."""
    coords = instance.coordinates
    n = instance.dimension
    dist = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            d = euclidean_distance(coords[i], coords[j])
            dist[i, j] = d
            dist[j, i] = d
    return dist


def tour_length(tour: np.ndarray, distance_matrix: np.ndarray) -> float:
    """Compute closed tour length."""
    n = len(tour)
    total = 0.0
    for i in range(n):
        total += distance_matrix[tour[i], tour[(i + 1) % n]]
    return total


def is_valid_tour(tour: np.ndarray, n_cities: int) -> bool:
    """Check tour is a valid permutation of city indices."""
    if len(tour) != n_cities:
        return False
    return len(set(tour.tolist())) == n_cities and tour.min() >= 0 and tour.max() < n_cities


def load_tsplib(path: str | Path) -> TSPInstance:
    """Parse a TSPLIB .tsp file (EUC_2D coordinate format)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    name = path.stem
    dimension = 0
    edge_weight_type = "EUC_2D"
    coordinates: list[list[float]] = []

    in_coord_section = False
    for line in lines:
        upper = line.upper()
        if upper.startswith("NAME"):
            name = re.split(r"[: ]+", line, maxsplit=1)[-1].strip()
        elif upper.startswith("DIMENSION"):
            dimension = int(re.findall(r"\d+", line)[-1])
        elif upper.startswith("EDGE_WEIGHT_TYPE"):
            edge_weight_type = re.split(r"[: ]+", line, maxsplit=1)[-1].strip()
        elif upper.startswith("NODE_COORD_SECTION"):
            in_coord_section = True
            continue
        elif upper.startswith("EOF") or upper.startswith("TOUR_SECTION"):
            break
        elif in_coord_section:
            parts = line.split()
            if len(parts) >= 3:
                coordinates.append([float(parts[1]), float(parts[2])])

    if dimension == 0:
        dimension = len(coordinates)

    coords = np.array(coordinates, dtype=np.float64)
    if coords.shape[0] != dimension:
        raise ValueError(
            f"Expected {dimension} coordinates in {path}, found {coords.shape[0]}"
        )

    return TSPInstance(
        name=name,
        dimension=dimension,
        coordinates=coords,
        edge_weight_type=edge_weight_type,
    )


def load_instance_by_name(data_dir: str | Path, instance_name: str) -> TSPInstance:
    """Load a TSPLIB instance from data directory by name (without extension)."""
    data_dir = Path(data_dir)
    path = data_dir / f"{instance_name}.tsp"
    if not path.exists():
        raise FileNotFoundError(f"Instance not found: {path}")
    return load_tsplib(path)
