from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASED = "RELEASED"


@dataclass
class Order:
    id: str
    sampleId: str
    customerName: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
    createdAt: datetime = field(default_factory=datetime.now)
