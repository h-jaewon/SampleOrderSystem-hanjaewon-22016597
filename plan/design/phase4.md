# Phase 4 설계 문서: 주문 승인 / 거절 서비스

> 기준 문서: plan.md (Phase 4), PRD.md v1.0 | 작성일: 2026-05-08

---

## 1. 개요

### 목표

주문 승인·거절 비즈니스 로직과 재고 기반 자동 상태 분기를 구현하고, MVC 기반 UI를 함께 제공한다.
이 Phase가 시스템의 핵심 비즈니스 로직이다. RESERVED 상태의 주문에 대해 현재 재고를 확인하여
재고가 충분하면 CONFIRMED, 부족하면 생산 대기 큐에 등록하고 PRODUCING으로 전환한다.
Phase 4 완료 후 `python main.py` 실행 시 시료 관리(메뉴 1), 시료 주문(메뉴 2), 주문 승인/거절(메뉴 3)을 사용할 수 있다.

### 브랜치명

```
feat/phase-4-approval-service
```

### PRD 대응 요구사항

| 요구사항 ID | 내용 요약 |
|------------|----------|
| AP-01 | 승인 대상은 RESERVED 상태의 주문만 가능하다. 다른 상태의 주문은 거부한다. |
| AP-02 | 승인 시 현재 재고와 주문 수량을 비교하여 상태를 자동 분기한다. |
| AP-03 | 재고 >= 주문 수량인 경우 주문 상태를 CONFIRMED로 전환한다. 재고는 이 시점에 차감하지 않는다. |
| AP-04 | 재고 < 주문 수량인 경우 부족분 기반으로 실 생산량을 계산하고 생산 대기 큐에 등록한 뒤 상태를 PRODUCING으로 전환한다. |
| AP-05 | 실 생산량 공식: `math.ceil(부족분 / (수율 × 0.9))`. 총 생산 시간: `평균 생산시간 × 실 생산량`. |
| AP-06 | 거절 시 주문 상태를 REJECTED로 전환한다. 다른 처리는 없다. |
| 5.4 | 주문 승인/거절 UI — RESERVED 주문 목록 표시 후 주문 ID 입력, 승인 또는 거절 선택, 결과 표시 |

### Phase 3과의 의존 관계

Phase 4는 Phase 3이 완전히 완료(모든 테스트 PASS, 커버리지 90% 이상)된 상태를 전제로 진행한다.

| Phase 4가 의존하는 결과물 | 출처 | 사용 목적 |
|--------------------------|------|----------|
| `src/models/order.py` — `Order`, `OrderStatus` | Phase 1 | 상태 전이 대상 엔티티 타입 |
| `src/models/sample.py` — `Sample` | Phase 1 | 재고(`stock`) 조회 및 수율(`yield_`), 평균 생산시간(`avgProductionTime`) 참조 |
| `src/models/production_job.py` — `ProductionJob` | Phase 1 | 생산 대기 큐에 등록할 작업 엔티티 |
| `src/repositories/order_repository.py` — `OrderRepository` | Phase 1 | 주문 조회 및 상태 갱신 |
| `src/repositories/sample_repository.py` — `SampleRepository` | Phase 1 | 시료 조회 (재고, 수율, 생산시간) |
| `src/repositories/production_queue.py` — `ProductionQueue` | Phase 1 | `ProductionJob` enqueue |
| `src/views/display.py` — 공통 출력 유틸 | Phase 2 | `ApprovalView`, `ApprovalController`에서 사용 |
| `src/controllers/order_controller.py`, `src/views/order_view.py` | Phase 3 | MVC 구현 패턴 참조 |
| `main.py` — 의존성 조립 구조 | Phase 3 | Phase 4에서 확장 |
| `dummy.py` — 더미 데이터 주입 구조 | Phase 3 | Phase 4에서 H-1 부분 해소 |

Phase 4에서 Phase 1~3 파일을 직접 수정하지 않는다.
단, `main.py`와 `dummy.py`는 Phase 4 요구사항을 반영하여 수정한다.

---

## 2. 구현 대상 파일 목록

| 구분 | 파일 | 작업 |
|------|------|------|
| 서비스 | `src/services/approval_service.py` | 신규 생성 |
| 뷰 | `src/views/approval_view.py` | 신규 생성 |
| 컨트롤러 | `src/controllers/approval_controller.py` | 신규 생성 |
| 진입점 | `main.py` | 수정 — `(3) 주문 승인/거절` 활성화 |
| 더미 데이터 | `dummy.py` | 수정 — H-1 부분 해소 (PRODUCING 1건을 approve_order 경유로 교체) |
| 테스트 | `tests/phase4/test_approval_service.py` | 신규 생성 |

