#!/usr/bin/env python3
"""
Command-line utility for running GA VRPTW experiments
Provides a simpler alternative to the UI for batch operations
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ga.genetic_algorithm import GeneticAlgorithm
from vrptw.instance import Instance
from vrptw.fitness import calculateFitness
from vrptw.generateInit import (
    random_generator, solomon_generator,
    cluster_first_route_second, savings_heuristic, make_mixed_initializer
)
from operators.crossover import (
    PMXCrossOver, crossover_ox, crossover_cx,
    edgeAssemblyCrossover, route_based_crossover
)
from operators.mutation import orOpt, mutate_scramble, twoOpt, mutate_insert
from ga.selection import tournamentSelection, rouletteSelection, selection_truncation
from stats import StatsManager

# Operator mapping
INITIALIZERS = {
    "random": random_generator,
    "solomon": solomon_generator,
    "cluster": cluster_first_route_second,
    "savings": savings_heuristic,
    "mixed": lambda inst: make_mixed_initializer()(inst)
}

CROSSOVERS = {
    "pmx": PMXCrossOver,
    "ox": crossover_ox,
    "cx": crossover_cx,
    "edge": edgeAssemblyCrossover,
    "route": route_based_crossover
}

MUTATIONS = {
    "oropt": orOpt,
    "scramble": mutate_scramble,
    "2opt": twoOpt,
    "insert": mutate_insert
}

SELECTIONS = {
    "tournament": tournamentSelection,
    "roulette": rouletteSelection,
    "truncation": selection_truncation
}


def run_experiment(args):
    """Run a GA experiment with given parameters"""
    
    # Load instance
    data_dir = "data"
    instance_path = os.path.join(data_dir, args.instance)
    
    if not os.path.exists(instance_path):
        print(f"Error: Instance file not found: {instance_path}")
        return False
    
    instance = Instance(instance_path)
    print(f"Loaded instance: {args.instance}")
    print(f"  Customers: {len(instance.customers)}")
    print(f"  Capacity: {instance.capacity}\n")
    
    # Get operators
    if args.init not in INITIALIZERS:
        print(f"Error: Unknown initializer '{args.init}'")
        print(f"Available: {', '.join(INITIALIZERS.keys())}")
        return False
    
    if args.crossover not in CROSSOVERS:
        print(f"Error: Unknown crossover '{args.crossover}'")
        print(f"Available: {', '.join(CROSSOVERS.keys())}")
        return False
    
    if args.mutation not in MUTATIONS:
        print(f"Error: Unknown mutation '{args.mutation}'")
        print(f"Available: {', '.join(MUTATIONS.keys())}")
        return False
    
    if args.selection not in SELECTIONS:
        print(f"Error: Unknown selection '{args.selection}'")
        print(f"Available: {', '.join(SELECTIONS.keys())}")
        return False
    
    init_fn = INITIALIZERS[args.init]
    cross_fn = CROSSOVERS[args.crossover]
    mut_fn = MUTATIONS[args.mutation]
    sel_fn = SELECTIONS[args.selection]
    
    print(f"Configuration:")
    print(f"  Initializer: {args.init}")
    print(f"  Crossover: {args.crossover}")
    print(f"  Mutation: {args.mutation}")
    print(f"  Selection: {args.selection}")
    print(f"  Population: {args.population}")
    print(f"  Generations: {args.generations}")
    print(f"  Mutation rate: {args.mut_rate}")
    print(f"  Runs: {args.runs}\n")
    
    stats_manager = StatsManager()
    params = {
        "population_size": args.population,
        "generations": args.generations,
        "mutation_rate": args.mut_rate,
        "initializer": args.init,
        "crossover": args.crossover,
        "mutation": args.mutation,
        "selection": args.selection
    }
    
    # Run GA multiple times
    print("Running experiments...")
    best_overall = float("inf")
    
    for run_num in range(args.runs):
        print(f"  Run {run_num + 1}/{args.runs}...", end=" ", flush=True)
        
        ga = GeneticAlgorithm(
            instance=instance,
            fnFitness=calculateFitness,
            fnInitPopulation=init_fn,
            fnSelection=sel_fn,
            fnCrossover=cross_fn,
            fnMutation=mut_fn,
            populationSize=args.population,
            generations=args.generations,
            mutationRate=args.mut_rate
        )
        
        result = ga.run()
        
        # Save result
        stats_manager.save_result(result, args.instance, run_num + 1, params)
        
        if result.bestFitness != float("inf"):
            print(f"✓ Fitness: {result.bestFitness:.2f}")
            if result.bestFitness < best_overall:
                best_overall = result.bestFitness
        else:
            print("✗ No feasible solution")
    
    print(f"\nResults saved to: results/{args.instance.replace('.txt', '')}")
    if best_overall != float("inf"):
        print(f"Best fitness: {best_overall:.2f}")
    
    return True


def list_operators(args):
    """List available operators"""
    print("Available Initializers:")
    for name in INITIALIZERS.keys():
        print(f"  {name}")
    
    print("\nAvailable Crossovers:")
    for name in CROSSOVERS.keys():
        print(f"  {name}")
    
    print("\nAvailable Mutations:")
    for name in MUTATIONS.keys():
        print(f"  {name}")
    
    print("\nAvailable Selections:")
    for name in SELECTIONS.keys():
        print(f"  {name}")


def list_instances(args):
    """List available data instances"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        return
    
    instances = sorted([f for f in os.listdir(data_dir) if f.endswith('.txt')])
    print(f"Available instances ({len(instances)}):")
    
    # Group by type
    c_instances = [f for f in instances if f.startswith('C')]
    r_instances = [f for f in instances if f.startswith('R')]
    rc_instances = [f for f in instances if f.startswith('RC')]
    
    if c_instances:
        print(f"\n  Clustered (C): {', '.join(c_instances)}")
    if r_instances:
        print(f"\n  Random (R): {', '.join(r_instances)}")
    if rc_instances:
        print(f"\n  Mixed (RC): {', '.join(rc_instances)}")


