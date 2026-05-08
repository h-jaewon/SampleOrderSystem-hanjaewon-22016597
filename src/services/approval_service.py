import math

from src.models.order import Order, OrderStatus

_PRODUCTION_SAFETY_FACTOR = 0.9  # 수율의 90%만 유효 생산으로 간주하는 안전계수 (PRD 5.6)
from src.models.production_job import ProductionJob
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.repositories.sample_repository import SampleRepository


class ApprovalService:
    def __init__(
        self,
        sample_repository: SampleRepository,
        order_repository: OrderRepository,
        production_queue: ProductionQueue,
    ) -> None:
        self._sample_repository = sample_repository
        self._order_repository = order_repository
        self._production_queue = production_queue

    def get_reserved_orders(self) -> list[Order]:
        return self._order_repository.get_by_status(OrderStatus.RESERVED)

    def approve_order(self, order_id: str) -> Order:
        order = self._order_repository.get(order_id)
        if order is None:
            raise ValueError("존재하지 않는 주문 ID입니다.")
        if order.status != OrderStatus.RESERVED:
            raise ValueError("RESERVED 상태의 주문만 처리 가능합니다.")

        sample = self._sample_repository.get(order.sampleId)

        if sample.stock >= order.quantity:
            order.status = OrderStatus.CONFIRMED
            self._order_repository.update_status(order.id, OrderStatus.CONFIRMED)
        else:
            deficit = order.quantity - sample.stock
            planned_quantity = self._calculate_production_quantity(deficit, sample.yield_)
            total_production_time = sample.avgProductionTime * planned_quantity
            job = ProductionJob(
                orderId=order.id,
                sampleId=order.sampleId,
                plannedQuantity=planned_quantity,
                totalProductionTime=total_production_time,
            )
            self._production_queue.enqueue(job)
            order.status = OrderStatus.PRODUCING
            self._order_repository.update_status(order.id, OrderStatus.PRODUCING)

        return order

    def reject_order(self, order_id: str) -> Order:
        order = self._order_repository.get(order_id)
        if order is None:
            raise ValueError("존재하지 않는 주문 ID입니다.")
        if order.status != OrderStatus.RESERVED:
            raise ValueError("RESERVED 상태의 주문만 처리 가능합니다.")

        order.status = OrderStatus.REJECTED
        self._order_repository.update_status(order.id, OrderStatus.REJECTED)
        return order

    def _calculate_production_quantity(self, deficit: int, yield_: float) -> int:
        return math.ceil(deficit / (yield_ * _PRODUCTION_SAFETY_FACTOR))