이 목록 외의 파일은 Phase 4에서 생성하거나 수정하지 않는다.

---

## 3. `ApprovalService` 설계

**파일:** `src/services/approval_service.py`

**임포트:**

```
import math

from src.models.order import Order, OrderStatus
from src.models.production_job import ProductionJob
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.repositories.sample_repository import SampleRepository
```

**클래스:** `ApprovalService`

`ApprovalService`는 생성자에서 `SampleRepository`, `OrderRepository`, `ProductionQueue` 인스턴스를 주입받는다.
저장소와 큐를 내부에서 직접 생성하지 않는다. 이 구조는 테스트 격리를 보장한다.

```
ApprovalService
├── __init__(self, sample_repository: SampleRepository, order_repository: OrderRepository, production_queue: ProductionQueue) -> None
├── approve_order(self, order_id: str) -> Order
├── reject_order(self, order_id: str) -> Order
└── _calculate_production_quantity(self, deficit: int, yield_: float) -> int
```

### 3.1 생성자

| 항목 | 내용 |
|------|------|
| 파라미터 | `sample_repository: SampleRepository`, `order_repository: OrderRepository`, `production_queue: ProductionQueue` |
| 동작 | 전달받은 세 객체를 각각 `self._sample_repository`, `self._order_repository`, `self._production_queue`로 저장한다. |
| 예외 | 없음 |

### 3.2 `approve_order()` 시그니처

```
approve_order(self, order_id: str) -> Order
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `order_id` | `str` | 승인 처리할 주문의 ID |

**반환값:** 상태가 갱신된 `Order` 인스턴스

#### 3.2.1 사전 검사

| 순서 | 검사 조건 | 위반 시 예외 메시지 (정확한 문자열) |
|------|-----------|----------------------------------|
| 1 | `self._order_repository.get(order_id)` 반환값이 `None` | `"존재하지 않는 주문 ID입니다."` |
| 2 | `order.status != OrderStatus.RESERVED` | `"RESERVED 상태의 주문만 처리 가능합니다."` |

검사는 위 순서대로 수행한다. 첫 번째 위반 항목에서 즉시 `ValueError`를 발생시키고 이후 검사는 진행하지 않는다.

#### 3.2.2 재고 충분 분기 (`재고 >= 주문 수량`)

조건: `sample.stock >= order.quantity`

| 단계 | 처리 내용 |
|------|----------|
| 1 | `order.status = OrderStatus.CONFIRMED` 으로 갱신 |
| 2 | 재고(`sample.stock`)는 **변경하지 않는다** (재고 차감은 출고 처리 시점에 수행) |
| 3 | 갱신된 `order` 인스턴스 반환 |

#### 3.2.3 재고 부족 분기 (`재고 < 주문 수량`)

조건: `sample.stock < order.quantity`

| 단계 | 처리 내용 |
|------|----------|
| 1 | 부족분 계산: `deficit = order.quantity - sample.stock` |
| 2 | 실 생산량 계산: `planned_quantity = self._calculate_production_quantity(deficit, sample.yield_)` |
| 3 | 총 생산 시간 계산: `total_production_time = sample.avgProductionTime * planned_quantity` |
| 4 | `ProductionJob` 생성: `ProductionJob(orderId=order.id, sampleId=order.sampleId, plannedQuantity=planned_quantity, totalProductionTime=total_production_time)` |
| 5 | `self._production_queue.enqueue(job)` 호출 |
| 6 | `order.status = OrderStatus.PRODUCING` 으로 갱신 |
| 7 | 갱신된 `order` 인스턴스 반환 |

#### 3.2.4 `approve_order()` 처리 흐름 전체

```
1. order = self._order_repository.get(order_id)
   — None이면 ValueError("존재하지 않는 주문 ID입니다.")

2. order.status != OrderStatus.RESERVED이면
   — ValueError("RESERVED 상태의 주문만 처리 가능합니다.")

3. sample = self._sample_repository.get(order.sampleId)
   — (이미 place_order에서 검증된 sampleId이므로 None 검사 생략)

