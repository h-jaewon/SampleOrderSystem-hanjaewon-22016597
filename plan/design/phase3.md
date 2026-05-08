# Phase 3 설계 문서: 시료 주문 서비스

> 기준 문서: plan.md (Phase 3), PRD.md v1.0 | 작성일: 2026-05-08

---

## 1. 개요

### 목표

주문 접수 비즈니스 로직과 MVC 기반 UI를 함께 구현한다.
`OrderService.place_order()`가 유일한 신규 비즈니스 로직이며, 주문을 RESERVED 상태로 등록하는 것이 이번 Phase의 전부다.
Phase 3 완료 후 `python main.py` 실행 시 시료 관리(메뉴 1)와 시료 주문(메뉴 2)을 함께 사용할 수 있다.

### 브랜치명

```
feat/phase-3-order-service
```

### PRD 대응 요구사항

| 요구사항 ID | 내용 요약 |
|------------|----------|
| OR-01 | 시료 ID는 기등록된 시료 중 하나여야 한다. 미등록 시료 ID는 거부한다. |
| OR-02 | 고객명은 필수 입력값이며 빈 값은 허용하지 않는다. |
| OR-03 | 주문 수량은 1 이상의 정수만 허용한다. |
| OR-04 | 주문 등록 즉시 상태는 RESERVED로 설정된다. |
| OR-05 | 주문 ID는 시스템이 자동 부여하며 중복되지 않아야 한다. |
| 5.3 | 시료 주문 UI — 시료 ID, 고객명, 수량 입력 후 접수 결과 표시 |

### Phase 2와의 의존 관계

Phase 3은 Phase 2가 완전히 완료(모든 테스트 PASS, 커버리지 90% 이상)된 상태를 전제로 진행한다.

| Phase 3이 의존하는 결과물 | 출처 | 사용 목적 |
|--------------------------|------|----------|
| `src/models/order.py` — `Order`, `OrderStatus` | Phase 1 | 서비스에서 생성·반환하는 엔티티 타입 |
| `src/repositories/order_repository.py` — `OrderRepository` | Phase 1 | 주문 저장 및 조회의 실제 구현체 |
| `src/repositories/sample_repository.py` — `SampleRepository` | Phase 1 | sampleId 존재 여부 검증용 |
| `src/views/display.py` — 공통 출력 유틸 | Phase 2 | OrderView, OrderController에서 사용 |
| `src/views/sample_view.py`, `src/controllers/sample_controller.py` | Phase 2 | MVC 구현 패턴 참조 |
| `main.py` — 의존성 조립 구조 | Phase 2 | Phase 3에서 확장 |
| `dummy.py` — 더미 데이터 주입 구조 | Phase 2 | Phase 3에서 OrderService 경유로 교체 |

Phase 3에서 Phase 1, Phase 2 파일을 직접 수정하지 않는다.
단, `main.py`와 `dummy.py`는 Phase 3 요구사항을 반영하여 수정한다.

---

## 2. 구현 대상 파일 목록

| 구분 | 파일 | 작업 |
|------|------|------|
| 서비스 | `src/services/order_service.py` | 신규 생성 |
| 뷰 | `src/views/order_view.py` | 신규 생성 |
| 컨트롤러 | `src/controllers/order_controller.py` | 신규 생성 |
| 진입점 | `main.py` | 수정 — `(2) 시료 주문` 활성화 |
| 더미 데이터 | `dummy.py` | 수정 — H-1 해소 (OrderService 경유) |
| 테스트 | `tests/phase3/test_order_service.py` | 신규 생성 |

이 목록 외의 파일은 Phase 3에서 생성하거나 수정하지 않는다.

---

## 3. `OrderService` 설계

**파일:** `src/services/order_service.py`

**임포트:**

```
from src.models.order import Order, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.sample_repository import SampleRepository
```

**클래스:** `OrderService`

`OrderService`는 생성자에서 `SampleRepository`와 `OrderRepository` 인스턴스를 주입받는다.
저장소를 내부에서 직접 생성하지 않는다. 이 구조는 테스트 격리를 보장한다.

```
OrderService
├── __init__(self, sample_repository: SampleRepository, order_repository: OrderRepository) -> None
└── place_order(self, sample_id: str, customer_name: str, quantity: int) -> Order
```

### 3.1 생성자

