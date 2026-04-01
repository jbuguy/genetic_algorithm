#!/usr/bin/env python3
"""Compare selection/crossover/mutation operators with plotting.

Usage:
  python compare_operators.py C101.txt
  python compare_operators.py C101.txt 50 150 0.2 3

Graphs produced:
  - Per-group: avg best fitness + std  |  time consumption  |  convergence curves
  - Combo heatmap: avg best fitness across all (selection x crossover) pairs
  - Combo leaderboard: ranked bar chart of all combos by avg best fitness + time overlay
"""

import os
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import numpy as np

from ga.genetic_algorithm import GeneticAlgorithm
from ga.selection import rouletteSelection, selection_truncation, tournamentSelection
from operators.crossover import edgeAssemblyCrossover, crossover_ox, PMXCrossOver,crossover_cx
from operators.mutation import twoOpt, orOpt,mutate_scramble
from vrptw.fitness import calculateFitness
from vrptw.instance import Instance

# ─── colour palette ────────────────────────────────────────────────────────────
PALETTE = ["#4C9BE8", "#F0AD4E", "#5CB85C", "#D9534F", "#9B59B6", "#1ABC9C"]
LIGHT_PALETTE = ["#ADD4F5", "#FAD89E", "#A8DBA8", "#F1A8A8", "#D2AEEE", "#A1E8D8"]


# ─── GA runner ─────────────────────────────────────────────────────────────────
def run_ga(instance, selection_fn, crossover_fn, mutation_fn,
           population_size, generations, mutation_rate):
    ga = GeneticAlgorithm(
        instance=instance,
        fnFitness=calculateFitness,
        fnSelection=selection_fn,
        fnCrossover=crossover_fn,
        fnMutation=mutation_fn,
        populationSize=population_size,
        generations=generations,
        mutationRate=mutation_rate,
    )
    result = ga.run()
    return {
        'best_fitness': result.bestFitness,
        'runtime': result.runtime,
        'best_record': result.bestRecord,
        'avg_record': result.avgRecord,
        'operator_stats': result.operatorStats,
    }


# ─── operator sets ─────────────────────────────────────────────────────────────
def get_operators():
    return (
        {
            'tournament': tournamentSelection,
            'roulette':   rouletteSelection,
            'truncation': selection_truncation,
        },
        {
            'edge_assembly': edgeAssemblyCrossover,
            'order_X':       crossover_ox,
            'PMX':           PMXCrossOver,
            'CX':            crossover_cx,
        },
        {
            'twoOpt': twoOpt,
            'orOpt':  orOpt,
            'mutate Scrumble': mutate_scramble,
        },
    )


# ─── helpers ───────────────────────────────────────────────────────────────────
def _avg_std(values):
    arr = np.array([v for v in values if v != float('inf')], dtype=float)
    return (float(np.nanmean(arr)), float(np.nanstd(arr))) if len(arr) else (float('nan'), 0.0)


SELECTION_COMPLEXITY = {
    'tournament': 'O(k·pop)',
    'roulette':   'O(pop²)',
    'truncation': 'O(pop·log pop)',
}
CROSSOVER_COMPLEXITY = {
    'edge_assembly': 'O(pop·n)',
    'order_X':       'O(n)',
    'PMX':           'O(n)',
}
MUTATION_COMPLEXITY = {
    'twoOpt': 'O(n)',
    'orOpt':  'O(n)',
}


