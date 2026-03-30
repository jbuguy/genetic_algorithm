#!/usr/bin/env python3

import os
import sys
import time
from ga.genetic_algorithm import GeneticAlgorithm
from vrptw.instance import Instance
from vrptw.fitness import calculateFitness


def run_instance(
    instance_name, population_size=50, generations=100, mutation_rate=0.2, runs=1
):
    data_dir = "data"
    instance_path = os.path.join(data_dir, instance_name)

    if not os.path.exists(instance_path):
        print(f"Instance file not found: {instance_path}")
        return

    print(f"Running algorithm on: {instance_name}")
    print(f"Population size: {population_size}")
    print(f"Generations: {generations}")
    print(f"Mutation rate: {mutation_rate}")
    print(f"Number of runs: {runs}\n")

    instance = Instance(instance_path)
    print(
        f"Instance loaded: {len(instance.customers)} customers, capacity={instance.capacity}"
    )
    print("-" * 60)

    best_overall_fitness = float("inf")
    best_overall_solution = None
    runtimes = []

    for run in range(runs):
        print(f"\nRun {run + 1}/{runs}...", end="", flush=True)

        start_time = time.time()

        # Create and run GA
        ga = GeneticAlgorithm(
            instance=instance,
            fnFitness=calculateFitness,
            populationSize=population_size,
            generations=generations,
            mutationRate=mutation_rate,
        )

        result = ga.run()
        runtime = time.time() - start_time
        runtimes.append(runtime)

        if result.bestFitness is not None and result.bestFitness != float("inf"):
            print(f" ✓ bestFitness={result.bestFitness:.2f}, time={runtime:.2f}s")

            if result.bestFitness < best_overall_fitness:
                best_overall_fitness = result.bestFitness
                best_overall_solution = result.bestSolution
        else:
            print(f" ✗ No feasible solution found, time={runtime:.2f}s")

    print("RESULTS")

    if best_overall_fitness != float("inf"):
        print(f"Best fitness found: {best_overall_fitness:.2f}")
        print(f"Average runtime: {sum(runtimes)/len(runtimes):.2f}s")
        print(f"Total runtime: {sum(runtimes):.2f}s")
        print(
            f"\nBest solution: {best_overall_solution}"
        )
    else:
        print("No feasible solution found in any run")
        print(f"Average runtime: {sum(runtimes)/len(runtimes):.2f}s")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode: python run_single_instance.py C101.txt
        instance = sys.argv[1]
        pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        gens = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        mut_rate = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
        num_runs = int(sys.argv[5]) if len(sys.argv) > 5 else 1

        run_instance(instance, pop_size, gens, mut_rate, num_runs)