| 항목 | 내용 |
|------|------|
| 파라미터 | `sample_repository: SampleRepository`, `order_repository: OrderRepository` |
| 동작 | 전달받은 두 저장소를 각각 `self._sample_repository`, `self._order_repository`로 저장한다. |
| 예외 | 없음 |

### 3.2 `place_order()` 시그니처

```
place_order(self, sample_id: str, customer_name: str, quantity: int) -> Order
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `sample_id` | `str` | 주문할 시료의 ID. 이미 등록된 시료의 ID여야 한다. |
| `customer_name` | `str` | 주문 고객명. 빈 문자열은 허용하지 않는다. |
| `quantity` | `int` | 주문 수량. 1 이상의 정수여야 한다. |

**반환값:** 등록이 완료된 `Order` 인스턴스

| 속성 | 값 |
|------|------|
| `id` | 자동 생성된 `ORD-{순번:03d}` 형식 문자열 |
| `sampleId` | 입력받은 `sample_id` |
| `customerName` | 입력받은 `customer_name` |
| `quantity` | 입력받은 `quantity` |
| `status` | `OrderStatus.RESERVED` |
| `createdAt` | `Order` 데이터 클래스의 `default_factory=datetime.now` 기본값 — 서비스에서 별도 설정하지 않는다 |

### 3.3 유효성 검사 규칙 (순서 고정)

유효성 검사는 아래 순서대로 수행한다. 첫 번째 위반 항목에서 즉시 `ValueError`를 발생시키고 이후 검사는 진행하지 않는다.

| 순서 | 검사 조건 | 위반 시 예외 메시지 (정확한 문자열) |
|------|-----------|----------------------------------|
| 1 | `self._sample_repository.get(sample_id)` 반환값이 `None` | `"등록되지 않은 시료 ID입니다."` |
| 2 | `not customer_name.strip()` | `"고객명은 필수 입력값입니다."` |
| 3 | `quantity < 1` | `"주문 수량은 1 이상의 정수여야 합니다."` |

**경계값 정리:**

| 파라미터 | 허용되지 않음 (ValueError) | 허용됨 |
|----------|--------------------------|--------|
| `sample_id` | 저장소에 없는 ID (`"S999"` 등) | 저장소에 존재하는 ID (`"S001"` 등) |
| `customer_name` | `""`, `"   "` (공백만) | `"홍길동"`, `"Kim"` 등 |
| `quantity` | `0`, `-1`, `-5` | `1`, `10`, `100` |

### 3.4 ID 생성 로직

형식: `ORD-{순번:03d}`

| 순번 | 생성된 ID |
|------|-----------|
| 1 | `ORD-001` |
| 2 | `ORD-002` |
| ... | ... |
| 999 | `ORD-999` |

생성 방법은 `SampleService`의 Sample ID 생성 패턴과 동일하다:

```
순번 = len(self._order_repository.get_all()) + 1
order_id = f"ORD-{순번:03d}"
```

주문 삭제 기능은 PRD 범위 밖이므로, `len(get_all()) + 1` 방식으로 순번이 단조 증가함이 보장된다.
저장소 레벨의 중복 방지는 `OrderRepository.add()`에서 이미 구현되어 있다(Phase 1).

### 3.5 `place_order()` 처리 흐름

```
1. sample_id 유효성 검사 (미등록 ID 여부)
2. customer_name 유효성 검사 (빈 값 여부)
3. quantity 유효성 검사 (1 미만 여부)
4. ID 자동 생성: f"ORD-{len(self._order_repository.get_all()) + 1:03d}"
5. Order 인스턴스 생성: Order(id=order_id, sampleId=sample_id, customerName=customer_name, quantity=quantity)
   — status=OrderStatus.RESERVED, createdAt은 Order 데이터 클래스 기본값 사용
