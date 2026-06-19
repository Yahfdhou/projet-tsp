"""Standalone Imperialist Competitive Algorithm for TSP."""

from __future__ import annotations

import numpy as np

from tsp_sba.algorithms.result import OptimizationResult
from tsp_sba.config import SBAParams
from tsp_sba.operators.genetic import (
    assimilate_tsp,
    inversion_mutation,
)
from tsp_sba.operators.local_search import maybe_two_opt
from tsp_sba.tsp.instance import TSPInstance


class ImperialistCompetitiveAlgorithm:
    """ICA adapted for TSP with position-copy assimilation and inversion revolution."""

    def __init__(self, instance: TSPInstance, params: SBAParams | None = None):
        self.instance = instance
        self.params = params or SBAParams()
        self.n = instance.n_cities
        self.num_countries = (
            self.params.num_countries * self.params.people_per_country
        )
        self.num_imperialists = self.params.num_imperialists

    def _evaluate(self, countries: np.ndarray) -> np.ndarray:
        return np.array([self.instance.tour_length(c) for c in countries])

    def _initialize(self, rng: np.random.Generator) -> np.ndarray:
        countries = np.array([rng.permutation(self.n) for _ in range(self.num_countries)])
        for i in range(min(3, self.num_countries)):
            start = int(rng.integers(0, self.n))
            countries[i] = self.instance.nearest_neighbor_tour(start=start)
        for i in range(self.num_countries):
            countries[i] = maybe_two_opt(countries[i], self.instance, self.params)
        return countries

    def _create_empires(
        self, countries: np.ndarray, costs: np.ndarray
    ) -> tuple[list[int], list[list[int]], np.ndarray]:
        """Form empires: imperialist indices and colony index lists."""
        sorted_idx = np.argsort(costs)
        imperialists = sorted_idx[: self.num_imperialists].tolist()
        colonies = sorted_idx[self.num_imperialists :].tolist()

        empire_colonies: list[list[int]] = [[] for _ in range(self.num_imperialists)]
        for i, col_idx in enumerate(colonies):
            empire_colonies[i % self.num_imperialists].append(int(col_idx))

        # Empire total cost = cost(imperialist) + mean(colony costs)
        empire_costs = np.zeros(self.num_imperialists)
        for e, imp_idx in enumerate(imperialists):
            col_costs = [costs[c] for c in empire_colonies[e]]
            empire_costs[e] = costs[imp_idx] + (np.mean(col_costs) if col_costs else 0)

        return imperialists, empire_colonies, empire_costs

    def _assimilate(
        self,
        countries: np.ndarray,
        imperialist_idx: int,
        colony_idx: int,
        rng: np.random.Generator,
        external: bool = False,
    ) -> np.ndarray:
        prob = self.params.pe if external else self.params.pi
        if rng.random() > prob:
            return countries[colony_idx]

        return assimilate_tsp(
            countries[colony_idx],
            countries[imperialist_idx],
            rng,
            use_crossover=not external,
        )

    def _revolution(self, tour: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        mutant = inversion_mutation(tour, rng)
        if rng.random() < self.params.pm:
            mutant = inversion_mutation(mutant, rng)
        return mutant

    def run(
        self,
        rng: np.random.Generator,
        max_decades: int | None = None,
        run_id: int = 0,
    ) -> OptimizationResult:
        max_dec = max_decades or self.n * self.params.decades_multiplier
        countries = self._initialize(rng)
        costs = self._evaluate(countries)
        history: list[float] = []

        best_idx = int(np.argmin(costs))
        best_cost = float(costs[best_idx])
        best_tour = countries[best_idx].copy()

        imperialists, empire_colonies, empire_costs = self._create_empires(countries, costs)

        for decade in range(max_dec):
            # Assimilation: internal (toward own imperialist) and external
            for e, imp_idx in enumerate(imperialists):
                for col_idx in empire_colonies[e]:
                    # Internal assimilation
                    new_tour = self._assimilate(
                        countries, imp_idx, col_idx, rng, external=False
                    )
                    # External assimilation (toward random other imperialist)
                    if rng.random() < self.params.pe and len(imperialists) > 1:
                        other = rng.choice(
                            [i for i in imperialists if i != imp_idx]
                        )
                        new_tour = self._assimilate(
                            countries, int(other), col_idx, rng, external=True
                        )

                    new_tour = maybe_two_opt(new_tour, self.instance, self.params)
                    new_cost = self.instance.tour_length(new_tour)
                    if new_cost < costs[col_idx]:
                        countries[col_idx] = new_tour
                        costs[col_idx] = new_cost

            # Revolution
            num_revolutions = max(
                1, int(self.params.revolution_rate * (self.num_countries - self.num_imperialists))
            )
            colony_indices = [
                c for cols in empire_colonies for c in cols
            ]
            if colony_indices:
                rev_targets = rng.choice(
                    colony_indices,
                    size=min(num_revolutions, len(colony_indices)),
                    replace=False,
                )
                for col_idx in rev_targets:
                    new_tour = self._revolution(countries[col_idx], rng)
                    new_tour = maybe_two_opt(new_tour, self.instance, self.params)
                    new_cost = self.instance.tour_length(new_tour)
                    countries[col_idx] = new_tour
                    costs[col_idx] = new_cost

            # Position exchange: colony replaces imperialist if better
            for e, imp_idx in enumerate(imperialists):
                for col_idx in empire_colonies[e]:
                    if costs[col_idx] < costs[imp_idx]:
                        countries[imp_idx], countries[col_idx] = (
                            countries[col_idx].copy(),
                            countries[imp_idx].copy(),
                        )
                        costs[imp_idx], costs[col_idx] = costs[col_idx], costs[imp_idx]
                        imp_idx = imperialists[e]  # updated

            # Recompute empire costs
            for e, imp_idx in enumerate(imperialists):
                col_costs = [costs[c] for c in empire_colonies[e]]
                empire_costs[e] = costs[imp_idx] + (
                    np.mean(col_costs) if col_costs else 0
                )

            # Imperialistic competition
            if len(imperialists) > 1:
                weakest_e = int(np.argmax(empire_costs))
                weakest_colonies = empire_colonies[weakest_e]
                if weakest_colonies:
                    # Remove weakest colony from weakest empire
                    weakest_col = weakest_colonies.pop(
                        int(np.argmax([costs[c] for c in weakest_colonies]))
                    )
                    # Assign to empire with highest power (lowest cost)
                    powers = 1.0 / (empire_costs + 1e-10)
                    powers /= powers.sum()
                    target_e = int(rng.choice(len(imperialists), p=powers))
                    empire_colonies[target_e].append(weakest_col)

                # Eliminate weakest empire if below threshold
                max_power = np.max(empire_costs)
                if empire_costs[weakest_e] < self.params.empire_elimination_factor * max_power:
                    if empire_colonies[weakest_e]:
                        # Merge colonies to strongest empire
                        strongest_e = int(np.argmin(empire_costs))
                        empire_colonies[strongest_e].extend(empire_colonies[weakest_e])
                        empire_colonies[weakest_e] = []

            dec_best = float(np.min(costs))
            if dec_best < best_cost:
                best_cost = dec_best
                best_tour = countries[int(np.argmin(costs))].copy()
            history.append(best_cost)

        return OptimizationResult(
            best_tour=best_tour,
            best_cost=best_cost,
            history=history,
            algorithm="ICA",
            instance_name=self.instance.name,
            run_id=run_id,
            decades=max_dec,
        )
