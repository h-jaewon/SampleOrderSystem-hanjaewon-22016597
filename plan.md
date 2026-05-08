# plan.md - 반도체 시료 생산 주문 관리 시스템 구현 계획
> 기준 문서: PRD.md v1.0 | 최초 작성일: 2026-05-08

---

## 개요

### 목표

PRD.md에 정의된 **S-Semi 반도체 시료 생산 주문 관리 시스템**을 Phase 단위로 점진적으로 구현한다.
각 Phase는 독립적으로 테스트 가능한 기능 단위로 구성되며, 이전 Phase가 안정화된 후 다음 Phase로 진행한다.

### 워크플로우 (Phase별 반복 사이클)

```
[SubAgent2: code-implementation]
  └─ 해당 Phase 코드 구현
        │
        ▼
[SubAgent6: clean-code]
  └─ SOLID·DRY·KISS·YAGNI 원칙 위반 탐지
  └─ 코드 스멜·네이밍·복잡도 검토 및 리팩토링
  └─ 기능 동작을 변경하지 않는 순수 구조 개선
        │
        ▼
[SubAgent3: test-verifier]
  └─ pytest + pytest-cov 테스트 작성 및 실행
  └─ HTML 커버리지 리포트 생성 (htmlcov/)
  └─ 리팩토링 후 기존 동작 보존 여부 검증
  └─ 사용자에게 검토 요청
        │
        ▼
[사용자 검토]
  └─ 결과 확인 후 진행 여부 결정
        │
     PASS ▼
[SubAgent4: compliance-verifier]
  └─ OWASP Top 10 보안 취약점 점검
  └─ 코딩 표준·라이선스·규제 요건 준수 확인
        │
     PASS ▼
[SubAgent5: repository-governance]
  └─ SubAgent6·SubAgent3·SubAgent4 PASS 여부 최종 확인
  └─ 브랜치 확인 → diff 검토 → 컨텍스트 문서 갱신
  └─ Conventional Commit 메시지 생성
  └─ git commit & push
        │
        ▼
  다음 Phase로 진행
```

### 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11+ |
| 테스트 프레임워크 | pytest |
| 커버리지 도구 | pytest-cov (HTML 리포트: `htmlcov/`) |
| 실행 환경 | CLI (콘솔) |
| 버전 관리 | Git / GitHub |

### 브랜치 전략

| 브랜치 | 용도 |
|--------|------|
| `master` | 안정적으로 검증된 코드만 존재 |
| `feat/phase-N-<설명>` | 각 Phase 구현용 작업 브랜치 |

---

## 프로젝트 디렉터리 구조

```
sampleordersystem/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── sample.py           # Sample 엔티티
│   │   ├── order.py            # Order 엔티티 + OrderStatus 열거형
│   │   └── production_job.py   # ProductionJob 엔티티
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── sample_repository.py   # 시료 인메모리 저장소
│   │   ├── order_repository.py    # 주문 인메모리 저장소
│   │   └── production_queue.py    # FIFO 생산 대기 큐
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sample_service.py      # 시료 등록/조회/검색 비즈니스 로직
│   │   ├── order_service.py       # 주문 접수 비즈니스 로직
│   │   ├── approval_service.py    # 주문 승인/거절 + 재고 분기 로직
│   │   ├── monitoring_service.py  # 주문량/재고량 집계 로직
│   │   ├── production_service.py  # 생산 라인 조회 + 완료 처리 로직
│   │   └── shipment_service.py    # 출고 처리 로직
│   └── ui/
│       ├── __init__.py
│       ├── display.py          # 공통 UI 헬퍼 (헤더, 구분선, 프롬프트)
│       ├── main_menu.py        # 메인 메뉴 화면
│       ├── sample_menu.py      # 시료 관리 화면
│       ├── order_menu.py       # 시료 주문 화면
│       ├── approval_menu.py    # 주문 승인/거절 화면
│       ├── monitoring_menu.py  # 모니터링 화면
│       ├── production_menu.py  # 생산 라인 조회 화면
│       └── shipment_menu.py    # 출고 처리 화면
├── tests/
│   ├── __init__.py
│   ├── phase1/
│   │   ├── __init__.py
│   │   └── test_models.py
│   ├── phase2/
│   │   ├── __init__.py
│   │   └── test_sample_service.py
│   ├── phase3/
│   │   ├── __init__.py
│   │   └── test_order_service.py
│   ├── phase4/
│   │   ├── __init__.py
│   │   └── test_approval_service.py
│   ├── phase5/
│   │   ├── __init__.py
│   │   └── test_monitoring_service.py
│   ├── phase6/
│   │   ├── __init__.py
│   │   └── test_production_service.py
│   ├── phase7/
│   │   ├── __init__.py
│   │   └── test_shipment_service.py
│   └── phase8/
│       ├── __init__.py
│       └── test_integration.py
├── htmlcov/                    # pytest-cov HTML 리포트 출력 디렉터리
├── .gitignore
├── pytest.ini
├── requirements.txt
├── CURRENT_STATE.md            # 현재 구현 상태 (SubAgent5 관리)
├── TASKS.md                    # 태스크 진행 상황 (SubAgent5 관리)
├── DECISIONS.md                # 아키텍처 결정 기록 (SubAgent5 관리)
├── PRD.md
└── plan.md
```

