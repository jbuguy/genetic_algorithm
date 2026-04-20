#!/usr/bin/env python3
"""
Example Usage Patterns for GA VRPTW UI
Shows common workflows and customization examples
"""

import os
import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""
EXAMPLE 1: Running a single instance from Python
"""
def example_single_run():
    from ga.genetic_algorithm import GeneticAlgorithm
    from vrptw.instance import Instance
    from vrptw.fitness import calculateFitness
    from vrptw.generateInit import solomon_generator
    from operators.crossover import edgeAssemblyCrossover
    from operators.mutation import twoOpt
    from ga.selection import tournamentSelection
    
    # Load instance
    instance = Instance("data/C101.txt")
    
    # Create GA
    ga = GeneticAlgorithm(
        instance=instance,
        fnFitness=calculateFitness,
        fnInitPopulation=solomon_generator,
        fnSelection=tournamentSelection,
        fnCrossover=edgeAssemblyCrossover,
        fnMutation=twoOpt,
        populationSize=50,
        generations=100,
        mutationRate=0.2
    )
    
    # Run
    result = ga.run()
    print(f"Best fitness: {result.bestFitness}")
    print(f"Runtime: {result.runtime:.2f}s")
    print(f"Best solution: {result.bestSolution[:20]}...")


"""
EXAMPLE 2: Running multiple instances with different operators
"""
def example_multiple_runs():
    from ga.genetic_algorithm import GeneticAlgorithm
    from vrptw.instance import Instance
    from vrptw.fitness import calculateFitness
    from vrptw.generateInit import random_generator, solomon_generator
    from operators.crossover import PMXCrossOver, edgeAssemblyCrossover
    from operators.mutation import twoOpt, mutate_scramble
    from ga.selection import tournamentSelection
    
    instances = ["C101.txt", "C102.txt", "R101.txt"]
    initializers = [random_generator, solomon_generator]
    crossovers = [PMXCrossOver, edgeAssemblyCrossover]
    mutations = [twoOpt, mutate_scramble]
    
    results = {}
    
    for instance_name in instances:
        for init_fn in initializers:
            for cross_fn in crossovers:
                for mut_fn in mutations:
                    instance = Instance(f"data/{instance_name}")
                    
                    ga = GeneticAlgorithm(
                        instance=instance,
                        fnFitness=calculateFitness,
                        fnInitPopulation=init_fn,
                        fnCrossover=cross_fn,
                        fnMutation=mut_fn,
                        populationSize=50,
                        generations=100,
                        mutationRate=0.2
                    )
                    
                    result = ga.run()
                    key = f"{instance_name}_{init_fn.__name__}_{cross_fn.__name__}_{mut_fn.__name__}"
                    results[key] = result.bestFitness
                    
                    print(f"✓ {key}: {result.bestFitness:.2f}")
    
    # Find best
    best_key = min(results, key=results.get)
    print(f"\nBest: {best_key} = {results[best_key]:.2f}")


"""
EXAMPLE 3: Custom initialization function
"""
def example_custom_initializer():
    from vrptw.instance import Instance
    from vrptw.generateInit import close_route, remove_trailing_zeros
    from typing import List
    import random
    
    def nearest_neighbor_init(instance: Instance) -> List[int]:
        """Simple nearest neighbor initialization"""
        unvisited = {c.num for c in instance.customers[1:]}
        solution = []
        route = [0]
        current = 0
        load = 0
        time = 0.0
        
        while unvisited:
            feasible = []
            for cid in unvisited:
                cust = instance.customer_map[cid]
                travel = instance.distances[current][cid]
                arrival = time + travel
                
                if arrival > cust.dueDate:
                    continue
                if load + cust.demand > instance.capacity:
                    continue
                
                feasible.append((travel, cid))
            
            if not feasible:
                close_route(route)
                solution.extend(route)
                route, current, load, time = [0], 0, 0, 0.0
                continue
            
            travel, next_cid = min(feasible)
            route.append(next_cid)
            unvisited.remove(next_cid)
            current = next_cid
            load += instance.customer_map[next_cid].demand
            time += travel
        
        close_route(route)
        solution.extend(route)
        return remove_trailing_zeros(solution)
    
    # Use custom initializer
    from ga.genetic_algorithm import GeneticAlgorithm
    from vrptw.fitness import calculateFitness
    from operators.crossover import edgeAssemblyCrossover
    from operators.mutation import twoOpt
    from ga.selection import tournamentSelection
    
    instance = Instance("data/C101.txt")
    ga = GeneticAlgorithm(
        instance=instance,
        fnFitness=calculateFitness,
        fnInitPopulation=nearest_neighbor_init,
        fnCrossover=edgeAssemblyCrossover,
        fnMutation=twoOpt,
        populationSize=50,
        generations=100
    )
    
    result = ga.run()
    print(f"Custom initializer result: {result.bestFitness:.2f}")


"""
EXAMPLE 4: Batch experiment with result saving
"""
def example_batch_with_saving():
    from ga.genetic_algorithm import GeneticAlgorithm
    from vrptw.instance import Instance
    from vrptw.fitness import calculateFitness
    from vrptw.generateInit import solomon_generator
    from operators.crossover import edgeAssemblyCrossover
    from operators.mutation import twoOpt
    from ga.selection import tournamentSelection
    from stats import StatsManager
    
    stats_manager = StatsManager()
    
    instances = ["C101.txt", "C102.txt"]
    
    for instance_name in instances:
        instance = Instance(f"data/{instance_name}")
        
        params = {
            "population_size": 50,
            "generations": 100,
            "mutation_rate": 0.2,
            "instance": instance_name
        }
        
        for run in range(3):
            ga = GeneticAlgorithm(
                instance=instance,
                fnFitness=calculateFitness,
                fnInitPopulation=solomon_generator,
                fnCrossover=edgeAssemblyCrossover,
                fnMutation=twoOpt,
                populationSize=50,
                generations=100,
                mutationRate=0.2
            )
            
            result = ga.run()
            
            # Save result
            stats_manager.save_result(result, instance_name, run + 1, params)
            print(f"✓ {instance_name} run {run + 1}: {result.bestFitness:.2f}")


"""
EXAMPLE 5: Adding a new operator to the UI
"""
def example_add_custom_operator():
    """
    To add a custom operator to the UI:
    
    1. Create your operator function:
    """
    
    def custom_crossover(parent1, parent2, instance):
        """Custom crossover operator"""
        # Your implementation here
        return parent1.copy()
    
    def custom_mutation(solution, mutation_rate, instance):
        """Custom mutation operator"""
        # Your implementation here
        return solution.copy()
    
    """
    2. Add to vrptw/view/app.py:
    
    CROSSOVERS = {
        "PMX": PMXCrossOver,
        "Custom": custom_crossover,  # Add this line
        ...
    }
    
    MUTATIONS = {
        "2-Opt": twoOpt,
        "Custom": custom_mutation,  # Add this line
        ...
    }
    
    3. Restart the UI and your operator will appear in the selection menu
    """
    pass


"""
EXAMPLE 6: Plotting results
"""
def example_plot_results():
    import plot_results
    import matplotlib.pyplot as plt
    
    # Load runs for an instance
    runs = plot_results.load_runs("C101")
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot convergence
    plot_results.plot_convergence("C101", runs, axes[0])
    
    # Plot distribution
    plot_results.plot_fitness_distribution("C101", runs, axes[1])
    
    plt.tight_layout()
    plt.show()


"""
EXAMPLE 7: Comparing different operator combinations
"""
def example_compare_operators():
    import json
    from pathlib import Path
    
    results_dir = Path("results")
    
    # Load all results for an instance
    instance_name = "C101"
    instance_dir = results_dir / instance_name
    
    combinations = {}
    
    for run_file in instance_dir.glob("run_*.json"):
        with open(run_file) as f:
            data = json.load(f)
            
            # Group by operators
            key = (
                data["parameters"].get("initializer", "unknown"),
                data["parameters"].get("crossover", "unknown"),
                data["parameters"].get("mutation", "unknown")
            )
            
            if key not in combinations:
                combinations[key] = []
            combinations[key].append(data["best_fitness"])
    
    # Print summary
    print(f"\nOperator Comparison for {instance_name}:")
    print(f"{'Initializer':<15} {'Crossover':<15} {'Mutation':<15} {'Avg Fitness':<15}")
    print("-" * 60)
    
    for (init, cross, mut), fitnesses in combinations.items():
        avg = sum(fitnesses) / len(fitnesses)
        print(f"{init:<15} {cross:<15} {mut:<15} {avg:<15.2f}")


# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GA VRPTW Usage Examples")
    parser.add_argument("example", type=int, choices=range(1, 8),
                       help="Example number to run (1-7)")
    
    args = parser.parse_args()
    
    examples = {
        1: example_single_run,
        2: example_multiple_runs,
        3: example_custom_initializer,
        4: example_batch_with_saving,
        5: example_add_custom_operator,
        6: example_plot_results,
        7: example_compare_operators,
    }
    
    example_func = examples.get(args.example)
    if example_func:
        try:
            example_func()
        except Exception as e:
            print(f"Error running example: {e}")
            import traceback
            traceback.print_exc()
    else:
        parser.print_help()
