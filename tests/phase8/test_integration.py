"""
Phase 8 Integration Tests
전체 시스템 흐름을 end-to-end 로 검증한다.
- 시나리오 A: 시료 등록 -> 주문 -> 승인(재고 부족) -> 생산 완료 -> 출고 처리
- 시나리오 B: 시료 등록 -> 주문 -> 승인(재고 충분) -> 출고 처리
- 시나리오 C: 시료 등록 -> 주문 -> 거절 (REJECTED 상태 확인)
- 모니터링: 상태별 집계 및 재고 상태 분류 검증
- 잘못된 입력 예외 처리
- 빈 큐에서 생산 완료 시도 ValueError 확인
"""
import math
import pytest

from src.repositories.sample_repository import SampleRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.services.sample_service import SampleService
from src.services.order_service import OrderService
from src.services.approval_service import ApprovalService
from src.services.production_service import ProductionService
from src.services.shipment_service import ShipmentService
from src.services.monitoring_service import MonitoringService
from src.models.order import OrderStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_repo(db_path):
    return SampleRepository(db_path=db_path)


@pytest.fixture
def order_repo(db_path):
    return OrderRepository(db_path=db_path)


@pytest.fixture
def prod_queue(db_path):
    return ProductionQueue(db_path=db_path)


@pytest.fixture
def sample_svc(sample_repo):
    return SampleService(sample_repo)


@pytest.fixture
def order_svc(sample_repo, order_repo):
    return OrderService(sample_repo, order_repo)


@pytest.fixture
def approval_svc(sample_repo, order_repo, prod_queue):
    return ApprovalService(sample_repo, order_repo, prod_queue)


@pytest.fixture
def production_svc(sample_repo, order_repo, prod_queue):
    return ProductionService(sample_repo, order_repo, prod_queue)


@pytest.fixture
def shipment_svc(sample_repo, order_repo):
    return ShipmentService(sample_repo, order_repo)


@pytest.fixture
def monitoring_svc(sample_repo, order_repo):
    return MonitoringService(sample_repo, order_repo)


# ---------------------------------------------------------------------------
# 시나리오 A: 시료 등록 -> 주문 -> 승인(재고 부족) -> 생산 완료 -> 출고 처리
# ---------------------------------------------------------------------------

