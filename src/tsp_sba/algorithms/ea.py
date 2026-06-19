"""Standalone Evolutionary Algorithm for TSP (baseline from SBA paper)."""

from __future__ import annotations

import numpy as np

from tsp_sba.algorithms.result import OptimizationResult
from tsp_sba.config import SBAParams
from tsp_sba.operators.genetic import (
    inversion_mutation,
    order_crossover,
    tournament_selection,
)
from tsp_sba.operators.local_search import maybe_two_opt
from tsp_sba.tsp.instance import TSPInstance


class EvolutionaryAlgorithm:
    """EA baseline using paper parameters: Pc=0.75, Pm=0.050505."""

    def __init__(self, instance: TSPInstance, params: SBAParams | None = None):
        self.instance = instance
        self.params = params or SBAParams()
        self.n = instance.n_cities
        # Match ICA/SBA total solution count for fair comparison (~88)
        self.pop_size = self.params.num_countries * self.params.people_per_country

    def _evaluate(self, population: np.ndarray) -> np.ndarray:
        dist = self.instance.distance_matrix
        return np.array([self.instance.tour_length(ind) for ind in population])

    def _initialize(self, rng: np.random.Generator) -> np.ndarray:
        pop = np.array([rng.permutation(self.n) for _ in range(self.pop_size)])
        # Seed with nearest-neighbor for diversity (one individual)
        pop[0] = self.instance.nearest_neighbor_tour(start=int(rng.integers(0, self.n)))
        for i in range(self.pop_size):
            pop[i] = maybe_two_opt(pop[i], self.instance, self.params)
        return pop

    def run(
        self,
        rng: np.random.Generator,
        max_decades: int | None = None,
        max_generations: int | None = None,
        run_id: int = 0,
    ) -> OptimizationResult:
        max_gen = max_decades or max_generations or self.n * self.params.decades_multiplier
        population = self._initialize(rng)
        costs = self._evaluate(population)
        history: list[float] = []

        best_idx = int(np.argmin(costs))
        best_cost = float(costs[best_idx])
        best_tour = population[best_idx].copy()

        for _ in range(max_gen):
            new_population = population.copy()
            new_costs = costs.copy()

            for i in range(self.pop_size):
                p1_idx = tournament_selection(population, costs, rng)
                p2_idx = tournament_selection(population, costs, rng)
                child = population[p1_idx].copy()

                if rng.random() < self.params.pc:
                    child = order_crossover(population[p1_idx], population[p2_idx], rng)

                if rng.random() < self.params.pm:
                    child = inversion_mutation(child, rng)

                child = maybe_two_opt(child, self.instance, self.params)
                child_cost = self.instance.tour_length(child)

                # Replacement: replace if better than current individual
                if child_cost < new_costs[i]:
                    new_population[i] = child
                    new_costs[i] = child_cost

            population = new_population
            costs = new_costs

            gen_best = float(np.min(costs))
            if gen_best < best_cost:
                best_cost = gen_best
                best_tour = population[int(np.argmin(costs))].copy()
            history.append(best_cost)

        return OptimizationResult(
            best_tour=best_tour,
            best_cost=best_cost,
            history=history,
            algorithm="EA",
            instance_name=self.instance.name,
            run_id=run_id,
            decades=max_gen,
        )
