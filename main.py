#!/usr/bin/env python3


import os
import sys
import time

from ga.genetic_algorithm import GeneticAlgorithm
from stats import StatsManager
from vrptw.fitness import calculateFitness, getSolutionStats, makeFitnessFunction
from vrptw.generateInit import make_mixed_initializer
from vrptw.instance import Instance


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

        fn_fitness = makeFitnessFunction(
            instance,
            alpha=0.5,   # weight vehicles (primary objective)
            beta=0.4,    # weight distance
            gamma=0.1,   # weight wait time
        )
        for run in range(num_runs):
            print(f"Run {run + 1}/{num_runs}...", end=" ", flush=True)

            ga = GeneticAlgorithm(
                instance=instance,
                fnFitness=fn_fitness,
                fnInitPopulation=make_mixed_initializer(),
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

        total_time = time.time() - total_time

        # Save summary
        summary_path = self.stats_manager.save_summary(instance_name, results, params)

        # Print summary
        self._print_summary(instance_name, results, total_time, instance)

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
            result = self.run_instance(
                instance,
                population_size=population_size,
                generations=generations,
                mutation_rate=mutation_rate,
                num_runs=num_runs,
                verbose=verbose,
            )
            all_results.append(result)

        return all_results

    @staticmethod
    def _print_summary(
        instance_name: str, results, total_time: float, instance: Instance
    ) -> None:
        valid_results = [r for r in results if r.bestFitness != float("inf")]

        print(f"\n{'-'*70}")
        print(f"SUMMARY: {instance_name}")
        print(f"{'-'*70}")

        if valid_results:
            fitness_values = [r.bestFitness for r in valid_results]
            best_result = min(valid_results, key=lambda r: r.bestFitness)
            best_stats = getSolutionStats(best_result.bestSolution, instance)

            print("FITNESS:")
            print(
                f"  Best: {min(fitness_values):>10.2f} | Avg: {sum(fitness_values)/len(fitness_values):>10.2f}"
            )

            print("\nBEST SOLUTION:")
            print(
                f"  Vehicles: {best_stats['num_vehicles']:>6} | Distance: {best_stats['total_distance']:>10.2f}"
            )
        else:
            print("  No feasible solutions found")

        # === NEW: TIME PROFILING SECTION ===
        print(f"\n{'*'*20} TIME PROFILING (AVG PER RUN) {'*'*20}")

        # Aggregate stats from all runs
        num_runs = len(results)
        avg_init = (
            sum(r.operatorStats.get("total_time_init", 0) for r in results) / num_runs
        )
        avg_sel = (
            sum(r.operatorStats.get("total_time_selection", 0) for r in results)
            / num_runs
        )
        avg_cross = (
            sum(r.operatorStats.get("total_time_crossover", 0) for r in results)
            / num_runs
        )
        avg_mut = (
            sum(r.operatorStats.get("total_time_mutation", 0) for r in results)
            / num_runs
        )
        avg_repair = (
            sum(r.operatorStats.get("total_time_repair", 0) for r in results) / num_runs
        )
        avg_total = sum(r.runtime for r in results) / num_runs

        print(f"  Initialization:  {avg_init:>8.4f}s")
        print(f"  Selection:       {avg_sel:>8.4f}s")
        print(f"  Crossover:       {avg_cross:>8.4f}s")
        print(f"  Mutation:        {avg_mut:>8.4f}s")
        print(f"  Repair Logic:    {avg_repair:>8.4f}s")
        print("  ---------------------------")
        print(f"  Avg Total Run:   {avg_total:>8.4f}s")
        print(f"  Wall Clock:      {total_time:>8.2f}s (Total experiment)")

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
