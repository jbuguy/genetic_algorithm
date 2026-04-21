#!/usr/bin/env python3
"""
Refactored Operator Comparison Pipeline - VRPTW GA

This module provides comprehensive operator comparison capabilities for genetic algorithm
configurations. It analyzes selection, crossover, and mutation operators individually
and in combination, producing meaningful visuals for each.

Usage:
  python compare_operators.py C101.txt [pop_size=50] [generations=150] [mutation_rate=0.2] [num_runs=3]
"""

import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Callable, Any
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from ga.genetic_algorithm import GeneticAlgorithm
from ga.selection import rouletteSelection, selection_truncation, tournamentSelection
from operators.crossover import edgeAssemblyCrossover, crossover_ox, PMXCrossOver
from operators.mutation import mutate_route_rebuild, mutate_scramble, twoOpt, orOpt
from vrptw.fitness import makeFitnessFunction
from vrptw.instance import Instance

# ─── Logging Setup ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# ─── Styling & Constants ───────────────────────────────────────────────────────
PALETTE = ["#4C9BE8", "#F0AD4E", "#5CB85C", "#D9534F", "#9B59B6", "#1ABC9C"]
LIGHT_PALETTE = ["#ADD4F5", "#FAD89E", "#A8DBA8", "#F1A8A8", "#D2AEEE", "#A1E8D8"]

OPERATOR_COMPLEXITY = {
    'selection': {
        'tournament': 'O(k·pop)',
        'roulette': 'O(pop²)',
        'truncation': 'O(pop·log pop)',
    },
    'crossover': {
        'edge_assembly': 'O(pop·n)',
        'order_X': 'O(n)',
        'PMX': 'O(n)',
    },
    'mutation': {
        'rebuild': 'O(n)',
        'scramble': 'O(n)',
        'orOpt': 'O(n)',
        'twoOpt': 'O(n²)',
    },
}


def _apply_style():
    """Apply consistent matplotlib styling"""
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.25,
        'grid.linestyle': '--',
        'figure.facecolor': 'white',
        'axes.facecolor': '#F8F9FA',
    })


# ─── Data Classes ──────────────────────────────────────────────────────────────
@dataclass
class GAResult:
    """Result from a single GA run"""
    best_fitness: float
    runtime: float
    best_record: List[float]
    avg_record: List[float]
    operator_stats: Dict = field(default_factory=dict)


@dataclass
class OperatorGroupResult:
    """Results for a group of operator runs"""
    operator_name: str
    runs: List[Dict[str, Any]] = field(default_factory=list)
    avg_fitness: float = 0.0
    std_fitness: float = 0.0
    avg_runtime: float = 0.0
    std_runtime: float = 0.0

    def calculate_stats(self):
        """Calculate average and std dev"""
        if not self.runs:
            return
        fitness_vals = [r['best_fitness'] for r in self.runs if r['best_fitness'] != float('inf')]
        runtime_vals = [r['runtime'] for r in self.runs]
        
        self.avg_fitness = float(np.nanmean(fitness_vals)) if fitness_vals else float('nan')
        self.std_fitness = float(np.nanstd(fitness_vals)) if fitness_vals else 0.0
        self.avg_runtime = float(np.nanmean(runtime_vals)) if runtime_vals else 0.0
        self.std_runtime = float(np.nanstd(runtime_vals)) if runtime_vals else 0.0


@dataclass
class CombinationResult:
    """Result for a combination of operators"""
    selection: str
    crossover: str
    mutation: str
    runs: List[Dict[str, Any]] = field(default_factory=list)
    avg_best: float = 0.0
    std_best: float = 0.0
    avg_time: float = 0.0
    std_time: float = 0.0

    @property
    def combo_name(self):
        return f"{self.selection}+{self.crossover}+{self.mutation}"

    def calculate_stats(self):
        """Calculate aggregate statistics"""
        if not self.runs:
            return
        bests = [r['best_fitness'] for r in self.runs if r['best_fitness'] != float('inf')]
        times = [r['runtime'] for r in self.runs]
        
        self.avg_best = float(np.nanmean(bests)) if bests else float('nan')
        self.std_best = float(np.nanstd(bests)) if bests else 0.0
        self.avg_time = float(np.nanmean(times)) if times else 0.0
        self.std_time = float(np.nanstd(times)) if times else 0.0


