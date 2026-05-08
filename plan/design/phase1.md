# Phase 1 설계 문서: 도메인 모델 및 저장소 기반 구축

> 기준 문서: plan.md (Phase 1) | 작성일: 2026-05-08

---

## 1. 개요

### 목표

시스템 전체의 뼈대가 되는 데이터 모델과 인메모리 저장소를 구현한다.
이후 모든 Phase(2~8)는 이 Phase에서 정의한 모델과 저장소 위에 서비스 레이어를 추가하는 방식으로 진행된다.

### 브랜치명

```
feat/phase-1-domain-models
```

### PRD 대응 요구사항

| 요구사항 ID | 내용 요약 |
|------------|----------|
| SM-01 | 저장소 레벨에서 시료 ID 중복 방지 |
| OR-04 | 주문 등록 시 상태(status) 초기값 설정 |
| OR-05 | 주문 생성 시각(createdAt) 자동 기록 |
| 7.1 | Sample 엔티티 정의 |
| 7.2 | Order 엔티티 및 OrderStatus 열거형 정의 |
| 7.3 | ProductionJob 엔티티 정의 |
| 7.4 | 인메모리 저장소(Repository) 정의 |

> SM-01 구현 책임 분리: 저장소는 ID 중복 등록을 거부하고(Phase 1), 서비스는 중복 없는 ID를 생성하여 전달한다(Phase 2~).

---

## 2. 디렉터리 및 파일 구조

Phase 1에서 생성하는 파일 목록이다. 이 목록 외의 파일은 이번 Phase에서 생성하지 않는다.

```
sampleordersystem/
├── src/
│   ├── __init__.py                          # 패키지 선언 (내용 없음)
│   ├── models/
│   │   ├── __init__.py                      # 패키지 선언 (내용 없음)
│   │   ├── sample.py                        # Sample 데이터 클래스
│   │   ├── order.py                         # OrderStatus 열거형 + Order 데이터 클래스
│   │   └── production_job.py               # ProductionJob 데이터 클래스
│   └── repositories/
│       ├── __init__.py                      # 패키지 선언 (내용 없음)
│       ├── sample_repository.py            # 시료 인메모리 저장소
│       ├── order_repository.py             # 주문 인메모리 저장소
│       └── production_queue.py             # FIFO 생산 대기 큐
├── tests/
│   ├── __init__.py                          # 패키지 선언 (내용 없음)
│   └── phase1/
│       ├── __init__.py                      # 패키지 선언 (내용 없음)
│       └── test_models.py                   # Phase 1 단위 테스트
├── pytest.ini                               # pytest 설정 파일
└── requirements.txt                         # 의존성 목록
```

### 각 파일의 역할

| 파일 | 역할 |
|------|------|
| `src/models/sample.py` | 시료(Sample) 엔티티 정의. 시스템에서 판매·생산하는 반도체 시료의 속성을 보유한다. |
| `src/models/order.py` | 주문 상태 열거형(OrderStatus)과 주문(Order) 엔티티 정의. |
| `src/models/production_job.py` | 생산 작업(ProductionJob) 엔티티 정의. 생산 대기 큐에 적재되는 단위이다. |
| `src/repositories/sample_repository.py` | Sample 객체를 dict 기반 인메모리 저장소에 보관하고 조회한다. |
| `src/repositories/order_repository.py` | Order 객체를 dict 기반 인메모리 저장소에 보관하고 조회한다. |
| `src/repositories/production_queue.py` | ProductionJob 객체를 FIFO 방식으로 관리하는 큐 저장소이다. |
| `tests/phase1/test_models.py` | 위 6개 구현 파일에 대한 단위 테스트를 포함한다. |
| `pytest.ini` | testpaths, addopts(--cov, --cov-report) 등 pytest 전역 설정을 포함한다. |
| `requirements.txt` | `pytest>=8.0.0`, `pytest-cov>=5.0.0` 의존성을 선언한다. |

---

## 3. 도메인 모델 설계

모든 모델은 Python `dataclasses.dataclass` 데코레이터를 사용한다.
변경 가능한 상태를 가져야 하므로 `frozen=False`(기본값)로 선언한다.

### 3.1 Sample 클래스

**파일:** `src/models/sample.py`

