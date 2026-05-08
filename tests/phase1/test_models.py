import pytest
from datetime import datetime

from src.models.sample import Sample
from src.models.order import Order, OrderStatus
from src.models.production_job import ProductionJob
from src.repositories.sample_repository import SampleRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue


# ---------------------------------------------------------------------------
# TC-1-01: Sample 객체 생성 및 속성 접근
# ---------------------------------------------------------------------------
def test_sample_creation_with_all_attributes():
    sample = Sample(id="S001", name="AlphaChip", avgProductionTime=5.0, yield_=0.8, stock=100)
    assert sample.id == "S001"
    assert sample.name == "AlphaChip"
    assert sample.avgProductionTime == 5.0
    assert sample.yield_ == 0.8
    assert sample.stock == 100


# ---------------------------------------------------------------------------
# TC-1-02: Sample stock 기본값
# ---------------------------------------------------------------------------
def test_sample_stock_default_zero():
    sample = Sample(id="S001", name="AlphaChip", avgProductionTime=5.0, yield_=0.8)
    assert sample.stock == 0


# ---------------------------------------------------------------------------
# TC-1-03: Order 객체 생성 및 상태 초기값 검증
# ---------------------------------------------------------------------------
def test_order_default_status_is_reserved():
    order = Order(id="ORD-001", sampleId="S001", customerName="홍길동", quantity=10)
    assert order.status == OrderStatus.RESERVED


# ---------------------------------------------------------------------------
# TC-1-04: Order createdAt 자동 설정
# ---------------------------------------------------------------------------
def test_order_created_at_is_datetime_and_not_future():
    before = datetime.now()
    order = Order(id="ORD-001", sampleId="S001", customerName="홍길동", quantity=10)
    assert isinstance(order.createdAt, datetime)
    assert order.createdAt <= datetime.now()
    assert order.createdAt >= before


# ---------------------------------------------------------------------------
# TC-1-05: Order createdAt 인스턴스별 독립성
# ---------------------------------------------------------------------------
def test_order_created_at_is_independent_per_instance():
    order1 = Order(id="ORD-001", sampleId="S001", customerName="홍길동", quantity=10)
    order2 = Order(id="ORD-002", sampleId="S001", customerName="김철수", quantity=5)
    assert order1.createdAt is not order2.createdAt


# ---------------------------------------------------------------------------
# TC-1-06: OrderStatus 열거형 전체 값 존재 확인
# ---------------------------------------------------------------------------
def test_order_status_has_all_five_members():
    member_names = {m.name for m in OrderStatus}
    assert "RESERVED" in member_names
    assert "REJECTED" in member_names
    assert "PRODUCING" in member_names
    assert "CONFIRMED" in member_names
    assert "RELEASED" in member_names
    assert len(member_names) == 5


# ---------------------------------------------------------------------------
# TC-1-07: ProductionJob 객체 생성 검증
# ---------------------------------------------------------------------------
def test_production_job_creation():
    job = ProductionJob(orderId="ORD-001", sampleId="S001", plannedQuantity=10, totalProductionTime=55.0)
    assert job.orderId == "ORD-001"
    assert job.sampleId == "S001"
    assert job.plannedQuantity == 10
    assert job.totalProductionTime == 55.0


# ---------------------------------------------------------------------------
# TC-1-08: SampleRepository — add 및 get
# ---------------------------------------------------------------------------
def test_sample_repository_add_and_get():
    repo = SampleRepository()
    sample = Sample(id="S001", name="AlphaChip", avgProductionTime=5.0, yield_=0.8)
    repo.add(sample)
    result = repo.get("S001")
    assert result == sample


# ---------------------------------------------------------------------------
# TC-1-09: SampleRepository — 중복 ID 예외
# ---------------------------------------------------------------------------
def test_sample_repository_duplicate_id_raises_value_error():
    repo = SampleRepository()
    sample1 = Sample(id="S001", name="AlphaChip", avgProductionTime=5.0, yield_=0.8)
    sample2 = Sample(id="S001", name="BetaChip", avgProductionTime=3.0, yield_=0.9)
    repo.add(sample1)
    with pytest.raises(ValueError):
        repo.add(sample2)


# ---------------------------------------------------------------------------
# TC-1-10: SampleRepository — get_all
# ---------------------------------------------------------------------------
def test_sample_repository_get_all_returns_all():
    repo = SampleRepository()
    repo.add(Sample(id="S001", name="AlphaChip", avgProductionTime=5.0, yield_=0.8))
    repo.add(Sample(id="S002", name="BetaChip", avgProductionTime=3.0, yield_=0.9))
    repo.add(Sample(id="S003", name="GammaChip", avgProductionTime=4.0, yield_=0.7))
    assert len(repo.get_all()) == 3


# ---------------------------------------------------------------------------
# TC-1-11: SampleRepository — get_all 빈 저장소
# ---------------------------------------------------------------------------
def test_sample_repository_get_all_empty():
    repo = SampleRepository()
    assert repo.get_all() == []


# ---------------------------------------------------------------------------
# TC-1-12: SampleRepository — find_by_name 부분 일치 (대소문자 무관)
# ---------------------------------------------------------------------------
def test_sample_repository_find_by_name_partial_case_insensitive():
    repo = SampleRepository()
    repo.add(Sample(id="S001", name="AlphaChip", avgProductionTime=5.0, yield_=0.8))
    repo.add(Sample(id="S002", name="BetaChip", avgProductionTime=3.0, yield_=0.9))
    results = repo.find_by_name("chip")
    assert len(results) == 2


