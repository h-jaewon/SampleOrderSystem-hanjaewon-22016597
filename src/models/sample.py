from dataclasses import dataclass


@dataclass
class Sample:
    id: str
    name: str
    avgProductionTime: float
    yield_: float
    stock: int = 0
