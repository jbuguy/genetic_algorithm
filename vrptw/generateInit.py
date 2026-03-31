import random
from typing import Callable, List, Optional

from vrptw.customer import Customer
from vrptw.instance import Instance


def remove_consecutive_zeros(solution: List[int]) -> List[int]:
    if not solution:
        return solution

    cleaned = [solution[0]]
    for i in range(1, len(solution)):
        if solution[i] != 0 or cleaned[-1] != 0:
            cleaned.append(solution[i])

    return cleaned


def remove_trailing_zeros(solution: List[int]) -> List[int]:
    if not solution:
        return solution

    cleaned = solution.copy()
    while cleaned and cleaned[-1] == 0:
        cleaned.pop()

    return cleaned


def build_customer_map(instance: Instance) -> dict[int, Customer]:
    return {c.num: c for c in instance.customers}


def close_route(solution: List[int]) -> None:
    if not solution or solution[-1] != 0:
        solution.append(0)


def try_insert(
    current: int,
    current_time: float,
    current_load: int,
    customer: Customer,
    instance: Instance,
) -> Optional[tuple[float, int]]:

    travel = instance.distances[current][customer.num]
    arrival = current_time + travel
    service_start = max(arrival, customer.readyTime)

    if service_start > customer.dueDate:
        return None
    if current_load + customer.demand > instance.capacity:
        return None

    return service_start + customer.serviceTime, current_load + customer.demand


def random_generator(instance: Instance) -> List[int]:

    unvisited = {c.num for c in instance.customers[1:]}
    solution: List[int] = []
    route: List[int] = [0]

    current, time, load = 0, 0.0, 0

    while unvisited:
        feasible = [
            (cid, new_time, new_load)
            for cid in unvisited
            if (
                result := try_insert(
                    current, time, load, instance.customer_map[cid], instance
                )
            )
            for new_time, new_load in [result]
        ]

        if not feasible:
            route.append(0)
            solution.extend(route)
            route, current, time, load = [0], 0, 0.0, 0
            continue

        cid, time, load = random.choice(feasible)
        route.append(cid)
        unvisited.remove(cid)
        current = cid

    route.append(0)
    solution.extend(route)
    solution = remove_consecutive_zeros(solution)
    return remove_trailing_zeros(solution)


def solomon_generator(instance: Instance, randomness: float = 0.3) -> List[int]:
    customer_map = build_customer_map(instance)
    unassigned = {c.num for c in instance.customers[1:]}

    if not unassigned:
        return [0]

    solution: List[int] = [0]
    current, time, load = 0, 0.0, 0

    while unassigned:
        candidates = []
        for cid in unassigned:
            customer = customer_map[cid]

            if load + customer.demand > instance.capacity:
                continue

            travel = instance.distances[current][cid]
            arrival = time + travel

            if arrival > customer.dueDate:
                continue

            service_start = max(arrival, customer.readyTime)
            wait = max(0.0, customer.readyTime - arrival)
            score = travel + wait

            candidates.append(
                (
                    score,
                    cid,
                    service_start + customer.serviceTime,
                    load + customer.demand,
                )
            )

        if not candidates:
            close_route(solution)
            current, time, load = 0, 0.0, 0

            forced_id = min(unassigned, key=lambda cid: customer_map[cid].dueDate)
            customer = customer_map[forced_id]
            solution.append(forced_id)
            unassigned.remove(forced_id)

            travel = instance.distances[0][forced_id]
            time = max(travel, customer.readyTime) + customer.serviceTime
            load = customer.demand
            current = forced_id
            continue

        candidates.sort(key=lambda x: x[0])
        top_n = max(1, int(len(candidates) * (1 - randomness)) + 1)
        _, best_id, time, load = random.choice(candidates[:top_n])

        solution.append(best_id)
        unassigned.remove(best_id)
        current = best_id

    close_route(solution)
    solution = remove_consecutive_zeros(solution)
    return remove_trailing_zeros(solution)


