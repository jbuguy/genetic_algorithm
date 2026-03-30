import random
from typing import List, Optional

from vrptw.customer import Customer
from vrptw.instance import Instance


def remove_consecutive_zeros(solution: List[int]) -> List[int]:
    """Remove consecutive 0s from solution while preserving at least one 0 between routes."""
    if not solution:
        return solution
    
    cleaned = [solution[0]]
    for i in range(1, len(solution)):
        if solution[i] != 0 or cleaned[-1] != 0:
            cleaned.append(solution[i])
    
    return cleaned


def remove_trailing_zeros(solution: List[int]) -> List[int]:
    """Remove trailing zeros from solution (represents unused vehicle routes)."""
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
