from src.models.order import Order, OrderStatus
from src.models.sample import Sample
from src.repositories.order_repository import OrderRepository
from src.repositories.sample_repository import SampleRepository

_MONITORED_STATUSES = [
    OrderStatus.RESERVED,
    OrderStatus.PRODUCING,
    OrderStatus.CONFIRMED,
    OrderStatus.RELEASED,
]


class MonitoringService:
    def __init__(
        self,
        sample_repository: SampleRepository,
        order_repository: OrderRepository,
    ) -> None:
        self._sample_repository = sample_repository
        self._order_repository = order_repository

    def get_order_summary(self) -> dict:
        counts: dict[str, int] = {}
        orders: dict[str, list[Order]] = {}

        for status in _MONITORED_STATUSES:
            key = status.value
            status_orders = self._order_repository.get_by_status(status)
            counts[key] = len(status_orders)
            orders[key] = status_orders

        return {"counts": counts, "orders": orders}

    def get_stock_status(self) -> list[dict]:
        all_orders = self._order_repository.get_all()
        samples = self._sample_repository.get_all()
        return [
            {"sample": sample, "status": self._classify_stock(sample, all_orders)}
            for sample in samples
        ]

    def _classify_stock(self, sample: Sample, all_orders: list[Order]) -> str:
        if sample.stock == 0:
            return "고갈"
        producing_sample_ids = {
            o.sampleId for o in all_orders if o.status == OrderStatus.PRODUCING
        }
        if sample.id in producing_sample_ids:
            return "부족"
        return "여유"