def cluster_first_route_second(instance: Instance) -> List[int]:
    """Cluster-First, Route-Second initialization."""
    unvisited = {c.num for c in instance.customers[1:]}
    clusters: List[List[int]] = []

    # Step 1: Clustering based on nearest to cluster centroid
    while unvisited:
        seed = unvisited.pop()
        cluster = [seed]
        load = instance.customer_map[seed].demand

        while True:
            if not unvisited:
                break

            # Compute current cluster centroid
            x_mean = sum(instance.customer_map[cid].x for cid in cluster) / len(cluster)
            y_mean = sum(instance.customer_map[cid].y for cid in cluster) / len(cluster)

            # Find nearest feasible customer
            feasible_neighbors = []
            for cid in unvisited:
                cust = instance.customer_map[cid]
                distance = ((cust.x - x_mean) ** 2 + (cust.y - y_mean) ** 2) ** 0.5
                if load + cust.demand <= instance.capacity:
                    feasible_neighbors.append((distance, cid))

            if not feasible_neighbors:
                break

            _, next_cid = min(feasible_neighbors, key=lambda x: x[0])
            cluster.append(next_cid)
            load += instance.customer_map[next_cid].demand
            unvisited.remove(next_cid)

        clusters.append(cluster)

    # Step 2: Build routes within each cluster using Solomon insertion
    solution: List[int] = []
    for cluster in clusters:
        route = [0]
        current, time, load = 0, 0.0, 0
        unassigned = set(cluster)

        while unassigned:
            # Try feasible insertions
            candidates = []
            for cid in unassigned:
                customer = instance.customer_map[cid]
                res = try_insert(current, time, load, customer, instance)
                if res:
                    new_time, new_load = res
                    travel = instance.distances[current][cid]
                    wait = max(0.0, customer.readyTime - (time + travel))
                    score = travel + wait
                    candidates.append((score, cid, new_time, new_load))

            if not candidates:
                route.append(0)
                solution.extend(route)
                route = [0]
                current, time, load = 0, 0.0, 0
                continue

            candidates.sort(key=lambda x: x[0])
            _, best_cid, time, load = candidates[0]
            route.append(best_cid)
            unassigned.remove(best_cid)
            current = best_cid

        route.append(0)
        solution.extend(route)

    solution = remove_consecutive_zeros(solution)
    return remove_trailing_zeros(solution)


def savings_heuristic(instance: Instance) -> List[int]:
    customer_map = build_customer_map(instance)
    routes = {c.num: [0, c.num, 0] for c in instance.customers[1:]}

    # Step 2: Compute savings
    savings = []
    for i in customer_map:
        if i == 0:
            continue
        for j in customer_map:
            if j == 0 or i >= j:
                continue
            S = (
                instance.distances[0][i]
                + instance.distances[0][j]
                - instance.distances[i][j]
            )
            savings.append((S, i, j))
    savings.sort(reverse=True)

    # Step 3: Merge routes based on savings
    for S, i, j in savings:
        route_i = next((r for r in routes.values() if r[1:-1] and i in r[1:-1]), None)
        route_j = next((r for r in routes.values() if r[1:-1] and j in r[1:-1]), None)

        if not route_i or not route_j or route_i == route_j:
            continue

        # Check if i is at the end of route_i and j at start of route_j
        if route_i[-2] == i and route_j[1] == j:
            combined = route_i[:-1] + route_j[1:]
            # Check capacity and time feasibility
            load = sum(customer_map[cid].demand for cid in combined[1:-1])
            if load > instance.capacity:
                continue

            # Check time windows
            feasible = True
            time = 0.0
            for k in range(1, len(combined)):
                prev = combined[k - 1]
                curr = combined[k]
                travel = instance.distances[prev][curr]
                arrival = time + travel
                cust = customer_map[curr]
                start_service = max(arrival, cust.readyTime)
                if start_service > cust.dueDate:
                    feasible = False
                    break
                time = start_service + cust.serviceTime

            if feasible:
                # Merge routes
                route_i[:] = combined
                del routes[next(key for key, val in routes.items() if val == route_j)]

    # Flatten routes
    solution = []
    for r in routes.values():
        solution.extend(r)

    solution = remove_consecutive_zeros(solution)
    return remove_trailing_zeros(solution)


def make_mixed_initializer(
    randomness: float = 0.3, weights: dict = None
) -> Callable[[Instance], List[int]]:
    """
    Returns an initializer function for GA.

    Args:
        randomness: controls stochasticity for solomon/random
        weights: dict of probabilities for each initializer
                 keys: "random", "solomon", "cluster", "savings"

    Returns:
        A function that takes an instance and returns a single individual.
    """
    if weights is None:
        weights = {"random": 0.25, "solomon": 0.25, "cluster": 0.25, "savings": 0.25}

    initers = list(weights.keys())
    probs = [weights[k] for k in initers]
    total = sum(probs)
    probs = [p / total for p in probs]

    def initializer(instance: Instance) -> List[int]:
        # Randomly choose which heuristic to use
        chosen = random.choices(initers, probs)[0]

        if chosen == "random":
            return random_generator(instance)
        elif chosen == "solomon":
            return solomon_generator(instance, randomness=randomness)
        elif chosen == "cluster":
            return cluster_first_route_second(instance)
        elif chosen == "savings":
            return savings_heuristic(instance)
        else:
            raise ValueError(f"Unknown initializer {chosen}")

    return initializer
