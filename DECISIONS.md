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
- **Phase:** Phase 1
- **결정:** Phase 1 도메인 모델은 유효성 검사를 수행하지 않는다. 입력값 검증(빈 문자열, 범위 초과 등)은 Phase 2+ 서비스 레이어의 책임으로 위임한다.
- **이유:**
  - 단일 책임 원칙(SRP): 모델은 데이터 보유, 서비스는 비즈니스 규칙 적용.
  - Phase 1 범위를 최소화하여 안정적 기반 마련.
- **영향:** `src/models/` 전체 — `__post_init__` 검증 없음.
