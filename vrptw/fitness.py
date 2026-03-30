from typing import List
from vrptw.instance import Instance


def calculateFitness(solution: List[int], instance: Instance) -> float:
    """
    Returns:
        Total distance + penalties for violations, or infinity if fundamentally invalid
    """
    if not solution or solution[0] != 0:
        return float('inf')

    total_distance = 0.0
    total_penalty = 0.0
    current_time = 0.0
    current_load = 0
    current_location = 0

    visited = set()

    i = 1  
    while i < len(solution):
        if solution[i] == 0:
            distance = instance.distances[current_location][0]
            total_distance += distance
            current_time += distance
            current_load = 0
            current_location = 0
            i += 1
            continue

        customer_id = solution[i]
        if customer_id in visited:
            return float('inf')  

        customer = next((c for c in instance.customers if c.num == customer_id), None)
        if not customer:
            return float('inf')  

        if current_load + customer.demand > instance.capacity:
            return float('inf')

        travel_time = instance.distances[current_location][customer_id]
        arrival_time = current_time + travel_time

        # Penalize late arrivals instead of rejecting
        if arrival_time > customer.dueDate:
            lateness = arrival_time - customer.dueDate
            total_penalty += lateness * 100  # Penalty for time window violation

        service_start = max(arrival_time, customer.readyTime)
        departure_time = service_start + customer.serviceTime

        total_distance += travel_time
        current_time = departure_time
        current_load += customer.demand
        current_location = customer_id
        visited.add(customer_id)

        i += 1

    all_customers = {c.num for c in instance.customers[1:]}  
    if visited != all_customers:
        missing = len(all_customers - visited)
        penalty = missing * 1e6
        return total_distance + total_penalty + penalty

    return total_distance + total_penalty