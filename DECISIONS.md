# DECISIONS.md — 아키텍처 결정 기록 (ADR)

> 관리 주체: SubAgent5 (repository-governance) | 최종 갱신: 2026-05-08

---

## ADR-001: 도메인 모델 구현 방식 — `dataclasses.dataclass` 사용

- **날짜:** 2026-05-08
- **Phase:** Phase 1
- **결정:** 모든 도메인 모델(`Sample`, `Order`, `ProductionJob`)을 Python 표준 라이브러리 `dataclasses.dataclass`로 구현한다.
- **이유:**
  - 외부 라이브러리 의존 없이 속성 정의, `__init__`, `__repr__`, `__eq__` 자동 생성 가능.
  - `frozen=False`(기본값)로 상태 변경이 필요한 `Order.status` 필드를 허용.
  - `field(default_factory=...)` 를 통해 인스턴스별 독립적 기본값 설정 가능 (`Order.createdAt`).
- **대안:** `__init__` 직접 작성, Pydantic 사용 — 표준 라이브러리 우선 원칙으로 배제.

---

## ADR-002: `Order.createdAt` 기본값 — `field(default_factory=datetime.now)`

- **날짜:** 2026-05-08
- **Phase:** Phase 1
- **결정:** `Order.createdAt`의 기본값을 `field(default_factory=datetime.now)`로 설정한다.
- **이유:**
  - `default=datetime.now()`는 클래스 정의 시점의 단일 datetime 객체를 모든 인스턴스가 공유하는 문제 발생.
  - `default_factory=datetime.now`는 각 인스턴스 생성 시 `datetime.now()`를 호출하여 독립적인 타임스탬프를 부여한다.
- **영향 파일:** `src/models/order.py`

---

## ADR-003: 생산 대기 큐 자료구조 — `collections.deque` FIFO

- **날짜:** 2026-05-08
- **Phase:** Phase 1
- **결정:** `ProductionQueue`의 내부 자료구조로 `collections.deque`를 사용하고, `append()`(오른쪽 추가) + `popleft()`(왼쪽 제거)로 FIFO를 구현한다.
- **이유:**
  - `list.pop(0)`은 O(n) 시간 복잡도. `deque.popleft()`는 O(1).
  - 표준 라이브러리 내 큐 적합 자료구조로 큐 의미론(FIFO)이 명확하다.
- **대안:** `queue.Queue` — 스레드 안전성이 불필요한 단일 스레드 환경에서 오버헤드.
- **영향 파일:** `src/repositories/production_queue.py`

---

## ADR-004: 예외 타입 선택 — 저장소 중복 ID

- **날짜:** 2026-05-08
- **Phase:** Phase 1
- **결정:** 저장소(`SampleRepository`, `OrderRepository`)에서 중복 ID로 `add()` 시 `ValueError`를 발생시킨다.
- **이유:**
  - 잘못된 값(이미 존재하는 ID)을 전달한 경우로 Python 표준 예외 `ValueError` 의미론에 부합.
  - 커스텀 예외는 Phase 2 이후 서비스 레이어에서 필요 시 도입.
- **메시지 형식:** `"이미 존재하는 {엔티티} ID입니다: {id}"`
- **영향 파일:** `src/repositories/sample_repository.py`, `src/repositories/order_repository.py`

---

## ADR-005: 예외 타입 선택 — 빈 큐 dequeue

- **날짜:** 2026-05-08
- **Phase:** Phase 1
- **결정:** `ProductionQueue.dequeue()` 시 큐가 비어있으면 `IndexError`를 발생시킨다.
- **이유:**
  - `collections.deque`의 `popleft()` 빈 큐 동작과 일관성 유지.
  - 인덱스/시퀀스 접근 실패에 해당하는 표준 예외 의미론에 부합.
- **메시지 형식:** `"생산 큐가 비어있습니다."`
- **영향 파일:** `src/repositories/production_queue.py`

---

## ADR-006: 유효성 검사 책임 분리 — 모델 vs 서비스

- **날짜:** 2026-05-08
- **Phase:** Phase 1 (결정), Phase 2 (적용)
- **결정:** Phase 1 도메인 모델은 유효성 검사를 수행하지 않는다. 입력값 검증(빈 문자열, 범위 초과 등)은 Phase 2+ 서비스 레이어의 책임으로 위임한다.
- **이유:**
  - 단일 책임 원칙(SRP): 모델은 데이터 보유, 서비스는 비즈니스 규칙 적용.
  - Phase 1 범위를 최소화하여 안정적 기반 마련.