# ─── data collection ───────────────────────────────────────────────────────────
def evaluate_operator_group(instance, population_size, generations, mutation_rate, num_runs):
    sel_ops, cross_ops, mut_ops = get_operators()

    results = {'selection': {}, 'crossover': {}, 'mutation': {}}

    for name, fn in sel_ops.items():
        runs = []
        print(f"\n== Selection: {name} ==")
        for r in range(num_runs):
            out = run_ga(instance, fn, edgeAssemblyCrossover, twoOpt,
                         population_size, generations, mutation_rate)
            out['run'] = r + 1
            runs.append(out)
            print(f"  run {r+1}/{num_runs}: best={out['best_fitness']:.2f}  t={out['runtime']:.2f}s")
        results['selection'][name] = runs

    for name, fn in cross_ops.items():
        runs = []
        print(f"\n== Crossover: {name} ==")
        for r in range(num_runs):
            out = run_ga(instance, tournamentSelection, fn, twoOpt,
                         population_size, generations, mutation_rate)
            out['run'] = r + 1
            runs.append(out)
            print(f"  run {r+1}/{num_runs}: best={out['best_fitness']:.2f}  t={out['runtime']:.2f}s")
        results['crossover'][name] = runs

    for name, fn in mut_ops.items():
        runs = []
        print(f"\n== Mutation: {name} ==")
        for r in range(num_runs):
            out = run_ga(instance, tournamentSelection, edgeAssemblyCrossover, fn,
                         population_size, generations, mutation_rate)
            out['run'] = r + 1
            runs.append(out)
            print(f"  run {r+1}/{num_runs}: best={out['best_fitness']:.2f}  t={out['runtime']:.2f}s")
        results['mutation'][name] = runs

    return results


def evaluate_operator_combinations(instance, population_size, generations, mutation_rate, num_runs):
    sel_ops, cross_ops, mut_ops = get_operators()
    combo_results = []

    print('\n=== Full Combination Comparison ===')
    for sel_name, sel_fn in sel_ops.items():
        for cross_name, cross_fn in cross_ops.items():
            for mut_name, mut_fn in mut_ops.items():
                combo_name = f'{sel_name}+{cross_name}+{mut_name}'
                print(f'\n> {combo_name}')
                bests, runtimes = [], []
                for r in range(num_runs):
                    out = run_ga(instance, sel_fn, cross_fn, mut_fn,
                                 population_size, generations, mutation_rate)
                    bests.append(out['best_fitness'])
                    runtimes.append(out['runtime'])
                    print(f"  run {r+1}/{num_runs}: best={out['best_fitness']:.2f}  t={out['runtime']:.2f}s")

                avg_best, std_best = _avg_std(bests)
                avg_time, std_time = _avg_std(runtimes)
                combo_results.append({
                    'combo': combo_name,
                    'selection': sel_name, 'crossover': cross_name, 'mutation': mut_name,
                    'avg_best': avg_best, 'std_best': std_best,
                    'avg_time': avg_time, 'std_time': std_time,
                    'runs': num_runs,
                })

    return combo_results


# ══════════════════════════════════════════════════════════════════════════════
#  VISUALISATION
# ══════════════════════════════════════════════════════════════════════════════

def _apply_style():
    plt.rcParams.update({
        'font.family':       'DejaVu Sans',
        'axes.spines.top':   False,
        'axes.spines.right': False,
        'axes.grid':         True,
        'grid.alpha':        0.25,
        'grid.linestyle':    '--',
        'figure.facecolor':  'white',
        'axes.facecolor':    '#F8F9FA',
    })


