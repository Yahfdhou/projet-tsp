"""Algorithm parameters from Ramezani & Lotfi (2012/2013) SBA paper."""

from dataclasses import dataclass, field
from typing import Literal

SocialStructure = Literal["monarchy", "republic", "autocracy", "multinational"]


@dataclass
class SBAParams:
    """Parameters reported in the SBA paper and used in this TSP adaptation."""

    # Evolutionary Algorithm (within-country) operators
    pc: float = 0.75  # crossover probability
    pm: float = 0.050505  # mutation probability

    # Imperialist Competitive Algorithm (between-country) operators
    pe: float = 0.1  # external assimilation probability
    pi: float = 0.1  # internal assimilation probability
    assimilation_coefficient: float = 2.0  # beta in ICA assimilation
    revolution_rate: float = 0.3  # fraction of colonies that undergo revolution
    revolution_deviation: float = 0.1  # zeta: revolution perturbation scale
    empire_elimination_factor: float = 0.02  # tau: weakest empire elimination threshold

    # Population structure (ICA standard: ~88 solutions, 8 imperialists)
    num_imperialists: int = 8
    num_countries: int = 22  # countries at the ICA level
    people_per_country: int = 4  # persons (solutions) inside each country
    # Total population = num_countries * people_per_country = 88

    # Social structure (Monarchy achieved best results in the paper)
    social_structure: SocialStructure = "monarchy"

    # Termination: decades = full EA+ICA cycles
    # Paper (continuous functions): n × 100
    # TSP + 2-opt: n × 20 is enough (2-opt compensates; ×100 is impractically slow)
    decades_multiplier: int = 100  # overridden at CLI when use_two_opt (see run_comparison)

    # TSP-adapted defaults (Ramezani paper uses 100 on continuous benchmarks)
    paper_decades_multiplier: int = 100
    tsp_2opt_decades_multiplier: int = 20

    # TSP local search (2-opt) — applied after offspring/assimilation when enabled
    use_two_opt: bool = True

    # Experimental protocol (paper)
    num_runs: int = 30
    random_seed: int | None = None


@dataclass
class ExperimentConfig:
    """Configuration for benchmark experiments on TSPLIB instances."""

    instances: list[str] = field(
        default_factory=lambda: ["berlin52", "eil51", "kroA100"]
    )
    algorithms: list[str] = field(default_factory=lambda: ["SBA", "EA", "ICA"])
    params: SBAParams = field(default_factory=SBAParams)
    data_dir: str = "data/tsplib"
    results_dir: str = "results"

    # Known optimal tour lengths (TSPLIB)
    known_optima: dict[str, float] = field(
        default_factory=lambda: {
            "berlin52": 7542.0,
            "eil51": 426.0,
            "kroA100": 21282.0,
        }
    )
