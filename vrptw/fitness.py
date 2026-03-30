from vrptw.instance import Instance


def calculateFitness(solution: list[int], instance: Instance) -> float:
    if not solution or solution[0] != 0:
        return float('inf')

    total_distance = 0.0
    current_time = 0.0
    current_load = 0
    current_location = 0
    visited = set()

    for node in solution[1:]:
        if node == 0:
            total_distance += instance.distances[current_location][0]
            current_time = 0.0  
            current_load = 0
            current_location = 0
            continue

        if node in visited:
            return float('inf')

        customer = instance.customer_map.get(node)
        if not customer:
            return float('inf')

        if current_load + customer.demand > instance.capacity:
            return float('inf')

        travel_time = instance.distances[current_location][node]
        arrival_time = current_time + travel_time

        if arrival_time > customer.dueDate:
            return float('inf')

        total_distance += travel_time
        current_time = max(arrival_time, customer.readyTime) + customer.serviceTime
        current_load += customer.demand
        current_location = node
        visited.add(node)

    # Final return to depot if route doesn't explicitly end with 0
    if current_location != 0:
        total_distance += instance.distances[current_location][0]
        current_time += instance.distances[current_location][0]

    # all customers should be served once
    if visited != instance.customer_ids:
        return float('inf')

    return total_distance