---

## pytest.ini 설정

```ini
[pytest]
testpaths = tests
addopts = --cov=src --cov-report=html:htmlcov --cov-report=term-missing -v
```

## requirements.txt

```
pytest>=8.0.0
pytest-cov>=5.0.0
```

---

## Phase 구현 계획

---

### Phase 1: 도메인 모델 및 저장소 기반 구축

**브랜치:** `feat/phase-1-domain-models`

**목표:** 시스템 전체의 뼈대가 되는 데이터 모델과 인메모리 저장소를 구현한다.
이후 모든 Phase는 이 기반 위에 서비스 레이어를 추가하는 방식으로 진행된다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/models/sample.py` | `Sample` 데이터 클래스 (id, name, avgProductionTime, yield_, stock) |
| `src/models/order.py` | `OrderStatus` Enum (RESERVED/REJECTED/PRODUCING/CONFIRMED/RELEASED), `Order` 데이터 클래스 (id, sampleId, customerName, quantity, status, createdAt) |
| `src/models/production_job.py` | `ProductionJob` 데이터 클래스 (orderId, sampleId, plannedQuantity, totalProductionTime) |
| `src/repositories/sample_repository.py` | 인메모리 시료 저장소 (add, get, get_all, find_by_name) |
| `src/repositories/order_repository.py` | 인메모리 주문 저장소 (add, get, get_all, get_by_status) |
| `src/repositories/production_queue.py` | FIFO 생산 대기 큐 (enqueue, dequeue, peek, get_all, is_empty) |

**PRD 대응 요구사항:** SM-01 (저장소 레벨 ID 중복 방지), OR-04, OR-05, 7.1, 7.2, 7.3, 7.4

**ID 생성 규칙:**
- Sample ID: `S{순번:03d}` → `S001`, `S002`, ...
- Order ID: `ORD-{순번:03d}` → `ORD-001`, `ORD-002`, ...

> SM-01 구현 책임 분리: 저장소에서 ID 중복 방지(Phase 1), 서비스에서 ID 자동 생성 시 중복 없는 값 생성(Phase 2)

**테스트 대상 (`tests/phase1/test_models.py`):**
- Sample 객체 생성 및 속성 접근
- Order 객체 생성 및 상태 초기값 검증
- Order 생성 시 createdAt 자동 설정 확인 (datetime 타입, 현재 시각 기준)
- OrderStatus 열거형 전체 값 존재 확인
- ProductionJob 객체 생성 검증
- SampleRepository CRUD 동작
- OrderRepository 상태별 필터링
- ProductionQueue FIFO 순서 보장
- ProductionQueue 빈 큐에서 dequeue 시 예외 처리

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상

---

### Phase 2: 시료 관리 서비스

**브랜치:** `feat/phase-2-sample-service`

**목표:** 시료 등록, 전체 조회, 이름 검색 비즈니스 로직을 구현한다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/sample_service.py` | `register_sample()`, `get_all_samples()`, `search_samples_by_name()` |

**PRD 대응 요구사항:** SM-01 ~ SM-06, 5.2.1, 5.2.2, 5.2.3

**비즈니스 규칙:**
- 이름 빈 값 → `ValueError: 시료 이름은 필수 입력값입니다.`
- avgProductionTime ≤ 0 → `ValueError: 평균 생산시간은 0보다 커야 합니다.`
- yield_ ≤ 0 또는 yield_ > 1 → `ValueError: 수율은 0 초과 1 이하여야 합니다.`
- ID 자동 부여: 현재 저장된 시료 수 + 1 기반으로 `S{순번:03d}` 생성
- 검색: 대소문자 무관 부분 일치 (`in` 연산자 또는 `lower()` 활용)

