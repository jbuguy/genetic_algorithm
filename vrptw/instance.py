import numpy as np
from vrptw.customer import Customer


class Instance:
    def __init__(self, file: str) -> None:
        self.customers: list[Customer] = []

        with open(file) as f:
            lines = f.readlines()

        self.name = lines[0].strip()
        self.capacity = int(lines[4].split()[1])

        for line in lines[9:]:
            sp = line.split()
            self.customers.append(Customer(
                int(sp[0]), int(sp[1]), int(sp[2]),
                int(sp[3]), int(sp[4]), int(sp[5]), int(sp[6]),
            ))

        self.customer_map: dict[int, Customer] = {
            c.num: c for c in self.customers
        }

        self.customer_ids: set[int] = {c.num for c in self.customers[1:]}

        self.distances: list[list[float]] = self._compute_distances()

    def _compute_distances(self) -> list[list[float]]:
        coords = np.array([(c.x, c.y) for c in self.customers])
        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]  # 
        dist_matrix = np.sqrt((diff ** 2).sum(axis=2))
        return dist_matrix.tolist()