import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ga.genetic_algorithm import GAResult


class StatsManager:
    """Manages saving and loading GA results and statistics."""

    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

    def save_result(
        self,
        result: GAResult,
        instance_name: str,
        run_number: int,
        params: dict[str, Any],
    ) -> str:
        """
        Save a single GA result to JSON.

        Args:
            result: GAResult object from GA.run()
            instance_name: Name of the instance (e.g., 'C101.txt')
            run_number: Which run number this is
            params: Dictionary of GA parameters (population_size, generations, mutation_rate)

        Returns:
            Path to saved file
        """
        # Create instance directory
        instance_dir = self.results_dir / instance_name.replace(".txt", "")
        instance_dir.mkdir(exist_ok=True)

        # Prepare data
        data = {
            "timestamp": datetime.now().isoformat(),
            "instance": instance_name,
            "run_number": run_number,
            "parameters": params,
            "best_solution": result.bestSolution,
            "best_fitness": result.bestFitness,
            "generations": result.generations,
            "runtime": result.runtime,
            "best_record": result.bestRecord,
            "avg_record": result.avgRecord,
            "operator_stats": result.operatorStats,
        }

        # Save to JSON
        filename = f"run_{run_number:03d}.json"
        filepath = instance_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def save_summary(
        self,
        instance_name: str,
        results: list[GAResult],
        params: dict[str, Any],
    ) -> str:
        """
        Save a summary of multiple runs for an instance.

        Args:
            instance_name: Name of the instance
            results: List of GAResult objects
            params: GA parameters

        Returns:
            Path to saved summary file
        """
        instance_dir = self.results_dir / instance_name.replace(".txt", "")
        instance_dir.mkdir(exist_ok=True)

        # Calculate statistics
        valid_results = [r for r in results if r.bestFitness != float("inf")]
        fitness_values = [r.bestFitness for r in valid_results]

        summary = {
            "timestamp": datetime.now().isoformat(),
            "instance": instance_name,
            "parameters": params,
            "total_runs": len(results),
            "successful_runs": len(valid_results),
            "best_fitness": min(fitness_values) if fitness_values else None,
            "worst_fitness": max(fitness_values) if fitness_values else None,
            "avg_fitness": sum(fitness_values) / len(fitness_values) if fitness_values else None,
            "std_fitness": self._calculate_std(fitness_values) if fitness_values else None,
            "avg_runtime": sum(r.runtime for r in results) / len(results),
            "total_runtime": sum(r.runtime for r in results),
            "convergence_stats": self._calculate_convergence(results),
            "operator_stats": self._aggregate_operator_stats(results),
        }

        filepath = instance_dir / "summary.json"
        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)

        return str(filepath)

    @staticmethod
    def load_result(filepath: str) -> dict[str, Any]:
        """Load a single result from JSON."""
        with open(filepath, "r") as f:
            return json.load(f)

    @staticmethod
    def load_summary(filepath: str) -> dict[str, Any]:
        """Load a summary from JSON."""
        with open(filepath, "r") as f:
            return json.load(f)

    @staticmethod
    def _calculate_std(values: list[float]) -> float:
        """Calculate standard deviation."""
        if not values or len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    @staticmethod
    def _calculate_convergence(results: list[GAResult]) -> dict[str, Any]:
        """Calculate convergence statistics across runs."""
        if not results:
            return {}

        convergence = {
            "avg_best_at_generation": [],
            "avg_avg_fitness_at_generation": [],
        }

        # Average convergence curve
        max_gens = max(len(r.bestRecord) for r in results)
        for gen in range(max_gens):
            best_values = [
                r.bestRecord[gen] for r in results if gen < len(r.bestRecord)
            ]
            avg_values = [
                r.avgRecord[gen] for r in results if gen < len(r.avgRecord)
            ]

            if best_values:
                convergence["avg_best_at_generation"].append(sum(best_values) / len(best_values))
            if avg_values:
                convergence["avg_avg_fitness_at_generation"].append(sum(avg_values) / len(avg_values))

        return convergence

    @staticmethod
    def _aggregate_operator_stats(results: list[GAResult]) -> dict[str, Any]:
        """
        Aggregate operator statistics across multiple runs.

        Calculates averages and standard deviations for:
        - Call counts per operator
        - Improvement rates per operator
        - Timing statistics
        """
        if not results:
            return {}

        # Extract operator stats from all runs
        op_stats_list = [r.operatorStats for r in results]

        # Initialize aggregation
        aggregated = {
            "selection": {},
            "crossover": {},
            "mutation": {},
            "overall": {},
        }

        # ===== SELECTION STATS =====
        selection_calls = [s.get("selection_calls", 0) for s in op_stats_list]
        selection_improvements = [s.get("selection_improvements", 0) for s in op_stats_list]

        aggregated["selection"]["avg_calls"] = (
            sum(selection_calls) / len(selection_calls) if selection_calls else 0
        )
        aggregated["selection"]["avg_improvements"] = (
            sum(selection_improvements) / len(selection_improvements)
            if selection_improvements
            else 0
        )
        aggregated["selection"]["total_calls"] = sum(selection_calls)
        aggregated["selection"]["total_improvements"] = sum(selection_improvements)
        aggregated["selection"]["improvement_rate"] = (
            sum(selection_improvements) / sum(selection_calls)
            if sum(selection_calls) > 0
            else 0
        )
        aggregated["selection"]["std_calls"] = StatsManager._calculate_std(selection_calls)
        aggregated["selection"]["std_improvements"] = StatsManager._calculate_std(
            selection_improvements
        )

        # ===== CROSSOVER STATS =====
        crossover_calls = [s.get("crossover_calls", 0) for s in op_stats_list]
        crossover_improvements = [s.get("crossover_improvements", 0) for s in op_stats_list]

        aggregated["crossover"]["avg_calls"] = (
            sum(crossover_calls) / len(crossover_calls) if crossover_calls else 0
        )
        aggregated["crossover"]["avg_improvements"] = (
            sum(crossover_improvements) / len(crossover_improvements)
            if crossover_improvements
            else 0
        )
        aggregated["crossover"]["total_calls"] = sum(crossover_calls)
        aggregated["crossover"]["total_improvements"] = sum(crossover_improvements)
        aggregated["crossover"]["improvement_rate"] = (
            sum(crossover_improvements) / sum(crossover_calls)
            if sum(crossover_calls) > 0
            else 0
        )
        aggregated["crossover"]["std_calls"] = StatsManager._calculate_std(crossover_calls)
        aggregated["crossover"]["std_improvements"] = StatsManager._calculate_std(
            crossover_improvements
        )

        # ===== MUTATION STATS =====
        mutation_calls = [s.get("mutation_calls", 0) for s in op_stats_list]
        mutation_improvements = [s.get("mutation_improvements", 0) for s in op_stats_list]
        infeasible_solutions = [s.get("infeasible_solutions", 0) for s in op_stats_list]

        aggregated["mutation"]["avg_calls"] = (
            sum(mutation_calls) / len(mutation_calls) if mutation_calls else 0
        )
        aggregated["mutation"]["avg_improvements"] = (
            sum(mutation_improvements) / len(mutation_improvements)
            if mutation_improvements
            else 0
        )
        aggregated["mutation"]["total_calls"] = sum(mutation_calls)
        aggregated["mutation"]["total_improvements"] = sum(mutation_improvements)
        aggregated["mutation"]["improvement_rate"] = (
            sum(mutation_improvements) / sum(mutation_calls) if sum(mutation_calls) > 0 else 0
        )
        aggregated["mutation"]["avg_infeasible"] = (
            sum(infeasible_solutions) / len(infeasible_solutions)
            if infeasible_solutions
            else 0
        )
        aggregated["mutation"]["total_infeasible"] = sum(infeasible_solutions)
        aggregated["mutation"]["std_calls"] = StatsManager._calculate_std(mutation_calls)
        aggregated["mutation"]["std_improvements"] = StatsManager._calculate_std(
            mutation_improvements
        )

        # ===== TIMING STATS =====
        # Extract timing data if available
        selection_times = []
        crossover_times = []
        mutation_times = []

        for stats in op_stats_list:
            timings = stats.get("operator_timings", {})
            if timings.get("selection"):
                selection_times.extend(timings["selection"])
            if timings.get("crossover"):
                crossover_times.extend(timings["crossover"])
            if timings.get("mutation"):
                mutation_times.extend(timings["mutation"])

        if selection_times:
            aggregated["selection"]["avg_time_ms"] = (
                sum(selection_times) / len(selection_times) * 1000
            )
            aggregated["selection"]["std_time_ms"] = (
                StatsManager._calculate_std(selection_times) * 1000
            )

        if crossover_times:
            aggregated["crossover"]["avg_time_ms"] = (
                sum(crossover_times) / len(crossover_times) * 1000
            )
            aggregated["crossover"]["std_time_ms"] = (
                StatsManager._calculate_std(crossover_times) * 1000
            )

        if mutation_times:
            aggregated["mutation"]["avg_time_ms"] = (
                sum(mutation_times) / len(mutation_times) * 1000
            )
            aggregated["mutation"]["std_time_ms"] = (
                StatsManager._calculate_std(mutation_times) * 1000
            )

        # ===== OVERALL EFFECTIVENESS =====
        total_ops = (
            sum(selection_calls) + sum(crossover_calls) + sum(mutation_calls)
        )
        total_improvements = (
            sum(selection_improvements) + sum(crossover_improvements) + sum(mutation_improvements)
        )

        aggregated["overall"]["total_operators_called"] = total_ops
        aggregated["overall"]["total_improvements"] = total_improvements
        aggregated["overall"]["overall_improvement_rate"] = (
            total_improvements / total_ops if total_ops > 0 else 0
        )
        aggregated["overall"]["selection_contribution"] = (
            sum(selection_improvements) / total_improvements if total_improvements > 0 else 0
        )
        aggregated["overall"]["crossover_contribution"] = (
            sum(crossover_improvements) / total_improvements if total_improvements > 0 else 0
        )
        aggregated["overall"]["mutation_contribution"] = (
            sum(mutation_improvements) / total_improvements if total_improvements > 0 else 0
        )

        return aggregated
        """List all result files for an instance."""
        instance_dir = self.results_dir / instance_name.replace(".txt", "")
        if not instance_dir.exists():
            return []
        return sorted([f.name for f in instance_dir.glob("run_*.json")])

    def export_to_csv(self, instance_name: str, output_file: Optional[str] = None) -> str:
        """
        Export all results for an instance to CSV.

        Args:
            instance_name: Name of instance
            output_file: Output CSV file path (default: results/{instance}/results.csv)

        Returns:
            Path to CSV file
        """
        import csv

        instance_dir = self.results_dir / instance_name.replace(".txt", "")
        if output_file is None:
            output_file = instance_dir / "results.csv"
        else:
            output_file = Path(output_file)

        result_files = sorted(instance_dir.glob("run_*.json"))
        if not result_files:
            raise FileNotFoundError(f"No results found for {instance_name}")

        with open(output_file, "w", newline="") as f:
            writer = None
            for result_file in result_files:
                data = self.load_result(str(result_file))
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=data.keys())
                    writer.writeheader()
                writer.writerow(data)

        return str(output_file)
