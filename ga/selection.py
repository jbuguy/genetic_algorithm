import random


def tournamentSelection(
    scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]:
    k = min(k, len(scored_population))

    indices = random.sample(range(len(scored_population)), k)
    
    best_id = min(indices, key=lambda i: scored_population[i][1])
    individual, fitness = scored_population[best_id]
    return individual[:], fitness