4. if sample.stock >= order.quantity:
       order.status = OrderStatus.CONFIRMED

   else:
       deficit = order.quantity - sample.stock
       planned_quantity = self._calculate_production_quantity(deficit, sample.yield_)
       total_production_time = sample.avgProductionTime * planned_quantity
       job = ProductionJob(
           orderId=order.id,
           sampleId=order.sampleId,
           plannedQuantity=planned_quantity,
           totalProductionTime=total_production_time,
       )
       self._production_queue.enqueue(job)
       order.status = OrderStatus.PRODUCING

5. return order
```

### 3.3 `reject_order()` 시그니처

```
reject_order(self, order_id: str) -> Order
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `order_id` | `str` | 거절 처리할 주문의 ID |

**반환값:** 상태가 REJECTED로 갱신된 `Order` 인스턴스

#### 3.3.1 사전 검사

`approve_order()`와 동일한 순서로 동일한 메시지를 사용한다.

| 순서 | 검사 조건 | 위반 시 예외 메시지 (정확한 문자열) |
|------|-----------|----------------------------------|
| 1 | `self._order_repository.get(order_id)` 반환값이 `None` | `"존재하지 않는 주문 ID입니다."` |
| 2 | `order.status != OrderStatus.RESERVED` | `"RESERVED 상태의 주문만 처리 가능합니다."` |

#### 3.3.2 상태 전이

| 단계 | 처리 내용 |
|------|----------|
| 1 | `order.status = OrderStatus.REJECTED` 로 갱신 |
| 2 | 재고 변경 없음. 생산 큐 등록 없음. 다른 처리 없음. |
| 3 | 갱신된 `order` 인스턴스 반환 |

#### 3.3.3 `reject_order()` 처리 흐름

```
1. order = self._order_repository.get(order_id)
   — None이면 ValueError("존재하지 않는 주문 ID입니다.")

2. order.status != OrderStatus.RESERVED이면
   — ValueError("RESERVED 상태의 주문만 처리 가능합니다.")

3. order.status = OrderStatus.REJECTED

4. return order
```

### 3.4 `_calculate_production_quantity()` 시그니처

```
_calculate_production_quantity(self, deficit: int, yield_: float) -> int
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `deficit` | `int` | 부족분 (`order.quantity - sample.stock`) |
| `yield_` | `float` | 시료 수율 (0 초과 1 이하) |

**반환값:** 실 생산량 (`int`)

**계산 공식:**

```
실 생산량 = math.ceil(deficit / (yield_ * 0.9))
```

0.9는 생산 안전 계수(safety factor)로, 실제 수율의 10%를 여유분으로 확보한다.
`math.ceil`을 적용하므로 반환값은 항상 양의 정수이다.

**계산 예시:**

| deficit | yield_ | 계산 과정 | 결과 |
|---------|--------|----------|------|
| 7 | 0.8 | `ceil(7 / (0.8 × 0.9))` = `ceil(7 / 0.72)` = `ceil(9.722...)` | `10` |
| 5 | 0.9 | `ceil(5 / (0.9 × 0.9))` = `ceil(5 / 0.81)` = `ceil(6.172...)` | `7` |
| 10 | 1.0 | `ceil(10 / (1.0 × 0.9))` = `ceil(10 / 0.9)` = `ceil(11.111...)` | `12` |

**총 생산 시간 계산 예시 (approve_order 내부):**

| avgProductionTime | planned_quantity | 결과 |
|-------------------|-----------------|------|
| 5.5 | 10 | `5.5 × 10 = 55.0` |

### 3.5 예외 메시지 정확한 문자열 정리

| 메서드 | 조건 | 예외 메시지 |
|--------|------|------------|
| `approve_order` | 주문 ID 미존재 | `"존재하지 않는 주문 ID입니다."` |
| `approve_order` | RESERVED 외 상태 | `"RESERVED 상태의 주문만 처리 가능합니다."` |
| `reject_order` | 주문 ID 미존재 | `"존재하지 않는 주문 ID입니다."` |
| `reject_order` | RESERVED 외 상태 | `"RESERVED 상태의 주문만 처리 가능합니다."` |

---

## 4. `ApprovalView` 설계

**파일:** `src/views/approval_view.py`

**임포트:**

```
from src.models.order import Order, OrderStatus
from src.views.display import (
    Color,
    colorize,
    ljust_v,
    pause,
    print_divider,
    print_error,
    print_header,
    print_success,
    print_table,
)
```

**구현 원칙:** `render_*()` 메서드만 보유한다. 서비스 호출 금지. 데이터를 받아 출력만 한다.

```
ApprovalView
├── render_reserved_list(self, orders: list[Order]) -> None
├── render_approved(self, order: Order) -> None
├── render_rejected(self, order: Order) -> None
└── render_error(self, message: str) -> None
```

### 4.1 `render_reserved_list(orders)` 출력 형식

```
render_reserved_list(self, orders: list[Order]) -> None
```

RESERVED 상태 주문 목록을 테이블 형식으로 표시한다.
`display.print_table()`을 사용하여 박스 드로잉 문자 기반 테이블을 출력한다.

출력 예시 (주문 있는 경우):
```
[ 주문 승인 / 거절 ]
------------------------------------------------------------
  승인 대기 중인 주문 목록