def main():
    parser = argparse.ArgumentParser(
        description="GA VRPTW Command-line Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ga_cli.py run C101.txt                    # Run with defaults
  python ga_cli.py run R101.txt -g 200 -p 100 -r 5  # Custom parameters
  python ga_cli.py run C101.txt --init random --crossover ox --mutation 2opt
  python ga_cli.py list instances                  # List available instances
  python ga_cli.py list operators                  # List operators
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run GA experiment')
    run_parser.add_argument('instance', help='Instance file (e.g., C101.txt)')
    run_parser.add_argument('-p', '--population', type=int, default=50,
                           help='Population size (default: 50)')
    run_parser.add_argument('-g', '--generations', type=int, default=100,
                           help='Number of generations (default: 100)')
    run_parser.add_argument('-m', '--mut-rate', type=float, default=0.2,
                           help='Mutation rate (default: 0.2)')
    run_parser.add_argument('-r', '--runs', type=int, default=3,
                           help='Number of runs (default: 3)')
    run_parser.add_argument('--init', default='random',
                           help='Initializer (default: random)')
    run_parser.add_argument('--crossover', default='edge',
                           help='Crossover operator (default: edge)')
    run_parser.add_argument('--mutation', default='2opt',
                           help='Mutation operator (default: 2opt)')
    run_parser.add_argument('--selection', default='tournament',
                           help='Selection method (default: tournament)')
    run_parser.set_defaults(func=run_experiment)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available options')
    list_parser.add_argument('type', choices=['instances', 'operators'],
                            help='What to list')
    list_parser.set_defaults(func=lambda args: list_instances(args) 
                            if args.type == 'instances' else list_operators(args))
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Change to project directory
    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent.parent
    os.chdir(project_dir)
    
    # Run command
    if args.command == 'run':
        success = run_experiment(args)
        sys.exit(0 if success else 1)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
