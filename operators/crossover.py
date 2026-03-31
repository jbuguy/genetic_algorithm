import random
from typing import List

def PMXCrossOver(parent1: List[int], parent2: List[int], instance) -> List[int]:
    child=[]
    length=min(len(parent1),len(parent2))
    point1=random.randint(0,length-1)
    point2=random.randint(point1,length-1)
    mappage={}
    for i in range(point1,point2):
        mappage[parent1[i]]=parent2[i]
        mappage[parent2[i]]=parent1[i]
    for elm in parent1:
        if mappage.get(elm)==None:
            child.append(elm)
        else :child.append(mappage.get(elm))
    return child
    
    
    
def edgeAssemblyCrossover(parent1: List[int], parent2: List[int], instance) -> List[int]:
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