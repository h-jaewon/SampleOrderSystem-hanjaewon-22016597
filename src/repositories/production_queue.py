import collections
from typing import Optional

from src.models.production_job import ProductionJob


class ProductionQueue:
    def __init__(self) -> None:
        self._queue: collections.deque[ProductionJob] = collections.deque()

    def enqueue(self, job: ProductionJob) -> None:
        self._queue.append(job)

    def dequeue(self) -> ProductionJob:
        if not self._queue:
            raise IndexError("생산 큐가 비어있습니다.")
        return self._queue.popleft()

    def peek(self) -> Optional[ProductionJob]:
        if not self._queue:
            return None
        return self._queue[0]

    def get_all(self) -> list[ProductionJob]:
        return list(self._queue)

    def is_empty(self) -> bool:
        return len(self._queue) == 0