# ─── Operator Comparator Class ──────────────────────────────────────────────────
class OperatorComparator:
    """Encapsulates operator comparison logic"""

    def __init__(self, instance: Instance, pop_size: int = 50, 
                 generations: int = 100, mutation_rate: float = 0.2):
        self.instance = instance
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        
        self.operators = self._get_default_operators()
        logger.info(f"Initialized OperatorComparator with pop_size={pop_size}, "
                   f"generations={generations}, mutation_rate={mutation_rate}")

    def _get_default_operators(self) -> Dict[str, Dict[str, Callable]]:
        """Get all available operators"""
        return {
            'selection': {
                'tournament': tournamentSelection,
                'roulette': rouletteSelection,
                'truncation': selection_truncation,
            },
            'crossover': {
                'edge_assembly': edgeAssemblyCrossover,
                'order_X': crossover_ox,
                'PMX': PMXCrossOver,
            },
            'mutation': {
                'rebuild': mutate_route_rebuild,
                'scramble': mutate_scramble,
                'twoOpt': twoOpt,
                'orOpt': orOpt,
            },
        }

    def _run_ga(self, selection_fn: Callable, crossover_fn: Callable, 
                mutation_fn: Callable) -> GAResult:
        """Execute a single GA run"""
        fn_fitness = makeFitnessFunction(
            self.instance, alpha=0.5, beta=0.4, gamma=0.1
        )
        
        ga = GeneticAlgorithm(
            instance=self.instance,
            fnFitness=fn_fitness,
            fnSelection=selection_fn,
            fnCrossover=crossover_fn,
            fnMutation=mutation_fn,
            populationSize=self.pop_size,
            generations=self.generations,
            mutationRate=self.mutation_rate,
        )
        
        result = ga.run()
        return GAResult(
            best_fitness=result.bestFitness,
            runtime=result.runtime,
            best_record=result.bestRecord,
            avg_record=result.avgRecord,
            operator_stats=result.operatorStats,
        )

    def evaluate_operator_group(self, operator_type: str, 
                                num_runs: int = 3,
                                fixed_selection: Callable = None,
                                fixed_crossover: Callable = None,
                                fixed_mutation: Callable = None) -> Dict[str, OperatorGroupResult]:
        """
        Evaluate all operators of a specific type while keeping others fixed.
        
        Args:
            operator_type: 'selection', 'crossover', or 'mutation'
            num_runs: Number of runs per operator
            fixed_*: Functions to use for other operator types
        """
        if operator_type not in self.operators:
            raise ValueError(f"Unknown operator_type: {operator_type}")

        # Use sensible defaults if not specified
        if fixed_selection is None:
            fixed_selection = tournamentSelection
        if fixed_crossover is None:
            fixed_crossover = edgeAssemblyCrossover
        if fixed_mutation is None:
            fixed_mutation = twoOpt

        results = {}
        ops_dict = self.operators[operator_type]

        logger.info(f"Evaluating {operator_type} operators ({len(ops_dict)} variants, "
                   f"{num_runs} runs each)")

        for op_name, op_fn in ops_dict.items():
            logger.info(f"  Testing {operator_type}: {op_name}")
            group_result = OperatorGroupResult(operator_name=op_name)

            for run_idx in range(num_runs):
                # Select which function to use based on operator type
                sel_fn = op_fn if operator_type == 'selection' else fixed_selection
                cross_fn = op_fn if operator_type == 'crossover' else fixed_crossover
                mut_fn = op_fn if operator_type == 'mutation' else fixed_mutation

                ga_result = self._run_ga(sel_fn, cross_fn, mut_fn)
                
                run_data = {
                    'run': run_idx + 1,
                    'best_fitness': ga_result.best_fitness,
                    'runtime': ga_result.runtime,
                    'best_record': ga_result.best_record,
                }
                group_result.runs.append(run_data)
                
                logger.debug(f"    Run {run_idx + 1}: fitness={ga_result.best_fitness:.2f}, "
                            f"time={ga_result.runtime:.2f}s")

            group_result.calculate_stats()
            results[op_name] = group_result
            logger.info(f"  {op_name}: avg_fitness={group_result.avg_fitness:.2f} "
                       f"± {group_result.std_fitness:.2f}")

        return results

    def evaluate_combinations(self, num_runs: int = 3) -> List[CombinationResult]:
        """Evaluate all combinations of operators"""
        sel_ops = self.operators['selection']
        cross_ops = self.operators['crossover']
        mut_ops = self.operators['mutation']

        total_combos = len(sel_ops) * len(cross_ops) * len(mut_ops)
        logger.info(f"Evaluating combinations: {total_combos} combos × {num_runs} runs = "
                   f"{total_combos * num_runs} GA instances")

        results = []
        combo_idx = 1

        for sel_name, sel_fn in sel_ops.items():
            for cross_name, cross_fn in cross_ops.items():
                for mut_name, mut_fn in mut_ops.items():
                    combo_result = CombinationResult(
                        selection=sel_name,
                        crossover=cross_name,
                        mutation=mut_name
                    )
                    
                    logger.info(f"[{combo_idx}/{total_combos}] {combo_result.combo_name}")

                    for run_idx in range(num_runs):
                        ga_result = self._run_ga(sel_fn, cross_fn, mut_fn)
                        combo_result.runs.append({
                            'run': run_idx + 1,
                            'best_fitness': ga_result.best_fitness,
                            'runtime': ga_result.runtime,
                            'best_record': ga_result.best_record,
                        })
                        
                        logger.debug(f"  Run {run_idx + 1}: fitness={ga_result.best_fitness:.2f}, "
                                    f"time={ga_result.runtime:.2f}s")

                    combo_result.calculate_stats()
                    results.append(combo_result)
                    logger.info(f"  avg_fitness={combo_result.avg_best:.2f} ± {combo_result.std_best:.2f}")

                    combo_idx += 1

        return results


