import math

from vrptw.customer import Customer


class Instance:
    def __init__(self, file: str) -> None:
        self.customers: list[Customer] = []

        with open(file) as f:
            lines = f.readlines()

        self.name = lines[0].strip()
        self.numberVehicle, self.capacity = map(lambda x: int(x), lines[4].split())

        for i in range(9, len(lines)):
            sp = lines[i].split()
            self.customers.append(
                Customer(
                    int(sp[0]),
                    int(sp[1]),
                    int(sp[2]),
                    int(sp[3]),
                    int(sp[4]),
                    int(sp[5]),
                    int(sp[6]),
                )
            )
        self.distances= self.compute_distance()

    def compute_distance(self):
        n = len(self.customers)
        dist = [[0.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                c1 = self.customers[i]
                c2 = self.customers[j]

                dx = c1.x - c2.x
                dy = c1.y - c2.y

                dist[i][j] = math.sqrt(dx * dx + dy * dy)

        return dist