| 속성명 | 타입 | 기본값 | 제약조건 |
|--------|------|--------|----------|
| `id` | `str` | 없음 (필수) | `S{순번:03d}` 형식. 저장소에서 중복 불가. |
| `name` | `str` | 없음 (필수) | 빈 문자열 불가 (서비스 레이어에서 검증, Phase 2). |
| `avgProductionTime` | `float` | 없음 (필수) | 0 초과 (서비스 레이어에서 검증, Phase 2). |
| `yield_` | `float` | 없음 (필수) | 0 초과 1 이하 (서비스 레이어에서 검증, Phase 2). 예약어 `yield` 회피를 위해 trailing underscore 사용. |
| `stock` | `int` | `0` | 0 이상의 정수. |

> 모델 클래스 자체는 유효성 검사를 수행하지 않는다. 유효성 검사는 서비스 레이어 책임이다.

### 3.2 OrderStatus 열거형

**파일:** `src/models/order.py`

Python 표준 `enum.Enum`을 상속한다.

| 열거값 | 의미 |
|--------|------|
| `RESERVED` | 주문 접수 완료, 승인 대기 중 |
| `REJECTED` | 주문 거절 |
| `PRODUCING` | 재고 부족으로 생산 진행 중 |
| `CONFIRMED` | 승인 완료 (재고 충분하거나 생산 완료), 출고 대기 중 |
| `RELEASED` | 출고 처리 완료 |

### 3.3 Order 클래스

**파일:** `src/models/order.py` (OrderStatus와 동일 파일)

| 속성명 | 타입 | 기본값 | 제약조건 |
|--------|------|--------|----------|
| `id` | `str` | 없음 (필수) | `ORD-{순번:03d}` 형식. 저장소에서 중복 불가. |
| `sampleId` | `str` | 없음 (필수) | 등록된 Sample의 id 값이어야 함 (서비스 레이어에서 검증, Phase 3). |
| `customerName` | `str` | 없음 (필수) | 빈 문자열 불가 (서비스 레이어에서 검증, Phase 3). |
| `quantity` | `int` | 없음 (필수) | 1 이상의 정수 (서비스 레이어에서 검증, Phase 3). |
| `status` | `OrderStatus` | `OrderStatus.RESERVED` | OrderStatus 열거값만 허용. |
| `createdAt` | `datetime` | `field(default_factory=datetime.now)` | 객체 생성 시각이 자동으로 설정된다. `datetime` 타입. |

`createdAt` 기본값 설정 방법:

- `dataclasses.field(default_factory=datetime.now)` 를 사용한다.
- `from datetime import datetime` 임포트가 필요하다.
- 이 방식으로 각 Order 인스턴스 생성 시점의 `datetime` 객체가 독립적으로 할당된다.

### 3.4 ProductionJob 클래스

**파일:** `src/models/production_job.py`

| 속성명 | 타입 | 기본값 | 비고 |
|--------|------|--------|------|
| `orderId` | `str` | 없음 (필수) | 연관된 Order의 id 값. |
| `sampleId` | `str` | 없음 (필수) | 연관된 Sample의 id 값. |
| `plannedQuantity` | `int` | 없음 (필수) | 실제 생산 예정 수량. `math.ceil(부족분 / (수율 × 0.9))` 계산 결과 (Phase 4에서 계산). |
| `totalProductionTime` | `float` | 없음 (필수) | 총 생산 시간. `평균 생산시간 × plannedQuantity` 계산 결과 (Phase 4에서 계산). |

---

## 4. 저장소(Repository) 설계

모든 저장소는 인메모리 방식(`dict` 또는 `collections.deque`)으로 구현한다.
영속성(디스크 저장)은 요구사항에 없으므로 구현하지 않는다.

### 4.1 SampleRepository

**파일:** `src/repositories/sample_repository.py`

**내부 상태:** `_store: dict[str, Sample]` — key는 Sample.id

#### 메서드 명세

**`add(sample: Sample) -> None`**
- 동작: `sample.id`를 키로 `_store`에 저장한다.
- 예외: `sample.id`가 이미 `_store`에 존재하면 `ValueError("이미 존재하는 시료 ID입니다: {id}")` 를 발생시킨다.

