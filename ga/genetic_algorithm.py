import time
from typing import Any, Callable

from ga.selection import tournamentSelection
from operators.crossover import edgeAssemblyCrossover
from operators.mutation import twoOpt
from vrptw.generateInit import random_generator, remove_trailing_zeros
from vrptw.instance import Instance


class GAResult:
    def __init__(self) -> None:
        self.bestSolution: list[int] | None = None
        self.bestFitness: float | None = None

        self.bestRecord: list[float] = []
        self.avgRecord: list[float] = []

        self.generations: int = 0
        self.runtime: float = 0.0

        self.operatorStats: dict[str, Any] = {
            "selection_calls": 0,
            "crossover_calls": 0,
            "mutation_calls": 0,
            "selection_improvements": 0,
            "crossover_improvements": 0,
            "mutation_improvements": 0,
            "infeasible_solutions": 0,
            "operator_timings": {"selection": [], "crossover": [], "mutation": []},
        }


class GeneticAlgorithm:
    def __init__(
        self,
        instance: Instance,
        fnFitness: Callable[[list[int], Instance], float],
        fnSelection: Callable[
            [list[tuple[list[int], float]]], tuple[list[int], float]
        ] = tournamentSelection,
        fnCrossover: Callable[
            [list[int], list[int], Instance], list[int]
        ] = edgeAssemblyCrossover,
        fnMutation: Callable[[list[int], float, Instance], list[int]] = twoOpt,
        fnInitPopulation: Callable[[Instance], list[int]] = random_generator,
        populationSize: int = 100,
        generations: int = 200,
        mutationRate: float = 0.2,
    ) -> None:

        self.instance = instance
        self.fnFitness = fnFitness
        self.fnSelection = fnSelection
        self.fnCrossover = fnCrossover
        self.fnMutation = fnMutation
        self.fnInitPopulation = fnInitPopulation

        self.PopulationSize = populationSize
        self.generations = generations
        self.mutationRate = mutationRate

    def initPopulation(self) -> list[list[int]]:
        return [
            self.fnInitPopulation(self.instance) for _ in range(self.PopulationSize)
        ]

    def evaluatePopulation(
        self, population: list[list[int]]
    ) -> list[tuple[list[int], float]]:

        return [(ind, self.fnFitness(ind, self.instance)) for ind in population]

    def _buildRouteArrays(self, route: list[int]) -> tuple[list[float], list[float]]:
        """Precompute cumulative time and load at each position in the route."""
        time_at = [0.0] * len(route)
        load_at = [0.0] * len(route)

        for i in range(1, len(route)):
            node = route[i]

            if node == 0:  # depot reset
                time_at[i] = 0.0
                load_at[i] = 0.0
                continue

            customer = self.instance.customer_map[node]
            travel_time = self.instance.distances[route[i - 1]][node]
            arrival = time_at[i - 1] + travel_time

            time_at[i] = max(arrival, customer.readyTime) + customer.serviceTime
            load_at[i] = load_at[i - 1] + customer.demand

        return time_at, load_at

    def _canInsert(
        self,
        route: list[int],
        pos: int,
        customer_id: int,
        time_at: list[float],
        load_at: list[float],
    ) -> bool:
        """
        O(1) feasibility check for inserting customer_id at position pos.
        Only inspects the immediate neighbourhood — no full route scan.
        """
        customer = self.instance.customer_map[customer_id]
        prev_node = route[pos - 1]
        next_node = route[pos]

        # --- Capacity: load up to prev + new demand must not exceed capacity ---
        if load_at[pos - 1] + customer.demand > self.instance.capacity:
            return False

        # --- Time window: can we reach the new customer in time? ---
        travel_to_new = self.instance.distances[prev_node][customer_id]
        arrival_at_new = time_at[pos - 1] + travel_to_new

        if arrival_at_new > customer.dueDate:
            return False

        # --- Propagation: does the delay push the next node past its due date? ---
        depart_new = max(arrival_at_new, customer.readyTime) + customer.serviceTime
        travel_to_next = self.instance.distances[customer_id][next_node]
        arrival_at_next = depart_new + travel_to_next

        if next_node != 0:  # depot has no time window
            next_customer = self.instance.customer_map[next_node]
            if arrival_at_next > next_customer.dueDate:
                return False

        return True

    def repairSolution(self, solution: list[int]) -> list[int]:
        repaired = [0]
        current_time = 0
        current_load = 0
        skipped = []

        for i in range(1, len(solution)):
            customer_id = solution[i]

            if customer_id == 0:
                repaired.append(0)
                current_time = 0
                current_load = 0
                continue

            customer = self.instance.customer_map[customer_id]
            travel_time = self.instance.distances[repaired[-1]][customer_id]
            arrival_time = current_time + travel_time

            if (
                current_load + customer.demand <= self.instance.capacity
                and arrival_time <= customer.dueDate
            ):
                start_service = max(arrival_time, customer.readyTime)
                repaired.append(customer_id)
                current_time = start_service + customer.serviceTime
                current_load += customer.demand
            else:
                skipped.append(customer_id)

        repaired.append(0)

        for customer_id in skipped:
            time_at, load_at = self._buildRouteArrays(repaired)

            best_pos = None
            best_cost = float("inf")

            for pos in range(1, len(repaired)):
                if self._canInsert(repaired, pos, customer_id, time_at, load_at):
                    prev_node = repaired[pos - 1]
                    next_node = repaired[pos]
                    cost = (
                        self.instance.distances[prev_node][customer_id]
                        + self.instance.distances[customer_id][next_node]
                        - self.instance.distances[prev_node][next_node]
                    )

                    if cost < best_cost:
                        best_cost = cost
                        best_pos = pos

            if best_pos is not None:
                repaired = repaired[:best_pos] + [customer_id] + repaired[best_pos:]

        return repaired

    def run(self) -> GAResult:
        start = time.time()
        result = GAResult()
        population = self.initPopulation()

        scored = self.evaluatePopulation(population)

        for generation in range(self.generations):
            scored.sort(key=lambda x: x[1])

            best_fit = scored[0][1]
            avg_fit = sum(f for _, f in scored) / len(scored)
            result.bestRecord.append(best_fit)
            result.avgRecord.append(avg_fit)

            elite_count = max(1, self.PopulationSize // 20)  # top 5%
            new_population = [ind[:] for ind, _ in scored[:elite_count]]

            while len(new_population) < self.PopulationSize:
                # Selection — reuse pre-computed fitness
                p1, p1_fit = self.fnSelection(scored)
                p2, p2_fit = self.fnSelection(scored)
                result.operatorStats["selection_calls"] += 2

                # Crossover
                child = self.fnCrossover(p1, p2, self.instance)
                child = self.repairSolution(child)
                child_fitness = self.fnFitness(child, self.instance)
                result.operatorStats["crossover_calls"] += 1
                if child_fitness < (p1_fit + p2_fit) / 2:
                    result.operatorStats["crossover_improvements"] += 1

                # Mutation
                mutated = self.fnMutation(child, self.mutationRate, self.instance)
                mutated = self.repairSolution(mutated)
                mutated_fitness = self.fnFitness(mutated, self.instance)
                result.operatorStats["mutation_calls"] += 1

                if mutated_fitness < child_fitness:
                    result.operatorStats["mutation_improvements"] += 1
                    child, child_fitness = mutated, mutated_fitness
                elif mutated_fitness == float("inf"):
                    result.operatorStats["infeasible_solutions"] += 1

                if child_fitness == float("inf"):
                    if p1_fit != float("inf") or p2_fit != float("inf"):
                        if p1_fit <= p2_fit:
                            child, child_fitness = p1[:], p1_fit
                        else:
                            child, child_fitness = p2[:], p2_fit

                new_population.append(child)

            scored = [
                (ind, self.fnFitness(ind, self.instance))
                for ind in new_population[elite_count:]
            ] + [(ind, fit) for ind, fit in scored[:elite_count]]

        scored.sort(key=lambda x: x[1])
        best_solution, best_fitness = scored[0]
        result.bestSolution = remove_trailing_zeros(best_solution)
        result.bestFitness = best_fitness
        result.generations = self.generations
        result.runtime = time.time() - start
        return result
