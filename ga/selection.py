import random



def selection_truncation(
   scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]: 
    sorted_population= sorted(scored_population,key=lambda x:x[1])
    survivors_count = max(1, len(sorted_population) // 2)
    selected = random.sample(sorted_population[:survivors_count], 1)
    return selected[0]

def rouletteSelection(
    scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]:
    # Invert fitness for minimization
    epsilon = 1e-10
    weights = [1.0 / (fitness + epsilon) for _, fitness in scored_population]
    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]
    
    # Roulette wheel selection
    r = random.random()
    cumulative = 0.0
    for i, prob in enumerate(probabilities):
        cumulative += prob
        if r <= cumulative:
            # Return a copy of the individual
            return scored_population[i][0][:], scored_population[i][1]
    return scored_population[-1][0][:], scored_population[-1][1]

def selection_sus(
    scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]:
    epsilon = 1e-10
    weights = [1.0 / (fitness + epsilon) for _, fitness in scored_population]
    total_weight = sum(weights)
    n = len(scored_population)
    distance = total_weight / n
    start = random.uniform(0, distance)
    pointers = [start + i * distance for i in range(n)]
    
    # Select one individual (SUS normally selects n, but here we just pick one)
    r = random.choice(pointers)
    cumulative = 0.0
    for i, w in enumerate(weights):
        cumulative += w
        if r <= cumulative:
            return scored_population[i][0][:], scored_population[i][1]
    return scored_population[-1][0][:], scored_population[-1][1]

def tournamentSelection(
    scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]:
    k = min(k, len(scored_population))

    indices = random.sample(range(len(scored_population)), k)
    
    best_id = min(indices, key=lambda i: scored_population[i][1])
    individual, fitness = scored_population[best_id]
    return individual[:], fitness
fn=[rouletteSelection,selection_truncation,tournamentSelection]