**`get(sample_id: str) -> Sample | None`**
- 동작: `_store.get(sample_id)`를 반환한다.
- 예외 없음: 존재하지 않으면 `None`을 반환한다.

**`get_all() -> list[Sample]`**
- 동작: `list(_store.values())`를 반환한다. 등록 순서 보장은 Python 3.7+ dict 삽입 순서에 의존한다.
- 예외 없음: 저장소가 비어있으면 빈 리스트를 반환한다.

**`find_by_name(name: str) -> list[Sample]`**
- 동작: `_store` 전체를 순회하며 `name.lower() in sample.name.lower()` 조건을 만족하는 Sample 목록을 반환한다 (대소문자 무관 부분 일치).
- 예외 없음: 일치하는 시료가 없으면 빈 리스트를 반환한다.

### 4.2 OrderRepository

**파일:** `src/repositories/order_repository.py`

**내부 상태:** `_store: dict[str, Order]` — key는 Order.id

#### 메서드 명세

**`add(order: Order) -> None`**
- 동작: `order.id`를 키로 `_store`에 저장한다.
- 예외: `order.id`가 이미 `_store`에 존재하면 `ValueError("이미 존재하는 주문 ID입니다: {id}")` 를 발생시킨다.

**`get(order_id: str) -> Order | None`**
- 동작: `_store.get(order_id)`를 반환한다.
- 예외 없음: 존재하지 않으면 `None`을 반환한다.

**`get_all() -> list[Order]`**
- 동작: `list(_store.values())`를 반환한다.
- 예외 없음: 저장소가 비어있으면 빈 리스트를 반환한다.

**`get_by_status(status: OrderStatus) -> list[Order]`**
- 동작: `_store` 전체를 순회하며 `order.status == status` 조건을 만족하는 Order 목록을 반환한다.
- 예외 없음: 해당 상태의 주문이 없으면 빈 리스트를 반환한다.

### 4.3 ProductionQueue

**파일:** `src/repositories/production_queue.py`

**내부 상태:** `_queue: collections.deque[ProductionJob]`

FIFO 보장 방식: `collections.deque`의 `append()`(오른쪽 추가)와 `popleft()`(왼쪽 제거)를 사용하여 선입선출을 구현한다.

#### 메서드 명세

**`enqueue(job: ProductionJob) -> None`**
- 동작: `_queue.append(job)`으로 큐의 맨 뒤에 작업을 추가한다.
- 예외 없음.

**`dequeue() -> ProductionJob`**
- 동작: `_queue.popleft()`로 큐의 맨 앞 항목을 꺼내어 반환한다.
- 예외: `_queue`가 비어있으면 `IndexError("생산 큐가 비어있습니다.")` 를 발생시킨다.

**`peek() -> ProductionJob | None`**
- 동작: `_queue[0]`을 반환한다. 큐를 변경하지 않는다.
- 예외 없음: `_queue`가 비어있으면 `None`을 반환한다.

**`get_all() -> list[ProductionJob]`**
- 동작: `list(_queue)`를 반환한다. 순서는 enqueue 순서(FIFO)를 유지한다.
- 예외 없음: 큐가 비어있으면 빈 리스트를 반환한다.

**`is_empty() -> bool`**
- 동작: `len(_queue) == 0`을 반환한다.
- 예외 없음.

---

## 5. ID 생성 규칙

> ID 생성은 서비스 레이어(Phase 2~)의 책임이다. 저장소는 전달받은 ID의 중복만 검사한다.

### Sample ID

| 항목 | 내용 |
|------|------|
| 형식 | `S{순번:03d}` |
| 예시 | `S001`, `S002`, `S003`, ..., `S999` |
| 생성 방식 | Phase 2의 `SampleService.register_sample()` 내부에서 `len(sample_repository.get_all()) + 1`을 순번으로 사용하여 생성한다. |

### Order ID

| 항목 | 내용 |
|------|------|
| 형식 | `ORD-{순번:03d}` |
| 예시 | `ORD-001`, `ORD-002`, `ORD-003`, ..., `ORD-999` |
| 생성 방식 | Phase 3의 `OrderService.place_order()` 내부에서 `len(order_repository.get_all()) + 1`을 순번으로 사용하여 생성한다. |