- **영향:** `src/models/` 전체 — `__post_init__` 검증 없음.
- **Phase 2 적용 결과:** `SampleService.register_sample()`에서 `name`, `avgProductionTime`, `yield_` 세 파라미터에 대한 유효성 검사를 순서대로 수행하며 위반 시 즉시 `ValueError`를 발생시킨다.

---

## ADR-007: SampleService 의존성 주입 방식 — 생성자 주입

- **날짜:** 2026-05-08
- **Phase:** Phase 2
- **결정:** `SampleService`는 `SampleRepository` 인스턴스를 생성자(`__init__`)에서 파라미터로 주입받는다. 서비스 내부에서 저장소를 직접 생성하지 않는다.
- **이유:**
  - 테스트 격리: 각 테스트 케이스가 독립적인 `SampleRepository` 인스턴스를 주입하여 상태 공유 없이 실행 가능.
  - 느슨한 결합(Loose Coupling): 서비스가 저장소 구현 세부에 의존하지 않아 향후 교체 또는 Mock 적용 용이.
  - 표준 DI 패턴 준수: 외부 프레임워크 없이 Python 기본 생성자 파라미터로 의존성 주입 구현.
- **대안:** 서비스 내부에서 `SampleRepository()` 직접 인스턴스화 — 테스트 격리 불가로 배제.
- **영향 파일:** `src/services/sample_service.py`

---

## ADR-008: 시료 ID 자동 생성 전략 — `len(get_all()) + 1` 기반 순번

- **날짜:** 2026-05-08
- **Phase:** Phase 2
- **결정:** `register_sample()` 내부에서 `f"S{len(self._sample_repository.get_all()) + 1:03d}"` 형식으로 ID를 자동 생성한다.
- **이유:**
  - PRD에서 시료 삭제 기능을 정의하지 않으므로, 등록 수 기반 단조 증가 순번이 중복 없이 고유함을 보장한다.
  - 별도 카운터 상태 관리 없이 저장소 크기에서 직접 순번을 도출하여 구현 단순화.
  - `SampleRepository.add()`가 중복 ID에 대해 `ValueError`를 발생시켜(ADR-004) 이중 안전망 역할을 한다.
- **형식:** `S{순번:03d}` — 예) `S001`, `S002`, `S999`
- **제약:** 시료 삭제 기능이 추가될 경우 이 전략을 재검토해야 한다.
- **영향 파일:** `src/services/sample_service.py`

---

## ADR-009: UI 공통 유틸 분리 — `display.py` 단일 모듈

- **날짜:** 2026-05-08
- **Phase:** Phase 2 UI
- **결정:** 출력/입력 관련 모든 공통 함수(`print_header`, `print_divider`, `print_success`, `print_error`, `input_prompt`, `pause`)를 `src/ui/display.py` 한 모듈에 집중시킨다.
- **이유:**
  - 각 메뉴 모듈(`sample_menu.py` 등)이 동일한 스타일의 출력을 재사용할 수 있어 일관된 UI 보장.
  - 향후 출력 형식 변경 시 `display.py` 한 곳만 수정하면 전체 UI에 반영 가능(단일 변경점 원칙).
  - `DIVIDER` 상수를 모듈 수준에서 정의하여 길이 변경도 한 곳에서 관리.
- **대안:** 각 메뉴 파일 내 인라인 출력 — 중복 코드 증가 및 스타일 불일치 위험으로 배제.
- **영향 파일:** `src/ui/display.py`, `src/ui/sample_menu.py`, `main.py`

---

## ADR-010: `pause()` 메시지 파라미터화

- **날짜:** 2026-05-08
- **Phase:** Phase 2 UI
- **결정:** `display.pause()` 함수의 안내 메시지를 하드코딩하지 않고, `message: str = "이전 메뉴로 돌아갑니다"` 파라미터로 받는다.
- **이유:**
  - 호출 맥락에 따라 "이전 메뉴로 돌아갑니다", "계속하려면 엔터를 누르세요" 등 다양한 메시지가 필요.
  - 기본값 제공으로 대부분의 호출 지점에서 인자 생략 가능 — 하위 호환성 유지.
  - SubAgent4 High-01 이슈 수정 결과로 확정.
- **형식:** `input(f"\n  엔터를 누르면 {message}.")`
- **영향 파일:** `src/ui/display.py`

---

## ADR-011: 메인 진입점 KeyboardInterrupt 처리

