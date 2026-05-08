from src.models.order import Order, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.repositories.sample_repository import SampleRepository


class ProductionService:
    def __init__(
        self,
        sample_repository: SampleRepository,
        order_repository: OrderRepository,
        production_queue: ProductionQueue,
    ) -> None:
        self._sample_repository = sample_repository
        self._order_repository = order_repository
        self._production_queue = production_queue

    def get_production_status(self) -> dict:
        all_jobs = self._production_queue.get_all()
        if not all_jobs:
            return {"current": None, "queue": []}

        current_job = all_jobs[0]
        current_order = self._order_repository.get(current_job.orderId)
        current = {
            "job": current_job,
            "quantity": current_order.quantity if current_order else 0,
        }

        queue = []
        for job in all_jobs[1:]:
            order = self._order_repository.get(job.orderId)
            queue.append({
                "job": job,
                "quantity": order.quantity if order else 0,
            })

        return {"current": current, "queue": queue}

    def complete_production(self) -> Order:
        if self._production_queue.is_empty():
            raise ValueError("진행 중인 생산 작업이 없습니다.")

        job = self._production_queue.dequeue()

        sample = self._sample_repository.get(job.sampleId)
        new_stock = sample.stock + job.plannedQuantity
        self._sample_repository.update_stock(job.sampleId, new_stock)

        self._order_repository.update_status(job.orderId, OrderStatus.CONFIRMED)
        order = self._order_repository.get(job.orderId)
        return order
