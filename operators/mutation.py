import random


def twoOpt(solution: list[int], mutationRate: float, instance) -> list[int]:

    if random.random() > mutationRate:
        return solution.copy()
    
    mutated_solution = solution.copy()
    
    routes = []
    start = 0
    for i in range(len(mutated_solution)):
        if mutated_solution[i] == 0 and i > 0:
            if start < i:
                routes.append((start, i))
            start = i + 1
    
    if not routes:
        return mutated_solution
    
    route_start, route_end = random.choice(routes)
    
    route_length = route_end - route_start
    
    if route_length < 3:
        return mutated_solution
    
    i = random.randint(route_start, route_end - 2)
    j = random.randint(i + 1, route_end - 1)
    
    mutated_solution[i:j + 1] = reversed(mutated_solution[i:j + 1])
    
    return mutated_solution

