from vrptw.instance import Instance


def calculateFitness(solution: list[int], instance: Instance) -> float:
    if not solution or solution[0] != 0:
        return float('inf')

    total_distance = 0.0
    total_wait_time = 0.0
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

        # Calculate wait time if arriving early
        wait_time = 0.0
        if arrival_time < customer.readyTime:
            wait_time = customer.readyTime - arrival_time
            total_wait_time += wait_time

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

    # Return distance + wait time penalty
    return total_distance + total_wait_time

def calculateFitnessStrict(solution, instance, weight_distance=1.0, weight_vehicles=1.0, max_vehicles=None):
    if max_vehicles is None:
        max_vehicles = len(instance.customer_ids)

    if not solution or solution[0] != 0:
        return float('inf')

    distances = instance.distances
    customer_map = instance.customer_map
    customer_ids = instance.customer_ids

    total_distance = 0.0
    total_wait_time = 0.0
    vehicle_count = 1
    current_time = 0.0
    current_load = 0
    current_location = 0
    visited = set()

    for node in solution[1:]:
        if node == 0:
            total_distance += distances[current_location][0]
            current_time = 0.0
            current_load = 0
            current_location = 0
            vehicle_count += 1
            continue

        if node in visited:
            return float('inf')

        customer = customer_map.get(node)
        if not customer:
            return float('inf')

        if current_load + customer.demand > instance.capacity:
            return float('inf')

        travel_time = distances[current_location][node]
        arrival_time = current_time + travel_time

        if arrival_time > customer.dueDate:
            return float('inf')

        wait_time = max(0.0, customer.readyTime - arrival_time)
        total_wait_time += wait_time

        total_distance += travel_time
        current_time = arrival_time + wait_time + customer.serviceTime
        current_load += customer.demand
        current_location = node
        visited.add(node)

    if current_location != 0:
        total_distance += distances[current_location][0]

    if len(visited) != len(customer_ids):
        return float('inf')

    normalized_vehicles = vehicle_count / max_vehicles
    fitness = weight_distance * (total_distance + total_wait_time) + weight_vehicles * normalized_vehicles

    return fitness