┌──────────┬────────────┬──────────────┬────────┬──────────┐
│ 주문 ID  │ 시료 ID    │ 고객명       │ 수량   │ 상태     │
├──────────┼────────────┼──────────────┼────────┼──────────┤
│ ORD-001  │ S001       │ 홍길동       │ 10     │ RESERVED │
├──────────┼────────────┼──────────────┼────────┼──────────┤
│ ORD-002  │ S002       │ 김철수       │  5     │ RESERVED │
└──────────┴────────────┴──────────────┴────────┴──────────┘
```

출력 예시 (주문 없는 경우):
```
[ 주문 승인 / 거절 ]
------------------------------------------------------------
  승인 대기 중인 주문이 없습니다.
```

구현 내역:
- `orders`가 비어있으면 `"  승인 대기 중인 주문이 없습니다."` 출력
- 비어있지 않으면 `"  승인 대기 중인 주문 목록"` 출력 후 `print_table()` 호출
  - 헤더: `["주문 ID", "시료 ID", "고객명", "수량", "상태"]`
  - 각 행: `[order.id, order.sampleId, order.customerName, str(order.quantity), order.status.value]`
  - 컬럼 너비: `[10, 10, 14, 6, 10]` (유니코드 너비 기준)
  - 상태 셀은 `colorize(order.status.value, Color.BLUE)`로 강조

### 4.2 `render_approved(order)` 출력 형식

```
render_approved(self, order: Order) -> None
```

승인 처리 성공 후 결과를 표시한다. 최종 상태(CONFIRMED 또는 PRODUCING)에 따라 다른 메시지와 색상을 사용한다.

출력 예시 (CONFIRMED 전환):
```
(빈 줄)
------------------------------------------------------------
  [완료] 주문이 승인되었습니다. (재고 충분 → CONFIRMED)
    주문 ID   : ORD-001
    시료 ID   : S001
    고객명    : 홍길동
    수량      : 10 개
    상태      : CONFIRMED
(엔터를 누르면 이전 메뉴로 돌아갑니다.)
```

출력 예시 (PRODUCING 전환):
```
(빈 줄)
------------------------------------------------------------
  [완료] 주문이 승인되었습니다. (재고 부족 → 생산 대기 등록)
    주문 ID   : ORD-002
    시료 ID   : S002
    고객명    : 김철수
    수량      : 15 개
    상태      : PRODUCING
(엔터를 누르면 이전 메뉴로 돌아갑니다.)
```

구현 내역:
- `print()` — 빈 줄
- `print_divider()`
- 상태별 완료 메시지:
  - `order.status == OrderStatus.CONFIRMED` → `print_success("주문이 승인되었습니다. (재고 충분 → CONFIRMED)")`
  - `order.status == OrderStatus.PRODUCING` → `print_success("주문이 승인되었습니다. (재고 부족 → 생산 대기 등록)")`
- `print(f"    주문 ID   : {order.id}")`
- `print(f"    시료 ID   : {order.sampleId}")`
- `print(f"    고객명    : {order.customerName}")`
- `print(f"    수량      : {order.quantity} 개")`
- 상태 색상:
  - CONFIRMED → `colorize(order.status.value, Color.GREEN)`
  - PRODUCING → `colorize(order.status.value, Color.YELLOW)`
- `print(f"    상태      : {colored_status}")`
- `pause()`

### 4.3 `render_rejected(order)` 출력 형식

```
render_rejected(self, order: Order) -> None
```

거절 처리 성공 후 결과를 표시한다.

출력 예시:
```
(빈 줄)
------------------------------------------------------------
  [완료] 주문이 거절되었습니다.
    주문 ID   : ORD-001
    시료 ID   : S001
    고객명    : 홍길동
    수량      : 10 개
    상태      : REJECTED
