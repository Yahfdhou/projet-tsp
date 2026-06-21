"""CLI entry point for running TSP-SBA experiments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running without package install
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tsp_sba.config import ExperimentConfig, SBAParams
from tsp_sba.experiments.runner import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SBA vs EA vs ICA on TSPLIB instances (Ramezani & Lotfi adaptation for TSP)"
    )
    parser.add_argument(
        "--instances",
        nargs="+",
        default=["berlin52", "eil51", "kroA100"],
        help="TSPLIB instance names (without .tsp)",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        default=["SBA", "EA", "ICA"],
        help="Algorithms to compare",
    )
    parser.add_argument("--runs", type=int, default=30, help="Independent runs per algorithm")
    parser.add_argument(
        "--decades-multiplier",
        type=int,
        default=100,
        help="max_decades = n_cities * multiplier",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(ROOT / "data" / "tsplib"),
        help="Directory containing .tsp files",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=str(ROOT / "results"),
        help="Output directory for results",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test: 3 runs, fewer decades",
    )
    parser.add_argument(
        "--no-2-opt",
        action="store_true",
        help="Disable 2-opt local search (baseline mode)",
    )
    args = parser.parse_args()

    params = SBAParams(
        num_runs=args.runs,
        decades_multiplier=args.decades_multiplier,
        use_two_opt=not args.no_2_opt,
    )
    config = ExperimentConfig(
        instances=args.instances,
        algorithms=args.algorithms,
        params=params,
        data_dir=args.data_dir,
        results_dir=args.results_dir,
    )

    num_runs = 3 if args.quick else args.runs
    print("=" * 60, flush=True)
    print("TSP-SBA Experiment", flush=True)
    print(f"  instances: {', '.join(args.instances)}", flush=True)
    print(f"  algorithms: {', '.join(args.algorithms)}", flush=True)
    print(f"  runs: {num_runs}", flush=True)
    print(f"  decades_multiplier: {args.decades_multiplier}", flush=True)
    print(f"  2-opt: {'off' if args.no_2_opt else 'on'}", flush=True)
    print("=" * 60, flush=True)

    run_experiment(config, quick=args.quick)


if __name__ == "__main__":
    main()
