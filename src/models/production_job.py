from dataclasses import dataclass


@dataclass
class ProductionJob:
    orderId: str
    sampleId: str
    plannedQuantity: int
    totalProductionTime: float