6. self._order_repository.add(order) 호출
7. 저장된 order 인스턴스 반환
```

---

## 4. `OrderController` 설계

**파일:** `src/controllers/order_controller.py`

**임포트:**

```
from src.services.order_service import OrderService
from src.views.display import input_prompt, print_divider, print_error, print_header
from src.views.order_view import OrderView
```

**MVC 패턴 기준:** `SampleController`와 동일한 구조를 따른다.

```
OrderController
├── __init__(self, service: OrderService, view: OrderView) -> None
├── run(self) -> None
└── _handle_place_order(self) -> None
```

### 4.1 생성자

| 항목 | 내용 |
|------|------|
| 파라미터 | `service: OrderService`, `view: OrderView` |
| 동작 | `self._service = service`, `self._view = view`로 저장 |

### 4.2 `run()` 흐름

`SampleController.run()`과 동일한 루프 구조를 사용한다.

```
while True:
    print_header("시료 주문")
    (1) 주문 접수
    (0) 돌아가기 출력
    print_divider()

    choice = input_prompt("선택")

    "1" → self._handle_place_order()
    "0" → break
    그 외 → print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")
```

### 4.3 `_handle_place_order()` 상세

비즈니스 로직은 `OrderService`에 위임한다. 컨트롤러는 입력 수신과 서비스 호출, 뷰 렌더링만 담당한다.

```
1. print_header("시료 주문 > 주문 접수")
2. print()

3. while True:
   a. sample_id = input_prompt("시료 ID        ")
      — 빈 문자열이면 self._view.render_error("시료 ID를 입력해 주세요.") 후 continue
      — 비어있지 않으면 다음 단계로

   b. customer_name = input_prompt("고객명         ")
      — 빈 문자열이면 self._view.render_error("고객명을 입력해 주세요.") 후 continue
      — 비어있지 않으면 다음 단계로

   c. quantity_raw = input_prompt("수량           ")
      try:
          quantity = int(quantity_raw)
      except ValueError:
          self._view.render_error("수량은 정수로 입력해 주세요.")
          continue

   d. try:
          order = self._service.place_order(sample_id, customer_name, quantity)
          break
      except ValueError as e:
          self._view.render_error(str(e))
          continue

4. self._view.render_placed(order)
```

**설계 원칙:**
- 컨트롤러가 수행하는 유효성 검사(빈 sample_id, 빈 customer_name, 정수 변환 실패)는 UI 입력 편의 목적의 사전 필터링이다.
- 비즈니스 규칙 위반(미등록 시료 ID, 고객명 공백, quantity < 1)은 서비스가 `ValueError`로 처리하며 컨트롤러가 그대로 `render_error`에 전달한다.
- 유효한 주문이 접수될 때까지 루프를 반복한다.

---

## 5. `OrderView` 설계

**파일:** `src/views/order_view.py`

**임포트:**

```
from src.models.order import Order
from src.views.display import pause, print_divider, print_error, print_success
```

**구현 원칙:** `SampleView`와 동일하게 `render_*()` 메서드만 보유한다. 서비스 호출 금지. 데이터를 받아 출력만 한다.

```
OrderView
├── render_placed(self, order: Order) -> None
└── render_error(self, message: str) -> None
```

### 5.1 `render_placed(order)` 출력 형식

```
render_placed(self, order: Order) -> None
```

주문 접수 성공 시 호출된다.

출력 예시:
```
(빈 줄)
------------------------------------------------------------
  [완료] 주문이 접수되었습니다.
    주문 ID   : ORD-001
    시료 ID   : S002
    고객명    : 홍길동
    수량      : 10 개
    상태      : RESERVED
(엔터를 누르면 이전 메뉴로 돌아갑니다.)
```

구현 내역:
- `print()` — 빈 줄
- `print_divider()` — 구분선
- `print_success("주문이 접수되었습니다.")`
- `print(f"    주문 ID   : {order.id}")`
- `print(f"    시료 ID   : {order.sampleId}")`
- `print(f"    고객명    : {order.customerName}")`
- `print(f"    수량      : {order.quantity} 개")`
- `print(f"    상태      : {order.status.value}")`
- `pause()`

### 5.2 `render_error(message)` 출력 형식

```
render_error(self, message: str) -> None
```

`SampleView.render_error()`와 동일하게 `print_error(message)`를 호출한다.

출력 예시:
```
  [오류] 등록되지 않은 시료 ID입니다.
