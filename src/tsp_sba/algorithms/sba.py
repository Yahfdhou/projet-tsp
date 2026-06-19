"""Social-Based Algorithm (SBA) with Monarchy structure for TSP.

Hybrid of EA (within-country) and ICA (between-country/empire), following
Ramezani & Lotfi (2013) with permutation-based operators for TSP.
"""

from __future__ import annotations

import numpy as np

from tsp_sba.algorithms.result import OptimizationResult
from tsp_sba.config import SBAParams
from tsp_sba.operators.genetic import (
    assimilate_tsp,
    inversion_mutation,
    order_crossover,
    tournament_selection,
)
from tsp_sba.operators.local_search import maybe_two_opt
from tsp_sba.tsp.instance import TSPInstance


class Country:
    """A country: group of people (candidate tours) with a leader."""

    __slots__ = ("people", "costs", "leader_idx")

    def __init__(self, people: np.ndarray, costs: np.ndarray):
        self.people = people
        self.costs = costs
        self.leader_idx = int(np.argmin(costs))

    @property
    def leader(self) -> np.ndarray:
        return self.people[self.leader_idx]

    @property
    def leader_cost(self) -> float:
        return float(self.costs[self.leader_idx])

    def update_leader(self) -> None:
        self.leader_idx = int(np.argmin(self.costs))