**테스트 대상 (`tests/phase2/test_sample_service.py`):**
- 정상 시료 등록 및 반환값 검증
- 이름 빈 값 입력 시 ValueError
- avgProductionTime 경계값 (0, 음수, 정상값)
- yield_ 경계값 (0, 1 초과, 0 초과~1 이하 정상값)
- 전체 조회 시 등록된 시료 수 일치
- 등록된 시료 없을 때 빈 리스트 반환
- 검색어 부분 일치 결과 반환
- 검색 결과 없을 때 빈 리스트 반환
- 복수 시료 등록 시 ID 중복 없음 확인

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상

---

### Phase 3: 시료 주문 서비스

**브랜치:** `feat/phase-3-order-service`

**목표:** 주문 접수 비즈니스 로직을 구현한다. 등록 즉시 RESERVED 상태로 저장된다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/order_service.py` | `place_order()` |

**PRD 대응 요구사항:** OR-01 ~ OR-05, 5.3

**비즈니스 규칙:**
- 존재하지 않는 sampleId → `ValueError: 등록되지 않은 시료 ID입니다.`
- customerName 빈 값 → `ValueError: 고객명은 필수 입력값입니다.`
- quantity < 1 또는 정수 아님 → `ValueError: 주문 수량은 1 이상의 정수여야 합니다.`
- 등록 즉시 status = `OrderStatus.RESERVED`
- ID 자동 부여: 현재 주문 수 + 1 기반으로 `ORD-{순번:03d}` 생성

**테스트 대상 (`tests/phase3/test_order_service.py`):**
- 정상 주문 등록 및 RESERVED 상태 확인
- 존재하지 않는 sampleId 입력 시 ValueError
- customerName 빈 값 시 ValueError
- quantity 경계값 (0, 음수, 1, 양수)
- 주문 ID 자동 부여 및 중복 없음 확인
- createdAt 자동 설정 확인

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상

---

### Phase 4: 주문 승인 / 거절 서비스

**브랜치:** `feat/phase-4-approval-service`

**목표:** 주문 승인·거절 및 재고 기반 자동 상태 분기 로직을 구현한다.
이 Phase가 시스템의 핵심 비즈니스 로직이다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/approval_service.py` | `approve_order()`, `reject_order()`, `_calculate_production_quantity()` |

**PRD 대응 요구사항:** AP-01 ~ AP-06, 5.4

**비즈니스 규칙:**
- 승인 대상은 RESERVED 상태의 주문만 가능
  - 다른 상태 주문 처리 시 → `ValueError: RESERVED 상태의 주문만 처리 가능합니다.`
- 승인 시 재고 분기:
  - `현재 재고 >= 주문 수량` → 상태: `CONFIRMED` (재고 차감은 출고 처리 시점에 수행, 승인 시 차감 없음)
  - `현재 재고 < 주문 수량` → 실 생산량 계산 후 생산 대기 큐 등록, 상태: `PRODUCING`
- 실 생산량 계산 공식: `math.ceil(부족분 / (수율 × 0.9))`
  - 부족분 = 주문 수량 - 현재 재고
- 총 생산 시간 계산: `평균 생산시간 × 실 생산량`
- 거절 시 상태: `REJECTED` (다른 처리 없음)

**테스트 대상 (`tests/phase4/test_approval_service.py`):**
- 재고 충분 시 승인 → CONFIRMED 전환 확인
- 재고 부족 시 승인 → PRODUCING 전환 + 생산 큐 등록 확인
- 재고 정확히 같을 때 (`재고 == 수량`) → CONFIRMED 확인
- 거절 → REJECTED 전환 확인
- RESERVED 외 상태 주문 승인 시도 시 ValueError
- 실 생산량 계산 정확성: `ceil(7 / (0.8 × 0.9)) = ceil(9.72) = 10` 검증
- 총 생산 시간 계산 정확성: `5.5 × 10 = 55.0` 검증
- 생산 큐 FIFO 순서로 등록되는지 확인

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상

---

### Phase 5: 모니터링 서비스

**브랜치:** `feat/phase-5-monitoring-service`

**목표:** 주문 현황 집계와 시료별 재고 현황 조회 로직을 구현한다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/monitoring_service.py` | `get_order_summary()`, `get_stock_status()`, `_classify_stock()` |

**PRD 대응 요구사항:** MN-01 ~ MN-04, 5.5.1, 5.5.2

**비즈니스 규칙:**
- `get_order_summary()`: REJECTED 제외한 상태별 주문 건수 집계 + 각 상태의 주문 목록 반환
- `get_stock_status()`: 시료별 현재 재고 + 재고 상태 분류
- 재고 상태 분류 (`_classify_stock()`):
  - `고갈`: 현재 재고 == 0
  - `부족`: 현재 재고 > 0 이고, PRODUCING 중인 해당 시료 주문이 존재하는 경우
  - `여유`: 그 외

**테스트 대상 (`tests/phase5/test_monitoring_service.py`):**
- REJECTED 주문이 집계에서 제외되는지 확인
- 상태별 카운트 정확성 검증
- 재고 0일 때 `고갈` 분류
- 재고 > 0이고 PRODUCING 주문 존재 시 `부족` 분류
- 재고 충분 시 `여유` 분류
- 시료가 없을 때 빈 결과 반환

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상

---

### Phase 6: 생산 라인 서비스

**브랜치:** `feat/phase-6-production-service`

**목표:** 생산 라인 현황 조회와 생산 완료 처리 로직을 구현한다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/production_service.py` | `get_production_status()`, `complete_production()` |