# ---------------------------------------------------------------------------
# TC-1-13: SampleRepository — find_by_name 결과 없음
# ---------------------------------------------------------------------------
def test_sample_repository_find_by_name_no_match():
    repo = SampleRepository()
    repo.add(Sample(id="S001", name="AlphaChip", avgProductionTime=5.0, yield_=0.8))
    results = repo.find_by_name("존재하지않는이름")
    assert results == []


# ---------------------------------------------------------------------------
# TC-1-14: OrderRepository — 상태별 필터링
# ---------------------------------------------------------------------------
def test_order_repository_get_by_status():
    repo = OrderRepository()
    repo.add(Order(id="ORD-001", sampleId="S001", customerName="홍길동", quantity=10))
    repo.add(Order(id="ORD-002", sampleId="S001", customerName="김철수", quantity=5))
    confirmed_order = Order(id="ORD-003", sampleId="S001", customerName="이영희", quantity=3)
    confirmed_order.status = OrderStatus.CONFIRMED
    repo.add(confirmed_order)

    reserved_orders = repo.get_by_status(OrderStatus.RESERVED)
    assert len(reserved_orders) == 2
    assert all(o.status == OrderStatus.RESERVED for o in reserved_orders)


# ---------------------------------------------------------------------------
# TC-1-15: OrderRepository — 중복 ID 예외
# ---------------------------------------------------------------------------
def test_order_repository_duplicate_id_raises_value_error():
    repo = OrderRepository()
    order1 = Order(id="ORD-001", sampleId="S001", customerName="홍길동", quantity=10)
    order2 = Order(id="ORD-001", sampleId="S001", customerName="김철수", quantity=5)
    repo.add(order1)
    with pytest.raises(ValueError):
        repo.add(order2)


# ---------------------------------------------------------------------------
# TC-1-16: OrderRepository — get 존재하지 않는 ID
# ---------------------------------------------------------------------------
def test_order_repository_get_nonexistent_returns_none():
    repo = OrderRepository()
    assert repo.get("ORD-999") is None


# ---------------------------------------------------------------------------
# TC-1-17: ProductionQueue — FIFO 순서 보장
# ---------------------------------------------------------------------------
def test_production_queue_fifo_order():
    queue = ProductionQueue()
    queue.enqueue(ProductionJob(orderId="ORD-001", sampleId="S001", plannedQuantity=10, totalProductionTime=50.0))
    queue.enqueue(ProductionJob(orderId="ORD-002", sampleId="S001", plannedQuantity=5, totalProductionTime=25.0))
    queue.enqueue(ProductionJob(orderId="ORD-003", sampleId="S001", plannedQuantity=8, totalProductionTime=40.0))

    assert queue.dequeue().orderId == "ORD-001"
    assert queue.dequeue().orderId == "ORD-002"
    assert queue.dequeue().orderId == "ORD-003"


# ---------------------------------------------------------------------------
# TC-1-18: ProductionQueue — 빈 큐에서 dequeue 예외
# ---------------------------------------------------------------------------
def test_production_queue_dequeue_empty_raises_index_error():
    queue = ProductionQueue()
    with pytest.raises(IndexError):
        queue.dequeue()


# ---------------------------------------------------------------------------
# TC-1-19: ProductionQueue — peek
# ---------------------------------------------------------------------------
def test_production_queue_peek_returns_first_without_removing():
    queue = ProductionQueue()
    queue.enqueue(ProductionJob(orderId="ORD-001", sampleId="S001", plannedQuantity=10, totalProductionTime=50.0))
    queue.enqueue(ProductionJob(orderId="ORD-002", sampleId="S001", plannedQuantity=5, totalProductionTime=25.0))

    peeked = queue.peek()
    assert peeked.orderId == "ORD-001"
    assert len(queue.get_all()) == 2


# ---------------------------------------------------------------------------
# TC-1-20: ProductionQueue — 빈 큐에서 peek
# ---------------------------------------------------------------------------
def test_production_queue_peek_empty_returns_none():
    queue = ProductionQueue()
    assert queue.peek() is None


# ---------------------------------------------------------------------------
# TC-1-21: ProductionQueue — is_empty
# ---------------------------------------------------------------------------
def test_production_queue_is_empty():
    queue = ProductionQueue()
    assert queue.is_empty() is True

    queue.enqueue(ProductionJob(orderId="ORD-001", sampleId="S001", plannedQuantity=10, totalProductionTime=50.0))
    assert queue.is_empty() is False


# ---------------------------------------------------------------------------
# TC-1-22: ProductionQueue — get_all FIFO 순서
# ---------------------------------------------------------------------------
def test_production_queue_get_all_fifo_order():
    queue = ProductionQueue()
    queue.enqueue(ProductionJob(orderId="ORD-001", sampleId="S001", plannedQuantity=10, totalProductionTime=50.0))
    queue.enqueue(ProductionJob(orderId="ORD-002", sampleId="S001", plannedQuantity=5, totalProductionTime=25.0))
    queue.enqueue(ProductionJob(orderId="ORD-003", sampleId="S001", plannedQuantity=8, totalProductionTime=40.0))

    all_jobs = queue.get_all()
    assert [j.orderId for j in all_jobs] == ["ORD-001", "ORD-002", "ORD-003"]
