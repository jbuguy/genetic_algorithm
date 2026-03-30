import os
import time
import statistics
from collections import defaultdict
from typing import Dict, List, Any
import json
import csv

from ga.genetic_algorithm import GeneticAlgorithm
from vrptw.instance import Instance
from vrptw.fitness import calculateFitness


def run_statistics_experiment():
    data_dir = "data"
    data_files = [f for f in os.listdir(data_dir) if f.endswith('.txt') and not f.startswith('__')]

    print(f"Found {len(data_files)} VRPTW instances to test")
    print("=" * 60)

    instance_stats = {}
    operator_stats = {
        'selection': defaultdict(list),
        'crossover': defaultdict(list),
        'mutation': defaultdict(list)
    }

    for instance_file in sorted(data_files):
        print(f"\n ca Testing instance: {instance_file}")
        print("-" * 40)

        instance_path = os.path.join(data_dir, instance_file)
        instance = Instance(instance_path)

        instance_results = {
            'instance': instance_file,
            'runs': [],
            'best_fitness': float('inf'),
            'worst_fitness': 0.0,
            'avg_fitness': 0.0,
            'std_fitness': 0.0,
            'best_solution': None,
            'convergence_generations': [],
            'runtime_stats': [],
            'operator_stats': {
                'selection_calls': [],
                'crossover_calls': [],
                'mutation_calls': [],
                'selection_improvements': [],
                'crossover_improvements': [],
                'mutation_improvements': [],
                'infeasible_solutions': [],
                'avg_selection_time': [],
                'avg_crossover_time': [],
                'avg_mutation_time': []
            }
        }

        fitness_values = []
        best_solution_for_instance = None
        best_fitness_for_instance = float('inf')

        for run in range(30):
            print(f"  Run {run + 1}/30...", end='', flush=True)

            start_time = time.time()

            # Create GA instance
            ga = GeneticAlgorithm(
                instance=instance,
                fnFitness=calculateFitness,
                populationSize=50,  # Reduced for testing
                generations=50,     # Reduced for testing
                mutationRate=0.2
            )

            # Run GA
            result = ga.run()

            runtime = time.time() - start_time

            # Handling result and stats
            if result.bestFitness is None or result.bestFitness == float('inf'):
                print(f" WARNING: Run {run + 1} found no feasible solution!", flush=True)
            else:
                print(f" bestFitness={result.bestFitness:.3f}, runTime={runtime:.3f}s", flush=True)

                if result.bestFitness < best_fitness_for_instance:
                    best_fitness_for_instance = result.bestFitness
                    best_solution_for_instance = result.bestSolution

            fitness_values.append(result.bestFitness if result.bestFitness is not None else float('inf'))
            instance_results['runs'].append({
                'run': run + 1,
                'best_fitness': result.bestFitness,
                'runtime': runtime,
                'best_record': result.bestRecord,
                'avg_record': result.avgRecord,
                'operator_stats': result.operatorStats
            })
            instance_results['runtime_stats'].append(runtime)
            instance_results['convergence_generations'].append(find_convergence_generation(result.bestRecord))

            instance_results['operator_stats']['selection_calls'].append(result.operatorStats['selection_calls'])
            instance_results['operator_stats']['crossover_calls'].append(result.operatorStats['crossover_calls'])
            instance_results['operator_stats']['mutation_calls'].append(result.operatorStats['mutation_calls'])
            instance_results['operator_stats']['selection_improvements'].append(result.operatorStats.get('selection_improvements', 0))
            instance_results['operator_stats']['crossover_improvements'].append(result.operatorStats.get('crossover_improvements', 0))
            instance_results['operator_stats']['mutation_improvements'].append(result.operatorStats.get('mutation_improvements', 0))
            instance_results['operator_stats']['infeasible_solutions'].append(result.operatorStats.get('infeasible_solutions', 0))

            op_timings = result.operatorStats.get('operator_timings', {})
            selection_times = op_timings.get('selection', [])
            crossover_times = op_timings.get('crossover', [])
            mutation_times = op_timings.get('mutation', [])
            instance_results['operator_stats']['avg_selection_time'].append(statistics.mean(selection_times) if selection_times else 0.0)
        instance_results['operator_stats']['avg_crossover_time'].append(statistics.mean(crossover_times) if crossover_times else 0.0)
        instance_results['operator_stats']['avg_mutation_time'].append(statistics.mean(mutation_times) if mutation_times else 0.0)

        finite_fitness = [v for v in fitness_values if v is not None and v != float('inf') and not (isinstance(v, float) and (v != v))]

        if finite_fitness:
            instance_results['best_fitness'] = min(finite_fitness)
            instance_results['worst_fitness'] = max(finite_fitness)
            instance_results['avg_fitness'] = statistics.mean(finite_fitness)
            instance_results['std_fitness'] = statistics.stdev(finite_fitness) if len(finite_fitness) > 1 else 0.0
        else:
            instance_results['best_fitness'] = float('inf')
            instance_results['worst_fitness'] = float('inf')
            instance_results['avg_fitness'] = float('inf')
            instance_results['std_fitness'] = 0.0

        instance_results['best_solution'] = best_solution_for_instance
        instance_stats[instance_file] = instance_results

        # Print instance summary
        print(f" Instance {instance_file} summary:")
        if instance_results['best_fitness'] == float('inf'):
            print("   result: no feasible solution found in this run set")
        else:
            print(f"   best_fitness: {instance_results['best_fitness']:.3f}")
            print(f"   worst_fitness: {instance_results['worst_fitness']:.3f}")
            print(f"   avg_fitness: {instance_results['avg_fitness']:.3f}")
            print(f"   std_fitness: {instance_results['std_fitness']:.3f}")
    # Generate comprehensive report
    generate_statistics_report(instance_stats, operator_stats)


