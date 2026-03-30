#!/usr/bin/env python3


import os
import sys
import time

from ga.genetic_algorithm import GeneticAlgorithm
from stats import StatsManager
from vrptw.fitness import calculateFitness, calculateFitnessStrict
from vrptw.generateInit import solomon_generator
from vrptw.instance import Instance

import cProfile


class ExperimentRunner:
    """Runs GA experiments and collects statistics."""

    def __init__(self, results_dir: str = "results"):
        self.stats_manager = StatsManager(results_dir)

    def run_instance(
        self,
        instance_name: str,
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.2,
        num_runs: int = 3,
        verbose: bool = True,
    ) -> dict:
        """
        Run GA on a single instance multiple times and collect stats.

        Args:
            instance_name: Name of instance file (e.g., 'C101.txt')
            population_size: GA population size
            generations: Number of generations
            mutation_rate: Mutation rate
            num_runs: Number of independent runs
            verbose: Print progress

        Returns:
            Dictionary with experiment results
        """
        data_dir = "data"
        instance_path = os.path.join(data_dir, instance_name)

        if not os.path.exists(instance_path):
            raise FileNotFoundError(f"Instance file not found: {instance_path}")

        print(f"\n{'='*70}")
        print(f"Running: {instance_name}")
        print(f"{'='*70}")
        print(f"Population size: {population_size}")
        print(f"Generations: {generations}")
        print(f"Mutation rate: {mutation_rate}")
        print(f"Number of runs: {num_runs}\n")

        instance = Instance(instance_path)
        print(
            f"Instance: {len(instance.customers)} customers, "
            f"capacity={instance.capacity}\n"
        )

        params = {
            "population_size": population_size,
            "generations": generations,
            "mutation_rate": mutation_rate,
        }

        results = []
        total_time = time.time()

        for run in range(num_runs):
            print(f"Run {run + 1}/{num_runs}...", end=" ", flush=True)

            try:
                ga = GeneticAlgorithm(
                    instance=instance,
                    fnFitness=calculateFitness,
                    fnInitPopulation=solomon_generator,
                    populationSize=population_size,
                    generations=generations,
                    mutationRate=mutation_rate,
                )
                result = ga.run()
                results.append(result)

                # Save individual result
                self.stats_manager.save_result(result, instance_name, run + 1, params)

                if result.bestFitness != float("inf"):
                    print(
                        f"✓ Fitness: {result.bestFitness:.2f}, "
                        f"Time: {result.runtime:.2f}s"
                    )
                else:
                    print("✗ Infeasible solution")

            except Exception as e:
                print(f"Error: {str(e)}")
                raise

        total_time = time.time() - total_time

        # Save summary
        summary_path = self.stats_manager.save_summary(instance_name, results, params)

        # Print summary
        self._print_summary(instance_name, results, total_time)

        return {
            "instance": instance_name,
            "results": results,
            "summary_path": summary_path,
            "total_time": total_time,
        }

    def run_batch(
        self,
        instances: list[str],
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.2,
        num_runs: int = 3,
        verbose: bool = True,
    ) -> list[dict]:
        all_results = []

        for instance in instances:
            try:
                result = self.run_instance(
                    instance,
                    population_size=population_size,
                    generations=generations,
                    mutation_rate=mutation_rate,
                    num_runs=num_runs,
                    verbose=verbose,
                )
                all_results.append(result)
            except Exception as e:
                if verbose:
                    print(f"Failed to run {instance}: {str(e)}")
                continue

        return all_results

    @staticmethod
    def _print_summary(instance_name: str, results, total_time: float) -> None:
        """Print comprehensive summary including operator statistics."""
        valid_results = [r for r in results if r.bestFitness != float("inf")]

        print(f"\n{'-'*70}")
        print(f"SUMMARY: {instance_name}")
        print(f"{'-'*70}")

        # === FITNESS STATISTICS ===
        print(f"\nFITNESS STATISTICS:")
        print(f"  Total runs: {len(results)}")
        print(f"  Successful runs: {len(valid_results)}")

        if valid_results:
            fitness_values = [r.bestFitness for r in valid_results]
            print(f"  Best fitness: {min(fitness_values):.2f}")
            print(f"  Worst fitness: {max(fitness_values):.2f}")
            print(f"  Avg fitness: {sum(fitness_values)/len(fitness_values):.2f}")
            std_val = ExperimentRunner._std_dev(fitness_values)
            print(f"  Std dev: {std_val:.2f}")
        else:
            print("  No feasible solutions found")

        print(
            f"  Avg runtime per run: {sum(r.runtime for r in results)/len(results):.2f}s"
        )
        print(f"  Total time: {total_time:.2f}s")

        # === OPERATOR STATISTICS ===
        print(f"\nOPERATOR STATISTICS (Averaged across {len(results)} runs):")

        # Selection
        selection_calls = [r.operatorStats["selection_calls"] for r in results]
        selection_improvements = [
            r.operatorStats["selection_improvements"] for r in results
        ]
        avg_sel_calls = sum(selection_calls) / len(selection_calls)
        avg_sel_improve = sum(selection_improvements) / len(selection_improvements)
        sel_improve_rate = (
            (sum(selection_improvements) / sum(selection_calls) * 100)
            if sum(selection_calls) > 0
            else 0
        )

        print(f"\n  SELECTION:")
        print(f"    Avg calls per run: {avg_sel_calls:.1f}")
        print(f"    Avg improvements per run: {avg_sel_improve:.1f}")
        print(f"    Improvement rate: {sel_improve_rate:.2f}%")

        # Crossover
        crossover_calls = [r.operatorStats["crossover_calls"] for r in results]
        crossover_improvements = [
            r.operatorStats["crossover_improvements"] for r in results
        ]
        avg_cross_calls = sum(crossover_calls) / len(crossover_calls)
        avg_cross_improve = sum(crossover_improvements) / len(crossover_improvements)
        cross_improve_rate = (
            (sum(crossover_improvements) / sum(crossover_calls) * 100)
            if sum(crossover_calls) > 0
            else 0
        )

        print(f"\n  CROSSOVER:")
        print(f"    Avg calls per run: {avg_cross_calls:.1f}")
        print(f"    Avg improvements per run: {avg_cross_improve:.1f}")
        print(f"    Improvement rate: {cross_improve_rate:.2f}%")

        # Mutation
        mutation_calls = [r.operatorStats["mutation_calls"] for r in results]
        mutation_improvements = [
            r.operatorStats["mutation_improvements"] for r in results
        ]
        infeasible_sols = [r.operatorStats["infeasible_solutions"] for r in results]
        avg_mut_calls = sum(mutation_calls) / len(mutation_calls)
        avg_mut_improve = sum(mutation_improvements) / len(mutation_improvements)
        mut_improve_rate = (
            (sum(mutation_improvements) / sum(mutation_calls) * 100)
            if sum(mutation_calls) > 0
            else 0
        )
        avg_infeasible = sum(infeasible_sols) / len(infeasible_sols)

        print(f"\n  MUTATION:")
        print(f"    Avg calls per run: {avg_mut_calls:.1f}")
        print(f"    Avg improvements per run: {avg_mut_improve:.1f}")
        print(f"    Improvement rate: {mut_improve_rate:.2f}%")
        print(f"    Avg infeasible solutions: {avg_infeasible:.1f}")

        # Overall effectiveness
        total_ops = sum(selection_calls) + sum(crossover_calls) + sum(mutation_calls)
        total_improvements = (
            sum(selection_improvements)
            + sum(crossover_improvements)
            + sum(mutation_improvements)
        )
        overall_rate = (total_improvements / total_ops * 100) if total_ops > 0 else 0

        print(f"\n  OVERALL:")
        print(f"    Total operators called: {total_ops}")
        print(f"    Total improvements: {total_improvements}")
        print(f"    Overall improvement rate: {overall_rate:.2f}%")

        if total_improvements > 0:
            print(
                f"    Selection contribution: {(sum(selection_improvements)/total_improvements*100):.1f}%"
            )
            print(
                f"    Crossover contribution: {(sum(crossover_improvements)/total_improvements*100):.1f}%"
            )
            print(
                f"    Mutation contribution: {(sum(mutation_improvements)/total_improvements*100):.1f}%"
            )

        print()

    @staticmethod
    def _std_dev(values: list[float]) -> float:
        """Calculate standard deviation."""
        if not values or len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance**0.5


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "  python main.py <instance> [pop_size] [generations] [mut_rate] [num_runs]"
        )
        print("  python main.py batch <pop_size> [generations] [mut_rate] [num_runs]")
        print("\nExamples:")
        print("  python main.py C101.txt")
        print("  python main.py C101.txt 50 100 0.2 3")
        print("  python main.py batch 50 100 0.2 1  # (runs all instances in data/)")
        sys.exit(1)

    runner = ExperimentRunner()

    if sys.argv[1] == "batch":
        data_dir = "data"
        instances = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
        instances.sort()

        pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        gens = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        mut_rate = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
        num_runs = int(sys.argv[5]) if len(sys.argv) > 5 else 1

        print(f"Found {len(instances)} instances")
        print(f"Total experiments: {len(instances) * num_runs}")

        runner.run_batch(
            instances,
            population_size=pop_size,
            generations=gens,
            mutation_rate=mut_rate,
            num_runs=num_runs,
        )

        print("\n" + "=" * 70)
        print("BATCH COMPLETE - All results saved to 'results/' directory")
        print("=" * 70)

    else:
        # Run single instance
        instance = sys.argv[1]
        pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        gens = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        mut_rate = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
        num_runs = int(sys.argv[5]) if len(sys.argv) > 5 else 3

        runner.run_instance(
            instance,
            population_size=pop_size,
            generations=gens,
            mutation_rate=mut_rate,
            num_runs=num_runs,
        )

        print("=" * 70)
        print(f"Results saved to 'results/{instance.replace('.txt', '')}/' directory")
        print("=" * 70)


if __name__ == "__main__":
    main()