**PRD 대응 요구사항:** PL-01 ~ PL-04, 5.6

**비즈니스 규칙:**
- `get_production_status()`:
  - 현재 생산 중: 큐의 맨 앞(peek) 항목 반환
    - 반환 데이터: ProductionJob(orderId, sampleId, plannedQuantity, totalProductionTime) + Order.quantity (Order 엔티티에서 조회하여 함께 반환)
  - 생산 대기 큐: peek 제외한 나머지 항목을 FIFO 순서로 반환 (동일하게 Order.quantity 포함)
  - 큐가 비어있으면 빈 결과 반환
- `complete_production()`:
  - 큐에서 맨 앞 항목 dequeue
  - 해당 주문의 상태를 `PRODUCING` → `CONFIRMED`로 전환
  - 생산된 수량(plannedQuantity)을 해당 시료의 재고(stock)에 추가 (PRD 4.3 및 PL-03 명시: `stock += 실 생산량`)
  - 큐가 비어있으면 → `ValueError: 진행 중인 생산 작업이 없습니다.`

**테스트 대상 (`tests/phase6/test_production_service.py`):**
- 생산 중인 항목이 있을 때 현황 조회 정확성
- 대기 큐 FIFO 순서 반환 확인
- 큐가 비어있을 때 빈 결과 반환
- 생산 완료 시 PRODUCING → CONFIRMED 전환
- 생산 완료 시 재고 증가 검증 (plannedQuantity만큼)
- 빈 큐에서 complete_production 시 ValueError
- 복수 항목 연속 완료 시 FIFO 순서 처리 확인

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상

---

### Phase 7: 출고 처리 서비스

**브랜치:** `feat/phase-7-shipment-service`

**목표:** CONFIRMED 상태 주문의 출고 처리 로직을 구현한다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/shipment_service.py` | `get_confirmed_orders()`, `release_order()` |

**PRD 대응 요구사항:** RL-01 ~ RL-03, 5.7

**비즈니스 규칙:**
- `get_confirmed_orders()`: CONFIRMED 상태 주문 목록 반환
- `release_order(order_id)`:
  - 해당 주문이 존재하지 않으면 → `ValueError: 존재하지 않는 주문 ID입니다.`
  - 해당 주문이 CONFIRMED 상태가 아니면 → `ValueError: CONFIRMED 상태의 주문만 출고 처리 가능합니다.`
  - 상태를 `CONFIRMED` → `RELEASED`로 전환
  - 해당 시료의 재고에서 주문 수량만큼 차감

**테스트 대상 (`tests/phase7/test_shipment_service.py`):**
- CONFIRMED 주문 목록 조회 정확성
- 정상 출고 처리 → RELEASED 전환 확인
- 출고 처리 후 재고 차감 확인
- 존재하지 않는 주문 ID 입력 시 ValueError
- CONFIRMED 아닌 상태 주문 출고 시도 시 ValueError
- CONFIRMED 주문 없을 때 빈 목록 반환

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상

---

### Phase 8: UI 레이어 및 시스템 통합

**브랜치:** `feat/phase-8-ui-integration`

**목표:** CLI UI 레이어를 구현하고 전체 시스템을 통합한다. 메인 진입점(`main.py`)을 작성하여 실행 가능한 완성 시스템을 완성한다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/ui/display.py` | `print_header()`, `print_divider()`, `print_box()`, `input_prompt()` 공통 UI 유틸 |
| `src/ui/main_menu.py` | 메인 메뉴 화면 + 요약 정보 표시 |
| `src/ui/sample_menu.py` | 시료 관리 서브메뉴 (등록/조회/검색) |
| `src/ui/order_menu.py` | 시료 주문 화면 |
| `src/ui/approval_menu.py` | 주문 승인/거절 화면 |
| `src/ui/monitoring_menu.py` | 모니터링 화면 (주문량/재고량) |
| `src/ui/production_menu.py` | 생산 라인 조회 화면 |
| `src/ui/shipment_menu.py` | 출고 처리 화면 |
| `main.py` | 시스템 진입점 (루트 디렉터리에 위치) |

