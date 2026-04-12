import random
from typing import List

# ------------------------------------------------------------
# Existing crossovers (PMX, OX, CX, Edge Assembly)
# ------------------------------------------------------------

def PMXCrossOver(parent1: List[int], parent2: List[int], instance) -> List[int]:
    child = []
    length = min(len(parent1), len(parent2))
    point1 = random.randint(0, length - 1)
    point2 = random.randint(point1, length - 1)
    mapping = {}
    for i in range(point1, point2):
        mapping[parent1[i]] = parent2[i]
        mapping[parent2[i]] = parent1[i]
    for elm in parent1:
        if mapping.get(elm) is None:
            child.append(elm)
        else:
            child.append(mapping.get(elm))
    return child


def crossover_ox(p1, p2, instance):
    # 1. Extract customer sequences (same as before)
    cust1 = [c for c in p1 if c != 0]
    cust2 = [c for c in p2 if c != 0]
    if set(cust1) != set(cust2) or len(cust1) != len(cust2):
        return p1.copy()

    size = len(cust1)
    start, end = sorted(random.sample(range(size), 2))
    child_seq = [None] * size
    child_seq[start:end] = cust1[start:end]
    used = set(child_seq[start:end])
    p2_idx = end
    c_idx = end
    while None in child_seq:
        if p2_idx >= size: p2_idx = 0
        if c_idx >= size: c_idx = 0
        while child_seq[c_idx] is not None:
            c_idx += 1
            if c_idx >= size: c_idx = 0
        while cust2[p2_idx] in used:
            p2_idx += 1
            if p2_idx >= size: p2_idx = 0
        child_seq[c_idx] = cust2[p2_idx]
        used.add(cust2[p2_idx])
        p2_idx += 1
        c_idx += 1

    # 2. Build routes from the sequence using a greedy split (O(n²))
    routes = []
    i = 0
    while i < size:
        # Start a new route
        route = [child_seq[i]]
        load = instance.customer_map[child_seq[i]].demand
        time = 0.0
        prev = 0
        # Compute arrival time at first customer
        travel = instance.distances[prev][child_seq[i]]
        arrival = time + travel
        cust_obj = instance.customer_map[child_seq[i]]
        if arrival > cust_obj.dueDate:
            # Should not happen, but fallback: put alone
            routes.append(route)
            i += 1
            continue
        time = max(arrival, cust_obj.readyTime) + cust_obj.serviceTime
        prev = child_seq[i]
        j = i + 1
        # Try to add more customers to this route
        while j < size:
            next_cust = child_seq[j]
            travel = instance.distances[prev][next_cust]
            arrival = time + travel
            cust_obj_next = instance.customer_map[next_cust]
            if arrival <= cust_obj_next.dueDate and load + cust_obj_next.demand <= instance.capacity:
                # feasible, add it
                route.append(next_cust)
                load += cust_obj_next.demand
                time = max(arrival, cust_obj_next.readyTime) + cust_obj_next.serviceTime
                prev = next_cust
                j += 1
            else:
                break
        routes.append(route)
        i = j

    # 3. Rebuild solution with depot separators
    child = []
    for r in routes:
        child.extend(r)
        child.append(0)
    return child


def _feasible_insertion(route, pos, cust, instance):
    """Check capacity and time windows when inserting cust at position pos."""
    temp = route[:pos] + [cust] + route[pos:]

    # Capacity check
    load = 0
    for c in temp:
        load += instance.customer_map[c].demand
        if load > instance.capacity:
            return False

    # Time window check
    time = 0.0
    prev = 0
    for c in temp:
        travel = instance.distances[prev][c]
        arrival = time + travel
        cust_obj = instance.customer_map[c]
        if arrival > cust_obj.dueDate:
            return False
        time = max(arrival, cust_obj.readyTime) + cust_obj.serviceTime
        prev = c
    return True


def crossover_cx(p1, p2, instance):
    size = len(p1)
    child = [-1] * size
    indices = list(range(size))
    while -1 in child:
        start = indices[0]
        val = p1[start]
        while True:
            child[start] = p1[start]
            val2 = p2[start]
            start = p1.index(val2)
            if val2 == val:
                break
        for i in range(size):
            if child[i] == -1:
                child[i] = p2[i]
        break
    return child