class TestScenarioA:
    """재고 부족 경로: RESERVED -> PRODUCING -> CONFIRMED -> RELEASED"""

    def test_A01_sample_registration(self, sample_svc):
        """시료 등록 후 조회 가능"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        assert sample.id == "S001"
        assert sample.name == "SiC-300"
        assert sample.stock == 0

    def test_A02_order_placed_as_reserved(self, sample_svc, order_svc):
        """주문 접수 시 상태가 RESERVED"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        assert order.status == OrderStatus.RESERVED

    def test_A03_approval_with_no_stock_produces(self, sample_svc, order_svc, approval_svc):
        """재고 0 상태에서 주문 승인 시 PRODUCING으로 전환"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approved = approval_svc.approve_order(order.id)
        assert approved.status == OrderStatus.PRODUCING

    def test_A04_production_job_enqueued_on_approval(self, sample_svc, order_svc, approval_svc, prod_queue):
        """재고 부족 승인 시 생산 큐에 job이 등록됨"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)
        assert not prod_queue.is_empty()
        job = prod_queue.peek()
        assert job.orderId == order.id
        assert job.sampleId == sample.id

    def test_A05_planned_quantity_formula(self, sample_svc, order_svc, approval_svc, prod_queue):
        """실 생산량 = ceil(부족분 / (수율 * 0.9)) 공식 검증 — stock=0, qty=10, yield=0.8"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)
        job = prod_queue.peek()
        expected = math.ceil(10 / (0.8 * 0.9))  # = 14
        assert job.plannedQuantity == expected

    def test_A06_total_production_time_formula(self, sample_svc, order_svc, approval_svc, prod_queue):
        """총 생산 시간 = 평균 생산시간 * 실 생산량"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)
        job = prod_queue.peek()
        expected_qty = math.ceil(10 / (0.8 * 0.9))
        assert job.totalProductionTime == pytest.approx(5.5 * expected_qty)

    def test_A07_complete_production_transitions_to_confirmed(
        self, sample_svc, order_svc, approval_svc, production_svc, order_repo
    ):
        """생산 완료 처리 시 주문 상태가 CONFIRMED로 전환"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)
        completed = production_svc.complete_production()
        assert completed.status == OrderStatus.CONFIRMED
        # DB에서 다시 조회해도 CONFIRMED 유지
        db_order = order_repo.get(order.id)
        assert db_order.status == OrderStatus.CONFIRMED

    def test_A08_complete_production_updates_stock(
        self, sample_svc, order_svc, approval_svc, production_svc, sample_repo
    ):
        """생산 완료 후 stock += 실 생산량 반영"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)
        expected_qty = math.ceil(10 / (0.8 * 0.9))
        production_svc.complete_production()
        updated = sample_repo.get(sample.id)
        assert updated.stock == expected_qty  # 초기 재고 0 + 실 생산량

    def test_A09_production_queue_empty_after_complete(
        self, sample_svc, order_svc, approval_svc, production_svc, prod_queue
    ):
        """생산 완료 후 큐가 비어있어야 함"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)
        production_svc.complete_production()
        assert prod_queue.is_empty()

    def test_A10_shipment_release_after_production(
        self, sample_svc, order_svc, approval_svc, production_svc, shipment_svc, sample_repo
    ):
        """생산 완료 후 출고 처리 시 RELEASED로 전환 및 stock 차감"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)
        expected_qty = math.ceil(10 / (0.8 * 0.9))
        production_svc.complete_production()

        released = shipment_svc.release_order(order.id)
        assert released.status == OrderStatus.RELEASED

        updated = sample_repo.get(sample.id)
        # stock = 실 생산량 - 주문 수량
        assert updated.stock == expected_qty - 10

    def test_A11_full_scenario_stock_deficit_with_partial_initial_stock(
        self, sample_svc, order_svc, approval_svc, production_svc, shipment_svc, sample_repo
    ):
        """초기 재고 3, 주문 10 — 부족분 7 기준 생산량 계산 및 전체 흐름"""
        # 시료 등록 (stock=0)
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        # 재고를 3으로 수동 설정
        sample_repo.update_stock(sample.id, 3)

        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        # 승인: 재고 3 < 주문 10 → 부족분 7
        approved = approval_svc.approve_order(order.id)
        assert approved.status == OrderStatus.PRODUCING

        expected_qty = math.ceil(7 / (0.8 * 0.9))  # ceil(9.722) = 10
        assert expected_qty == 10

        # 생산 완료: stock = 3 + 10 = 13
        production_svc.complete_production()
        stock_after_prod = sample_repo.get(sample.id).stock
        assert stock_after_prod == 13

        # 출고: stock = 13 - 10 = 3
        shipment_svc.release_order(order.id)
        stock_after_release = sample_repo.get(sample.id).stock
        assert stock_after_release == 3


# ---------------------------------------------------------------------------
# 시나리오 B: 시료 등록 -> 주문 -> 승인(재고 충분) -> 출고 처리
# ---------------------------------------------------------------------------

