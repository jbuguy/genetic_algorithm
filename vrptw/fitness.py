from functools import partial
from typing import Callable
from vrptw.instance import Instance


def calculateFitness(
    solution: list[int],
    instance: Instance,
    alpha: float = 0.5,
    beta: float = 0.4,
    gamma: float = 0.1,
    K_max: int | None = None,
    D_max: float | None = None,
    W_max: float | None = None,
) -> float:
    """
    Normalized multi-objective fitness:
        Z = α·(K / K_max) + β·(D / D_max) + γ·(W / W_max)

    Normalization constants (computed from instance if not provided):
        K_max = number of customers          (worst case: 1 vehicle per customer)
        D_max = sum of all pairwise distances used in a naive nearest-depot tour
        W_max = Σ (dueDate - readyTime)      (upper bound on total wait)
    """
    if not solution or solution[0] != 0:
        return float("inf")

    # --- Resolve normalization constants ---
    n = len(instance.customer_ids)

    if K_max is None:
        K_max = n

    if W_max is None:
        W_max = sum(
            c.dueDate - c.readyTime
            for c in instance.customer_map.values()
        )
        W_max = max(W_max, 1.0)  # guard against zero

    if D_max is None:
        # Fallback: sum of every customer's distance to the depot (×2 round-trip)
        D_max = 2.0 * sum(
            instance.distances[0][cid] for cid in instance.customer_ids
        )
        D_max = max(D_max, 1.0)

    # --- Simulate the routes ---
    total_distance = 0.0
    total_wait = 0.0
    current_time = 0.0
    current_load = 0
    current_location = 0
    visited: set[int] = set()
    num_vehicles = 0

    for node in solution[1:]:
        if node == 0:
            total_distance += instance.distances[current_location][0]
            current_time = 0.0
            current_load = 0
            current_location = 0
            num_vehicles += 1
            continue

        if node in visited:
            return float("inf")

        customer = instance.customer_map.get(node)
        if not customer:
            return float("inf")

        if current_load + customer.demand > instance.capacity:
            return float("inf")

        travel_time = instance.distances[current_location][node]
        arrival_time = current_time + travel_time

        if arrival_time > customer.dueDate:
            return float("inf")

        wait_time = max(0.0, customer.readyTime - arrival_time)
        total_wait += wait_time
        total_distance += travel_time
        current_time = arrival_time + wait_time + customer.serviceTime
        current_load += customer.demand
        current_location = node
        visited.add(node)

    # Final return to depot
    if current_location != 0:
        total_distance += instance.distances[current_location][0]
        num_vehicles += 1

    if visited != instance.customer_ids:
        return float("inf")

    # --- Normalized objective ---
    z = (
        alpha * (num_vehicles / K_max)
        + beta  * (total_distance / D_max)
        + gamma * (total_wait    / W_max)
    )
    return z


def makeFitnessFunction(
    instance: Instance,
    alpha: float = 0.5,
    beta: float = 0.4,
    gamma: float = 0.1,
    D_max: float | None = None,
) -> Callable[[list[int], Instance], float]:
    """
    Returns a fitness callable pre-bound to the given weights and
    normalization constants. Pass this directly to GeneticAlgorithm.

    D_max should ideally come from a reference solution (e.g. Solomon's
    nearest-neighbour heuristic). If omitted, a depot-distance upper bound
    is used automatically.

    Example
    -------
    >>> fn = makeFitnessFunction(instance, alpha=0.5, beta=0.4, gamma=0.1,
    ...                          D_max=reference_distance)
    >>> ga = GeneticAlgorithm(instance, fnFitness=fn, ...)
    """
    if abs(alpha + beta + gamma - 1.0) > 1e-9:
        raise ValueError(f"Weights must sum to 1. Got {alpha+beta+gamma}")

    n = len(instance.customer_ids)
    K_max = n

    W_max = sum(c.dueDate - c.readyTime for c in instance.customer_map.values())
    W_max = max(W_max, 1.0)

    if D_max is None:
        D_max = 2.0 * sum(instance.distances[0][cid] for cid in instance.customer_ids)
        D_max = max(D_max, 1.0)

    return partial(
        calculateFitness,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        K_max=K_max,
        D_max=D_max,
        W_max=W_max,
    )


def getSolutionStats(solution: list[int], instance: Instance) -> dict:
    total_distance = 0.0
    total_wait_time = 0.0
    current_time = 0.0
    current_load = 0
    current_location = 0
    num_vehicles = 0

    for node in solution[1:]:
        if node == 0:
            total_distance += instance.distances[current_location][0]
            current_time = 0.0
            current_load = 0
            current_location = 0
            num_vehicles += 1
            continue

        customer = instance.customer_map[node]
        travel_time = instance.distances[current_location][node]
        arrival_time = current_time + travel_time
        wait_time = max(0.0, customer.readyTime - arrival_time)

        total_wait_time += wait_time
        total_distance += travel_time
        current_time = arrival_time + wait_time + customer.serviceTime
        current_load += customer.demand
        current_location = node

    if current_location != 0:
        total_distance += instance.distances[current_location][0]
        num_vehicles += 1

    return {
        "num_vehicles": num_vehicles,
        "total_distance": round(total_distance, 2),
        "total_wait_time": round(total_wait_time, 2),
    }