---

## 6. 테스트 명세

### 테스트 파일 위치

```
tests/phase1/test_models.py
```

### 테스트 케이스 목록

#### TC-1-01: Sample 객체 생성 및 속성 접근

| 항목 | 내용 |
|------|------|
| 입력 | `id="S001"`, `name="AlphaChip"`, `avgProductionTime=5.0`, `yield_=0.8`, `stock=100` |
| 기대 결과 | Sample 인스턴스 생성 성공. 각 속성이 입력값과 일치한다. |

#### TC-1-02: Sample stock 기본값

| 항목 | 내용 |
|------|------|
| 입력 | `id="S001"`, `name="AlphaChip"`, `avgProductionTime=5.0`, `yield_=0.8` (stock 생략) |
| 기대 결과 | `sample.stock == 0` |

#### TC-1-03: Order 객체 생성 및 상태 초기값 검증

| 항목 | 내용 |
|------|------|
| 입력 | `id="ORD-001"`, `sampleId="S001"`, `customerName="홍길동"`, `quantity=10` (status, createdAt 생략) |
| 기대 결과 | `order.status == OrderStatus.RESERVED` |

#### TC-1-04: Order createdAt 자동 설정

| 항목 | 내용 |
|------|------|
| 입력 | TC-1-03과 동일 |
| 기대 결과 | `order.createdAt`이 `datetime` 타입이다. 테스트 실행 시각 기준 과거 또는 현재 시각이다 (`order.createdAt <= datetime.now()`). |

#### TC-1-05: Order createdAt 인스턴스별 독립성

| 항목 | 내용 |
|------|------|
| 입력 | Order 인스턴스 2개를 연속으로 생성 |
| 기대 결과 | 두 인스턴스의 `createdAt`이 동일한 객체가 아니다 (`is not`). |

#### TC-1-06: OrderStatus 열거형 전체 값 존재 확인

| 항목 | 내용 |
|------|------|
| 입력 | 없음 |
| 기대 결과 | `OrderStatus` 멤버로 `RESERVED`, `REJECTED`, `PRODUCING`, `CONFIRMED`, `RELEASED` 5개가 모두 존재한다. |

#### TC-1-07: ProductionJob 객체 생성 검증

| 항목 | 내용 |
|------|------|
| 입력 | `orderId="ORD-001"`, `sampleId="S001"`, `plannedQuantity=10`, `totalProductionTime=55.0` |
| 기대 결과 | ProductionJob 인스턴스 생성 성공. 각 속성이 입력값과 일치한다. |

#### TC-1-08: SampleRepository — add 및 get

| 항목 | 내용 |
|------|------|
| 입력 | Sample(`id="S001"`, ...) 을 add 후 `get("S001")` 호출 |
| 기대 결과 | 반환된 Sample 객체가 저장한 객체와 동일하다. |

#### TC-1-09: SampleRepository — 중복 ID 예외

| 항목 | 내용 |
|------|------|
| 입력 | 동일한 `id="S001"`을 가진 Sample 2개를 연속으로 add |
| 기대 결과 | 두 번째 add 시 `ValueError` 발생. |

#### TC-1-10: SampleRepository — get_all

| 항목 | 내용 |
|------|------|
| 입력 | Sample 3개(`S001`, `S002`, `S003`)를 add 후 `get_all()` 호출 |
| 기대 결과 | 반환된 리스트의 길이가 3이다. |

#### TC-1-11: SampleRepository — get_all 빈 저장소

| 항목 | 내용 |
|------|------|
| 입력 | 아무것도 add하지 않은 SampleRepository에서 `get_all()` 호출 |
| 기대 결과 | 빈 리스트 `[]` 반환. |

#### TC-1-12: SampleRepository — find_by_name 부분 일치

| 항목 | 내용 |
|------|------|
| 입력 | `name="AlphaChip"` 시료와 `name="BetaChip"` 시료를 등록 후 `find_by_name("chip")` 호출 |
| 기대 결과 | 2개의 시료가 반환된다 (대소문자 무관 부분 일치). |

#### TC-1-13: SampleRepository — find_by_name 결과 없음