def plot_group(group_name, group_results, out_dir):
    """
    3-panel figure per operator group:
      [0] Avg best fitness ± STD   (bar)
      [1] Avg runtime ± STD        (bar)
      [2] Convergence curve        (line)
    """
    _apply_style()
    operators = list(group_results.keys())
    n = len(operators)
    colours = PALETTE[:n]

    avg_fitness, std_fitness, avg_time, std_time = [], [], [], []
    for name in operators:
        runs = group_results[name]
        af, sf = _avg_std([r['best_fitness'] for r in runs])
        at, st = _avg_std([r['runtime']      for r in runs])
        avg_fitness.append(af); std_fitness.append(sf)
        avg_time.append(at);    std_time.append(st)

    fig = plt.figure(figsize=(16, 5), constrained_layout=True)
    fig.suptitle(f"Operator comparison — {group_name.upper()}", fontsize=15, fontweight='bold')
    gs  = gridspec.GridSpec(1, 3, figure=fig)

    # ── panel 0 : fitness ──────────────────────────────────────────────────
    ax0 = fig.add_subplot(gs[0])
    bars = ax0.bar(operators, avg_fitness, yerr=std_fitness,
                   color=colours, capsize=8, edgecolor='white', linewidth=1.2)
    ax0.set_ylabel('Avg best fitness (lower = better)')
    ax0.set_title('Solution Quality', fontweight='bold')
    for bar, val in zip(bars, avg_fitness):
        ax0.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(std_fitness) * 0.05,
                 f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # ── panel 1 : runtime ──────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[1])
    bars2 = ax1.bar(operators, avg_time, yerr=std_time,
                    color=LIGHT_PALETTE[:n], capsize=8, edgecolor='white', linewidth=1.2)
    ax1.set_ylabel('Avg runtime (seconds)')
    ax1.set_title('⏱  Time Consumption', fontweight='bold')
    for bar, val in zip(bars2, avg_time):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(std_time) * 0.05,
                 f'{val:.2f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # annotate fastest / slowest
    fastest_idx = int(np.argmin(avg_time))
    slowest_idx = int(np.argmax(avg_time))
    ax1.get_children()[fastest_idx].set_edgecolor('#2ECC40')
    ax1.get_children()[fastest_idx].set_linewidth(2.5)
    ax1.get_children()[slowest_idx].set_edgecolor('#D9534F')
    ax1.get_children()[slowest_idx].set_linewidth(2.5)
    ax1.legend(
        handles=[
            plt.Line2D([0], [0], color='#2ECC40', linewidth=2.5, label='Fastest'),
            plt.Line2D([0], [0], color='#D9534F', linewidth=2.5, label='Slowest'),
        ],
        fontsize=8, framealpha=0.6,
    )

    # ── panel 2 : convergence ──────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[2])
    for name, colour in zip(operators, colours):
        curves = [r['best_record'] for r in group_results[name] if r.get('best_record')]
        if not curves:
            continue
        min_len     = min(len(c) for c in curves)
        mean_curve  = np.mean([c[:min_len] for c in curves], axis=0)
        std_curve   = np.std ([c[:min_len] for c in curves], axis=0)
        gens        = range(min_len)
        ax2.plot(gens, mean_curve, label=name, color=colour, linewidth=2)
        ax2.fill_between(gens,
                         mean_curve - std_curve,
                         mean_curve + std_curve,
                         color=colour, alpha=0.15)
    ax2.set_xlabel('Generation')
    ax2.set_ylabel('Best fitness')
    ax2.set_title('Convergence (mean ± σ)', fontweight='bold')
    ax2.legend(fontsize=9)

    out_file = Path(out_dir) / f'compare_{group_name}.png'
    plt.savefig(out_file, dpi=150, bbox_inches='tight')
    print(f"Saved {out_file}")
    plt.show()
    plt.close()


def plot_combo_leaderboard(combo_results, out_dir):
    """
    Ranked bar chart: all combos ordered by avg best fitness.
    A secondary axis overlays avg runtime as a line.
    Top-3 combos are highlighted in gold / silver / bronze.
    """
    _apply_style()
    sorted_combos = sorted(combo_results, key=lambda r: r['avg_best'])
    labels   = [r['combo']    for r in sorted_combos]
    fitness  = [r['avg_best'] for r in sorted_combos]
    std_fit  = [r['std_best'] for r in sorted_combos]
    runtimes = [r['avg_time'] for r in sorted_combos]

    medal_colours = ['#FFD700', '#C0C0C0', '#CD7F32']  # gold, silver, bronze
    bar_colours   = [medal_colours[i] if i < 3 else '#ADB5BD' for i in range(len(labels))]

    fig, ax1 = plt.subplots(figsize=(max(12, len(labels) * 1.1), 6), constrained_layout=True)
    fig.suptitle('Combination Leaderboard — Solution Quality & Time', fontsize=15, fontweight='bold')

    x = np.arange(len(labels))
    bars = ax1.bar(x, fitness, yerr=std_fit, color=bar_colours,
                   capsize=5, edgecolor='white', linewidth=1.1)

    # value labels on bars
    for bar, val, std in zip(bars, fitness, std_fit):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + std + (max(fitness) - min(fitness)) * 0.01,
                 f'{val:.1f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=42, ha='right', fontsize=8)
    ax1.set_ylabel('Avg best fitness  (lower = better)', fontsize=10)
    ax1.set_xlabel('Operator Combination', fontsize=10)

    # secondary axis – runtime line
    ax2 = ax1.twinx()
    ax2.spines['right'].set_visible(True)
    ax2.plot(x, runtimes, color='#E74C3C', linewidth=2, marker='o',
             markersize=5, label='Avg runtime (s)', zorder=5)
    ax2.set_ylabel('Avg runtime (s)', color='#E74C3C', fontsize=10)
    ax2.tick_params(axis='y', labelcolor='#E74C3C')

    # legend
    medal_patches = [
        plt.Rectangle((0, 0), 1, 1, color=medal_colours[i],
                       label=f'Top {i+1}: {labels[i].split("+")[0]}…')
        for i in range(min(3, len(labels)))
    ]
    ax1.legend(handles=medal_patches, loc='upper left', fontsize=8, framealpha=0.7)
    ax2.legend(loc='upper right', fontsize=8)

    out_file = Path(out_dir) / 'combo_leaderboard.png'
    plt.savefig(out_file, dpi=150, bbox_inches='tight')
    print(f"Saved {out_file}")
    plt.show()
    plt.close()


