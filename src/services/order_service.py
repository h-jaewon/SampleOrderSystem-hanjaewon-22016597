from src.models.order import Order, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.sample_repository import SampleRepository


class OrderService:
    def __init__(self, sample_repository: SampleRepository, order_repository: OrderRepository) -> None:
        self._sample_repository = sample_repository
        self._order_repository = order_repository

    def place_order(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        if self._sample_repository.get(sample_id) is None:
            raise ValueError("등록되지 않은 시료 ID입니다.")
        if not customer_name.strip():
            raise ValueError("고객명은 필수 입력값입니다.")
        if quantity < 1:
            raise ValueError("주문 수량은 1 이상의 정수여야 합니다.")

        order_id = f"ORD-{len(self._order_repository.get_all()) + 1:03d}"
        order = Order(
            id=order_id,
            sampleId=sample_id,
            customerName=customer_name,
            quantity=quantity,
            status=OrderStatus.RESERVED,
        )
        self._order_repository.add(order)
        return order