(엔터를 누르면 이전 메뉴로 돌아갑니다.)
```

구현 내역:
- `print()` — 빈 줄
- `print_divider()`
- `print_success("주문이 거절되었습니다.")`
- `print(f"    주문 ID   : {order.id}")`
- `print(f"    시료 ID   : {order.sampleId}")`
- `print(f"    고객명    : {order.customerName}")`
- `print(f"    수량      : {order.quantity} 개")`
- `print(f"    상태      : {colorize(order.status.value, Color.RED)}")`
- `pause()`

### 4.4 `render_error(message)` 출력 형식

```
render_error(self, message: str) -> None
```

`OrderView.render_error()`와 동일하게 `print_error(message)`를 호출한다.

출력 예시:
```
  [오류] RESERVED 상태의 주문만 처리 가능합니다.
```

---

## 5. `ApprovalController` 설계

**파일:** `src/controllers/approval_controller.py`

**임포트:**

```
from src.services.approval_service import ApprovalService
from src.repositories.order_repository import OrderRepository
from src.models.order import OrderStatus
from src.views.display import input_prompt, print_divider, print_error, print_header
from src.views.approval_view import ApprovalView
```

**MVC 패턴 기준:** `OrderController`와 동일한 구조를 따른다.

```
ApprovalController
├── __init__(self, service: ApprovalService, view: ApprovalView, order_repository: OrderRepository) -> None
├── run(self) -> None
├── _handle_approve(self) -> None
└── _handle_reject(self) -> None
```

### 5.1 생성자

| 항목 | 내용 |
|------|------|
| 파라미터 | `service: ApprovalService`, `view: ApprovalView`, `order_repository: OrderRepository` |
| 동작 | `self._service = service`, `self._view = view`, `self._order_repository = order_repository`로 저장 |
| 비고 | RESERVED 주문 목록 조회를 위해 `order_repository`를 직접 보유한다. 컨트롤러는 목록 조회만 수행하며 비즈니스 로직은 서비스에 위임한다. |

### 5.2 `run()` 흐름

```
while True:
    reserved_orders = self._order_repository.get_by_status(OrderStatus.RESERVED)
    self._view.render_reserved_list(reserved_orders)

    print_header("주문 승인 / 거절")
    (1) 승인
    (2) 거절
    (0) 돌아가기 출력
    print_divider()

    choice = input_prompt("선택")

    "1" → self._handle_approve()
    "2" → self._handle_reject()
    "0" → break
    그 외 → print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")
```

루프가 반복될 때마다 최신 RESERVED 목록을 다시 조회하여 표시한다.
이를 통해 이전 처리 결과가 목록에 즉시 반영된다.

### 5.3 `_handle_approve()` 상세

```
1. print_header("주문 승인 / 거절 > 승인")
2. print()

3. while True:
   a. order_id = input_prompt("주문 ID        ")
      — 빈 문자열이면 self._view.render_error("주문 ID를 입력해 주세요.") 후 continue
      — 비어있지 않으면 다음 단계로

   b. try:
          order = self._service.approve_order(order_id)
          break
      except ValueError as e:
          self._view.render_error(str(e))
          continue

4. self._view.render_approved(order)
```

### 5.4 `_handle_reject()` 상세

```
1. print_header("주문 승인 / 거절 > 거절")
2. print()

3. while True:
   a. order_id = input_prompt("주문 ID        ")
      — 빈 문자열이면 self._view.render_error("주문 ID를 입력해 주세요.") 후 continue
      — 비어있지 않으면 다음 단계로

   b. try:
          order = self._service.reject_order(order_id)
          break
      except ValueError as e:
          self._view.render_error(str(e))
          continue