class SocialBasedAlgorithm:
    """SBA with Monarchy social structure (best performing in original paper)."""

    def __init__(self, instance: TSPInstance, params: SBAParams | None = None):
        self.instance = instance
        self.params = params or SBAParams()
        self.n = instance.n_cities
        self.num_imperialists = self.params.num_imperialists
        self.people_per_country = self.params.people_per_country
        self.num_countries = self.params.num_countries

    def _init_countries(self, rng: np.random.Generator) -> list[Country]:
        countries: list[Country] = []
        for c in range(self.num_countries):
            people = np.array(
                [rng.permutation(self.n) for _ in range(self.people_per_country)]
            )
            if c == 0:
                people[0] = self.instance.nearest_neighbor_tour(start=0)
            for p in range(self.people_per_country):
                people[p] = maybe_two_opt(people[p], self.instance, self.params)
            costs = np.array([self.instance.tour_length(p) for p in people])
            countries.append(Country(people, costs))
        return countries

    def _ea_within_country(self, country: Country, rng: np.random.Generator) -> None:
        """Level 1: EA operators within each country (Selection, Crossover, Mutation, Replacement)."""
        n_people = len(country.people)
        for i in range(n_people):
            p1 = tournament_selection(country.people, country.costs, rng)
            p2 = tournament_selection(country.people, country.costs, rng)
            child = country.people[p1].copy()

            if rng.random() < self.params.pc:
                child = order_crossover(country.people[p1], country.people[p2], rng)

            if rng.random() < self.params.pm:
                child = inversion_mutation(child, rng)

            child = maybe_two_opt(child, self.instance, self.params)
            child_cost = self.instance.tour_length(child)
            if child_cost < country.costs[i]:
                country.people[i] = child
                country.costs[i] = child_cost

        country.update_leader()

    def _get_emperor(self, countries: list[Country]) -> tuple[int, np.ndarray]:
        """Monarchy: emperor is the best leader among all countries."""
        costs = [c.leader_cost for c in countries]
        emperor_idx = int(np.argmin(costs))
        return emperor_idx, countries[emperor_idx].leader

    def _form_empires(
        self, countries: list[Country]
    ) -> tuple[list[int], list[list[int]], np.ndarray]:
        """Form empires from country leaders (high-level ICA structure)."""
        leader_costs = np.array([c.leader_cost for c in countries])
        sorted_idx = np.argsort(leader_costs)
        imperialists = sorted_idx[: self.num_imperialists].tolist()
        colonies = sorted_idx[self.num_imperialists :].tolist()

        empire_colonies: list[list[int]] = [[] for _ in range(self.num_imperialists)]
        for i, col_idx in enumerate(colonies):
            empire_colonies[i % self.num_imperialists].append(int(col_idx))

        empire_costs = np.zeros(self.num_imperialists)
        for e, imp_idx in enumerate(imperialists):
            col_costs = [countries[c].leader_cost for c in empire_colonies[e]]
            empire_costs[e] = countries[imp_idx].leader_cost + (
                np.mean(col_costs) if col_costs else 0
            )

        return imperialists, empire_colonies, empire_costs

    def _assimilate_person(
        self,
        person: np.ndarray,
        source: np.ndarray,
        rng: np.random.Generator,
        prob: float,
        external: bool = False,
    ) -> np.ndarray:
        if rng.random() > prob:
            return person
        return assimilate_tsp(person, source, rng, use_crossover=not external)

    def _ica_between_countries(
        self,
        countries: list[Country],
        imperialists: list[int],
        empire_colonies: list[list[int]],
        empire_costs: np.ndarray,
        emperor_tour: np.ndarray,
        rng: np.random.Generator,
    ) -> tuple[list[int], list[list[int]], np.ndarray]:
        """Level 2: ICA operators between countries and empires."""

        # Internal assimilation: colony country people toward own imperialist leader
        for e, imp_idx in enumerate(imperialists):
            imp_leader = countries[imp_idx].leader
            for col_country_idx in empire_colonies[e]:
                country = countries[col_country_idx]
                for p in range(len(country.people)):
                    new_tour = self._assimilate_person(
                        country.people[p],
                        imp_leader,
                        rng,
                        self.params.pi,
                        external=False,
                    )
                    new_tour = maybe_two_opt(new_tour, self.instance, self.params)
                    new_cost = self.instance.tour_length(new_tour)
                    if new_cost < country.costs[p]:
                        country.people[p] = new_tour
                        country.costs[p] = new_cost
                country.update_leader()

        # External assimilation + Monarchy: toward emperor and other imperialists
        for e, imp_idx in enumerate(imperialists):
            for col_country_idx in empire_colonies[e]:
                country = countries[col_country_idx]
                for p in range(len(country.people)):
                    source = emperor_tour  # Monarchy: emperor guides all
                    if rng.random() < self.params.pe and len(imperialists) > 1:
                        other_imp = int(
                            rng.choice([i for i in imperialists if i != imp_idx])
                        )
                        source = countries[other_imp].leader
                    new_tour = self._assimilate_person(
                        country.people[p], source, rng, self.params.pe, external=True
                    )
                    new_tour = maybe_two_opt(new_tour, self.instance, self.params)
                    new_cost = self.instance.tour_length(new_tour)
                    if new_cost < country.costs[p]:
                        country.people[p] = new_tour
                        country.costs[p] = new_cost
                country.update_leader()

        # Revolution: random inversion on random persons in colony countries
        all_colony_countries = [c for cols in empire_colonies for c in cols]
        num_rev = max(
            1,
            int(
                self.params.revolution_rate
                * len(all_colony_countries)
                * self.people_per_country
                * 0.1
            ),
        )
        for _ in range(num_rev):
            if not all_colony_countries:
                break
            c_idx = int(rng.choice(all_colony_countries))
            p_idx = int(rng.integers(0, self.people_per_country))
            new_tour = inversion_mutation(countries[c_idx].people[p_idx], rng)
            new_tour = maybe_two_opt(new_tour, self.instance, self.params)
            new_cost = self.instance.tour_length(new_tour)
            countries[c_idx].people[p_idx] = new_tour
            countries[c_idx].costs[p_idx] = new_cost
            countries[c_idx].update_leader()

        # Position exchange: colony country leader replaces imperialist if better
        for e, imp_idx in enumerate(imperialists):
            for col_idx in empire_colonies[e]:
                if countries[col_idx].leader_cost < countries[imp_idx].leader_cost:
                    # Swap leaders (exchange best tours between countries)
                    imp_leader_p = countries[imp_idx].leader_idx
                    col_leader_p = countries[col_idx].leader_idx
                    (
                        countries[imp_idx].people[imp_leader_p],
                        countries[col_idx].people[col_leader_p],
                    ) = (
                        countries[col_idx].people[col_leader_p].copy(),
                        countries[imp_idx].people[imp_leader_p].copy(),
                    )
                    (
                        countries[imp_idx].costs[imp_leader_p],
                        countries[col_idx].costs[col_leader_p],
                    ) = (
                        countries[col_idx].costs[col_leader_p],
                        countries[imp_idx].costs[imp_leader_p],
                    )
                    countries[imp_idx].update_leader()
                    countries[col_idx].update_leader()

        # Imperialistic competition on empire structure
        if len(imperialists) > 1:
            weakest_e = int(np.argmax(empire_costs))
            weakest_cols = empire_colonies[weakest_e]
            if weakest_cols:
                costs = [countries[c].leader_cost for c in weakest_cols]
                removed = weakest_cols.pop(int(np.argmax(costs)))
                powers = 1.0 / (empire_costs + 1e-10)
                powers /= powers.sum()
                target_e = int(rng.choice(len(imperialists), p=powers))
                empire_colonies[target_e].append(removed)

            max_power = np.max(empire_costs)
            if empire_costs[weakest_e] < self.params.empire_elimination_factor * max_power:
                if empire_colonies[weakest_e]:
                    strongest_e = int(np.argmin(empire_costs))
                    empire_colonies[strongest_e].extend(empire_colonies[weakest_e])
                    empire_colonies[weakest_e] = []

        # Recompute empire costs
        for e, imp_idx in enumerate(imperialists):
            col_costs = [countries[c].leader_cost for c in empire_colonies[e]]
            empire_costs[e] = countries[imp_idx].leader_cost + (
                np.mean(col_costs) if col_costs else 0
            )

        return imperialists, empire_colonies, empire_costs

    def run(
        self,
        rng: np.random.Generator,
        max_decades: int | None = None,
        run_id: int = 0,
    ) -> OptimizationResult:
        max_dec = max_decades or self.n * self.params.decades_multiplier
        countries = self._init_countries(rng)
        history: list[float] = []

        all_costs = [c.leader_cost for c in countries]
        best_cost = float(min(all_costs))
        best_tour = countries[int(np.argmin(all_costs))].leader.copy()

        imperialists, empire_colonies, empire_costs = self._form_empires(countries)

        for _ in range(max_dec):
            # Level 1: EA within each country
            for country in countries:
                self._ea_within_country(country, rng)

            # Update emperor (Monarchy)
            _, emperor_tour = self._get_emperor(countries)

            # Re-form empires based on updated leaders
            imperialists, empire_colonies, empire_costs = self._form_empires(countries)

            # Level 2: ICA between countries
            imperialists, empire_colonies, empire_costs = self._ica_between_countries(
                countries,
                imperialists,
                empire_colonies,
                empire_costs,
                emperor_tour,
                rng,
            )

            dec_best = min(c.leader_cost for c in countries)
            if dec_best < best_cost:
                best_cost = dec_best
                best_idx = int(np.argmin([c.leader_cost for c in countries]))
                best_tour = countries[best_idx].leader.copy()
            history.append(best_cost)

        return OptimizationResult(
            best_tour=best_tour,
            best_cost=best_cost,
            history=history,
            algorithm="SBA",
            instance_name=self.instance.name,
            run_id=run_id,
            decades=max_dec,
        )
