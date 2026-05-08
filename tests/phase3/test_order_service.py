from datetime import datetime

import pytest

from src.repositories.order_repository import OrderRepository
from src.repositories.sample_repository import SampleRepository
from src.models.order import OrderStatus
from src.services.order_service import OrderService
from src.services.sample_service import SampleService


@pytest.fixture
def sample_repo():
    return SampleRepository()


@pytest.fixture
def order_repo():
    return OrderRepository()


@pytest.fixture
def service(sample_repo, order_repo):
    return OrderService(sample_repo, order_repo)


@pytest.fixture
def registered_sample(sample_repo):
    sample_service = SampleService(sample_repo)
    return sample_service.register_sample("GaAs-100", 2.5, 0.85)


def test_tc_3_01_place_order_returns_reserved(service, registered_sample):
    order = service.place_order(registered_sample.id, "홍길동", 10)

    assert order.sampleId == registered_sample.id
    assert order.customerName == "홍길동"
    assert order.quantity == 10
    assert order.status == OrderStatus.RESERVED


def test_tc_3_02_first_order_id_is_ord_001(service, registered_sample):
    order = service.place_order(registered_sample.id, "홍길동", 5)

    assert order.id == "ORD-001"


def test_tc_3_03_unknown_sample_id_raises(service):
    with pytest.raises(ValueError, match="등록되지 않은 시료 ID입니다."):
        service.place_order("S999", "홍길동", 10)


def test_tc_3_04_empty_customer_name_raises(service, registered_sample):
    with pytest.raises(ValueError, match="고객명은 필수 입력값입니다."):
        service.place_order(registered_sample.id, "", 10)


def test_tc_3_05_whitespace_customer_name_raises(service, registered_sample):
    with pytest.raises(ValueError, match="고객명은 필수 입력값입니다."):
        service.place_order(registered_sample.id, "   ", 10)


def test_tc_3_06_quantity_zero_raises(service, registered_sample):
    with pytest.raises(ValueError, match="주문 수량은 1 이상의 정수여야 합니다."):
        service.place_order(registered_sample.id, "홍길동", 0)


def test_tc_3_07_quantity_negative_raises(service, registered_sample):
    with pytest.raises(ValueError, match="주문 수량은 1 이상의 정수여야 합니다."):
        service.place_order(registered_sample.id, "홍길동", -5)


def test_tc_3_08_quantity_one_is_allowed(service, registered_sample):
    order = service.place_order(registered_sample.id, "홍길동", 1)

    assert order.quantity == 1


def test_tc_3_09_multiple_orders_have_unique_sequential_ids(service, registered_sample):
    order1 = service.place_order(registered_sample.id, "홍길동", 5)
    order2 = service.place_order(registered_sample.id, "김철수", 3)
    order3 = service.place_order(registered_sample.id, "이영희", 7)

    assert order1.id == "ORD-001"
    assert order2.id == "ORD-002"
    assert order3.id == "ORD-003"
    assert len({order1.id, order2.id, order3.id}) == 3


def test_tc_3_10_created_at_is_datetime(service, registered_sample):
    order = service.place_order(registered_sample.id, "홍길동", 10)

    assert order.createdAt is not None
    assert isinstance(order.createdAt, datetime)


def test_tc_3_11_validation_order_sample_id_checked_first(service):
    with pytest.raises(ValueError, match="등록되지 않은 시료 ID입니다."):
        service.place_order("S999", "", 0)