- **날짜:** 2026-05-08
- **Phase:** Phase 2 UI
- **결정:** `main.py`의 `if __name__ == "__main__"` 블록에서 `main()` 호출을 `try/except KeyboardInterrupt`로 감싸 Ctrl+C 입력 시 안내 메시지를 출력하고 정상 종료한다.
- **이유:**
  - Ctrl+C를 누르면 Python 기본 동작으로 `KeyboardInterrupt` 스택 트레이스가 터미널에 출력되어 사용자 혼란 유발.
  - 안내 메시지(`시스템을 종료합니다.`)를 출력하고 종료함으로써 CLI 사용성 개선.
  - SubAgent4 High-01 이슈 수정 결과로 확정.
- **영향 파일:** `main.py`

---

## ADR-012: MVC 패턴 도입 — `src/ui/` → `src/views/` + `src/controllers/`

- **날짜:** 2026-05-08
- **Phase:** Phase 2 MVC 리팩터링
- **결정:** 기존 `src/ui/` 패키지를 MVC 패턴에 따라 `src/views/`(화면 출력 담당)와 `src/controllers/`(비즈니스 흐름 제어 담당)로 분리한다.
- **이유:**
  - mvc-poc 브랜치에서 검증된 패턴을 본 브랜치에 적용하여 관심사 분리(SoC) 강화.
  - 뷰(View)는 출력만, 컨트롤러(Controller)는 서비스 호출 및 흐름 제어만 담당 — 단일 책임 원칙(SRP) 준수.
  - Phase 3 이후 주문·승인·모니터링 메뉴 추가 시 각 도메인별 controller/view 파일을 독립적으로 확장 가능.
- **대안:** `src/ui/` 구조 유지 — 뷰·컨트롤러 역할 혼재로 향후 유지보수 복잡도 증가 우려로 배제.
- **영향 파일:** `src/views/__init__.py`, `src/views/display.py`, `src/views/sample_view.py`, `src/controllers/__init__.py`, `src/controllers/sample_controller.py`, `main.py`
- **제거 파일:** `src/ui/__init__.py`, `src/ui/display.py`, `src/ui/sample_menu.py`

---

## ADR-013: 모니터링 뷰 유니코드 테이블 — `rich` 라이브러리 활용

- **날짜:** 2026-05-08
- **Phase:** Phase 2 MVC 리팩터링 (monitor-poc 참고)
- **결정:** 향후 모니터링 뷰(`src/views/monitoring_view.py`)에서 유니코드 테이블 출력이 필요할 경우 `rich` 라이브러리를 사용한다.
- **이유:**
  - monitor-poc 브랜치에서 검증된 유니코드 테이블 렌더링 품질이 CLI 사용성을 크게 개선.
  - `rich.table.Table`은 컬럼 정렬, 색상, 테두리 스타일 등을 선언적으로 설정 가능.
  - `requirements.txt`에 `rich` 패키지 버전 고정 추가 예정.
- **대안:** 순수 Python f-string 정렬 — 한글 가변 폭 문자로 인한 정렬 오류 발생 위험으로 배제.
- **영향 파일:** `requirements.txt`, `src/views/monitoring_view.py` (Phase 5 이후 생성 예정)

---

## ADR-014: Faker Korean 더미 데이터 생성기 — `dummy.py`

- **날짜:** 2026-05-08
- **Phase:** Phase 2 MVC 리팩터링
- **결정:** `Faker('ko_KR')` 로케일을 사용하는 `dummy.py` 스크립트를 프로젝트 루트에 추가하여 개발·테스트용 한국어 더미 데이터를 생성한다.
- **이유:**
  - 시료 이름, 담당자 등 한국어 필드가 다수 포함된 도메인 특성상 Korean 로케일 Faker가 현실적인 테스트 데이터 제공.
  - `dummy.py`를 독립 스크립트로 분리하여 실제 서비스 코드와 테스트 코드에 영향 없이 실행 가능.
  - SubAgent3 판정에서 `dummy.py` 정상 동작 확인.
- **대안:** 고정 문자열 하드코딩 — 다양한 입력값 검증 부족으로 배제.
- **영향 파일:** `dummy.py`, `requirements.txt` (`faker` 패키지 버전 고정)

---

## ADR-015: OrderService 설계 — SampleRepository 공유 및 생성자 주입

- **날짜:** 2026-05-08
- **Phase:** Phase 3
- **결정:** `OrderService`는 생성자에서 `SampleRepository`와 `OrderRepository` 두 인스턴스를 주입받는다. `main.py`에서 생성된 단일 `SampleRepository` 인스턴스를 `SampleService`와 `OrderService` 모두에 전달(공유)한다.
- **이유:**
  - `place_order()` 시 `sample_id` 유효성 검사를 위해 `SampleRepository.get()` 호출이 필요하다.
  - `SampleRepository`를 공유하지 않으면 `SampleService`에서 등록한 시료가 `OrderService`에서 조회되지 않아 주문 접수가 불가능해진다.
  - 생성자 주입으로 테스트 격리 보장: 각 테스트 케이스가 독립적인 저장소 인스턴스를 주입하여 상태 공유 없이 실행 가능.
  - SampleService의 ADR-007과 동일한 DI 패턴을 일관되게 적용.
