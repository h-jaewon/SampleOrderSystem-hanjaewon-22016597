"""더미 데이터 주입 스크립트.

사용법:
    python dummy.py          # 더미 데이터 주입 후 main.py 자동 시작
    python dummy.py --only   # 더미 주입만 (main.py 실행 안 함)
    python dummy.py --reset  # 기존 데이터 초기화 후 재주입 (+ main.py 자동 시작)
"""

import sys

from faker import Faker

from src.models.order import Order, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.repositories.sample_repository import SampleRepository
from src.services.approval_service import ApprovalService
from src.services.order_service import OrderService
from src.services.sample_service import SampleService

fake = Faker("ko_KR")

_SAMPLES = [
    ("Si-Wafer-200", 3.0, 0.90, 45),
    ("SiC-300",      5.5, 0.80,  3),
    ("GaAs-100",     2.5, 0.85,  0),
    ("InP-150",      4.0, 0.75,  8),
    ("GaN-200",      6.0, 0.70,  2),
]


def _inject(
    sample_repo: SampleRepository,
    order_repo: OrderRepository,
    production_queue: ProductionQueue,
) -> None:
    if sample_repo.get_all():
        print("  [정보] 이미 데이터가 존재합니다.")
        print("  재주입하려면: python dummy.py --reset")
        return

    service = SampleService(sample_repo)

    registered = []
    for name, avg_time, yield_, stock in _SAMPLES:
        sample = service.register_sample(name, avg_time, yield_)
        sample_repo.update_stock(sample.id, stock)
        registered.append(sample)

    order_service = OrderService(sample_repo, order_repo)
    approval_service = ApprovalService(sample_repo, order_repo, production_queue)

    # RESERVED 1건: registered[0] (Si-Wafer-200)
    order_service.place_order(registered[0].id, fake.name(), fake.random_int(min=1, max=20))

    # RESERVED 1건: registered[1] (SiC-300)
    order_service.place_order(registered[1].id, fake.name(), fake.random_int(min=1, max=20))

    # PRODUCING 1건: registered[2] (GaAs-100, stock=0) — place_order → approve_order 경로
    producing_order = order_service.place_order(registered[2].id, fake.name(), fake.random_int(min=1, max=20))
    approval_service.approve_order(producing_order.id)

    # CONFIRMED 1건: registered[3] (InP-150) — Phase 6에서 해소 예정 (H-1 유지)
    order_id_confirmed = f"ORD-{len(order_repo.get_all()) + 1:03d}"
    order_repo.add(Order(
        id=order_id_confirmed,
        sampleId=registered[3].id,
        customerName=fake.name(),
        quantity=fake.random_int(min=1, max=20),
        status=OrderStatus.CONFIRMED,
    ))

    # RELEASED 2건: registered[4] (GaN-200), registered[0] (Si-Wafer-200) — Phase 7에서 해소 예정 (H-1 유지)
    for sample in [registered[4], registered[0]]:
        order_id_released = f"ORD-{len(order_repo.get_all()) + 1:03d}"
        order_repo.add(Order(
            id=order_id_released,
            sampleId=sample.id,
            customerName=fake.name(),
            quantity=fake.random_int(min=1, max=20),
            status=OrderStatus.RELEASED,
        ))

    total_orders = len(order_repo.get_all())
    print("  [더미 데이터 주입 완료]")
    print(f"  - 시료 {len(registered)}종 등록")
    print(f"  - 주문 {total_orders}건 등록")


def main() -> None:
    reset = "--reset" in sys.argv
    only = "--only" in sys.argv

    if reset:
        import src.database as _db
        from src.database import get_connection
        with get_connection(_db.DB_PATH) as conn:
            conn.execute("DELETE FROM production_queue")
            conn.execute("DELETE FROM orders")
            conn.execute("DELETE FROM samples")
        print("  [초기화 완료] 기존 데이터가 삭제되었습니다.")

    sample_repo = SampleRepository()
    order_repo = OrderRepository()
    production_queue = ProductionQueue()

    _inject(sample_repo, order_repo, production_queue)

    if not only:
        from main import main as run_main
        run_main(
            sample_repository=sample_repo,
            order_repository=order_repo,
            production_queue=production_queue,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  시스템을 종료합니다.")
