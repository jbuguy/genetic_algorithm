import random

def _check_route_feasibility(solution: list[int], route_start: int,
                              route_end: int, instance) -> bool:
    """Verify capacity and time-window feasibility for one route segment."""
    load = 0
    time = 0.0
    prev = 0  # depot
    for idx in range(route_start, route_end):
        cust = solution[idx]
        if cust == 0:
            continue
        cust_obj = instance.customer_map[cust]
        load += cust_obj.demand
        if load > instance.capacity:
            return False
        arrival = time + instance.distances[prev][cust]
        if arrival > cust_obj.dueDate:
            return False
        time = max(arrival, cust_obj.readyTime) + cust_obj.serviceTime
        prev = cust
    return True

def _extract_route_spans(solution: list[int]) -> list[tuple[int, int]]:
    """Return (start, end) index spans of each route (excluding depot markers)."""
    routes = []
    start = 0
    for i, val in enumerate(solution):
        if val == 0 and i > 0:
            if start < i:
                routes.append((start, i))
            start = i + 1
    return routes


def orOpt(solution: list[int], mutationRate: float, instance) -> list[int]:
    """
    OR-OPT: extract a contiguous segment of k in {1,2,3} customers from a
    randomly chosen route and reinsert it at a different position in the
    same route.
    """
    if random.random() > mutationRate:
        return solution.copy()

    routes = _extract_route_spans(solution)
    if not routes:
        return solution.copy()

    r_start, r_end = random.choice(routes)
    route_len = r_end - r_start

    # Choose segment length k in {1, 2, 3}
    max_k = min(3, route_len - 1)   # need at least one customer left
    if max_k < 1:
        return solution.copy()
    k = random.randint(1, max_k)

    # Pick segment position
    seg_start = random.randint(r_start, r_end - k)
    segment   = solution[seg_start : seg_start + k]

    # Remove segment from solution
    mutated   = solution[:seg_start] + solution[seg_start + k:]

    # Compute new valid insertion range inside the same route
    new_r_end  = r_end - k
    valid_positions = [p for p in range(r_start, new_r_end + 1)
                       if p != seg_start]
    if not valid_positions:
        return solution.copy()

    insert_pos = random.choice(valid_positions)
    mutated    = mutated[:insert_pos] + segment + mutated[insert_pos:]
    return mutated


def twoOpt(solution: list[int], mutationRate: float, instance) -> list[int]:
    """
    2-OPT: reverse a sub-segment [i, j] within one randomly chosen route.
    The swap is accepted only if the resulting route remains feasible
    (capacity + time windows).
    """
    if random.random() > mutationRate:
        return solution.copy()

    routes = _extract_route_spans(solution)
    if not routes:
        return solution.copy()

    route_start, route_end = random.choice(routes)
    if route_end - route_start < 3:
        return solution.copy()

    i = random.randint(route_start, route_end - 2)
    j = random.randint(i + 1,       route_end - 1)

    candidate = solution.copy()
    candidate[i : j + 1] = reversed(candidate[i : j + 1])

    # Accept only if feasible
    if _check_route_feasibility(candidate, route_start, route_end, instance):
        return candidate
    return solution.copy()


def mutate_scramble(solution: list[int], mutation_rate: float = 0.1,
                    instance=None) -> list[int]:
    """
    Scramble Mutation: randomly shuffle a sub-segment within one route.
    The segment is chosen entirely inside a single route to avoid breaking
    the depot structure.
    """
    if random.random() >= mutation_rate:
        return solution

    routes = _extract_route_spans(solution)
    if not routes:
        return solution

    r_start, r_end = random.choice(routes)
    if r_end - r_start < 2:
        return solution

    i, j = sorted(random.sample(range(r_start, r_end), 2))
    subset = solution[i:j]
    random.shuffle(subset)
    result      = solution.copy()
    result[i:j] = subset
    return result