# ─── Plotting Functions ─────────────────────────────────────────────────────────
class OperatorPlotter:
    """Handles all plot generation"""

    @staticmethod
    def plot_group_comparison(group_name: str, group_results: Dict[str, OperatorGroupResult],
                             output_dir: Path):
        """Plot 3-panel comparison for an operator group"""
        _apply_style()
        
        operators = list(group_results.keys())
        n = len(operators)
        colours = PALETTE[:n]

        avg_fitness = [group_results[op].avg_fitness for op in operators]
        std_fitness = [group_results[op].std_fitness for op in operators]
        avg_time = [group_results[op].avg_runtime for op in operators]
        std_time = [group_results[op].std_runtime for op in operators]

        fig = plt.figure(figsize=(16, 5), constrained_layout=True)
        fig.suptitle(f"Operator comparison — {group_name.upper()}", 
                    fontsize=15, fontweight='bold')
        gs = gridspec.GridSpec(1, 3, figure=fig)

        # Panel 0: Fitness
        ax0 = fig.add_subplot(gs[0])
        bars = ax0.bar(operators, avg_fitness, yerr=std_fitness,
                       color=colours, capsize=8, edgecolor='white', linewidth=1.2)
        ax0.set_ylabel('Avg best fitness (lower = better)')
        ax0.set_title('Solution Quality', fontweight='bold')
        for bar, val in zip(bars, avg_fitness):
            ax0.text(bar.get_x() + bar.get_width() / 2, val + max(std_fitness) * 0.05,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Panel 1: Runtime
        ax1 = fig.add_subplot(gs[1])
        bars2 = ax1.bar(operators, avg_time, yerr=std_time,
                       color=LIGHT_PALETTE[:n], capsize=8, edgecolor='white', linewidth=1.2)
        ax1.set_ylabel('Avg runtime (seconds)')
        ax1.set_title('⏱  Time Consumption', fontweight='bold')
        for bar, val in zip(bars2, avg_time):
            ax1.text(bar.get_x() + bar.get_width() / 2, val + max(std_time) * 0.05,
                    f'{val:.2f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Highlight fastest/slowest
        fastest_idx = int(np.argmin(avg_time))
        slowest_idx = int(np.argmax(avg_time))
        bars2[fastest_idx].set_edgecolor('#2ECC40')
        bars2[fastest_idx].set_linewidth(2.5)
        bars2[slowest_idx].set_edgecolor('#D9534F')
        bars2[slowest_idx].set_linewidth(2.5)

        # Panel 2: Convergence
        ax2 = fig.add_subplot(gs[2])
        for name, colour in zip(operators, colours):
            curves = [r['best_record'] for r in group_results[name].runs 
                     if r.get('best_record')]
            if not curves:
                continue
            min_len = min(len(c) for c in curves)
            mean_curve = np.mean([c[:min_len] for c in curves], axis=0)
            std_curve = np.std([c[:min_len] for c in curves], axis=0)
            gens = range(min_len)
            ax2.plot(gens, mean_curve, label=name, color=colour, linewidth=2)
            ax2.fill_between(gens, mean_curve - std_curve, mean_curve + std_curve,
                            color=colour, alpha=0.15)
        ax2.set_xlabel('Generation')
        ax2.set_ylabel('Best fitness')
        ax2.set_title('Convergence (mean ± σ)', fontweight='bold')
        ax2.legend(fontsize=9)

        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f'compare_{group_name}.png'
        plt.savefig(out_file, dpi=150, bbox_inches='tight')
        logger.info(f"Saved {out_file}")
        plt.close()

    @staticmethod
    def plot_combo_leaderboard(combo_results: List[CombinationResult], output_dir: Path):
        """Plot ranked bar chart of all combinations"""
        _apply_style()
        
        sorted_combos = sorted(combo_results, key=lambda r: r.avg_best)
        labels = [r.combo_name for r in sorted_combos]
        fitness = [r.avg_best for r in sorted_combos]
        std_fit = [r.std_best for r in sorted_combos]
        runtimes = [r.avg_time for r in sorted_combos]

        medal_colours = ['#FFD700', '#C0C0C0', '#CD7F32']
        bar_colours = [medal_colours[i] if i < 3 else '#ADB5BD' for i in range(len(labels))]

        fig, ax1 = plt.subplots(figsize=(max(12, len(labels) * 1.1), 6), 
                               constrained_layout=True)
        fig.suptitle('Combination Leaderboard — Solution Quality & Time',
                    fontsize=15, fontweight='bold')

        x = np.arange(len(labels))
        bars = ax1.bar(x, fitness, yerr=std_fit, color=bar_colours,
                      capsize=5, edgecolor='white', linewidth=1.1)

        for bar, val, std in zip(bars, fitness, std_fit):
            ax1.text(bar.get_x() + bar.get_width() / 2,
                    val + std + (max(fitness) - min(fitness)) * 0.01,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')

        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=42, ha='right', fontsize=8)
        ax1.set_ylabel('Avg best fitness (lower = better)', fontsize=10)
        ax1.set_xlabel('Operator Combination', fontsize=10)

        # Secondary axis for runtime
        ax2 = ax1.twinx()
        ax2.plot(x, runtimes, color='#E74C3C', linewidth=2, marker='o',
                markersize=5, label='Avg runtime (s)', zorder=5)
        ax2.set_ylabel('Avg runtime (s)', color='#E74C3C', fontsize=10)
        ax2.tick_params(axis='y', labelcolor='#E74C3C')

        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / 'combo_leaderboard.png'
        plt.savefig(out_file, dpi=150, bbox_inches='tight')
        logger.info(f"Saved {out_file}")
        plt.close()

    @staticmethod
    def plot_combo_heatmap(combo_results: List[CombinationResult], output_dir: Path):
        """Plot heatmaps of operator combinations"""
        _apply_style()

        sel_ops = sorted({r.selection for r in combo_results})
        cross_ops = sorted({r.crossover for r in combo_results})
        mut_ops = sorted({r.mutation for r in combo_results})

        for mut in mut_ops:
            fitness_mat = np.full((len(sel_ops), len(cross_ops)), np.nan)
            time_mat = np.full((len(sel_ops), len(cross_ops)), np.nan)

            for row in combo_results:
                if row.mutation != mut:
                    continue
                i = sel_ops.index(row.selection)
                j = cross_ops.index(row.crossover)
                fitness_mat[i, j] = row.avg_best
                time_mat[i, j] = row.avg_time

            fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
            fig.suptitle(f'Fitness Heatmap (mutation = {mut})\nDarker = lower fitness = better',
                         fontsize=13, fontweight='bold')

            vmin = np.nanmin(fitness_mat)
            vmax = np.nanmax(fitness_mat)
            im = ax.imshow(fitness_mat, cmap='YlGn_r', vmin=vmin, vmax=vmax, aspect='auto')

            ax.set_xticks(range(len(cross_ops)))
            ax.set_xticklabels(cross_ops, fontsize=10)
            ax.set_yticks(range(len(sel_ops)))
            ax.set_yticklabels(sel_ops, fontsize=10)
            ax.set_xlabel('Crossover Operator', fontsize=11)
            ax.set_ylabel('Selection Operator', fontsize=11)

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

            output_dir.mkdir(parents=True, exist_ok=True)
            out_file = output_dir / f'heatmap_mutation_{mut}.png'
            plt.savefig(out_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved {out_file}")
            plt.close()


# ─── Reporting ────────────────────────────────────────────────────────────────
def print_comparison_table(combo_results: List[CombinationResult]) -> List[CombinationResult]:
    """Print formatted comparison table"""
    sorted_results = sorted(combo_results, key=lambda r: (r.avg_best, r.avg_time))
    
    print('\n' + '=' * 100)
    print('COMBINATION COMPARISON RESULTS')
    print('=' * 100)
    
    header = (f"{'Combination':<45} {'Avg Fitness':>12} {'Std':>8} "
              f"{'Avg Time (s)':>12} {'Std':>8}")
    print(header)
    print('-' * 100)
    
    for row in sorted_results:
        print(
            f"{row.combo_name:<45} {row.avg_best:>12.2f} {row.std_best:>8.2f} "
            f"{row.avg_time:>12.2f} {row.std_time:>8.2f}"
        )
    
    best = sorted_results[0]
    print('-' * 100)
    print(f"🏆 BEST COMBINATION: {best.combo_name}")
    print(f"   Fitness: {best.avg_best:.2f} ± {best.std_best:.2f}")
    print(f"   Runtime: {best.avg_time:.2f} ± {best.std_time:.2f}s")
    print('=' * 100 + '\n')
    
    return sorted_results


# ─── Entry Point ────────────────────────────────────────────────────────────────
def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print('Usage: python compare_operators.py <instance> '
              '[pop_size=50] [generations=150] [mutation_rate=0.2] [num_runs=3]')
        sys.exit(1)

    instance_name = sys.argv[1]
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    generations = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    mutation_rate = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
    num_runs = int(sys.argv[5]) if len(sys.argv) > 5 else 3

    instance_path = Path('data') / instance_name
    if not instance_path.exists():
        logger.error(f'Instance file not found: {instance_path}')
        sys.exit(1)

    instance = Instance(str(instance_path))
    logger.info(f"Loaded instance: {instance_name}")

    # Initialize comparator
    comparator = OperatorComparator(
        instance, pop_size=pop_size, generations=generations, 
        mutation_rate=mutation_rate
    )

    # Evaluate individual operator groups
    logger.info("=" * 80)
    logger.info("PHASE 1: Evaluating Individual Operator Groups")
    logger.info("=" * 80)
    
    selection_results = comparator.evaluate_operator_group('selection', num_runs=num_runs)
    crossover_results = comparator.evaluate_operator_group('crossover', num_runs=num_runs)
    mutation_results = comparator.evaluate_operator_group('mutation', num_runs=num_runs)

    # Evaluate combinations
    logger.info("=" * 80)
    logger.info("PHASE 2: Evaluating Operator Combinations")
    logger.info("=" * 80)
    
    combo_results = comparator.evaluate_combinations(num_runs=num_runs)

    # Print results
    print_comparison_table(combo_results)

    # Visualize
    logger.info("=" * 80)
    logger.info("PHASE 3: Generating Visualizations")
    logger.info("=" * 80)
    
    instance_clean = instance_name.replace('.txt', '')
    output_dir = Path('results') / instance_clean / 'operator_comparison'
    
    plotter = OperatorPlotter()
    
    # Individual group plots
    plotter.plot_group_comparison('selection', selection_results, output_dir)
    plotter.plot_group_comparison('crossover', crossover_results, output_dir)
    plotter.plot_group_comparison('mutation', mutation_results, output_dir)
    
    # Combination plots
    plotter.plot_combo_leaderboard(combo_results, output_dir)
    plotter.plot_combo_heatmap(combo_results, output_dir)
    
    logger.info("=" * 80)
    logger.info(f"All results saved to: {output_dir}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()