def edgeAssemblyCrossover(parent1: List[int], parent2: List[int], instance) -> List[int]:
    if len(parent1) != len(parent2):
        return parent1.copy()

    routes1 = _extract_routes(parent1)
    routes2 = _extract_routes(parent2)

    if not routes1 or not routes2:
        return parent1.copy()

    route1 = random.choice(routes1)
    route2 = random.choice(routes2)

    if len(route1) < 2 or len(route2) < 2:
        return parent1.copy()

    min_len = min(len(route1), len(route2))
    if min_len < 2:
        return parent1.copy()

    start = random.randint(0, min_len - 2)
    end = random.randint(start + 1, min_len)

    child_route = route1[:start] + route2[start:end] + route1[end:]

    seen = set()
    unique_route = []
    for customer in child_route:
        if customer not in seen:
            seen.add(customer)
            unique_route.append(customer)

    child_solution = _replace_route(parent1, route1, unique_route)
    return child_solution


def _extract_routes(solution: List[int]) -> List[List[int]]:
    routes = []
    current_route = []
    for customer in solution:
        if customer == 0:
            if current_route:
                routes.append(current_route)
                current_route = []
        else:
            current_route.append(customer)
    if current_route:
        routes.append(current_route)
    return routes


def _replace_route(solution: List[int], old_route: List[int], new_route: List[int]) -> List[int]:
    routes = _extract_routes(solution)
    for i, route in enumerate(routes):
        if route == old_route:
            routes[i] = new_route
            break
    result = []
    for route in routes:
        result.extend(route)
        result.append(0)
    return result


# ------------------------------------------------------------
# New: Route‑Based Crossover (RBX) for VRPTW
# ------------------------------------------------------------

def route_based_crossover(parent1: List[int], parent2: List[int], instance) -> List[int]:
    """
    Route‑Based Crossover (RBX) for VRPTW.
    Operates at the route level, preserving complete feasible routes.
    """
    # Extract routes from both parents
    routes1 = _extract_routes(parent1)
    routes2 = _extract_routes(parent2)

    if not routes1 or not routes2:
        return parent1.copy()

    # Choose a random subset of routes from parent1 (e.g., half of them)
    num_keep = max(1, len(routes1) // 2)
    keep_indices = set(random.sample(range(len(routes1)), num_keep))
    kept_routes = [routes1[i] for i in keep_indices]

    # Collect customers already assigned
    assigned = set()
    for route in kept_routes:
        assigned.update(route)

    # Collect remaining customers from parent2 (not already assigned)
    remaining = []
    for route in routes2:
        for cust in route:
            if cust not in assigned:
                remaining.append(cust)

    # Insert remaining customers using cheapest feasible insertion
    child_routes = [route[:] for route in kept_routes]

    for cust in remaining:
        best_route_idx = None
        best_pos = None
        best_cost_inc = float('inf')

        for r_idx, route in enumerate(child_routes):
            # Try all insertion positions (including at ends)
            for pos in range(len(route) + 1):
                if _feasible_insertion(route, pos, cust, instance):
                    # Compute distance increase
                    prev = route[pos - 1] if pos > 0 else 0
                    nxt = route[pos] if pos < len(route) else 0
                    old_dist = instance.distances[prev][nxt] if pos not in (0, len(route)) else 0
                    new_dist = instance.distances[prev][cust] + instance.distances[cust][nxt]
                    increase = new_dist - old_dist
                    if increase < best_cost_inc:
                        best_cost_inc = increase
                        best_route_idx = r_idx
                        best_pos = pos

        if best_route_idx is not None:
            child_routes[best_route_idx].insert(best_pos, cust)
        else:
            # Create a new route if no feasible insertion found
            child_routes.append([cust])

    # Rebuild the solution list with depot separators
    child = []
    for route in child_routes:
        child.extend(route)
        child.append(0)
    return child



# ------------------------------------------------------------
# List of crossovers for easy selection (optional)
# ------------------------------------------------------------
fn = [edgeAssemblyCrossover, crossover_ox, PMXCrossOver, route_based_crossover]