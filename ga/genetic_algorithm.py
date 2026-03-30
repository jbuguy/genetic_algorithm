import time
from typing import Any, Callable

from ga.selection import tournamentSelection
from operators.crossover import edgeAssemblyCrossover
from operators.mutation import twoOpt
from vrptw.generateInit import random_generator
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
                child_fitness = self.fnFitness(child, self.instance)
                result.operatorStats["crossover_calls"] += 1
                if child_fitness < (p1_fit + p2_fit) / 2:
                    result.operatorStats["crossover_improvements"] += 1

                # Mutation
                mutated = self.fnMutation(child, self.mutationRate, self.instance)
                mutated_fitness = self.fnFitness(mutated, self.instance)
                result.operatorStats["mutation_calls"] += 1

                if mutated_fitness < child_fitness:
                    result.operatorStats["mutation_improvements"] += 1
                    child, child_fitness = mutated, mutated_fitness
                elif mutated_fitness == float("inf"):
                    result.operatorStats["infeasible_solutions"] += 1

                # If the new child is infeasible, fallback to the best of parents (still ignoring numberVehicle)
                if child_fitness == float("inf"):
                    if p1_fit != float("inf") or p2_fit != float("inf"):
                        if p1_fit <= p2_fit:
                            child, child_fitness = p1[:], p1_fit
                        else:
                            child, child_fitness = p2[:], p2_fit
                    # else keep infeasible, no feasible parent available

                new_population.append(child)

            # Re-evaluate only new individuals (elites already scored)
            scored = [
                (ind, self.fnFitness(ind, self.instance))
                for ind in new_population[elite_count:]
            ] + [(ind, fit) for ind, fit in scored[:elite_count]]

        scored.sort(key=lambda x: x[1])
        result.bestSolution, result.bestFitness = scored[0]
        result.generations = self.generations
        result.runtime = time.time() - start
        return result
