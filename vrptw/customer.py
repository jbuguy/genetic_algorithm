class Customer(object):
    def __init__(
        self,
        num: int,
        x: int,
        y: int,
        demand: int,
        readyTime: int,
        dueDate: int,
        serviceTime: int,
    ) -> None:
        self.num = num
        self.x = x
        self.y = y
        self.demand = demand
        self.readyTime = readyTime
        self.dueDate = dueDate
        self.serviceTime = serviceTime