| 항목 | 내용 |
|------|------|
| 입력 | `find_by_name("존재하지않는이름")` 호출 |
| 기대 결과 | 빈 리스트 `[]` 반환. |

#### TC-1-14: OrderRepository — 상태별 필터링

| 항목 | 내용 |
|------|------|
| 입력 | `status=RESERVED` Order 2개, `status=CONFIRMED` Order 1개를 add 후 `get_by_status(OrderStatus.RESERVED)` 호출 |
| 기대 결과 | 반환된 리스트의 길이가 2이고, 모든 요소의 status가 `RESERVED`이다. |

#### TC-1-15: OrderRepository — 중복 ID 예외

| 항목 | 내용 |
|------|------|
| 입력 | 동일한 `id="ORD-001"`을 가진 Order 2개를 연속으로 add |
| 기대 결과 | 두 번째 add 시 `ValueError` 발생. |

#### TC-1-16: OrderRepository — get 존재하지 않는 ID

| 항목 | 내용 |
|------|------|
| 입력 | `get("ORD-999")` 호출 (저장소에 없는 ID) |
| 기대 결과 | `None` 반환. |

#### TC-1-17: ProductionQueue — FIFO 순서 보장

| 항목 | 내용 |
|------|------|
| 입력 | `orderId="ORD-001"`, `orderId="ORD-002"`, `orderId="ORD-003"` 순으로 enqueue 후 dequeue 3회 |
| 기대 결과 | dequeue 결과가 `ORD-001`, `ORD-002`, `ORD-003` 순서로 반환된다. |

#### TC-1-18: ProductionQueue — 빈 큐에서 dequeue 예외

| 항목 | 내용 |
|------|------|
| 입력 | 아무것도 enqueue하지 않은 큐에서 `dequeue()` 호출 |
| 기대 결과 | `IndexError` 발생. |

#### TC-1-19: ProductionQueue — peek

| 항목 | 내용 |
|------|------|
| 입력 | `orderId="ORD-001"`, `orderId="ORD-002"` 를 enqueue 후 `peek()` 호출 |
| 기대 결과 | `orderId="ORD-001"`인 ProductionJob 반환. 큐 상태 변경 없음 (`get_all()` 길이 == 2). |

#### TC-1-20: ProductionQueue — 빈 큐에서 peek

| 항목 | 내용 |
|------|------|
| 입력 | 빈 큐에서 `peek()` 호출 |
| 기대 결과 | `None` 반환. |

#### TC-1-21: ProductionQueue — is_empty

| 항목 | 내용 |
|------|------|
| 입력 1 | 빈 큐에서 `is_empty()` 호출 |
| 기대 결과 1 | `True` 반환. |
| 입력 2 | 항목 1개 enqueue 후 `is_empty()` 호출 |
| 기대 결과 2 | `False` 반환. |

#### TC-1-22: ProductionQueue — get_all FIFO 순서

| 항목 | 내용 |
|------|------|
| 입력 | `ORD-001`, `ORD-002`, `ORD-003` 순으로 enqueue 후 `get_all()` 호출 |
| 기대 결과 | 반환된 리스트의 `orderId` 순서가 `["ORD-001", "ORD-002", "ORD-003"]`이다. |

---

## 7. 완료 기준

### PASS 조건

- `tests/phase1/test_models.py` 내 모든 테스트 케이스가 PASS 상태여야 한다.
- 테스트 실행 명령: `pytest tests/phase1/ -v`
- 단 하나의 FAILED 또는 ERROR도 허용하지 않는다.

### 커버리지 기준

- Phase 1 구현 대상 파일(`src/models/`, `src/repositories/`)의 라인 커버리지가 **90% 이상**이어야 한다.
- 커버리지 측정 명령: `pytest tests/phase1/ --cov=src --cov-report=term-missing`
- HTML 리포트: `pytest tests/phase1/ --cov=src --cov-report=html:htmlcov` 실행 후 `htmlcov/index.html` 에서 확인.

### 참고: pytest.ini 전역 설정

`pytest.ini`에 아래 설정이 적용되어 있으므로 `pytest` 단독 실행 시 커버리지 리포트가 자동 생성된다.

```ini
[pytest]
testpaths = tests
addopts = --cov=src --cov-report=html:htmlcov --cov-report=term-missing -v
```