- **대안:** OrderService 내부에서 SampleRepository를 직접 생성 — 테스트 격리 불가 및 main.py와의 인스턴스 불일치로 배제.
- **의존성 주입 구조:**
  ```
  main()
  ├── SampleRepository (단일 인스턴스)
  ├── OrderRepository (단일 인스턴스)
  ├── SampleService(sample_repository)
  └── OrderService(sample_repository, order_repository)  ← SampleRepository 공유
  ```
- **영향 파일:** `src/services/order_service.py`, `main.py`

---

## ADR-016: dummy.py H-1 단계적 해소 전략

- **날짜:** 2026-05-08
- **Phase:** Phase 3
- **결정:** `dummy.py`의 H-1 이슈(OrderRepository 직접 접근)를 단계적으로 해소한다. Phase 3에서 RESERVED 상태 주문 2건을 `OrderService.place_order()` 경유로 교체하고, 나머지 PRODUCING/CONFIRMED/RELEASED 4건은 Phase 4 이후 해소 예정으로 직접 주입 방식을 유지한다.
- **이유:**
  - RESERVED 주문은 `OrderService.place_order()`가 Phase 3에서 구현되므로 즉시 교체 가능하며, 서비스 레이어를 통한 정상 경로 사용이 올바른 설계이다.
  - PRODUCING/CONFIRMED/RELEASED 상태 전환 로직은 Phase 4(`ApprovalService`)에서 구현 예정이다. Phase 3 범위에서 해당 상태를 서비스 레이어 없이 강제 주입하는 것은 불가피하다.
  - 단계적 해소를 통해 각 Phase 완료 시 해당 Phase의 서비스 레이어를 거치도록 점진적으로 개선한다.
- **H-1 잔여 항목:** PRODUCING 1건, CONFIRMED 1건, RELEASED 2건 — Phase 4 완료 후 해소 예정.
- **코드 명시:** 직접 주입이 남아 있는 코드 블록에 `# PRODUCING/CONFIRMED/RELEASED 상태는 Phase 4 이후 해소 예정이므로 직접 주입 유지 (H-1).` 주석 유지.
- **영향 파일:** `dummy.py`

---

## ADR-017: approve_order 재고 차감 금지 — 출고 시점 보류

- **날짜:** 2026-05-08
- **Phase:** Phase 4
- **결정:** `ApprovalService.approve_order()`는 주문 승인 시 재고를 차감하지 않는다. 재고 차감은 출고(Phase 7 ShipmentService) 시점까지 보류한다.
- **이유:**
  - 주문 승인은 "생산 진행 동의"를 의미하며, 물리적 재고 이동은 실제 출고 시점에 발생한다.
  - 승인 단계에서 재고를 선차감하면, 출고 취소/반려 발생 시 재고 복원 로직이 복잡해진다.
  - 단계별 책임 분리(SRP): 승인 서비스는 상태 전환(RESERVED → CONFIRMED)만 담당하고, 재고 관리는 출고 서비스에 위임한다.
- **상태 전환:** `RESERVED` → `CONFIRMED` (approve_order), `RESERVED` → `REJECTED`(reject_order, 신규 상태)
- **영향 파일:** `src/services/approval_service.py`

---

## ADR-018: dummy.py H-1 단계적 해소 — PRODUCING 경로 완료

- **날짜:** 2026-05-08
- **Phase:** Phase 4
- **결정:** Phase 4에서 `dummy.py`의 PRODUCING 상태 주문 1건을 `ApprovalService.approve_order()` 경유 방식으로 교체 완료한다. CONFIRMED/RELEASED 2건(+추가분)은 Phase 5 이후 해소 예정으로 직접 주입 유지.
- **이유:**
  - PRODUCING 상태는 `ApprovalService.approve_order()` → `OrderStatus.CONFIRMED` 전환 후 `ProductionQueue` 진입 경로로 Phase 4에서 구현되므로 즉시 교체 가능하다.
  - CONFIRMED/RELEASED 상태는 Phase 5(모니터링) 이후 출고 서비스(Phase 7)까지 연계가 필요하므로 현 Phase에서 서비스 레이어 경유 교체가 불가능하다.
  - 단계적 해소 원칙(ADR-016) 준수: 각 Phase 완료 시점에 해당 Phase의 서비스 레이어 경로로 전환.
