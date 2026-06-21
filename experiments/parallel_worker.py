"""Worker process for parallel experiment runs (imported by child processes)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def pin_single_thread() -> None:
    """Each worker uses exactly 1 CPU thread so N workers = N cores at 100%."""
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"


def run_one(payload: dict) -> dict:
    """Execute a single (instance, algorithm, run_id) experiment."""
    pin_single_thread()

    root = Path(payload["root"])
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    from tsp_sba.config import ExperimentConfig, SBAParams
    from tsp_sba.experiments.runner import run_single_task_row

    instance = payload["instance"]
    algorithm = payload["algorithm"]
    run_id = payload["run_id"]
    num_runs = payload["num_runs"]

    print(
        f"[worker pid={os.getpid()}] START {algorithm}/{instance} "
        f"run {run_id + 1}/{num_runs}",
        flush=True,
    )

    params = SBAParams(**payload["params"])
    config = ExperimentConfig(
        instances=[instance],
        algorithms=[algorithm],
        params=params,
        data_dir=payload["data_dir"],
        results_dir=payload["results_dir"],
    )
    row = run_single_task_row(instance, algorithm, config, run_id, quick=payload["quick"])

    print(
        f"[worker pid={os.getpid()}] DONE {algorithm}/{instance} "
        f"run {run_id + 1}/{num_runs} cost={row['best_cost']:.2f}",
        flush=True,
    )
    return row