```

---

## 6. `main.py` 수정 사항

### 6.1 `(2) 시료 주문` 활성화 방법

현재 `main.py`는 `elif choice in ("2", "3", "4", "5", "6"):` 분기에서 "아직 준비 중인 기능입니다."를 출력한다.

**수정 내용:**

1. 상단 임포트에 추가:
   ```
   from src.controllers.order_controller import OrderController
   from src.repositories.order_repository import OrderRepository
   from src.services.order_service import OrderService
   from src.views.order_view import OrderView
   ```

2. `_print_main_menu()` 함수에서 `(2) 시료 주문` 줄의 `(준비 중)` 텍스트 제거:
   ```
   |  (2) 시료 주문                                       |
   ```

3. `main()` 함수 시그니처 변경 — `order_repository` 파라미터 추가:
   ```
   def main(
       sample_repository: SampleRepository | None = None,
       order_repository: OrderRepository | None = None,
   ) -> None:
   ```

4. `main()` 함수 본문에 의존성 조립 추가:
   ```
   if order_repository is None:
       order_repository = OrderRepository()

   order_service = OrderService(sample_repository, order_repository)
   order_view = OrderView()
   order_controller = OrderController(order_service, order_view)
   ```

5. 메뉴 루프 분기 수정:
   ```
   if choice == "1":
       sample_controller.run()
   elif choice == "2":
       order_controller.run()
   elif choice in ("3", "4", "5", "6"):
       print("\n  아직 준비 중인 기능입니다.")
   elif choice == "0":
       ...
   ```

### 6.2 의존성 주입 흐름

```
main()
├── SampleRepository (인메모리)
├── OrderRepository (인메모리)
│
├── SampleService(sample_repository)
│   └── SampleController(sample_service, SampleView())
│
└── OrderService(sample_repository, order_repository)
    └── OrderController(order_service, OrderView())
```

`OrderService`는 시료 존재 여부 검증을 위해 `SampleRepository`를 공유한다.
`main()`에서 생성된 단일 `SampleRepository` 인스턴스를 `SampleService`와 `OrderService` 모두에 전달한다.
`OrderRepository` 또한 단일 인스턴스를 `OrderService`에 전달한다.

---

## 7. `dummy.py` 수정 사항 (H-1 해소)

### 7.1 현재 상태 및 문제점

`dummy.py` 내 주석(H-1):
```
# OrderService가 Phase 3에서 구현되기 전까지 OrderRepository를 직접 사용한다.
# Phase 3 완료 후 OrderService.place_order()로 교체할 것 (H-1).
```

현재 더미 데이터의 주문 6건은 `OrderRepository.add()`를 직접 호출하며,
`Order` 객체를 수동으로 생성하고 `status`를 임의로 지정한다.

### 7.2 수정 방법

Phase 3 완료 후 RESERVED 상태 주문 2건만 `OrderService.place_order()`로 교체한다.
나머지 4건(PRODUCING 1건, CONFIRMED 1건, RELEASED 2건)은 Phase 4 이후에서 처리할 상태이므로,
더미 데이터에서 해당 상태를 직접 주입하는 방식을 유지한다(Phase 3 범위 밖).

**구체적 교체 내용:**

`_inject()` 함수에서 `OrderService` 인스턴스를 생성하고,
RESERVED 상태에 해당하는 첫 두 건(`statuses[0]`, `statuses[1]`)을 `place_order()`로 처리한다.

```
order_service = OrderService(sample_repo, order_repo)
```

주문 생성 루프를 분기 처리한다:
- `status == OrderStatus.RESERVED` → `order_service.place_order(sample.id, customer_name, quantity)` 호출
  - 이 경우 주문 ID는 OrderService가 자동 생성하므로 `order_id` 변수를 사용하지 않는다.
- 그 외 상태 → 기존 방식 유지 (`Order` 직접 생성 + `order_repo.add()`)
  - H-1 주석을 해당 코드에 유지한다 (Phase 4 이후 해소 예정).

상단 임포트에 추가:
```
from src.services.order_service import OrderService
```

`main()` 함수의 `run_main()` 호출 시 `order_repository` 인수 전달:
```
run_main(sample_repository=sample_repo, order_repository=order_repo)
```

---

## 8. 테스트 명세

**파일:** `tests/phase3/test_order_service.py`

### 픽스처 설계

각 테스트는 독립적인 저장소와 서비스 인스턴스를 사용한다.

```
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
    # 테스트에서 유효한 sampleId로 사용할 시료를 미리 등록해 둔다.
    sample_service = SampleService(sample_repo)
    return sample_service.register_sample("GaAs-100", 2.5, 0.85)
