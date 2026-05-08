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

- [x] **Phase 2**: 시료 관리 서비스 + MVC 리팩터링
  - [x] `src/services/__init__.py`
  - [x] `src/services/sample_service.py` — SampleService 구현
  - [x] `tests/phase2/__init__.py`
  - [x] `tests/phase2/test_sample_service.py` — SampleService 단위 테스트 (17개, 커버리지 100%)
  - [x] `plan/design/phase2.md` — Phase 2 설계 문서
  - [x] `src/views/__init__.py` — View 패키지 초기화 (MVC 리팩터링, 구 `src/ui/` 대체)
  - [x] `src/views/display.py` — 공통 출력/입력 유틸 (`print_header`, `print_success`, `print_error`, `input_prompt`, `pause`)
  - [x] `src/views/sample_view.py` — 시료 관리 뷰 (등록/조회/검색)
  - [x] `src/controllers/__init__.py` — Controller 패키지 초기화
  - [x] `src/controllers/sample_controller.py` — 시료 관리 컨트롤러
  - [x] `main.py` — MVC 진입점으로 갱신 (KeyboardInterrupt 처리 포함)
  - [x] `dummy.py` — Faker Korean 더미 데이터 생성기
  - [x] ~~`src/ui/__init__.py`~~ — 삭제 (MVC 리팩터링)
  - [x] ~~`src/ui/display.py`~~ — 삭제 (MVC 리팩터링)
  - [x] ~~`src/ui/sample_menu.py`~~ — 삭제 (MVC 리팩터링)

- [x] **Phase 3**: 주문 접수 서비스
  - [x] `src/services/order_service.py` — OrderService 구현 (place_order())
  - [x] `src/views/order_view.py` — 주문 접수 뷰
  - [x] `src/controllers/order_controller.py` — 주문 접수 컨트롤러
  - [x] `tests/phase3/__init__.py`
  - [x] `tests/phase3/test_order_service.py` — OrderService 단위 테스트 (11개)
  - [x] `main.py` — 시료 주문 메뉴 활성화, OrderController 조립
  - [x] `dummy.py` — RESERVED H-1 해소 (OrderService.place_order() 경유 교체)
  - [x] `plan/design/phase3.md` — Phase 3 설계 문서

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