def mutate_insert(solution: list[int], mutationRate: float,
                  instance) -> list[int]:
    """
    OR-OPT k=1: pick one customer inside a randomly chosen route and
    reinsert it at a different position within the same route.
    """
    if random.random() > mutationRate:
        return solution.copy()

    routes = _extract_route_spans(solution)
    if not routes:
        return solution.copy()

    r_start, r_end = random.choice(routes)
    if r_end - r_start < 2:
        return solution.copy()

    idx = random.randint(r_start, r_end - 1)
    new_pos = random.randint(r_start, r_end - 1)
    while new_pos == idx:
        new_pos = random.randint(r_start, r_end - 1)

    mutated  = solution.copy()
    customer = mutated.pop(idx)
    if new_pos > idx:
        new_pos -= 1
    mutated.insert(new_pos, customer)
    return mutated

def mutate_route_rebuild(solution: list[int], mutationRate: float,
                         instance) -> list[int]:
    """
    Route-Rebuild Mutation: keep the largest routes, dissolve the smallest
    ones, and greedily reinsert their clients into the surviving routes.

    Steps:
      1. Extract all routes and sort by length (descending).
      2. Keep the top ceil(m/2) routes unchanged (the 'survivors').
      3. Collect all clients from the dissolved routes as 'homeless'.
      4. For each homeless client, find the cheapest feasible insertion
         position among the survivor routes.
      5. If no feasible insertion exists, open a new singleton route.
    """
    if random.random() > mutationRate:
        return solution.copy()

    routes = _extract_route_spans(solution)
    if len(routes) < 2:
        return solution.copy()

    # Build actual route lists (customer sequences, no depots)
    route_lists = [solution[s:e] for s, e in routes]

    # Sort by length descending; keep the largest half
    route_lists.sort(key=len, reverse=True)
    n_keep = math.ceil(len(route_lists) / 2)
    survivors  = [r[:] for r in route_lists[:n_keep]]
    dissolved  = route_lists[n_keep:]

    # Collect homeless clients (preserve order of appearance)
    homeless = [cust for route in dissolved for cust in route]

    # Greedy cheapest feasible insertion
    for cust in homeless:
        best_route_idx = None
        best_pos       = None
        best_delta     = float('inf')

        for r_idx, route in enumerate(survivors):
            for pos in range(len(route) + 1):
                # Build temporary route with cust inserted at pos
                temp = route[:pos] + [cust] + route[pos:]

                # Feasibility check (capacity + time windows)
                load = 0
                time = 0.0
                prev = 0
                feasible = True
                for c in temp:
                    cust_obj = instance.customer_map[c]
                    load += cust_obj.demand
                    if load > instance.capacity:
                        feasible = False
                        break
                    arrival = time + instance.distances[prev][c]
                    if arrival > cust_obj.dueDate:
                        feasible = False
                        break
                    time = max(arrival, cust_obj.readyTime) + cust_obj.serviceTime
                    prev = c

                if not feasible:
                    continue

                # Distance increase (cheapest insertion cost)
                prev_c = route[pos - 1] if pos > 0       else 0
                next_c = route[pos]     if pos < len(route) else 0
                if pos == 0 or pos == len(route):
                    old_d = 0
                else:
                    old_d = instance.distances[prev_c][next_c]
                new_d  = (instance.distances[prev_c][cust] +
                          instance.distances[cust][next_c])
                delta  = new_d - old_d

                if delta < best_delta:
                    best_delta     = delta
                    best_route_idx = r_idx
                    best_pos       = pos

        if best_route_idx is not None:
            survivors[best_route_idx].insert(best_pos, cust)
        else:
            survivors.append([cust])   # open a new singleton route

    # Rebuild chromosome with depot separators
    result = []
    for route in survivors:
        result.extend(route)
        result.append(0)
    return result


import math   # add at top of file
fn = [twoOpt, orOpt, mutate_scramble, mutate_route_rebuild]
