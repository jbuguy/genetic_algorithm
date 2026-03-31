#!/usr/bin/env python3


import os
import sys
import time

from ga.genetic_algorithm import GeneticAlgorithm
from stats import StatsManager
from vrptw.fitness import calculateFitness, getSolutionStats
from vrptw.generateInit import solomon_generator
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
        self._print_summary(instance_name, results, total_time,instance)

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
    def _print_summary(instance_name: str, results, total_time: float, instance: Instance) -> None:
        valid_results = [r for r in results if r.bestFitness != float("inf")]

        print(f"\n{'-'*70}")
        print(f"SUMMARY: {instance_name}")
        print(f"{'-'*70}")

        # === FITNESS STATISTICS ===
        print("\nFITNESS STATISTICS:")
        print(f"  Total runs:       {len(results)}")
        print(f"  Successful runs:  {len(valid_results)}")

        if valid_results:
            fitness_values = [r.bestFitness for r in valid_results]
            best_result = min(valid_results, key=lambda r: r.bestFitness)
            best_stats = getSolutionStats(best_result.bestSolution, instance)

            print(f"  Best fitness:     {min(fitness_values):.2f}")
            print(f"  Worst fitness:    {max(fitness_values):.2f}")
            print(f"  Avg fitness:      {sum(fitness_values)/len(fitness_values):.2f}")
            std_val = ExperimentRunner._std_dev(fitness_values)
            print(f"  Std dev:          {std_val:.2f}")

            # === BEST SOLUTION BREAKDOWN ===
            print(f"\nBEST SOLUTION BREAKDOWN:")
            print(f"  Vehicles used:    {best_stats['num_vehicles']}")
            print(f"  Total distance:   {best_stats['total_distance']}")
            print(f"  Total wait time:  {best_stats['total_wait_time']}")

            # Vehicle stats across all valid runs
            all_stats = [getSolutionStats(r.bestSolution, instance) for r in valid_results]
            avg_vehicles = sum(s["num_vehicles"] for s in all_stats) / len(all_stats)
            avg_distance = sum(s["total_distance"] for s in all_stats) / len(all_stats)
            print(f"\n  Avg vehicles across runs:  {avg_vehicles:.1f}")
            print(f"  Avg distance across runs:  {avg_distance:.2f}")
        else:
            print("  No feasible solutions found")

        print(f"\n  Avg runtime per run: {sum(r.runtime for r in results)/len(results):.2f}s")
        print(f"  Total time:          {total_time:.2f}s")

    # === OPERATOR STATISTICS ===
    # ... rest stays exactly the same as before ...

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
