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
from tsp_sba.experiments.runner import (
    append_checkpoint_row,
    completed_task_keys,
    load_checkpoint_rows,
    run_instance_algorithm,
    save_experiment_results,
)


def resolve_decades_multiplier(
    explicit: int | None,
    use_two_opt: bool,
    quick: bool,
) -> tuple[int, str]:
    """Pick decades multiplier: paper ×100 without 2-opt, TSP ×20 with 2-opt."""
    if explicit is not None:
        return explicit, "manual (--decades-multiplier)"
    if quick:
        return 100, "quick mode (decades divided by 20 in runner)"
    if use_two_opt:
        return 20, "TSP default with 2-opt (paper uses ×100 on continuous functions only)"
    return 100, "paper default without 2-opt (×100)"


def resolve_workers(requested: int, sequential: bool) -> int:
    """Always use the requested worker count unless --sequential."""
    if sequential:
        return 1
    env_workers = os.environ.get("TSP_WORKERS")
    if env_workers is not None:
        return max(1, int(env_workers))
    return max(1, requested)


def find_latest_partial_run(results_dir: Path, expected_tasks: int) -> Path | None:
    """Find the most recent experiment folder that is not finished yet."""
    candidates = sorted(results_dir.glob("experiment_*"), reverse=True)
    for run_dir in candidates:
        rows = load_checkpoint_rows(run_dir)
        if 0 < len(rows) < expected_tasks:
            return run_dir
    return None


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
        default=None,
        help="max_decades = n_cities × multiplier (default: 20 with 2-opt, 100 without)",
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
        default=int(os.environ.get("TSP_WORKERS", "2")),
        help="Number of parallel worker processes (default: 2)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run on a single core (disable parallel processing)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default="",
        help="Resume a partial experiment folder (e.g. results/experiment_20260621_175659)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start a new experiment folder (do not auto-resume old partial runs)",
    )
    args = parser.parse_args()

    use_two_opt = not args.no_2_opt
    decades_multiplier, decades_reason = resolve_decades_multiplier(
        args.decades_multiplier, use_two_opt, args.quick
    )

    params = SBAParams(
        num_runs=args.runs,
        decades_multiplier=decades_multiplier,
        use_two_opt=use_two_opt,
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
    total_tasks = len(args.instances) * len(args.algorithms) * num_runs
    run_tasks = [
        (instance, algorithm, run_id)
        for instance, algorithm in product(args.instances, args.algorithms)
        for run_id in range(num_runs)
    ]

    results_dir = Path(config.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    if args.resume:
        run_dir = Path(args.resume)
        if not run_dir.exists():
            run_dir = results_dir / Path(args.resume).name
    elif args.fresh:
        run_dir = None
    else:
        run_dir = find_latest_partial_run(results_dir, total_tasks)

    if run_dir is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = results_dir / f"experiment_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        existing_rows: list[dict] = []
    else:
        existing_rows = load_checkpoint_rows(run_dir)
        print(f"Resuming experiment: {run_dir} ({len(existing_rows)}/{total_tasks} done)", flush=True)

    completed = completed_task_keys(existing_rows)

    print("=" * 60, flush=True)
    print("TSP-SBA Experiment (Multi-Core v5 — reduced decades for TSP)", flush=True)
    print(f"  main pid: {os.getpid()}", flush=True)
    print(f"  os.cpu_count(): {os.cpu_count()}", flush=True)
    print(f"  parallel workers: {workers}", flush=True)
    print(f"  OMP_NUM_THREADS: {os.environ.get('OMP_NUM_THREADS', '1')}", flush=True)
    print(f"  output: {run_dir}", flush=True)
    print(f"  instances: {', '.join(args.instances)}", flush=True)
    print(f"  algorithms: {', '.join(args.algorithms)}", flush=True)
    print(f"  runs per algo: {num_runs}", flush=True)
    print(f"  decades_multiplier: {decades_multiplier} ({decades_reason})", flush=True)
    print(
        f"  max_decades (= n_villes × {decades_multiplier}):",
        flush=True,
    )
    for inst in args.instances:
        try:
            from tsp_sba.tsp.instance import load_instance_by_name

            n = load_instance_by_name(args.data_dir, inst).n_cities
            max_dec = n * decades_multiplier
            if args.quick:
                max_dec = max(50, max_dec // 20)
            print(f"    {inst}: {n} villes → {max_dec} decades", flush=True)
        except Exception:
            print(f"    {inst}: n × {decades_multiplier}", flush=True)
    print(f"  total tasks: {total_tasks} | remaining: {total_tasks - len(completed)}", flush=True)
    print(f"  2-opt: {'off' if args.no_2_opt else 'on'}", flush=True)
    print("=" * 60, flush=True)

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
        if (instance, algorithm, run_id) not in completed
    ]

    all_rows = list(existing_rows)

    if not payloads:
        print("All tasks already completed.", flush=True)
    elif workers == 1:
        print("SEQUENTIAL mode (1 CPU)", flush=True)
        for instance, algorithm in product(args.instances, args.algorithms):
            rows = run_instance_algorithm(
                instance, algorithm, config, quick=args.quick, verbose=True
            )
            for row in rows:
                if (row["instance"], row["algorithm"], int(row["run_id"])) not in completed:
                    append_checkpoint_row(run_dir, row)
                    all_rows.append(row)
    else:
        print(
            f"PARALLEL mode: {workers} workers run AT THE SAME TIME on {workers} vCPUs",
            flush=True,
        )
        print(f"Submitting {len(payloads)} remaining tasks...", flush=True)

        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=ctx,
            initializer=pin_single_thread,
            max_tasks_per_child=1,
        ) as executor:
            futures = [executor.submit(run_one, p) for p in payloads]
            done = len(completed)
            for future in as_completed(futures):
                row = future.result()
                append_checkpoint_row(run_dir, row)
                all_rows.append(row)
                done += 1
                if done % workers == 0 or done == total_tasks:
                    print(f"Progress: {done}/{total_tasks} runs saved", flush=True)

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
