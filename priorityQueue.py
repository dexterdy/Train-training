import heapq
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class PriorityQueue(Generic[T]):
    idLookup: dict[T, int]
    queue: list[tuple[int, tuple[int, T]]]
    deleted: set[int]
    currentId: int

    def __init__(self):
        self.queue = []
        self.deleted = set()
        self.currentId = 0
        self.idLookup = dict()

    def insert(self, item: T, priority: int):
        heapq.heappush(self.queue, (priority, (self.currentId, item)))
        self.idLookup[item] = self.currentId
        self.currentId += 1

    def pop(self) -> tuple[int, T]:
        while len(self.queue) > 0:
            cost, (id, item) = heapq.heappop(self.queue)
            if id not in self.deleted:
                return (cost, item)
        raise IndexError("queue is empty")

    def delete(self, item: T):
        if item in self.idLookup:
            self.deleted.add(self.idLookup[item])

    def modify(self, item: T, newPriority: int):
        self.delete(item)
        self.insert(item, newPriority)

    def __len__(self):
        return len(self.queue)
