"""Experiment runner: SBA vs EA vs ICA on TSPLIB instances."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from tsp_sba.algorithms.ea import EvolutionaryAlgorithm
from tsp_sba.algorithms.ica import ImperialistCompetitiveAlgorithm
from tsp_sba.algorithms.result import OptimizationResult
from tsp_sba.algorithms.sba import SocialBasedAlgorithm
from tsp_sba.config import ExperimentConfig, SBAParams
from tsp_sba.statistics.wilcoxon import (
    performance_improvement,
    summarize_runs,
    wilcoxon_signed_rank_test,
)
from tsp_sba.tsp.instance import load_instance_by_name
from tsp_sba.utils.random import make_rng


def get_algorithm(instance, name: str, params: SBAParams):
    algorithms = {
        "SBA": SocialBasedAlgorithm,
        "EA": EvolutionaryAlgorithm,
        "ICA": ImperialistCompetitiveAlgorithm,
    }
    if name not in algorithms:
        raise ValueError(f"Unknown algorithm: {name}")
    return algorithms[name](instance, params)


def run_single_algorithm(
    instance_name: str,
    algorithm_name: str,
    config: ExperimentConfig,
    run_id: int,
    seed: int,
    quick: bool = False,
) -> OptimizationResult:
    instance = load_instance_by_name(config.data_dir, instance_name)
    algo = get_algorithm(instance, algorithm_name, config.params)
    rng = make_rng(seed)

    max_decades = instance.n_cities * config.params.decades_multiplier
    if quick:
        max_decades = max(50, max_decades // 20)

    return algo.run(rng=rng, max_decades=max_decades, run_id=run_id)


def make_run_seed(instance_name: str, algorithm_name: str, run_id: int) -> int:
    """Reproducible seed for one independent run."""
    return (hash(instance_name) % 10000) * 1000 + run_id * 17 + hash(algorithm_name) % 100


def run_single_task_row(
    instance_name: str,
    algorithm_name: str,
    config: ExperimentConfig,
    run_id: int,
    quick: bool = False,
) -> dict:
    """Execute one run and return a single result row."""
    seed = make_run_seed(instance_name, algorithm_name, run_id)
    result = run_single_algorithm(
        instance_name, algorithm_name, config, run_id, seed, quick=quick
    )
    return {
        "instance": instance_name,
        "algorithm": algorithm_name,
        "run_id": run_id,
        "best_cost": result.best_cost,
        "decades": result.decades,
        "seed": seed,
    }


def run_instance_algorithm(
    instance_name: str,
    algorithm_name: str,
    config: ExperimentConfig,
    quick: bool = False,
    verbose: bool = True,
) -> list[dict]:
    """Run all independent runs for one (instance, algorithm) pair."""
    num_runs = 3 if quick else config.params.num_runs
    rows: list[dict] = []

    if verbose:
        print(f"  [{instance_name}] {algorithm_name} — starting {num_runs} runs...", flush=True)

    for run_id in range(num_runs):
        if verbose:
            print(
                f"    [{instance_name}/{algorithm_name}] run {run_id + 1}/{num_runs}...",
                end=" ",
                flush=True,
            )
        seed = make_run_seed(instance_name, algorithm_name, run_id)
        result = run_single_algorithm(
            instance_name, algorithm_name, config, run_id, seed, quick=quick
        )
        rows.append(
            {
                "instance": instance_name,
                "algorithm": algorithm_name,
                "run_id": run_id,
                "best_cost": result.best_cost,
                "decades": result.decades,
                "seed": seed,
            }
        )
        if verbose:
            print(f"cost={result.best_cost:.2f}", flush=True)

    if verbose:
        costs = [r["best_cost"] for r in rows]
        print(
            f"  [{instance_name}] {algorithm_name} done: "
            f"mean={np.mean(costs):.2f}, best={np.min(costs):.2f}",
            flush=True,
        )

    return rows


def load_checkpoint_rows(run_dir: Path) -> list[dict]:
    """Load rows already saved in a partial experiment."""
    path = run_dir / "raw_results.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    return df.to_dict("records")


def completed_task_keys(rows: list[dict]) -> set[tuple[str, str, int]]:
    return {
        (str(r["instance"]), str(r["algorithm"]), int(r["run_id"]))
        for r in rows
    }


def append_checkpoint_row(run_dir: Path, row: dict) -> None:
    """Append one finished run to raw_results.csv (safe for long parallel jobs)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "raw_results.csv"
    df = pd.DataFrame([row])
    if path.exists():
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)