4. self._view.render_rejected(order)
```

**설계 원칙:**
- 컨트롤러가 수행하는 유효성 검사(빈 order_id)는 UI 입력 편의 목적의 사전 필터링이다.
- 비즈니스 규칙 위반(미존재 주문 ID, RESERVED 외 상태)은 서비스가 `ValueError`로 처리하며 컨트롤러가 그대로 `render_error`에 전달한다.
- 유효한 처리가 완료될 때까지 루프를 반복한다.

---

## 6. `main.py` 수정 사항

### 6.1 `(3) 주문 승인/거절` 활성화 방법

현재 `main.py`는 `elif choice in ("3", "4", "5", "6"):` 분기에서 "아직 준비 중인 기능입니다."를 출력한다.

**수정 내용:**

1. 상단 임포트에 추가:
   ```
   from src.controllers.approval_controller import ApprovalController
   from src.repositories.production_queue import ProductionQueue
   from src.services.approval_service import ApprovalService
   from src.views.approval_view import ApprovalView
   ```

2. `_print_main_menu()` 함수에서 `(3) 주문 승인 / 거절` 줄의 `(준비 중)` 텍스트 제거:
   ```
   |  (3) 주문 승인 / 거절                                |
   ```

3. `main()` 함수 시그니처 변경 — `production_queue` 파라미터 추가:
   ```
   def main(
       sample_repository: SampleRepository | None = None,
       order_repository: OrderRepository | None = None,
       production_queue: ProductionQueue | None = None,
   ) -> None:
   ```

4. `main()` 함수 본문에 의존성 조립 추가:
   ```
   if production_queue is None:
       production_queue = ProductionQueue()

   approval_service = ApprovalService(sample_repository, order_repository, production_queue)
   approval_view = ApprovalView()
   approval_controller = ApprovalController(approval_service, approval_view, order_repository)
   ```

5. 메뉴 루프 분기 수정:
   ```
   if choice == "1":
       sample_controller.run()
   elif choice == "2":
       order_controller.run()
   elif choice == "3":
       approval_controller.run()
   elif choice in ("4", "5", "6"):
       print("\n  아직 준비 중인 기능입니다.")
   elif choice == "0":
       ...
   ```

### 6.2 의존성 주입 흐름

```
main()
├── SampleRepository (인메모리)
├── OrderRepository (인메모리)
├── ProductionQueue (인메모리 FIFO 큐)
│
├── SampleService(sample_repository)
│   └── SampleController(sample_service, SampleView())
│
├── OrderService(sample_repository, order_repository)
│   └── OrderController(order_service, OrderView())
│
└── ApprovalService(sample_repository, order_repository, production_queue)
    └── ApprovalController(approval_service, ApprovalView(), order_repository)
```

`ApprovalService`는 시료 재고·수율·생산시간 조회를 위해 `SampleRepository`를,
주문 상태 갱신을 위해 `OrderRepository`를,
생산 작업 등록을 위해 `ProductionQueue`를 공유한다.
세 저장소 모두 `main()`에서 생성된 단일 인스턴스를 공유한다.

---

## 7. `dummy.py` 수정 사항 (H-1 부분 해소)

### 7.1 현재 상태 및 문제점

Phase 3 완료 후 `dummy.py`의 현재 상태:

- RESERVED 2건: `OrderService.place_order()` 경유로 이미 처리됨 (Phase 3에서 해소)
- PRODUCING 1건, CONFIRMED 1건, RELEASED 2건: 여전히 `Order` 직접 생성 + `order_repo.add()` 방식으로 주입

Phase 4에서는 PRODUCING 1건을 `place_order()` → `approve_order()` 경로로 교체하여 H-1을 부분 해소한다.

### 7.2 수정 방법

`_inject()` 함수에 `ProductionQueue`를 추가로 주입받고, `ApprovalService`를 생성한다.

**함수 시그니처 변경:**

```
def _inject(
    sample_repo: SampleRepository,
    order_repo: OrderRepository,
    production_queue: ProductionQueue,
) -> None:
```

**추가 임포트:**

```
from src.repositories.production_queue import ProductionQueue
from src.services.approval_service import ApprovalService
```

**PRODUCING 주문 교체 로직:**

현재 PRODUCING 상태로 직접 주입되는 주문(세 번째 건, `registered[2]`, GaAs-100)을 다음 절차로 교체한다.

1. `order_service.place_order(sample.id, customer_name, quantity)`로 RESERVED 주문을 생성한다.
2. 반환된 `order.id`를 사용하여 `approval_service.approve_order(order.id)`를 호출한다.
3. GaAs-100 시료의 초기 재고는 `0`이므로 `재고(0) < 수량(N)` 조건을 만족하여 반드시 PRODUCING 분기로 진입한다.

이 교체 후 세 번째 주문은 `place_order` → `approve_order` 경로를 거쳐 PRODUCING 상태로 전환되고, `ProductionQueue`에도 `ProductionJob`이 등록된다.

**H-1 해소 범위:**

| 주문 건 | Phase 3 이전 | Phase 3 | Phase 4 | 비고 |
|---------|-------------|---------|---------|------|
| RESERVED 1건 | 직접 주입 | place_order 경유 | 변경 없음 | H-1 해소 완료 |
| RESERVED 1건 | 직접 주입 | place_order 경유 | 변경 없음 | H-1 해소 완료 |
| PRODUCING 1건 | 직접 주입 | 직접 주입 유지 | place_order + approve_order 경유 | H-1 부분 해소 |
| CONFIRMED 1건 | 직접 주입 | 직접 주입 유지 | 직접 주입 유지 | Phase 6에서 해소 예정 |
| RELEASED 2건 | 직접 주입 | 직접 주입 유지 | 직접 주입 유지 | Phase 7에서 해소 예정 |

**`main()` 함수 수정:**

```
def main() -> None:
    only = "--only" in sys.argv

    sample_repo = SampleRepository()
    order_repo = OrderRepository()
    production_queue = ProductionQueue()

    _inject(sample_repo, order_repo, production_queue)

    if not only:
        from main import main as run_main
        run_main(
            sample_repository=sample_repo,
            order_repository=order_repo,
            production_queue=production_queue,
        )
