"""Plot convergence curves from experiment results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def plot_summary(summary_csv: Path, output: Path) -> None:
    df = pd.read_csv(summary_csv)
    instances = df["instance"].unique()

    fig, axes = plt.subplots(1, len(instances), figsize=(5 * len(instances), 4))
    if len(instances) == 1:
        axes = [axes]

    for ax, inst in zip(axes, instances):
        sub = df[df["instance"] == inst]
        algos = sub["algorithm"].tolist()
        means = sub["mean"].tolist()
        stds = sub["std"].tolist()
        ax.bar(algos, means, yerr=stds, capsize=4, color=["#2ecc71", "#3498db", "#e74c3c"])
        opt = sub["known_optimum"].iloc[0]
        if pd.notna(opt):
            ax.axhline(opt, color="black", linestyle="--", label=f"Optimum ({opt:.0f})")
        ax.set_title(inst)
        ax.set_ylabel("Tour length (mean)")
        ax.legend()

    plt.tight_layout()
    plt.savefig(output, dpi=150)
    print(f"Saved: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=str, help="Experiment results directory")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    summary = results_dir / "summary_statistics.csv"
    if not summary.exists():
        print(f"Not found: {summary}")
        sys.exit(1)

    plot_summary(summary, results_dir / "comparison_barplot.png")


if __name__ == "__main__":
    main()