def save_experiment_results(
    all_rows: list[dict],
    config: ExperimentConfig,
    quick: bool,
    run_dir: Path,
    parallel_workers: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Write CSV/JSON artifacts from collected raw rows."""
    run_dir.mkdir(parents=True, exist_ok=True)
    num_runs = 3 if quick else config.params.num_runs

    df = pd.DataFrame(all_rows)
    df = df.sort_values(["instance", "algorithm", "run_id"]).reset_index(drop=True)
    df.to_csv(run_dir / "raw_results.csv", index=False)

    results_by_instance: dict[str, dict[str, list[float]]] = {}
    for instance_name in config.instances:
        results_by_instance[instance_name] = {alg: [] for alg in config.algorithms}

    for instance_name in config.instances:
        for alg in config.algorithms:
            alg_rows = df[(df["instance"] == instance_name) & (df["algorithm"] == alg)]
            results_by_instance[instance_name][alg] = alg_rows["best_cost"].tolist()

    summary_rows = []
    wilcoxon_rows = []
    optimal = config.known_optima

    for instance_name in config.instances:
        for alg in config.algorithms:
            costs = np.array(results_by_instance[instance_name][alg])
            stats = summarize_runs(costs)
            opt = optimal.get(instance_name)
            gap = 100.0 * (stats["mean"] - opt) / opt if opt else None
            summary_rows.append(
                {
                    "instance": instance_name,
                    "algorithm": alg,
                    "runs": len(costs),
                    "mean": stats["mean"],
                    "std": stats["std"],
                    "min": stats["min"],
                    "max": stats["max"],
                    "median": stats["median"],
                    "known_optimum": opt,
                    "gap_percent": gap,
                }
            )

        if "SBA" in config.algorithms:
            sba_costs = np.array(results_by_instance[instance_name]["SBA"])
            for other in ["EA", "ICA"]:
                if other not in config.algorithms:
                    continue
                other_costs = np.array(results_by_instance[instance_name][other])
                w = wilcoxon_signed_rank_test(sba_costs, other_costs, "SBA", other)
                wilcoxon_rows.append(
                    {
                        "instance": instance_name,
                        "algorithm_a": "SBA",
                        "algorithm_b": other,
                        "mean_sba": w.mean_a,
                        "mean_other": w.mean_b,
                        "p_value": w.p_value,
                        "significant_0.05": w.significant_at_05,
                        "better": w.better_algorithm,
                        "improvement_pct": performance_improvement(w.mean_a, w.mean_b),
                    }
                )

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(run_dir / "summary_statistics.csv", index=False)

    wilcoxon_df = pd.DataFrame(wilcoxon_rows)
    wilcoxon_df.to_csv(run_dir / "wilcoxon_tests.csv", index=False)

    timestamp = run_dir.name.removeprefix("experiment_")
    meta = {
        "timestamp": timestamp,
        "instances": config.instances,
        "algorithms": config.algorithms,
        "num_runs": num_runs,
        "quick_mode": quick,
        "parallel_workers": parallel_workers,
        "params": {
            "pc": config.params.pc,
            "pm": config.params.pm,
            "pe": config.params.pe,
            "pi": config.params.pi,
            "assimilation_coefficient": config.params.assimilation_coefficient,
            "num_imperialists": config.params.num_imperialists,
            "num_countries": config.params.num_countries,
            "people_per_country": config.params.people_per_country,
            "social_structure": config.params.social_structure,
            "decades_multiplier": config.params.decades_multiplier,
            "use_two_opt": config.params.use_two_opt,
        },
    }
    (run_dir / "experiment_config.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    return summary_df, wilcoxon_df


def run_experiment(
    config: ExperimentConfig | None = None,
    quick: bool = False,
    verbose: bool = True,
    parallel_workers: int = 1,
) -> Path:
    """Run full comparison experiment and save results to CSV/JSON."""
    config = config or ExperimentConfig()
    results_dir = Path(config.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = results_dir / f"experiment_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []

    for instance_name in config.instances:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Instance: {instance_name}")
            print(f"{'='*60}")

        for alg in config.algorithms:
            rows = run_instance_algorithm(
                instance_name, alg, config, quick=quick, verbose=verbose
            )
            all_rows.extend(rows)

    summary_df, wilcoxon_df = save_experiment_results(
        all_rows, config, quick, run_dir, parallel_workers=parallel_workers
    )

    if verbose:
        print(f"\n\nResults saved to: {run_dir}")
        print("\n--- Summary ---")
        print(summary_df.to_string(index=False))
        print("\n--- Wilcoxon Tests (SBA vs others) ---")
        print(wilcoxon_df.to_string(index=False))

    return run_dir
