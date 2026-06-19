"""Run a single algorithm on one instance (debug/demo)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tsp_sba.config import ExperimentConfig, SBAParams
from tsp_sba.experiments.runner import run_single_algorithm


def main() -> None:
    parser = argparse.ArgumentParser(description="Single TSP algorithm run")
    parser.add_argument("--instance", default="berlin52")
    parser.add_argument("--algorithm", default="SBA", choices=["SBA", "EA", "ICA"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument(
        "--no-2-opt",
        action="store_true",
        help="Disable 2-opt local search",
    )
    args = parser.parse_args()

    config = ExperimentConfig(
        data_dir=str(ROOT / "data" / "tsplib"),
        params=SBAParams(use_two_opt=not args.no_2_opt),
    )
    result = run_single_algorithm(
        args.instance, args.algorithm, config, run_id=0, seed=args.seed, quick=args.quick
    )
    print(f"Algorithm:  {result.algorithm}")
    print(f"Instance:   {result.instance_name}")
    print(f"Best cost:  {result.best_cost:.2f}")
    print(f"Decades:    {result.decades}")
    print(f"Tour start: {result.best_tour[:10]}...")


if __name__ == "__main__":
    main()