```

---

## 8. 테스트 명세

**파일:** `tests/phase4/test_approval_service.py`

### 픽스처 설계

각 테스트는 독립적인 저장소·큐·서비스 인스턴스를 사용한다.

```
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
    # 재고가 충분한 시료. yield_=0.8, avgProductionTime=5.5
    sample = Sample(id="S001", name="SiC-300", avgProductionTime=5.5, yield_=0.8, stock=20)
    sample_repo.add(sample)
    return sample

@pytest.fixture
def sample_no_stock(sample_repo):
    # 재고가 없는 시료. yield_=0.8, avgProductionTime=5.5
    sample = Sample(id="S002", name="GaAs-100", avgProductionTime=5.5, yield_=0.8, stock=0)
    sample_repo.add(sample)
    return sample

@pytest.fixture
def reserved_order_sufficient(order_repo, sample_with_stock):
    # stock(20) >= quantity(10) → CONFIRMED 분기
    order = Order(id="ORD-001", sampleId="S001", customerName="홍길동", quantity=10)
    order_repo.add(order)
    return order

@pytest.fixture
def reserved_order_deficit(order_repo, sample_no_stock):
    # stock(0) < quantity(7) → PRODUCING 분기, deficit=7
    order = Order(id="ORD-002", sampleId="S002", customerName="김철수", quantity=7)
    order_repo.add(order)
    return order
```

### 테스트 케이스 목록

---

#### TC-4-01: 재고 충분 시 승인 → CONFIRMED 전환 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `sample_with_stock` (stock=20), `reserved_order_sufficient` (quantity=10, status=RESERVED) |
| 입력 | `approve_order("ORD-001")` |
| 기대 결과 | 반환된 `order.status == OrderStatus.CONFIRMED` |

---

#### TC-4-02: 재고 충분 시 승인 → 재고 변경 없음 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `sample_with_stock` (stock=20), `reserved_order_sufficient` (quantity=10) |
| 입력 | `approve_order("ORD-001")` |
| 기대 결과 | 승인 후 `sample_with_stock.stock == 20` (재고 차감 없음) |

---

#### TC-4-03: 재고 정확히 같을 때 (`재고 == 수량`) → CONFIRMED 확인 [Happy Path — 경계값]

| 항목 | 내용 |
|------|------|
| 사전 조건 | stock=10인 시료, quantity=10인 RESERVED 주문 |
| 입력 | `approve_order(order_id)` |
| 기대 결과 | `order.status == OrderStatus.CONFIRMED`. 생산 큐가 비어있음(`production_queue.is_empty() == True`). |

---

#### TC-4-04: 재고 부족 시 승인 → PRODUCING 전환 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `sample_no_stock` (stock=0), `reserved_order_deficit` (quantity=7, status=RESERVED) |
| 입력 | `approve_order("ORD-002")` |
| 기대 결과 | 반환된 `order.status == OrderStatus.PRODUCING` |

---

#### TC-4-05: 재고 부족 시 승인 → 생산 큐 등록 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `sample_no_stock` (stock=0), `reserved_order_deficit` (quantity=7) |
| 입력 | `approve_order("ORD-002")` |
| 기대 결과 | `production_queue.is_empty() == False`. `production_queue.peek().orderId == "ORD-002"`. |

---

#### TC-4-06: 실 생산량 계산 정확성 검증 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | sample_no_stock (yield_=0.8, stock=0), 주문 quantity=7 → deficit=7 |
| 입력 | `approve_order("ORD-002")` |
| 기대 결과 | `production_queue.peek().plannedQuantity == 10` — `ceil(7 / (0.8 × 0.9)) = ceil(9.722...) = 10` |

---

#### TC-4-07: 총 생산 시간 계산 정확성 검증 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | sample_no_stock (avgProductionTime=5.5, yield_=0.8, stock=0), 주문 quantity=7 → plannedQuantity=10 |
| 입력 | `approve_order("ORD-002")` |
| 기대 결과 | `production_queue.peek().totalProductionTime == 55.0` — `5.5 × 10 = 55.0` |

---

#### TC-4-08: 거절 → REJECTED 전환 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `sample_with_stock`, `reserved_order_sufficient` (status=RESERVED) |
| 입력 | `reject_order("ORD-001")` |
| 기대 결과 | 반환된 `order.status == OrderStatus.REJECTED` |

---

#### TC-4-09: 거절 → 생산 큐 미등록 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `sample_with_stock`, `reserved_order_sufficient` |
| 입력 | `reject_order("ORD-001")` |
| 기대 결과 | `production_queue.is_empty() == True` |

---

#### TC-4-10: RESERVED 외 상태(CONFIRMED) 주문 승인 시도 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | status=CONFIRMED인 주문이 저장소에 존재 |
| 입력 | `approve_order(order_id)` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"RESERVED 상태의 주문만 처리 가능합니다."` 와 일치한다. |