class TestScenarioB:
    """재고 충분 경로: RESERVED -> CONFIRMED -> RELEASED"""

    def test_B01_approval_with_sufficient_stock_confirms_directly(
        self, sample_svc, order_svc, approval_svc, sample_repo
    ):
        """재고 충분 시 승인하면 CONFIRMED로 즉시 전환 (생산 큐 미등록)"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 50)

        order = order_svc.place_order(sample.id, "서울대학교 연구실", 20)
        confirmed = approval_svc.approve_order(order.id)
        assert confirmed.status == OrderStatus.CONFIRMED

    def test_B02_approval_sufficient_stock_no_production_job(
        self, sample_svc, order_svc, approval_svc, sample_repo, prod_queue
    ):
        """재고 충분 승인 시 생산 큐에 등록되지 않음"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 50)
        order = order_svc.place_order(sample.id, "서울대학교 연구실", 20)
        approval_svc.approve_order(order.id)
        assert prod_queue.is_empty()

    def test_B03_approval_sufficient_stock_does_not_deduct_stock_yet(
        self, sample_svc, order_svc, approval_svc, sample_repo
    ):
        """승인 시점에는 재고 차감 없음 (출고 시점에 차감)"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 50)
        order = order_svc.place_order(sample.id, "서울대학교 연구실", 20)
        approval_svc.approve_order(order.id)
        assert sample_repo.get(sample.id).stock == 50

    def test_B04_shipment_deducts_stock_and_sets_released(
        self, sample_svc, order_svc, approval_svc, shipment_svc, sample_repo
    ):
        """출고 처리 후 stock -= 주문 수량, 상태 RELEASED"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 50)
        order = order_svc.place_order(sample.id, "서울대학교 연구실", 20)
        approval_svc.approve_order(order.id)

        released = shipment_svc.release_order(order.id)
        assert released.status == OrderStatus.RELEASED
        assert sample_repo.get(sample.id).stock == 30

    def test_B05_boundary_stock_equals_quantity_confirmed(
        self, sample_svc, order_svc, approval_svc, sample_repo, prod_queue
    ):
        """경계값: 재고 == 주문 수량 → CONFIRMED (AP-03 요건)"""
        sample = sample_svc.register_sample("GaAs-100", 2.5, 0.85)
        sample_repo.update_stock(sample.id, 5)
        order = order_svc.place_order(sample.id, "ABC 팹리스", 5)
        confirmed = approval_svc.approve_order(order.id)
        assert confirmed.status == OrderStatus.CONFIRMED
        assert prod_queue.is_empty()

    def test_B06_confirmed_orders_appear_in_shipment_list(
        self, sample_svc, order_svc, approval_svc, shipment_svc, sample_repo
    ):
        """CONFIRMED 주문이 출고 대기 목록에 포함됨"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 50)
        order = order_svc.place_order(sample.id, "서울대학교 연구실", 10)
        approval_svc.approve_order(order.id)

        confirmed_list = shipment_svc.get_confirmed_orders()
        assert any(o.id == order.id for o in confirmed_list)


# ---------------------------------------------------------------------------
# 시나리오 C: 시료 등록 -> 주문 -> 거절 (REJECTED 상태 확인)
# ---------------------------------------------------------------------------

class TestScenarioC:
    """거절 경로: RESERVED -> REJECTED"""

    def test_C01_reject_order_sets_rejected(self, sample_svc, order_svc, approval_svc):
        """주문 거절 시 REJECTED로 전환"""
        sample = sample_svc.register_sample("GaN-200", 6.0, 0.7)
        order = order_svc.place_order(sample.id, "KAIST 연구팀", 30)
        rejected = approval_svc.reject_order(order.id)
        assert rejected.status == OrderStatus.REJECTED

    def test_C02_reject_does_not_enqueue_production(
        self, sample_svc, order_svc, approval_svc, prod_queue
    ):
        """거절 시 생산 큐에 등록되지 않음"""
        sample = sample_svc.register_sample("GaN-200", 6.0, 0.7)
        order = order_svc.place_order(sample.id, "KAIST 연구팀", 30)
        approval_svc.reject_order(order.id)
        assert prod_queue.is_empty()

    def test_C03_reject_does_not_change_stock(
        self, sample_svc, order_svc, approval_svc, sample_repo
    ):
        """거절 시 재고 변화 없음"""
        sample = sample_svc.register_sample("GaN-200", 6.0, 0.7)
        sample_repo.update_stock(sample.id, 10)
        order = order_svc.place_order(sample.id, "KAIST 연구팀", 5)
        approval_svc.reject_order(order.id)
        assert sample_repo.get(sample.id).stock == 10

    def test_C04_rejected_order_not_in_confirmed_list(
        self, sample_svc, order_svc, approval_svc, shipment_svc
    ):
        """거절된 주문은 출고 대기 목록에 나타나지 않음"""
        sample = sample_svc.register_sample("GaN-200", 6.0, 0.7)
        order = order_svc.place_order(sample.id, "KAIST 연구팀", 30)
        approval_svc.reject_order(order.id)
        confirmed_list = shipment_svc.get_confirmed_orders()
        assert not any(o.id == order.id for o in confirmed_list)


# ---------------------------------------------------------------------------
# 모니터링: 상태별 집계 및 재고 상태 분류 검증
# ---------------------------------------------------------------------------

class TestMonitoring:
    """MN-01~MN-04 요건 검증"""

    def test_M01_order_summary_excludes_rejected(
        self, sample_svc, order_svc, approval_svc, monitoring_svc
    ):
        """REJECTED 주문은 모니터링 집계에서 제외됨 (MN-01)"""
        sample = sample_svc.register_sample("GaN-200", 6.0, 0.7)
        order = order_svc.place_order(sample.id, "고객A", 5)
        approval_svc.reject_order(order.id)

        summary = monitoring_svc.get_order_summary()
        counts = summary["counts"]
        # REJECTED 키는 아예 없거나 0이어야 함
        assert counts.get("REJECTED", 0) == 0

    def test_M02_order_summary_counts_by_status(
        self, sample_svc, order_svc, approval_svc, monitoring_svc, sample_repo
    ):
        """상태별 주문 수 집계 검증 (MN-02)"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 100)

        # RESERVED 2건 생성
        o1 = order_svc.place_order(sample.id, "고객A", 5)
        o2 = order_svc.place_order(sample.id, "고객B", 5)
        # o2 승인 -> CONFIRMED (재고 충분)
        approval_svc.approve_order(o2.id)

        summary = monitoring_svc.get_order_summary()
        counts = summary["counts"]
        assert counts["RESERVED"] == 1
        assert counts["CONFIRMED"] == 1

    def test_M03_order_summary_contains_order_objects(
        self, sample_svc, order_svc, monitoring_svc
    ):
        """집계 결과에 주문 객체 목록 포함 검증"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        order = order_svc.place_order(sample.id, "고객A", 5)

        summary = monitoring_svc.get_order_summary()
        reserved_orders = summary["orders"]["RESERVED"]
        assert any(o.id == order.id for o in reserved_orders)

    def test_M04_stock_status_surplus(
        self, sample_svc, order_svc, monitoring_svc, sample_repo
    ):
        """재고 > 0, PRODUCING 주문 없음 -> 여유 (MN-04)"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 45)

        statuses = monitoring_svc.get_stock_status()
        entry = next(e for e in statuses if e["sample"].id == sample.id)
        assert entry["status"] == "여유"

    def test_M05_stock_status_shortage(
        self, sample_svc, order_svc, approval_svc, monitoring_svc, sample_repo
    ):
        """재고 > 0, PRODUCING 주문 있음 -> 부족 (MN-04)"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)
        sample_repo.update_stock(sample.id, 3)

        order = order_svc.place_order(sample.id, "한국반도체연구소", 10)
        approval_svc.approve_order(order.id)  # 재고 3 < 주문 10 -> PRODUCING

        statuses = monitoring_svc.get_stock_status()
        entry = next(e for e in statuses if e["sample"].id == sample.id)
        assert entry["status"] == "부족"

    def test_M06_stock_status_depleted(
        self, sample_svc, monitoring_svc
    ):
        """재고 == 0 -> 고갈 (MN-04)"""
        sample = sample_svc.register_sample("GaAs-100", 2.5, 0.85)
        # stock 기본값 0

        statuses = monitoring_svc.get_stock_status()
        entry = next(e for e in statuses if e["sample"].id == sample.id)
        assert entry["status"] == "고갈"

    def test_M07_producing_order_appears_in_producing_count(
        self, sample_svc, order_svc, approval_svc, monitoring_svc
    ):
        """PRODUCING 상태 주문 집계 검증"""
        sample = sample_svc.register_sample("GaAs-100", 2.5, 0.85)
        order = order_svc.place_order(sample.id, "ABC 팹리스", 5)
        approval_svc.approve_order(order.id)  # stock=0, 부족 -> PRODUCING

        summary = monitoring_svc.get_order_summary()
        assert summary["counts"]["PRODUCING"] == 1


# ---------------------------------------------------------------------------
# 잘못된 입력 예외 처리
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """경계값 및 예외 케이스 검증"""

    def test_E01_order_with_unregistered_sample_raises(self, order_svc):
        """미등록 시료 ID로 주문 시도 → ValueError (OR-01)"""
        with pytest.raises(ValueError, match="등록되지 않은 시료 ID입니다."):
            order_svc.place_order("S999", "고객A", 5)

    def test_E02_shipment_on_non_confirmed_order_raises(
        self, sample_svc, order_svc, shipment_svc
    ):
        """CONFIRMED 아닌 주문(RESERVED) 출고 시도 → ValueError (RL-02 조건)"""
        sample = sample_svc.register_sample("GaN-200", 6.0, 0.7)
        order = order_svc.place_order(sample.id, "고객A", 5)
        # 승인하지 않은 RESERVED 상태 그대로 출고 시도
        with pytest.raises(ValueError, match="CONFIRMED 상태의 주문만 출고 처리 가능합니다."):
            shipment_svc.release_order(order.id)

    def test_E03_shipment_on_producing_order_raises(
        self, sample_svc, order_svc, approval_svc, shipment_svc
    ):
        """PRODUCING 상태 주문 출고 시도 → ValueError"""
        sample = sample_svc.register_sample("GaN-200", 6.0, 0.7)
        order = order_svc.place_order(sample.id, "고객A", 30)
        approval_svc.approve_order(order.id)  # stock=0 -> PRODUCING
        with pytest.raises(ValueError, match="CONFIRMED 상태의 주문만 출고 처리 가능합니다."):
            shipment_svc.release_order(order.id)

    def test_E04_shipment_on_nonexistent_order_raises(self, shipment_svc):
        """존재하지 않는 주문 ID 출고 시도 → ValueError"""
        with pytest.raises(ValueError, match="존재하지 않는 주문 ID입니다."):
            shipment_svc.release_order("ORD-999")

    def test_E05_approve_nonexistent_order_raises(self, approval_svc):
        """존재하지 않는 주문 ID 승인 시도 → ValueError"""
        with pytest.raises(ValueError, match="존재하지 않는 주문 ID입니다."):
            approval_svc.approve_order("ORD-999")

    def test_E06_reject_nonexistent_order_raises(self, approval_svc):
        """존재하지 않는 주문 ID 거절 시도 → ValueError"""
        with pytest.raises(ValueError, match="존재하지 않는 주문 ID입니다."):
            approval_svc.reject_order("ORD-999")

    def test_E07_approve_already_confirmed_order_raises(
        self, sample_svc, order_svc, approval_svc, sample_repo
    ):
        """이미 CONFIRMED 주문 재승인 시도 → ValueError"""
        sample = sample_svc.register_sample("Si-Wafer-200", 3.0, 0.9)
        sample_repo.update_stock(sample.id, 50)
        order = order_svc.place_order(sample.id, "고객A", 10)
        approval_svc.approve_order(order.id)
        with pytest.raises(ValueError, match="RESERVED 상태의 주문만 처리 가능합니다."):
            approval_svc.approve_order(order.id)

    def test_E08_register_sample_empty_name_raises(self, sample_svc):
        """시료 이름 빈값 등록 시도 → ValueError (SM-02)"""
        with pytest.raises(ValueError, match="시료 이름은 필수 입력값입니다."):
            sample_svc.register_sample("", 2.5, 0.85)

    def test_E09_register_sample_zero_production_time_raises(self, sample_svc):
        """평균 생산시간 0 등록 시도 → ValueError (SM-03)"""
        with pytest.raises(ValueError, match="평균 생산시간은 0보다 커야 합니다."):
            sample_svc.register_sample("GaAs-100", 0, 0.85)

    def test_E10_register_sample_yield_out_of_range_raises(self, sample_svc):
        """수율 범위 위반 등록 시도 → ValueError (SM-04)"""
        with pytest.raises(ValueError, match="수율은 0 초과 1 이하여야 합니다."):
            sample_svc.register_sample("GaAs-100", 2.5, 0.0)
        with pytest.raises(ValueError, match="수율은 0 초과 1 이하여야 합니다."):
            sample_svc.register_sample("GaAs-100", 2.5, 1.1)

    def test_E11_order_quantity_zero_raises(self, sample_svc, order_svc):
        """주문 수량 0 → ValueError (OR-02)"""
        sample = sample_svc.register_sample("GaAs-100", 2.5, 0.85)
        with pytest.raises(ValueError, match="주문 수량은 1 이상의 정수여야 합니다."):
            order_svc.place_order(sample.id, "고객A", 0)

    def test_E12_order_empty_customer_name_raises(self, sample_svc, order_svc):
        """고객명 빈값 → ValueError (OR-03)"""
        sample = sample_svc.register_sample("GaAs-100", 2.5, 0.85)
        with pytest.raises(ValueError, match="고객명은 필수 입력값입니다."):
            order_svc.place_order(sample.id, "", 5)


# ---------------------------------------------------------------------------
# 빈 큐에서 생산 완료 시도 ValueError 확인
# ---------------------------------------------------------------------------

class TestProductionEdgeCases:
    """PL-05: 빈 큐 생산 완료 시도"""

    def test_P01_complete_production_on_empty_queue_raises_value_error(
        self, production_svc
    ):
        """생산 큐가 비어있을 때 complete_production 호출 시 ValueError (PL-05)"""
        with pytest.raises(ValueError, match="진행 중인 생산 작업이 없습니다."):
            production_svc.complete_production()

    def test_P02_get_production_status_empty_queue(self, production_svc):
        """생산 큐 비어있을 때 상태 조회: current=None, queue=[] (PL-04)"""
        status = production_svc.get_production_status()
        assert status["current"] is None
        assert status["queue"] == []

    def test_P03_production_status_shows_current_and_queue(
        self, sample_svc, order_svc, approval_svc, production_svc
    ):
        """생산 큐에 2건 등록 시 첫번째가 current, 나머지가 queue"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)

        o1 = order_svc.place_order(sample.id, "고객A", 10)
        o2 = order_svc.place_order(sample.id, "고객B", 5)
        approval_svc.approve_order(o1.id)  # PRODUCING (stock=0)
        approval_svc.approve_order(o2.id)  # PRODUCING (stock still 0)

        status = production_svc.get_production_status()
        assert status["current"] is not None
        assert status["current"]["job"].orderId == o1.id
        assert len(status["queue"]) == 1
        assert status["queue"][0]["job"].orderId == o2.id

    def test_P04_fifo_production_order(
        self, sample_svc, order_svc, approval_svc, production_svc, order_repo
    ):
        """생산 큐 FIFO 순서 검증: 먼저 승인된 주문이 먼저 완료됨"""
        sample = sample_svc.register_sample("SiC-300", 5.5, 0.8)

        o1 = order_svc.place_order(sample.id, "고객A", 10)
        o2 = order_svc.place_order(sample.id, "고객B", 5)
        approval_svc.approve_order(o1.id)
        approval_svc.approve_order(o2.id)

        first = production_svc.complete_production()
        assert first.id == o1.id

        second = production_svc.complete_production()
        assert second.id == o2.id