```

### 테스트 케이스 목록

---

#### TC-3-01: 정상 주문 등록 및 RESERVED 상태 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 `S001` 시료가 등록된 상태 |
| 입력 | `place_order("S001", "홍길동", 10)` |
| 기대 결과 | 반환된 `Order` 인스턴스의 `sampleId == "S001"`, `customerName == "홍길동"`, `quantity == 10`, `status == OrderStatus.RESERVED` |

---

#### TC-3-02: 첫 번째 주문의 ID가 `ORD-001`임을 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록. 주문 저장소 비어있음. |
| 입력 | `place_order("S001", "홍길동", 5)` |
| 기대 결과 | `order.id == "ORD-001"` |

---

#### TC-3-03: 존재하지 않는 sampleId 입력 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 시료 저장소 비어있음 |
| 입력 | `place_order("S999", "홍길동", 10)` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"등록되지 않은 시료 ID입니다."` 와 일치한다. |

---

#### TC-3-04: customerName 빈 문자열 입력 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록 |
| 입력 | `place_order("S001", "", 10)` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"고객명은 필수 입력값입니다."` 와 일치한다. |

---

#### TC-3-05: customerName 공백만 있는 경우 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록 |
| 입력 | `place_order("S001", "   ", 10)` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"고객명은 필수 입력값입니다."` 와 일치한다. |

---

#### TC-3-06: quantity = 0 입력 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록 |
| 입력 | `place_order("S001", "홍길동", 0)` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"주문 수량은 1 이상의 정수여야 합니다."` 와 일치한다. |

---

#### TC-3-07: quantity 음수 입력 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록 |
| 입력 | `place_order("S001", "홍길동", -5)` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"주문 수량은 1 이상의 정수여야 합니다."` 와 일치한다. |

---

#### TC-3-08: quantity = 1 허용 (경계값) [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록 |
| 입력 | `place_order("S001", "홍길동", 1)` |
| 기대 결과 | `ValueError` 미발생. `Order` 인스턴스 반환. `order.quantity == 1`. |

---

#### TC-3-09: 복수 주문 등록 시 ID 중복 없음 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록 |
| 입력 | 동일 서비스 인스턴스로 `place_order` 3회 호출 |
| 기대 결과 | 3개 주문의 `id`가 각각 `"ORD-001"`, `"ORD-002"`, `"ORD-003"`이며, 모두 서로 다르다. |

---

#### TC-3-10: createdAt 자동 설정 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `registered_sample` 픽스처로 시료 등록 |
| 입력 | `place_order("S001", "홍길동", 10)` |
| 기대 결과 | 반환된 `order.createdAt`이 `datetime` 타입이다. `None`이 아니다. |

---

#### TC-3-11: 유효성 검사 순서 확인 — 미등록 sampleId가 빈 customerName보다 먼저 검사됨 [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 시료 저장소 비어있음 |
| 입력 | `place_order("S999", "", 0)` — 세 파라미터 모두 위반 |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"등록되지 않은 시료 ID입니다."` 와 일치한다. (첫 번째 위반 항목의 메시지) |

---

## 9. 완료 기준

### PASS 조건

- `tests/phase3/test_order_service.py` 내 모든 테스트 케이스가 PASS 상태여야 한다.
- 테스트 실행 명령: `pytest tests/phase3/ -v`
- 단 하나의 FAILED 또는 ERROR도 허용하지 않는다.

### 커버리지 기준

- Phase 3 구현 대상 파일(`src/services/order_service.py`)의 라인 커버리지가 **90% 이상**이어야 한다.
- 커버리지 측정 명령: `pytest tests/phase3/ --cov=src/services/order_service --cov-report=term-missing`

### 동작 확인 기준

- `python main.py` 실행 후 메인 메뉴에서 `(2) 시료 주문` 선택 시 `(준비 중)` 메시지 없이 주문 접수 화면으로 진입한다.
- 시료 ID, 고객명, 수량을 입력하면 주문 접수 결과가 출력된다.
- 미등록 시료 ID, 빈 고객명, 0 이하 수량 입력 시 오류 메시지가 출력되고 재입력이 요청된다.
- `python dummy.py` 실행 시 오류 없이 완료되고 `main.py`가 자동으로 시작된다.
- H-1 주석의 RESERVED 주문 2건이 `OrderService.place_order()` 경유로 처리된다.
