from src.models.order import Order, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.sample_repository import SampleRepository


class ShipmentService:
    def __init__(
        self,
        sample_repository: SampleRepository,
        order_repository: OrderRepository,
    ) -> None:
        self._sample_repository = sample_repository
        self._order_repository = order_repository

    def get_confirmed_orders(self) -> list[Order]:
        return self._order_repository.get_by_status(OrderStatus.CONFIRMED)

    def release_order(self, order_id: str) -> Order:
        order = self._order_repository.get(order_id)
        if order is None:
            raise ValueError("존재하지 않는 주문 ID입니다.")
        if order.status != OrderStatus.CONFIRMED:
            raise ValueError("CONFIRMED 상태의 주문만 출고 처리 가능합니다.")

        sample = self._sample_repository.get(order.sampleId)
        new_stock = sample.stock - order.quantity
        self._sample_repository.update_stock(order.sampleId, new_stock)

        self._order_repository.update_status(order_id, OrderStatus.RELEASED)
        order.status = OrderStatus.RELEASED
        return order
