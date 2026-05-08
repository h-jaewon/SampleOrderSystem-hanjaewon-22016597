import pytest

from src.models.order import Order, OrderStatus
from src.models.sample import Sample
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.repositories.sample_repository import SampleRepository
from src.services.approval_service import ApprovalService


@pytest.fixture
def sample_repo():
    return SampleRepository()


@pytest.fixture
def order_repo():
    return OrderRepository()


@pytest.fixture
def production_queue():
    return ProductionQueue()


@pytest.fixture
def service(sample_repo, order_repo, production_queue):
    return ApprovalService(sample_repo, order_repo, production_queue)


@pytest.fixture
def sample_with_stock(sample_repo):
    sample = Sample(id="S001", name="SiC-300", avgProductionTime=5.5, yield_=0.8, stock=20)
    sample_repo.add(sample)
    return sample


@pytest.fixture
def sample_no_stock(sample_repo):
    sample = Sample(id="S002", name="GaAs-100", avgProductionTime=5.5, yield_=0.8, stock=0)
    sample_repo.add(sample)
    return sample


@pytest.fixture
def reserved_order_sufficient(order_repo, sample_with_stock):
    order = Order(id="ORD-001", sampleId="S001", customerName="홍길동", quantity=10)
    order_repo.add(order)
    return order


@pytest.fixture
def reserved_order_deficit(order_repo, sample_no_stock):
    order = Order(id="ORD-002", sampleId="S002", customerName="김철수", quantity=7)
    order_repo.add(order)
    return order


# TC-4-01: 재고 충분 시 승인 → CONFIRMED 전환 확인
def test_approve_sufficient_stock_returns_confirmed(service, reserved_order_sufficient):
    order = service.approve_order("ORD-001")
    assert order.status == OrderStatus.CONFIRMED


# TC-4-02: 재고 충분 시 승인 → 재고 변경 없음 확인
def test_approve_sufficient_stock_does_not_change_stock(service, sample_with_stock, reserved_order_sufficient):
    service.approve_order("ORD-001")
    assert sample_with_stock.stock == 20


# TC-4-03: 재고 정확히 같을 때 (재고 == 수량) → CONFIRMED 확인 (경계값)
def test_approve_stock_equals_quantity_returns_confirmed(sample_repo, order_repo, production_queue):
    sample = Sample(id="S010", name="BoundaryTest", avgProductionTime=3.0, yield_=0.9, stock=10)
    sample_repo.add(sample)
    order = Order(id="ORD-010", sampleId="S010", customerName="경계값테스트", quantity=10)
    order_repo.add(order)

    svc = ApprovalService(sample_repo, order_repo, production_queue)
    result = svc.approve_order("ORD-010")

    assert result.status == OrderStatus.CONFIRMED
    assert production_queue.is_empty() is True


# TC-4-04: 재고 부족 시 승인 → PRODUCING 전환 확인
def test_approve_insufficient_stock_returns_producing(service, reserved_order_deficit):
    order = service.approve_order("ORD-002")
    assert order.status == OrderStatus.PRODUCING


# TC-4-05: 재고 부족 시 승인 → 생산 큐 등록 확인
def test_approve_insufficient_stock_enqueues_job(service, production_queue, reserved_order_deficit):
    service.approve_order("ORD-002")
    assert production_queue.is_empty() is False
    assert production_queue.peek().orderId == "ORD-002"


# TC-4-06: 실 생산량 계산 정확성 검증 — ceil(7 / (0.8 × 0.9)) = 10
def test_approve_insufficient_stock_planned_quantity(service, production_queue, reserved_order_deficit):
    service.approve_order("ORD-002")
    assert production_queue.peek().plannedQuantity == 10


# TC-4-07: 총 생산 시간 계산 정확성 검증 — 5.5 × 10 = 55.0
def test_approve_insufficient_stock_total_production_time(service, production_queue, reserved_order_deficit):
    service.approve_order("ORD-002")
    assert production_queue.peek().totalProductionTime == 55.0


# TC-4-08: 거절 → REJECTED 전환 확인
def test_reject_returns_rejected(service, reserved_order_sufficient):
    order = service.reject_order("ORD-001")
    assert order.status == OrderStatus.REJECTED


# TC-4-09: 거절 → 생산 큐 미등록 확인
def test_reject_does_not_enqueue(service, production_queue, reserved_order_sufficient):
    service.reject_order("ORD-001")
    assert production_queue.is_empty() is True


# TC-4-10: RESERVED 외 상태(CONFIRMED) 주문 승인 시도 시 ValueError
def test_approve_confirmed_order_raises_value_error(sample_repo, order_repo, production_queue):
    sample = Sample(id="S003", name="TestSample", avgProductionTime=3.0, yield_=0.9, stock=10)
    sample_repo.add(sample)
    order = Order(id="ORD-003", sampleId="S003", customerName="테스트", quantity=5, status=OrderStatus.CONFIRMED)
    order_repo.add(order)

    svc = ApprovalService(sample_repo, order_repo, production_queue)
    with pytest.raises(ValueError, match="RESERVED 상태의 주문만 처리 가능합니다."):
        svc.approve_order("ORD-003")


# TC-4-11: RESERVED 외 상태(PRODUCING) 주문 거절 시도 시 ValueError
def test_reject_producing_order_raises_value_error(sample_repo, order_repo, production_queue):
    sample = Sample(id="S004", name="TestSample2", avgProductionTime=3.0, yield_=0.9, stock=0)
    sample_repo.add(sample)
    order = Order(id="ORD-004", sampleId="S004", customerName="테스트2", quantity=5, status=OrderStatus.PRODUCING)
    order_repo.add(order)

    svc = ApprovalService(sample_repo, order_repo, production_queue)
    with pytest.raises(ValueError, match="RESERVED 상태의 주문만 처리 가능합니다."):
        svc.reject_order("ORD-004")


# TC-4-12: 존재하지 않는 주문 ID 승인 시도 시 ValueError
def test_approve_nonexistent_order_raises_value_error(service):
    with pytest.raises(ValueError, match="존재하지 않는 주문 ID입니다."):
        service.approve_order("ORD-999")


# TC-4-13: 존재하지 않는 주문 ID 거절 시도 시 ValueError
def test_reject_nonexistent_order_raises_value_error(service):
    with pytest.raises(ValueError, match="존재하지 않는 주문 ID입니다."):
        service.reject_order("ORD-999")


# TC-4-14: _calculate_production_quantity 직접 단위 검증
def test_calculate_production_quantity_direct(service):
    result = service._calculate_production_quantity(deficit=7, yield_=0.8)
    assert result == 10


# TC-4-15: 생산 큐 FIFO 순서로 등록 확인
def test_approve_fifo_order_in_production_queue(sample_repo, order_repo, production_queue):
    sample = Sample(id="S005", name="FifoTest", avgProductionTime=3.0, yield_=0.9, stock=0)
    sample_repo.add(sample)

    order1 = Order(id="ORD-011", sampleId="S005", customerName="고객A", quantity=5)
    order2 = Order(id="ORD-012", sampleId="S005", customerName="고객B", quantity=3)
    order_repo.add(order1)
    order_repo.add(order2)

    svc = ApprovalService(sample_repo, order_repo, production_queue)
    svc.approve_order("ORD-011")
    svc.approve_order("ORD-012")

    jobs = production_queue.get_all()
    assert jobs[0].orderId == "ORD-011"
    assert jobs[1].orderId == "ORD-012"
