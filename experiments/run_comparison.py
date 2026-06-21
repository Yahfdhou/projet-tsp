"""CLI entry point for running TSP-SBA experiments."""

from __future__ import annotations

import argparse
import concurrent.futures
import itertools
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running without package install
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tsp_sba.config import ExperimentConfig, SBAParams
from tsp_sba.experiments.runner import run_instance_algorithm, save_experiment_results


def _run_parallel_task(payload: dict) -> list[dict]:
    """Worker: one (instance, algorithm) on a separate CPU core."""
    root = Path(payload["root"])
    if str(root / "src") not in sys.path:
        sys.path.insert(0, str(root / "src"))

    params = SBAParams(**payload["params"])
    config = ExperimentConfig(
        instances=[payload["instance"]],
        algorithms=[payload["algorithm"]],
        params=params,
        data_dir=payload["data_dir"],
        results_dir=payload["results_dir"],
    )
    return run_instance_algorithm(
        payload["instance"],
        payload["algorithm"],
        config,
        quick=payload["quick"],
        verbose=True,
    )


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
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of CPU cores for parallel execution (default: 4)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run on a single core (disable parallel processing)",
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
    workers = 1 if args.sequential else max(1, args.workers)
    tasks = list(itertools.product(args.instances, args.algorithms))

    print("=" * 60, flush=True)
    print("TSP-SBA Experiment", flush=True)
    print(f"  instances: {', '.join(args.instances)}", flush=True)
    print(f"  algorithms: {', '.join(args.algorithms)}", flush=True)
    print(f"  runs: {num_runs}", flush=True)
    print(f"  decades_multiplier: {args.decades_multiplier}", flush=True)
    print(f"  2-opt: {'off' if args.no_2_opt else 'on'}", flush=True)
    print(f"  parallel workers: {workers}", flush=True)
    print(f"  tasks: {len(tasks)} (instance × algorithm)", flush=True)
    print("=" * 60, flush=True)

    results_dir = Path(config.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = results_dir / f"experiment_{timestamp}"

    param_fields = {
        "num_runs": params.num_runs,
        "decades_multiplier": params.decades_multiplier,
        "use_two_opt": params.use_two_opt,
        "pc": params.pc,
        "pm": params.pm,
        "pe": params.pe,
        "pi": params.pi,
        "assimilation_coefficient": params.assimilation_coefficient,
        "num_imperialists": params.num_imperialists,
        "num_countries": params.num_countries,
        "people_per_country": params.people_per_country,
        "social_structure": params.social_structure,
    }

    all_rows: list[dict] = []

    if workers == 1:
        for instance, algorithm in tasks:
            rows = run_instance_algorithm(
                instance, algorithm, config, quick=args.quick, verbose=True
            )
            all_rows.extend(rows)
    else:
        print(f"Distributing {len(tasks)} tasks across {workers} CPU cores...", flush=True)
        payloads = [
            {
                "root": str(ROOT),
                "instance": instance,
                "algorithm": algorithm,
                "params": param_fields,
                "data_dir": args.data_dir,
                "results_dir": args.results_dir,
                "quick": args.quick,
            }
            for instance, algorithm in tasks
        ]

        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_run_parallel_task, payload): (
                    payload["instance"],
                    payload["algorithm"],
                )
                for payload in payloads
            }
            for future in concurrent.futures.as_completed(futures):
                instance, algorithm = futures[future]
                try:
                    rows = future.result()
                    all_rows.extend(rows)
                    print(
                        f"[done] {algorithm} on {instance} "
                        f"({len(rows)} runs completed)",
                        flush=True,
                    )
                except Exception as exc:
                    print(
                        f"[error] {algorithm} on {instance} failed: {exc}",
                        flush=True,
                    )
                    raise

    summary_df, wilcoxon_df = save_experiment_results(
        all_rows, config, args.quick, run_dir, parallel_workers=workers
    )

    print(f"\n\nResults saved to: {run_dir}", flush=True)
    print("\n--- Summary ---", flush=True)
    print(summary_df.to_string(index=False), flush=True)
    print("\n--- Wilcoxon Tests (SBA vs others) ---", flush=True)
    print(wilcoxon_df.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