def plot_combo_heatmap(combo_results, out_dir):
    """
    Heatmap: rows = selection operator, columns = crossover operator.
    Cell colour = avg best fitness (best = darkest green).
    Each cell is annotated with fitness value and runtime.
    One heatmap per mutation operator.
    """
    _apply_style()

    sel_ops    = sorted({r['selection']  for r in combo_results})
    cross_ops  = sorted({r['crossover']  for r in combo_results})
    mut_ops    = sorted({r['mutation']   for r in combo_results})

    for mut in mut_ops:
        fitness_mat = np.full((len(sel_ops), len(cross_ops)), np.nan)
        time_mat    = np.full((len(sel_ops), len(cross_ops)), np.nan)

        for row in combo_results:
            if row['mutation'] != mut:
                continue
            i = sel_ops.index(row['selection'])
            j = cross_ops.index(row['crossover'])
            fitness_mat[i, j] = row['avg_best']
            time_mat[i, j]    = row['avg_time']

        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        fig.suptitle(f'Fitness Heatmap  (mutation = {mut})\n'
                     f'Darker = lower fitness = better solution',
                     fontsize=13, fontweight='bold')

        # reverse so darker = lower = better
        vmin = np.nanmin(fitness_mat)
        vmax = np.nanmax(fitness_mat)
        im   = ax.imshow(fitness_mat, cmap='YlGn_r', vmin=vmin, vmax=vmax, aspect='auto')

        ax.set_xticks(range(len(cross_ops)));  ax.set_xticklabels(cross_ops, fontsize=10)
        ax.set_yticks(range(len(sel_ops)));    ax.set_yticklabels(sel_ops,   fontsize=10)
        ax.set_xlabel('Crossover Operator',    fontsize=11)
        ax.set_ylabel('Selection Operator',    fontsize=11)

        for i in range(len(sel_ops)):
            for j in range(len(cross_ops)):
                f = fitness_mat[i, j]
                t = time_mat[i, j]
                if not np.isnan(f):
                    brightness = (f - vmin) / (vmax - vmin + 1e-9)
                    txt_colour = 'white' if brightness < 0.5 else '#1a1a1a'
                    ax.text(j, i, f'fitness\n{f:.1f}\n⏱ {t:.2f}s',
                            ha='center', va='center', fontsize=8.5,
                            fontweight='bold', color=txt_colour)

        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Avg best fitness', fontsize=10)

        out_file = Path(out_dir) / f'heatmap_mutation_{mut}.png'
        plt.savefig(out_file, dpi=150, bbox_inches='tight')
        print(f"Saved {out_file}")
        plt.show()
        plt.close()


