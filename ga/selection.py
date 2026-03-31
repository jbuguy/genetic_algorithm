from functools import reduce
import random

def rouletteSelection(
    scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]:
    valeurtotal=reduce(lambda x,y:x+y[1],scored_population,0)
    listproba=list(map(lambda x: x[1]/valeurtotal,scored_population))
    cumul=0;
    randomvalue=random.random()
    for i in range(len(listproba)-1):
        if (listproba[i+1]+cumul>=randomvalue>listproba[i]+cumul):
            return scored_population[i]
        else:
            cumul+=listproba[i]
    return scored_population[-1]

def selection_truncation(
   scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]: 
    sorted_population= sorted(scored_population,key=lambda x:x[1])
    survivors_count = max(1, len(sorted_population) // 2)
    selected = random.sample(sorted_population[:survivors_count], 1)
    return selected[0]

def tournamentSelection(
    scored_population: list[tuple[list[int], float]], k: int = 5
) -> tuple[list[int], float]:
    k = min(k, len(scored_population))

    indices = random.sample(range(len(scored_population)), k)
    
    best_id = min(indices, key=lambda i: scored_population[i][1])
    individual, fitness = scored_population[best_id]
    return individual[:], fitness
fn=[rouletteSelection,selection_truncation,tournamentSelection]
