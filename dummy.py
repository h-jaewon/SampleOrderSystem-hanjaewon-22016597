"""더미 데이터 주입 스크립트.

사용법:
    python dummy.py          # 더미 데이터 주입 후 main.py 자동 시작
    python dummy.py --only   # 더미 주입만 (main.py 실행 안 함)
"""

import sys

from faker import Faker

from src.models.order import Order, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.sample_repository import SampleRepository
from src.services.sample_service import SampleService

fake = Faker("ko_KR")

_SAMPLES = [
    ("Si-Wafer-200", 3.0, 0.90, 45),
    ("SiC-300",      5.5, 0.80,  3),
    ("GaAs-100",     2.5, 0.85,  0),
    ("InP-150",      4.0, 0.75,  8),
    ("GaN-200",      6.0, 0.70,  2),
]


def _inject(sample_repo: SampleRepository, order_repo: OrderRepository) -> None:
    service = SampleService(sample_repo)

    registered = []
    for name, avg_time, yield_, stock in _SAMPLES:
        sample = service.register_sample(name, avg_time, yield_)
        sample.stock = stock  # Phase 2 범위: SampleService에 초기재고 설정 기능 미구현으로 직접 설정 (M-1)
        registered.append(sample)

    statuses = [
        OrderStatus.RESERVED,
        OrderStatus.RESERVED,
        OrderStatus.PRODUCING,
        OrderStatus.CONFIRMED,
        OrderStatus.RELEASED,
        OrderStatus.RELEASED,
    ]

    sample_cycle = [
        registered[0],
        registered[1],
        registered[2],
        registered[3],
        registered[4],
        registered[0],
    ]

    # OrderService가 Phase 3에서 구현되기 전까지 OrderRepository를 직접 사용한다.
    # Phase 3 완료 후 OrderService.place_order()로 교체할 것 (H-1).
    for i, (status, sample) in enumerate(zip(statuses, sample_cycle), start=1):
        order_id = f"ORD-{i:03d}"
        customer_name = fake.name()
        quantity = fake.random_int(min=1, max=20)

        order = Order(
            id=order_id,
            sampleId=sample.id,
            customerName=customer_name,
            quantity=quantity,
            status=status,
        )
        order_repo.add(order)

    print("  [더미 데이터 주입 완료]")
    print(f"  - 시료 {len(registered)}종 등록")
    print(f"  - 주문 {len(statuses)}건 등록")


def main() -> None:
    only = "--only" in sys.argv

    sample_repo = SampleRepository()
    order_repo = OrderRepository()

    _inject(sample_repo, order_repo)

    if not only:
        from main import main as run_main
        run_main(sample_repository=sample_repo)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  시스템을 종료합니다.")