def plot_runtime_summary(combo_results, out_dir):
    """
    Grouped bar chart: compare avg runtime across all 18 combos,
    grouped by selection operator.
    """
    _apply_style()
    sel_ops   = sorted({r['selection']  for r in combo_results})
    cross_ops = sorted({r['crossover']  for r in combo_results})
    mut_ops   = sorted({r['mutation']   for r in combo_results})

    # Build lookup
    lookup = {(r['selection'], r['crossover'], r['mutation']): r for r in combo_results}

    n_cross = len(cross_ops)
    n_mut   = len(mut_ops)
    n_groups = n_cross * n_mut
    x = np.arange(n_groups)
    width = 0.25

    fig, ax = plt.subplots(figsize=(16, 6), constrained_layout=True)
    fig.suptitle('⏱  Runtime Comparison — Grouped by Selection Operator',
                 fontsize=14, fontweight='bold')

    xlabels = [f'{c}\n({m})' for c in cross_ops for m in mut_ops]

    for i, sel in enumerate(sel_ops):
        times = []
        for c in cross_ops:
            for m in mut_ops:
                key = (sel, c, m)
                times.append(lookup[key]['avg_time'] if key in lookup else 0.0)
        offset = (i - len(sel_ops) / 2 + 0.5) * width
        ax.bar(x + offset, times, width=width * 0.9,
               label=sel, color=PALETTE[i], edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=8, rotation=20, ha='right')
    ax.set_ylabel('Avg runtime (seconds)', fontsize=11)
    ax.set_xlabel('Crossover + Mutation', fontsize=11)
    ax.legend(title='Selection', fontsize=9)

    out_file = Path(out_dir) / 'runtime_grouped.png'
    plt.savefig(out_file, dpi=150, bbox_inches='tight')
    print(f"Saved {out_file}")
    plt.show()
    plt.close()


# ─── orchestrator ──────────────────────────────────────────────────────────────
def visualize_results(instance_name, results, combo_results):
    out_dir = Path('results') / instance_name.replace('.txt', '') / 'operator_comparison'
    out_dir.mkdir(parents=True, exist_ok=True)

    # per-group: fitness + time + convergence
    for group_name in ['selection', 'crossover', 'mutation']:
        plot_group(group_name, results[group_name], out_dir)

    # combo charts
    plot_combo_leaderboard(combo_results, out_dir)
    plot_combo_heatmap(combo_results, out_dir)
    plot_runtime_summary(combo_results, out_dir)


def compare_and_print(combo_results):
    sorted_results = sorted(combo_results, key=lambda r: (r['avg_best'], r['avg_time']))
    print('\n=== Combination Comparison Table ===')
    header = (
        f"{'combo':<45} {'avg_best':>9} {'std_best':>9} "
        f"{'avg_time':>9} {'std_time':>9}"
    )
    print(header)
    print('-' * len(header))
    for row in sorted_results:
        print(
            f"{row['combo']:<45} {row['avg_best']:>9.2f} {row['std_best']:>9.2f} "
            f"{row['avg_time']:>9.2f} {row['std_time']:>9.2f}"
        )
    best = sorted_results[0]
    print(f"\n🏆  Best combination: {best['combo']}  "
          f"(avg_best={best['avg_best']:.2f}, avg_time={best['avg_time']:.2f}s)")
    return sorted_results


# ─── entry point ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print('Usage: python compare_operators.py <instance> '
              '[pop_size] [generations] [mut_rate] [num_runs]')
        sys.exit(1)

    instance_name = sys.argv[1]
    pop_size      = int(sys.argv[2])   if len(sys.argv) > 2 else 50
    generations   = int(sys.argv[3])   if len(sys.argv) > 3 else 100
    mut_rate      = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
    num_runs      = int(sys.argv[5])   if len(sys.argv) > 5 else 3

    data_dir      = 'data'
    instance_path = os.path.join(data_dir, instance_name)
    if not os.path.exists(instance_path):
        raise FileNotFoundError(f'Instance file not found: {instance_path}')
    instance = Instance(instance_path)

    print(f"Running operator comparison on {instance_name} — "
          f"pop={pop_size}, gens={generations}, mut_rate={mut_rate}, runs={num_runs}")

    results = evaluate_operator_group(
        instance, pop_size, generations, mut_rate, num_runs)

    combo_results = evaluate_operator_combinations(
        instance, pop_size, generations, mut_rate, max(1, num_runs))

    compare_and_print(combo_results)
    visualize_results(instance_name, results, combo_results)


if __name__ == '__main__':
    main()