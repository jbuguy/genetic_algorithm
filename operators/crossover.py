import random
from typing import List


def edgeAssemblyCrossover(parent1: List[int], parent2: List[int], instance) -> List[int]:
    """
    Simplified constraint-aware crossover for VRPTW.

    Performs route-based crossover while respecting basic capacity constraints.
    Much faster than full EAX while still being effective.
    """
    if len(parent1) != len(parent2):
        return parent1.copy()

    # Extract routes from both parents
    routes1 = _extract_routes(parent1)
    routes2 = _extract_routes(parent2)

    if not routes1 or not routes2:
        return parent1.copy()

    # Select one route from each parent to crossover
    route1 = random.choice(routes1)
    route2 = random.choice(routes2)

    # Perform simple ordered crossover on route sequences
    if len(route1) < 2 or len(route2) < 2:
        return parent1.copy()

    min_len = min(len(route1), len(route2))
    if min_len < 2:
        return parent1.copy()

    # Choose crossover points
    start = random.randint(0, min_len - 2)
    end = random.randint(start + 1, min_len)

    # Create child route using ordered crossover
    child_route = route1[:start] + route2[start:end] + route1[end:]

    # Remove any duplicate customers (each customer can only be visited once)
    seen = set()
    unique_route = []
    for customer in child_route:
        if customer not in seen:
            seen.add(customer)
            unique_route.append(customer)

    # Replace the original route in parent1 with the new route
    child_solution = _replace_route(parent1, route1, unique_route)

    # Quick feasibility check - if not feasible, return parent1
    if _quick_feasibility_check(child_solution, instance):
        return child_solution
    else:
        return parent1.copy()


def _extract_routes(solution: List[int]) -> List[List[int]]:
    """Extract individual routes from solution."""
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
    """Replace a route in the solution with a new route."""
    # Build new solution by replacing the old route with new route
    routes = _extract_routes(solution)
    
    # Find which route matches old_route
    for i, route in enumerate(routes):
        if route == old_route:
            routes[i] = new_route
            break
    
    # Rebuild solution from routes with depot separators
    result = []
    for route in routes:
        result.extend(route)
        result.append(0)
    
    return result


def _quick_feasibility_check(solution: List[int], instance) -> bool:
    """
    Quick feasibility check - ensures no duplicate customers, capacity, and time windows.
    """
    visited = set()
    current_load = 0
    current_time = 0.0
    current_location = 0

    for customer_id in solution:
        if customer_id == 0:
            # Return to depot
            current_load = 0
            current_time = 0.0
            current_location = 0
            continue

        if customer_id in visited:
            return False  # Duplicate customer

        customer = next((c for c in instance.customers if c.num == customer_id), None)
        if not customer:
            return False

        # Check capacity
        if current_load + customer.demand > instance.capacity:
            return False

        # Check time window
        travel_time = instance.distances[current_location][customer_id]
        arrival_time = current_time + travel_time
        
        if arrival_time > customer.dueDate:
            return False

        # Update state after visiting this customer
        current_time = max(arrival_time, customer.readyTime) + customer.serviceTime
        current_load += customer.demand
        current_location = customer_id
        visited.add(customer_id)

    # Check all customers are visited
    all_customers = {c.num for c in instance.customers[1:]}  # Skip depot
    return visited == all_customers