**PRD 대응 요구사항:** 5.1 (메인 메뉴), 5.2~5.7 (각 기능의 UI 레이어), 비기능 요구사항 전체 (6장)

**역할 구분 설계 결정:**
- PRD 3.2에서 고객·주문 담당자·생산 담당자 3역할을 정의하나, 이 시스템은 단일 콘솔 환경으로 별도 로그인·인증·인가를 구현하지 않는다.
- 역할 구분은 메뉴 진입점으로 대체한다: 고객은 `(2) 시료 주문` 메뉴를, 생산 담당자는 그 외 메뉴를 사용한다.

**UI 공통 규칙:**
- 모든 화면: 헤더 `[ 메뉴명 > 서브메뉴명 ]` 형식
- 구분선: `---` 또는 `===` 사용
- 입력 프롬프트: `>> ` 형식
- 잘못된 입력 시 오류 메시지 출력 후 재입력 요청 (시스템 종료 없음)
- 작업 완료 후: `엔터를 누르면 메인 메뉴로 돌아갑니다.` 메시지

**메인 메뉴 요약 정보:**
- 등록된 시료 수
- 총 재고 수량 (모든 시료 stock 합계)
- RESERVED 주문 건수
- PRODUCING 주문 건수

**테스트 대상 (`tests/phase8/test_integration.py`):**
- 전체 시나리오 통합 테스트: 시료 등록 → 주문 → 승인(재고 부족) → 생산 완료 → 출고 처리
- 전체 시나리오 통합 테스트: 시료 등록 → 주문 → 승인(재고 충분) → 출고 처리
- 잘못된 메뉴 번호 입력 시 재입력 유도 (시스템 종료 없음) — PRD 5.1, 6장 비기능 요구사항
- `0` 입력 시 종료 처리
- 시료 주문 화면에서 미등록 시료 ID 입력 시 오류 메시지 출력 후 재입력 — PRD OR-01
- 주문 승인/거절 화면에서 존재하지 않는 주문 ID 입력 시 오류 메시지 출력 후 재입력
- 출고 처리 화면에서 CONFIRMED 아닌 주문 ID 입력 시 오류 메시지 출력 후 재입력 — PRD RL-02

**완료 기준:** 통합 시나리오 테스트 PASS, 커버리지 85% 이상

---

## 컨텍스트 문서 관리 (SubAgent5 담당)

각 Phase commit 시 SubAgent5(repository-governance)가 아래 문서를 자동 갱신한다.

### CURRENT_STATE.md
현재 구현된 Phase, 마지막 변경 내용, 알려진 미해결 이슈, 다음 예정 작업을 기록한다.

### TASKS.md
각 Phase의 완료(`[x]`) / 진행 중(`[ ]`) / 대기(`[ ]`) 상태를 추적한다.

```
## 완료 [x]
- [x] Phase 1: 도메인 모델 및 저장소 기반 구축

## 진행 중 [ ]
- [ ] Phase 2: 시료 관리 서비스

## 대기 [ ]
- [ ] Phase 3: 시료 주문 서비스
- [ ] Phase 4: 주문 승인/거절 서비스
- [ ] Phase 5: 모니터링 서비스
- [ ] Phase 6: 생산 라인 서비스
- [ ] Phase 7: 출고 처리 서비스
- [ ] Phase 8: UI 레이어 및 시스템 통합
```

### DECISIONS.md
각 Phase에서 내린 아키텍처·설계 결정사항을 날짜와 함께 기록한다.

---

## 테스트 실행 명령

```bash
# 전체 테스트 + HTML 커버리지 리포트
pytest

# 특정 Phase만 실행
pytest tests/phase1/ -v

# HTML 리포트 열기 (Windows)
start htmlcov/index.html
```

---

## Phase별 Commit Message 예시

```
feat(phase-1): 도메인 모델 및 인메모리 저장소 구현
feat(phase-2): 시료 관리 서비스 구현 (등록/조회/검색)
feat(phase-3): 시료 주문 서비스 구현 (RESERVED 상태 등록)
feat(phase-4): 주문 승인/거절 서비스 구현 (재고 기반 자동 분기)
feat(phase-5): 모니터링 서비스 구현 (주문량/재고량 집계)
feat(phase-6): 생산 라인 서비스 구현 (FIFO 큐 + 완료 처리)
feat(phase-7): 출고 처리 서비스 구현 (CONFIRMED -> RELEASED)
feat(phase-8): UI 레이어 및 시스템 통합 완성
```
