#!/usr/bin/env python3
"""
Plot GA results from saved JSON files in the results/ directory.
Usage:
  python plot_results.py C101          # plots all runs for C101
  python plot_results.py C101 C201     # compare two instances
  python plot_results.py --all         # plots every instance found
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np


RESULTS_DIR = "results"


def load_runs(instance_name: str) -> list[dict]:
    """Load all run JSON files for a given instance."""
    folder = Path(RESULTS_DIR) / instance_name.replace(".txt", "")
    if not folder.exists():
        raise FileNotFoundError(f"No results found for {instance_name} at {folder}")

    runs = []
    for f in sorted(folder.glob("run_*.json")):
        with open(f) as fp:
            runs.append(json.load(fp))
    return runs


def load_summary(instance_name: str) -> dict | None:
    """Load summary JSON for a given instance."""
    folder = Path(RESULTS_DIR) / instance_name.replace(".txt", "")
    summary_path = folder / "summary.json"
    if summary_path.exists():
        with open(summary_path) as f:
            return json.load(f)
    return None


def plot_convergence(instance_name: str, runs: list[dict], ax: plt.Axes) -> None:
    """Plot best and average fitness over generations for all runs."""
    colors = plt.cm.tab10.colors

    for i, run in enumerate(runs):
        best_record = run.get("bestRecord", [])
        avg_record = run.get("avgRecord", [])
        generations = range(len(best_record))

        ax.plot(generations, best_record,
                color=colors[i % len(colors)],
                alpha=0.8, linewidth=1.5,
                label=f"Run {i+1} best")
        ax.plot(generations, avg_record,
                color=colors[i % len(colors)],
                alpha=0.3, linewidth=1, linestyle="--")

    ax.set_title(f"Convergence — {instance_name}", fontsize=12, fontweight="bold")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)


def plot_fitness_distribution(instance_name: str, runs: list[dict], ax: plt.Axes) -> None:
    """Box plot + scatter of best fitness per run."""
    fitness_values = [r["best_fitness"] for r in runs if r.get("best_fitness") != float("inf")]

    if not fitness_values:
        ax.text(0.5, 0.5, "No feasible solutions", ha="center", va="center")
        return

    bp = ax.boxplot(fitness_values, patch_artist=True,
                    boxprops=dict(facecolor="#4C9BE8", alpha=0.6),
                    medianprops=dict(color="red", linewidth=2))

    # Overlay individual points
    x = np.random.normal(1, 0.04, size=len(fitness_values))
    ax.scatter(x, fitness_values, alpha=0.7, color="#1a5fa8", s=30, zorder=3)

    ax.set_title(f"Fitness Distribution — {instance_name}", fontsize=12, fontweight="bold")
    ax.set_ylabel("Best Fitness")
    ax.set_xticks([])
    ax.grid(True, alpha=0.3, axis="y")

    # Annotate min/max
    ax.annotate(f"min: {min(fitness_values):.1f}",
                xy=(1, min(fitness_values)),
                xytext=(1.2, min(fitness_values)),
                fontsize=8, color="green")
    ax.annotate(f"max: {max(fitness_values):.1f}",
                xy=(1, max(fitness_values)),
                xytext=(1.2, max(fitness_values)),
                fontsize=8, color="red")


def plot_runtime(instance_name: str, runs: list[dict], ax: plt.Axes) -> None:
    """Bar chart of runtime per run."""
    runtimes = [r.get("runtime", 0) for r in runs]
    run_labels = [f"Run {i+1}" for i in range(len(runs))]

    bars = ax.bar(run_labels, runtimes, color="#5CB85C", alpha=0.75, edgecolor="white")
    ax.axhline(sum(runtimes) / len(runtimes), color="red",
               linestyle="--", linewidth=1.5, label=f"Avg: {sum(runtimes)/len(runtimes):.2f}s")

    ax.set_title(f"Runtime per Run — {instance_name}", fontsize=12, fontweight="bold")
    ax.set_ylabel("Time (seconds)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")

    for bar, val in zip(bars, runtimes):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.2f}s", ha="center", va="bottom", fontsize=8)


def plot_operator_stats(instance_name: str, runs: list[dict], ax: plt.Axes) -> None:
    """Stacked bar of improvement contributions per operator."""
    sel = [r["operatorStats"]["selection_improvements"] for r in runs]
    cross = [r["operatorStats"]["crossover_improvements"] for r in runs]
    mut = [r["operatorStats"]["mutation_improvements"] for r in runs]
    run_labels = [f"Run {i+1}" for i in range(len(runs))]

    x = np.arange(len(runs))
    width = 0.5

    ax.bar(x, sel,   width, label="Selection",  color="#4C9BE8", alpha=0.85)
    ax.bar(x, cross, width, bottom=sel, label="Crossover", color="#F0AD4E", alpha=0.85)
    ax.bar(x, mut,   width,
           bottom=[s + c for s, c in zip(sel, cross)],
           label="Mutation", color="#5CB85C", alpha=0.85)

    ax.set_title(f"Operator Improvements — {instance_name}", fontsize=12, fontweight="bold")
    ax.set_ylabel("Improvement Count")
    ax.set_xticks(x)
    ax.set_xticklabels(run_labels)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")


def plot_instance(instance_name: str) -> None:
    """Generate full 2x2 dashboard for one instance."""
    runs = load_runs(instance_name)
    if not runs:
        print(f"No runs found for {instance_name}")
        return

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(f"GA Results — {instance_name}", fontsize=15, fontweight="bold", y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

    plot_convergence(instance_name,        runs, fig.add_subplot(gs[0, :]))  # full width
    plot_fitness_distribution(instance_name, runs, fig.add_subplot(gs[1, 0]))
    plot_runtime(instance_name,            runs, fig.add_subplot(gs[1, 1]))

    out_dir = Path(RESULTS_DIR) / instance_name.replace(".txt", "")
    out_path = out_dir / "dashboard.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()


def plot_comparison(instance_names: list[str]) -> None:
    """Compare best fitness convergence across multiple instances."""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.tab10.colors

    for i, name in enumerate(instance_names):
        try:
            runs = load_runs(name)
            # Average best record across all runs
            min_len = min(len(r["bestRecord"]) for r in runs)
            avg_best = np.mean([r["bestRecord"][:min_len] for r in runs], axis=0)
            ax.plot(avg_best, color=colors[i % len(colors)],
                    linewidth=2, label=name)
        except FileNotFoundError as e:
            print(f"Skipping {name}: {e}")

    ax.set_title("Convergence Comparison", fontsize=13, fontweight="bold")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Avg Best Fitness")
    ax.legend()
    ax.grid(True, alpha=0.3)

    out_path = Path(RESULTS_DIR) / "comparison.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--all":
        instances = [d.name for d in Path(RESULTS_DIR).iterdir() if d.is_dir()]
        if not instances:
            print("No results found in results/ directory")
            sys.exit(1)
        for name in sorted(instances):
            plot_instance(name)

    elif len(sys.argv) > 2:
        # Multiple instances = comparison plot
        plot_comparison(sys.argv[1:])

    else:
        plot_instance(sys.argv[1])


if __name__ == "__main__":
    main()