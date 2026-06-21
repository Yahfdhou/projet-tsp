"""CLI entry point for running TSP-SBA experiments."""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

# Allow running without package install
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from parallel_worker import pin_single_thread, run_one
from tsp_sba.config import ExperimentConfig, SBAParams
from tsp_sba.experiments.runner import run_instance_algorithm, save_experiment_results


def resolve_workers(requested: int, sequential: bool) -> int:
    """Use exactly the requested worker count (default 4), unless --sequential."""
    if sequential:
        return 1
    env_workers = os.environ.get("TSP_WORKERS")
    if env_workers is not None:
        return max(1, int(env_workers))
    return max(1, requested)


def main() -> None:
    pin_single_thread()

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
        default=int(os.environ.get("TSP_WORKERS", "4")),
        help="Number of parallel worker processes (default: 4)",
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
    workers = resolve_workers(args.workers, args.sequential)
    run_tasks = [
        (instance, algorithm, run_id)
        for instance, algorithm in product(args.instances, args.algorithms)
        for run_id in range(num_runs)
    ]

    print("=" * 60, flush=True)
    print("TSP-SBA Experiment (Multi-Core v3)", flush=True)
    print(f"  main pid: {os.getpid()}", flush=True)
    print(f"  os.cpu_count(): {os.cpu_count()}", flush=True)
    print(f"  parallel workers: {workers}", flush=True)
    print(f"  OMP_NUM_THREADS: {os.environ.get('OMP_NUM_THREADS', 'not set')}", flush=True)
    print(f"  instances: {', '.join(args.instances)}", flush=True)
    print(f"  algorithms: {', '.join(args.algorithms)}", flush=True)
    print(f"  runs per algo: {num_runs}", flush=True)
    print(f"  total parallel tasks: {len(run_tasks)}", flush=True)
    print(f"  2-opt: {'off' if args.no_2_opt else 'on'}", flush=True)
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

    payloads = [
        {
            "root": str(ROOT),
            "instance": instance,
            "algorithm": algorithm,
            "run_id": run_id,
            "num_runs": num_runs,
            "params": param_fields,
            "data_dir": args.data_dir,
            "results_dir": args.results_dir,
            "quick": args.quick,
        }
        for instance, algorithm, run_id in run_tasks
    ]

    all_rows: list[dict] = []

    if workers == 1:
        print("SEQUENTIAL mode (1 CPU)", flush=True)
        for instance, algorithm in product(args.instances, args.algorithms):
            rows = run_instance_algorithm(
                instance, algorithm, config, quick=args.quick, verbose=True
            )
            all_rows.extend(rows)
    else:
        print(
            f"PARALLEL mode: {workers} worker processes will run AT THE SAME TIME",
            flush=True,
        )
        print(f"Submitting {len(payloads)} tasks...", flush=True)

        # spawn = safe on Windows and Linux/Docker
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=ctx,
            initializer=pin_single_thread,
        ) as executor:
            futures = [executor.submit(run_one, p) for p in payloads]
            done = 0
            for future in as_completed(futures):
                all_rows.append(future.result())
                done += 1
                if done % workers == 0 or done == len(futures):
                    print(f"Progress: {done}/{len(futures)} runs completed", flush=True)

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