---

#### TC-4-11: RESERVED 외 상태(PRODUCING) 주문 거절 시도 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | status=PRODUCING인 주문이 저장소에 존재 |
| 입력 | `reject_order(order_id)` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"RESERVED 상태의 주문만 처리 가능합니다."` 와 일치한다. |

---

#### TC-4-12: 존재하지 않는 주문 ID 승인 시도 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 주문 저장소 비어있음 |
| 입력 | `approve_order("ORD-999")` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"존재하지 않는 주문 ID입니다."` 와 일치한다. |

---

#### TC-4-13: 존재하지 않는 주문 ID 거절 시도 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 주문 저장소 비어있음 |
| 입력 | `reject_order("ORD-999")` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"존재하지 않는 주문 ID입니다."` 와 일치한다. |

---

#### TC-4-14: `_calculate_production_quantity` 직접 단위 검증 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 없음 |
| 입력 | `service._calculate_production_quantity(deficit=7, yield_=0.8)` |
| 기대 결과 | 반환값 `== 10` |

---

#### TC-4-15: 생산 큐 FIFO 순서로 등록 확인 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 재고 0인 시료, RESERVED 주문 2건 (ORD-001, ORD-002) |
| 입력 | `approve_order("ORD-001")` 후 `approve_order("ORD-002")` 순서로 호출 |
| 기대 결과 | `production_queue.get_all()[0].orderId == "ORD-001"`, `production_queue.get_all()[1].orderId == "ORD-002"` |

---

## 9. 완료 기준

### PASS 조건

- `tests/phase4/test_approval_service.py` 내 모든 테스트 케이스가 PASS 상태여야 한다.
- 테스트 실행 명령: `pytest tests/phase4/ -v`
- 단 하나의 FAILED 또는 ERROR도 허용하지 않는다.

### 커버리지 기준

- Phase 4 구현 대상 파일(`src/services/approval_service.py`)의 라인 커버리지가 **90% 이상**이어야 한다.
- 커버리지 측정 명령: `pytest tests/phase4/ --cov=src/services/approval_service --cov-report=term-missing`

### 동작 확인 기준

- `python main.py` 실행 후 메인 메뉴에서 `(3) 주문 승인 / 거절` 선택 시 `(준비 중)` 메시지 없이 승인/거절 화면으로 진입한다.
- RESERVED 주문 목록이 테이블 형식으로 표시된다.
- 승인 선택 후 주문 ID 입력 시:
  - 재고 충분: CONFIRMED로 전환되고 결과가 초록색으로 표시된다.
  - 재고 부족: PRODUCING으로 전환되고 결과가 노란색으로 표시된다.
- 거절 선택 후 주문 ID 입력 시 REJECTED로 전환되고 결과가 표시된다.
- 미존재 주문 ID 또는 RESERVED 외 상태 주문 처리 시도 시 오류 메시지가 출력되고 재입력이 요청된다.
- `python dummy.py` 실행 시 오류 없이 완료되고 `main.py`가 자동으로 시작된다.
- PRODUCING 1건이 `place_order` → `approve_order` 경로를 통해 생성되어 `ProductionQueue`에 `ProductionJob`이 정상 등록된다.