def find_convergence_generation(best_record: List[float], threshold: float = 0.001) -> int:
    """Find the generation where fitness improvement becomes minimal."""
    if len(best_record) < 2:
        return len(best_record)

    for i in range(1, len(best_record)):
        improvement = abs(best_record[i] - best_record[i-1]) / max(abs(best_record[i-1]), 1e-10)
        if improvement < threshold:
            return i + 1

    return len(best_record)


def generate_statistics_report(instance_stats: Dict[str, Any], operator_stats: Dict[str, Any]):

    print("\n" + "=" * 80)
    print("COMPREHENSIVE VRPTW GENETIC ALGORITHM STATISTICS REPORT")
    print("=" * 80)

    all_fitness = []
    all_runtimes = []
    all_convergence = []
    all_operator_stats = {
        'selection_calls': [],
        'crossover_calls': [],
        'mutation_calls': [],
        'selection_improvements': [],
        'crossover_improvements': [],
        'mutation_improvements': [],
        'infeasible_solutions': [],
        'avg_selection_time': [],
        'avg_crossover_time': [],
        'avg_mutation_time': []
    }

    for instance_data in instance_stats.values():
        all_fitness.extend([run['best_fitness'] for run in instance_data['runs']])
        all_runtimes.extend(instance_data['runtime_stats'])
        all_convergence.extend(instance_data['convergence_generations'])

        for stat_name in all_operator_stats.keys():
            if stat_name in instance_data['operator_stats']:
                all_operator_stats[stat_name].extend(instance_data['operator_stats'][stat_name])

    print("\nOVERALL PERFORMANCE:")
    print("-" * 40)
    if all_fitness:
        print(f"  total runs: {len(all_fitness)}")
        print(f"  best fitness: {min(all_fitness):.3f}")
        print(f"  worst fitness: {max(all_fitness):.3f}")
        print(f"  avg fitness: {statistics.mean(all_fitness):.3f}")
        print(f"  std fitness: {statistics.stdev(all_fitness) if len(all_fitness) > 1 else 0.0:.3f}")

    print("\nOPERATOR PERFORMANCE ANALYSIS:")
    print("-" * 50)

    if all_operator_stats['selection_calls']:
        avg_sel_calls = statistics.mean(all_operator_stats['selection_calls'])
        avg_sel_improve = statistics.mean(all_operator_stats['selection_improvements']) if all_operator_stats['selection_improvements'] else 0
        sel_success_rate = (avg_sel_improve / avg_sel_calls) * 100 if avg_sel_calls > 0 else 0
        print(f"  selection calls: {avg_sel_calls:.1f}, improvement events: {avg_sel_improve:.1f}, success rate: {sel_success_rate:.2f}%")

    if all_operator_stats['crossover_calls']:
        avg_cross_calls = statistics.mean(all_operator_stats['crossover_calls'])
        avg_cross_improve = statistics.mean(all_operator_stats['crossover_improvements']) if all_operator_stats['crossover_improvements'] else 0
        cross_success_rate = (avg_cross_improve / avg_cross_calls) * 100 if avg_cross_calls > 0 else 0
        print(f"  crossover calls: {avg_cross_calls:.1f}, improvement events: {avg_cross_improve:.1f}, success rate: {cross_success_rate:.2f}%")

    if all_operator_stats['mutation_calls']:
        avg_mut_calls = statistics.mean(all_operator_stats['mutation_calls'])
        avg_mut_improve = statistics.mean(all_operator_stats['mutation_improvements']) if all_operator_stats['mutation_improvements'] else 0
        mut_success_rate = (avg_mut_improve / avg_mut_calls) * 100 if avg_mut_calls > 0 else 0
        infeasible_rate = statistics.mean(all_operator_stats['infeasible_solutions']) if all_operator_stats['infeasible_solutions'] else 0
        print(f"  mutation calls: {avg_mut_calls:.1f}, improvement events: {avg_mut_improve:.1f}, success rate: {mut_success_rate:.2f}%, infeasible rate: {infeasible_rate:.2f}")

    # Operator timing analysis
    if all_operator_stats['avg_selection_time']:
        print(f"  avg selection time: {statistics.mean(all_operator_stats['avg_selection_time']):.6f}s")
    if all_operator_stats['avg_crossover_time']:
        print(f"  avg crossover time: {statistics.mean(all_operator_stats['avg_crossover_time']):.6f}s")
    if all_operator_stats['avg_mutation_time']:
        print(f"  avg mutation time: {statistics.mean(all_operator_stats['avg_mutation_time']):.6f}s")

    # Instance-by-instance breakdown
    print("\nINSTANCE-BY-INSTANCE RESULTS:")
    print("-" * 80)

    for instance_name, data in sorted(instance_stats.items()):
        print(f"  {instance_name}: best={data['best_fitness']:.3f}, worst={data['worst_fitness']:.3f}, avg={data['avg_fitness']:.3f}, std={data['std_fitness']:.3f}, avg_time={statistics.mean(data['runtime_stats']):.3f}s")

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    best_solutions_dir = os.path.join(output_dir, "best_solutions")
    os.makedirs(best_solutions_dir, exist_ok=True)

    # Save best solution per instance
    for instance_name, data in instance_stats.items():
        solution = data.get('best_solution')
        if solution:
            sol_path = os.path.join(best_solutions_dir, f"{instance_name}.txt")
            with open(sol_path, 'w') as f:
                f.write(','.join(str(x) for x in solution))

    # Save summary CSV for instance stats
    stats_csv_path = os.path.join(output_dir, "instance_stats.csv")
    with open(stats_csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["instance", "best_fitness", "worst_fitness", "avg_fitness", "std_fitness", "avg_runtime"])
        for instance_name, data in sorted(instance_stats.items()):
            avg_runtime = statistics.mean(data['runtime_stats']) if data['runtime_stats'] else 0.0
            writer.writerow([
                instance_name,
                data['best_fitness'],
                data['worst_fitness'],
                data['avg_fitness'],
                data['std_fitness'],
                avg_runtime
            ])

    # Save detailed results to JSON
    output_file = "vrptw_statistics_report.json"
    with open(output_file, 'w') as f:
        json.dump({
            'experiment_info': {
                'total_instances': len(instance_stats),
                'runs_per_instance': 30,
                'total_runs': len(instance_stats) * 30,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'overall_stats': {
                'best_fitness': min([v for v in all_fitness if v != float('inf') and v == v], default=float('inf')),
                'worst_fitness': max([v for v in all_fitness if v != float('inf') and v == v], default=float('inf')),
                'avg_fitness': statistics.mean([v for v in all_fitness if v != float('inf') and v == v]) if [v for v in all_fitness if v != float('inf') and v == v] else float('inf'),
                'std_fitness': statistics.stdev([v for v in all_fitness if v != float('inf') and v == v]) if len([v for v in all_fitness if v != float('inf') and v == v]) > 1 else 0.0,
                'avg_runtime': statistics.mean(all_runtimes) if all_runtimes else 0.0,
                'avg_convergence': statistics.mean(all_convergence) if all_convergence else 0.0
            },
            'instance_stats': instance_stats,
            'operator_stats': operator_stats
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")
    print(f"Best solutions saved to: {best_solutions_dir}")
    print(f"Instance stats CSV saved to: {stats_csv_path}")

    # Performance analysis
    print("\nPERFORMANCE ANALYSIS:")
    print("-" * 40)

    if instance_stats:
        best_instance = min(instance_stats.items(), key=lambda x: x[1]['best_fitness'])
        worst_instance = max(instance_stats.items(), key=lambda x: x[1]['best_fitness'])

        print(f"Best performing instance: {best_instance[0]} (fitness: {best_instance[1]['best_fitness']:.2f})")
        print(f"Worst performing instance: {worst_instance[0]} (fitness: {worst_instance[1]['best_fitness']:.2f})")

        # Runtime analysis
        fast_instance = min(instance_stats.items(), key=lambda x: statistics.mean(x[1]['runtime_stats']))
        slow_instance = max(instance_stats.items(), key=lambda x: statistics.mean(x[1]['runtime_stats']))

        print(f"Fastest instance: {fast_instance[0]} (avg: {statistics.mean(fast_instance[1]['runtime_stats']):.3f}s)")
        print(f"Slowest instance: {slow_instance[0]} (avg: {statistics.mean(slow_instance[1]['runtime_stats']):.3f}s)")
    else:
        print("No instances were processed, cannot compute best/worst performance points.")

    print("\n✅ Statistics experiment completed successfully!")


if __name__ == "__main__":
    run_statistics_experiment()