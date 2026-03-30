import random


def tournamentSelection(scored_population: list[tuple[list[int], float]], k=5) -> list[int]:
    population = [ind for ind, _ in scored_population]
    fitness = [fit for _, fit in scored_population]
    indices = random.sample(range(len(population)), k)
    best_id = min(indices, key=lambda i: fitness[i])
    return population[best_id][:]
