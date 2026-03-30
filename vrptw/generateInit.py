import random
from typing import List, Optional

from vrptw.customer import Customer
from vrptw.instance import Instance


def generateCustomerMap(instance: Instance) -> dict[int, Customer]:
    return {c.num: c for c in instance.customers}


def canAddToRoute(
    current_location: int,
    current_time: float,
    current_load: int,
    customer: Customer,
    instance: Instance,
) -> Optional[tuple[float, float, int]]:
    if current_load + customer.demand > instance.capacity:
        return None

    travel_time = instance.distances[current_location][customer.num]
    arrival_time = current_time + travel_time

    if arrival_time > customer.dueDate:
        return None

    service_start = max(arrival_time, customer.readyTime)
    departure_time = service_start + customer.serviceTime

    return departure_time, current_location, current_load + customer.demand


def closeRoute(solution: List[int]) -> None:
    if not solution or solution[-1] != 0:
        solution.append(0)


def randomGenerator(instance: Instance) -> List[int]:
    customer_map = generateCustomerMap(instance)
    unassigned = [c.num for c in instance.customers[1:]]

    if not unassigned:
        return [0]

    random.shuffle(unassigned)

    solution: List[int] = [0]
    current_time = 0.0
    current_load = 0
    current_location = 0

    while unassigned:
        feasible = [cid for cid in unassigned if canAddToRoute(current_location, current_time, current_load, customer_map[cid], instance) is not None]

        if not feasible:
            closeRoute(solution)
            current_time = 0.0
            current_load = 0
            current_location = 0

            feasible = [cid for cid in unassigned if canAddToRoute(0, 0.0, 0, customer_map[cid], instance) is not None]

            if not feasible:
                # If no candidate can be added feasibly even from depot, pick closest due date to avoid huge windows issues.
                feasible = sorted(unassigned, key=lambda cid: customer_map[cid].dueDate)

        next_id = random.choice(feasible)
        customer = customer_map[next_id]

        feas_state = canAddToRoute(current_location, current_time, current_load, customer, instance)
        if feas_state is None:
            closeRoute(solution)
            current_time = 0.0
            current_load = 0
            current_location = 0
            feas_state = canAddToRoute(0, 0.0, 0, customer, instance)

        if feas_state is None:
            # should not happen for feasible candidate, but keep route constructed safely
            solution.append(customer.num)
            current_location = customer.num
            current_time = max(instance.distances[0][customer.num], customer.readyTime) + customer.serviceTime
            current_load = customer.demand
        else:
            departure_time, _, new_load = feas_state
            solution.append(customer.num)
            current_location = customer.num
            current_time = departure_time
            current_load = new_load

        unassigned.remove(next_id)

    closeRoute(solution)
    return solution


def solomonGenerator(instance: Instance, randomness: float = 0.3) -> List[int]:
    customer_map = generateCustomerMap(instance)
    all_customers = instance.customers[1:]

    if not all_customers:
        return [0]

    unassigned = set(c.num for c in all_customers)
    solution: List[int] = [0]

    current_time = 0.0
    current_load = 0
    current_location = 0

    while unassigned:
        feasible_candidates = []  

        for cust_id in unassigned:
            customer = customer_map[cust_id]

            if current_load + customer.demand > instance.capacity:
                continue

            travel_time = instance.distances[current_location][cust_id]
            arrival_time = current_time + travel_time
            if arrival_time > customer.dueDate:
                continue

            service_start = max(arrival_time, customer.readyTime)
            departure_time = service_start + customer.serviceTime

            wait = max(0.0, customer.readyTime - arrival_time)
            score = travel_time + wait

            feasible_candidates.append((score, cust_id, departure_time, current_load + customer.demand))

        if not feasible_candidates:
            closeRoute(solution)
            current_time = 0.0
            current_load = 0
            current_location = 0
            if solution[-1] == 0 and unassigned:
                forced = min(unassigned, key=lambda cid: customer_map[cid].dueDate)
                customer = customer_map[forced]
                solution.append(forced)
                unassigned.remove(forced)
                current_time = max(instance.distances[0][forced], customer.readyTime) + customer.serviceTime
                current_load = customer.demand
                current_location = forced
            continue

        feasible_candidates.sort(key=lambda x: x[0])
        num_top = max(1, int(len(feasible_candidates) * (1 - randomness)) + 1)
        selected = random.choice(feasible_candidates[:num_top])

        best_score, best_candidate, best_next_time, best_next_load = selected

        solution.append(best_candidate)
        unassigned.remove(best_candidate)
        current_time = best_next_time
        current_load = best_next_load
        current_location = best_candidate

    closeRoute(solution)
    return solution