- **H-1 잔여 항목:** CONFIRMED 1건, RELEASED 2건 — Phase 7(출고 서비스) 완료 후 해소 예정.
- **영향 파일:** `dummy.py`

---

## ADR-019: MonitoringService 재고 상태 분류 — 3단계 기준

- **날짜:** 2026-05-08
- **Phase:** Phase 5
- **결정:** `MonitoringService._classify_stock()`은 재고 상태를 "고갈"(stock == 0) / "부족"(PRODUCING 주문에 해당 시료 포함) / "여유"(그 외) 3단계로 분류한다.
- **이유:**
  - stock == 0은 물리적 재고 고갈로 즉시 조치가 필요하므로 최우선 판정.
  - PRODUCING 중인 시료는 생산 중 소진 가능성이 있어 "부족" 경보 단계로 구분.
  - 두 조건 모두 해당하지 않으면 운영 정상 범위인 "여유"로 판정.
  - 3단계 분류는 운영자가 우선순위를 직관적으로 파악할 수 있는 최소 세분화 수준이다.
- **대안:** 수치 임계값(예: stock < 10) 기반 분류 — PRD에 임계값 정의 없으므로 배제.
- **영향 파일:** `src/services/monitoring_service.py`

---

## ADR-020: ProductionService complete_production DB 반영 — 재고 증가 + 상태 전환

- **날짜:** 2026-05-08
- **Phase:** Phase 6
- **결정:** `ProductionService.complete_production()`은 생산 완료 시 (1) `ProductionQueue`에서 job dequeue, (2) `SampleRepository.update_stock()`으로 재고 증가(`stock + plannedQuantity`), (3) `OrderRepository.update_status()`로 주문 상태를 `PRODUCING → CONFIRMED`로 전환하는 세 단계를 원자적 순서로 수행한다.
- **이유:**
  - 생산 완료는 물리적 재고 증가와 주문 상태 전환이 동시에 이루어져야 시스템 일관성이 보장된다.
  - dequeue 먼저 수행하여 중복 처리를 방지하고, 이후 재고·상태 변경을 순차 적용한다.
  - `PRODUCING → CONFIRMED` 전환은 ADR-017의 재고 차감 보류 원칙과 대칭: 생산 완료(재고 증가)는 즉시 반영, 출고(재고 차감)는 ShipmentService에 위임.
- **대안:** 재고 증가 없이 상태만 전환 — 시료 재고 실수와 주문 상태의 불일치 발생으로 배제.
- **영향 파일:** `src/services/production_service.py`

---

## ADR-021: ShipmentService release_order 출고 시 재고 차감

- **날짜:** 2026-05-08
- **Phase:** Phase 7
- **결정:** `ShipmentService.release_order()`는 CONFIRMED 주문 출고 시 `SampleRepository.update_stock()`으로 `stock - order.quantity`를 즉시 반영하고 주문 상태를 `CONFIRMED → RELEASED`로 전환한다.
- **이유:**
  - ADR-017에서 결정된 "재고 차감은 출고 시점" 원칙의 구현 완결.
  - 출고 전 CONFIRMED 상태 검증(`order.status != OrderStatus.CONFIRMED → ValueError`)으로 이중 출고 방지.
  - 재고가 주문 수량보다 부족한 경우에 대한 별도 가드는 PRD 범위 외이므로 미적용(운영 정책 영역).
- **상태 전환:** `CONFIRMED → RELEASED`
- **영향 파일:** `src/services/shipment_service.py`

---

## ADR-022: dummy.py H-1 완전 해소 — Phase 7 완료 시점

- **날짜:** 2026-05-08
- **Phase:** Phase 7
- **결정:** Phase 7 `ShipmentService` 구현 완료에 따라 `dummy.py`의 CONFIRMED/RELEASED 직접 주입 코드를 모두 `place_order → approve_order → release_order` 서비스 레이어 경유 방식으로 교체하여 H-1 이슈를 완전 해소한다.
- **이유:**
  - ADR-016·ADR-018의 단계적 해소 원칙에 따른 최종 완료 단계.
  - `ShipmentService.release_order()`가 Phase 7에서 구현되므로 CONFIRMED/RELEASED 경로를 정상 서비스 레이어로 전환 가능.
  - 직접 주입 코드(`# H-1`) 완전 제거로 `dummy.py`가 실제 사용자 시나리오와 동일한 경로를 검증하는 통합 시연 스크립트로 완성.
- **H-1 잔여 항목:** 없음 (완전 해소)
- **영향 파일:** `dummy.py`
