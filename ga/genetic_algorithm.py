import time
from typing import Any, Callable

from ga.selection import tournamentSelection
from operators.crossover import edgeAssemblyCrossover
from operators.mutation import twoOpt
from vrptw.generateInit import randomGenerator
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
            'selection_calls': 0,
            'crossover_calls': 0,
            'mutation_calls': 0,
            'selection_improvements': 0,
            'crossover_improvements': 0,
            'mutation_improvements': 0,
            'infeasible_solutions': 0,
            'operator_timings': {
                'selection': [],
                'crossover': [],
                'mutation': []
            }
        }


class GeneticAlgorithm:
    def __init__(
        self,
        instance: Instance,
        fnFitness: Callable[[list[int], Instance], float],
        fnSelection: Callable[
            [list[tuple[list[int], float]]], list[int]
        ] = tournamentSelection,
        fnCrossover: Callable[
            [list[int], list[int], Instance], list[int]
        ] = edgeAssemblyCrossover,
        fnMutation: Callable[[list[int], float, Instance], list[int]] = twoOpt,
        fnInitPopulation: Callable[[Instance], list[int]] = randomGenerator,
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

        for generation in range(self.generations):
            scored = self.evaluatePopulation(population)

            scored.sort(key=lambda x: x[1])

            _, best_fit = scored[0]

            avg_fit = sum(f for _, f in scored) / len(scored)

            result.bestRecord.append(best_fit)
            result.avgRecord.append(avg_fit)

            new_population = []

            if scored:
                elite = scored[0][0][:]  
                new_population.append(elite)

            while len(new_population) < self.PopulationSize:
                sel_start = time.time()
                p1 = self.fnSelection(scored)
                p2 = self.fnSelection(scored)
                sel_time = time.time() - sel_start
                result.operatorStats['selection_calls'] += 2
                result.operatorStats['operator_timings']['selection'].append(sel_time)

                cross_start = time.time()
                child = self.fnCrossover(p1, p2, self.instance)
                cross_time = time.time() - cross_start
                result.operatorStats['crossover_calls'] += 1
                result.operatorStats['operator_timings']['crossover'].append(cross_time)

                child_fitness = self.fnFitness(child, self.instance)
                parent_avg_fitness = (self.fnFitness(p1, self.instance) + self.fnFitness(p2, self.instance)) / 2
                if child_fitness < parent_avg_fitness and child_fitness != float('inf'):
                    result.operatorStats['crossover_improvements'] += 1

                mut_start = time.time()
                child = self.fnMutation(child, self.mutationRate, self.instance)
                mut_time = time.time() - mut_start
                result.operatorStats['mutation_calls'] += 1
                result.operatorStats['operator_timings']['mutation'].append(mut_time)

                mutated_fitness = self.fnFitness(child, self.instance)
                if mutated_fitness < child_fitness and mutated_fitness != float('inf'):
                    result.operatorStats['mutation_improvements'] += 1
                elif mutated_fitness == float('inf'):
                    result.operatorStats['infeasible_solutions'] += 1

                new_population.append(child)

            population = new_population

        best_solution, best_fitness = min(
            self.evaluatePopulation(population), key=lambda x: x[1]
        )

        result.bestSolution = best_solution
        result.bestFitness = best_fitness
        result.generations = self.generations
        result.runtime = time.time() - start

        return result
