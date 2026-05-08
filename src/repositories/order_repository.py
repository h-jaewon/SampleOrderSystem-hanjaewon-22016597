from typing import Optional

from src.models.order import Order, OrderStatus


class OrderRepository:
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def add(self, order: Order) -> None:
        if order.id in self._store:
            raise ValueError(f"이미 존재하는 주문 ID입니다: {order.id}")
        self._store[order.id] = order

    def get(self, order_id: str) -> Optional[Order]:
        return self._store.get(order_id)

    def get_all(self) -> list[Order]:
        return list(self._store.values())

    def get_by_status(self, status: OrderStatus) -> list[Order]:
        return [o for o in self._store.values() if o.status == status]
