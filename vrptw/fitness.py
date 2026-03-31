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

        wait_time = 0.0
        if arrival_time < customer.readyTime:
            wait_time = customer.readyTime - arrival_time
            total_wait_time += wait_time

        total_distance += travel_time
        current_time = max(arrival_time, customer.readyTime) + customer.serviceTime
        current_load += customer.demand
        current_location = node
        visited.add(node)

    # Final return to depot
    if current_location != 0:
        total_distance += instance.distances[current_location][0]
        current_time += instance.distances[current_location][0]
        num_vehicles += 1  # count the last route

    if visited != instance.customer_ids:
        return float('inf')

    # C101 optimal is 10 vehicles, ~828 distance
    VEHICLE_WEIGHT = 1000.0

    return (VEHICLE_WEIGHT * num_vehicles) + total_distance 

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
        current_time = max(arrival_time, customer.readyTime) + customer.serviceTime
        current_load += customer.demand
        current_location = node

    if current_location != 0:
        total_distance += instance.distances[current_location][0]
        num_vehicles += 1

    return {
        "num_vehicles": num_vehicles,
        "total_distance": round(total_distance, 2),
        "total_wait_time": round(total_wait_time, 2),
        "pure_distance": round(total_distance, 2),  # without penalties
    }