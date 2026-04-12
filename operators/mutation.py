import random


def orOpt(solution: list[int], mutationRate: float, instance) -> list[int]:
    length=len(solution)-1
    result=[elm for elm in solution]
    segmentlength=int(length*mutationRate)
    start=random.randint(0,length-segmentlength)
    s=result[start:start+segmentlength]
    result=result[0:start]+result[start+segmentlength::]
    s.reverse()
    result[start:start+segmentlength]=s
    return result

def mutate_scramble(tour, mutation_rate=0.1,instance=None):
    if random.random() < mutation_rate:
        start, end = sorted(random.sample(range(len(tour)), 2))
        subset = tour[start:end]
        random.shuffle(subset)
        tour[start:end] = subset
    return tour

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
def mutate_insert(solution: list[int], mutationRate: float, instance) -> list[int]:
    if random.random() > mutationRate:
        return solution.copy()
    
    # Extract routes
    routes = []
    start = 0
    for i, val in enumerate(solution):
        if val == 0 and i > 0:
            if start < i:
                routes.append((start, i))
            start = i + 1
    if not routes:
        return solution.copy()
    
    r_start, r_end = random.choice(routes)
    route_len = r_end - r_start
    if route_len < 2:
        return solution.copy()
    
    # Pick customer to move
    idx = random.randint(r_start, r_end - 1)
    # Pick new position (cannot be same as original)
    new_pos = random.randint(r_start, r_end - 1)
    while new_pos == idx:
        new_pos = random.randint(r_start, r_end - 1)
    
    mutated = solution.copy()
    customer = mutated.pop(idx)
    # Adjust new_pos if removal shifts indices
    if new_pos > idx:
        new_pos -= 1
    mutated.insert(new_pos, customer)
    return mutated

fn=[twoOpt,orOpt,mutate_scramble,mutate_insert]