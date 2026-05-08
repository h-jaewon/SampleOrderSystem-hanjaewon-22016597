# TASKS.md — 태스크 진행 상황

> 관리 주체: SubAgent5 (repository-governance) | 최종 갱신: 2026-05-08

---

## Phase 구현 현황

- [x] **Phase 1**: 도메인 모델 및 저장소 기반 구축
  - [x] `src/models/sample.py` — Sample 데이터 클래스
  - [x] `src/models/order.py` — OrderStatus Enum + Order 데이터 클래스
  - [x] `src/models/production_job.py` — ProductionJob 데이터 클래스
  - [x] `src/repositories/sample_repository.py` — 인메모리 시료 저장소
  - [x] `src/repositories/order_repository.py` — 인메모리 주문 저장소
  - [x] `src/repositories/production_queue.py` — FIFO 생산 대기 큐
  - [x] `tests/phase1/test_models.py` — 22개 단위 테스트 (커버리지 99%)
  - [x] `plan/design/phase1.md` — Phase 1 설계 문서
  - [x] `pytest.ini`, `requirements.txt` 설정

- [ ] **Phase 2**: 시료 관리 서비스
  - [ ] `src/services/__init__.py`
  - [ ] `src/services/sample_service.py` — SampleService 구현
  - [ ] `tests/phase2/test_sample_service.py` — SampleService 단위 테스트

- [ ] **Phase 3**: 주문 접수 서비스
  - [ ] `src/services/order_service.py`
  - [ ] `tests/phase3/test_order_service.py`

- [ ] **Phase 4**: 주문 승인/거절 서비스
  - [ ] `src/services/approval_service.py`
  - [ ] `tests/phase4/test_approval_service.py`

- [ ] **Phase 5**: 모니터링 서비스
  - [ ] `src/services/monitoring_service.py`
  - [ ] `tests/phase5/test_monitoring_service.py`

- [ ] **Phase 6**: 생산 라인 서비스
  - [ ] `src/services/production_service.py`
  - [ ] `tests/phase6/test_production_service.py`

- [ ] **Phase 7**: 출고 서비스
  - [ ] `src/services/shipment_service.py`
  - [ ] `tests/phase7/test_shipment_service.py`

- [ ] **Phase 8**: UI 및 통합 테스트
  - [ ] `src/ui/` 전체
  - [ ] `tests/phase8/test_integration.py`
