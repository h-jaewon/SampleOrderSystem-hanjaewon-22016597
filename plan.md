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
  └─ 해당 Phase 코드 구현 (서비스 + UI 포함)
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
        │
        ▼
[사용자 검토]
  └─ pytest 결과 확인
  └─ `python main.py` 직접 실행 → 구현된 기능 interactive 테스트
  └─ 진행 여부 결정
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

> **핵심 원칙:** Phase 2부터 모든 Phase는 서비스 레이어와 해당 UI를 함께 구현한다.
> 각 Phase 완료 시 `python main.py`를 실행하면 그 시점까지 구현된 기능을 직접 사용할 수 있어야 한다.

### 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11+ |
| 테스트 프레임워크 | pytest |
| 커버리지 도구 | pytest-cov (HTML 리포트: `htmlcov/`) |
| 실행 환경 | CLI (콘솔) |
| UI 아키텍처 | MVC (Model-View-Controller) |
| 더미 데이터 | Faker (Korean locale) |
| 버전 관리 | Git / GitHub |
| 데이터 저장소 | SQLite (sampleordersystem.db) |

### 브랜치 전략

| 브랜치 | 용도 |
|--------|------|
| `master` | 안정적으로 검증된 코드만 존재 |
| `feat/phase-N-<설명>` | 각 Phase 구현용 작업 브랜치 |

---

## UI 아키텍처 (MVC)

mvc-poc 참고: Model / View / Controller 세 레이어를 엄격히 분리한다.

| 레이어 | 책임 | 위치 |
|--------|------|------|
| **Model** | 도메인 엔티티, 저장소, 비즈니스 로직 | `src/models/`, `src/repositories/`, `src/services/` |
| **View** | 순수 출력 포맷팅. 서비스 직접 호출 금지. 데이터를 받아 화면에 표시만 함 | `src/views/` |
| **Controller** | 사용자 입력 수신 → 서비스 호출 → View에 결과 전달. 비즈니스 로직 구현 금지 | `src/controllers/` |

```
# 데이터 흐름
사용자 입력
    → Controller.handle_*(input)
        → Service.*(...)          ← 비즈니스 로직
        → View.render_*(result)   ← 순수 출력
```

### View 구현 원칙 (monitor-poc 참고)
- ANSI 색상코드로 상태 강조 (여유=초록, 부족=노랑, 고갈=빨강, RESERVED=파랑 등)
- 한글 문자 유니코드 너비 보정 (`unicodedata.east_asian_width`) — 테이블 정렬 정확성 확보
- 박스 드로잉 문자(`┌─┬─┐`) 사용 테이블 포맷

---

## 더미 데이터 (gen-dummy-poc 참고)

`dummy.py` 스크립트를 루트에 두어 `python dummy.py` 실행 시 시스템에 테스트 데이터를 즉시 주입한다.

```bash
python dummy.py          # 기본 더미 데이터 주입 후 main.py 자동 시작
python dummy.py --only   # 더미 주입만 (main.py 실행 안 함)
```

주입 내용:
- 시료 5종 (Si-Wafer-200, SiC-300, GaAs-100, InP-150, GaN-200) + 각 초기 재고
- 주문 6건 (RESERVED 2건, CONFIRMED 1건, PRODUCING 1건, RELEASED 2건)

---

## 프로젝트 디렉터리 구조

```
sampleordersystem/
├── src/
│   ├── __init__.py
│   ├── database.py                # SQLite 연결 및 테이블 초기화
│   ├── models/
│   │   ├── __init__.py
│   │   ├── sample.py              # Sample 엔티티
│   │   ├── order.py               # Order 엔티티 + OrderStatus 열거형
│   │   └── production_job.py      # ProductionJob 엔티티
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── sample_repository.py   # SQLite 기반 시료 저장소
│   │   ├── order_repository.py    # SQLite 기반 주문 저장소
│   │   └── production_queue.py    # SQLite 기반 FIFO 생산 대기 큐
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sample_service.py      # 시료 등록/조회/검색
│   │   ├── order_service.py       # 주문 접수
│   │   ├── approval_service.py    # 주문 승인/거절 + 재고 분기
│   │   ├── monitoring_service.py  # 주문량/재고량 집계
│   │   ├── production_service.py  # 생산 라인 조회 + 완료 처리
│   │   └── shipment_service.py    # 출고 처리
│   ├── controllers/               # MVC — Controller 레이어
│   │   ├── __init__.py
│   │   ├── sample_controller.py   # 시료 관리 입력 처리
│   │   ├── order_controller.py    # 시료 주문 입력 처리
│   │   ├── approval_controller.py # 승인/거절 입력 처리
│   │   ├── monitoring_controller.py
│   │   ├── production_controller.py
│   │   └── shipment_controller.py
│   └── views/                     # MVC — View 레이어 (순수 출력)
│       ├── __init__.py
│       ├── display.py             # 공통 UI 유틸 (헤더, 구분선, 색상, 테이블)
│       ├── sample_view.py
│       ├── order_view.py
│       ├── approval_view.py
│       ├── monitoring_view.py     # ANSI 색상 + 유니코드 테이블
│       ├── production_view.py
│       └── shipment_view.py
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
├── sampleordersystem.db           # SQLite 데이터베이스 파일 (런타임 생성)
├── htmlcov/                    # pytest-cov HTML 리포트 출력 디렉터리
├── .gitignore
├── htmlcov/                       # pytest-cov HTML 리포트
├── .gitignore
├── pytest.ini
├── requirements.txt
├── main.py                        # 시스템 진입점 (의존성 조립 + 메뉴 루프)
├── dummy.py                       # 더미 데이터 주입 스크립트
├── CURRENT_STATE.md
├── TASKS.md
├── DECISIONS.md
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
faker>=24.0.0
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
| `src/repositories/sample_repository.py` | SQLite 기반 시료 저장소 (add, get, get_all, find_by_name, update_stock). 저장소는 생성 시 자동으로 SQLite DB를 초기화한다. |
| `src/repositories/order_repository.py` | SQLite 기반 주문 저장소 (add, get, get_all, get_by_status, update_status). 저장소는 생성 시 자동으로 SQLite DB를 초기화한다. |
| `src/repositories/production_queue.py` | SQLite 기반 FIFO 생산 대기 큐 (enqueue, dequeue, peek, get_all, is_empty). 저장소는 생성 시 자동으로 SQLite DB를 초기화한다. |

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

### Phase 2: 시료 관리 서비스 + UI

**브랜치:** `feat/phase-2-sample-service`

**목표:** 시료 등록/조회/검색 비즈니스 로직과 UI를 함께 구현한다.
Phase 2 완료 후 `python main.py` 실행 시 시료 관리 기능을 직접 사용할 수 있다.

**구현 대상 파일:**

| 파일 | 구현 내용 | 비고 |
|------|---------|------|
| `src/services/sample_service.py` | `register_sample()`, `get_all_samples()`, `search_samples_by_name()` | 서비스 레이어 (완료) |
| `src/views/__init__.py` | 빈 패키지 파일 | MVC 리팩터링 |
| `src/views/display.py` | 공통 UI 유틸 + ANSI 색상 + 유니코드 테이블 헬퍼 | `src/ui/display.py` 이전·확장 |
| `src/views/sample_view.py` | 시료 목록/등록 결과/검색 결과 렌더링 (순수 출력만) | MVC View |
| `src/controllers/__init__.py` | 빈 패키지 파일 | MVC 리팩터링 |
| `src/controllers/sample_controller.py` | 시료 관리 입력 처리 → service 호출 → view 렌더링 | MVC Controller |
| `dummy.py` | 시료 5종 + 주문 6건 더미 데이터 주입 스크립트 | Faker Korean |
| `main.py` (수정) | `(1) 시료 관리`만 활성화. `src/ui/` → `src/controllers/` 경로로 교체 | MVC 적용 |

> **리팩터링 사항:** Phase 2 초기 구현의 `src/ui/` 구조를 MVC 패턴(`src/views/` + `src/controllers/`)으로 전환한다.
> `src/ui/display.py` → `src/views/display.py` (ANSI 색상 및 유니코드 테이블 기능 추가)
> `src/ui/sample_menu.py` → `src/controllers/sample_controller.py` + `src/views/sample_view.py` 로 분리

**PRD 대응 요구사항:** SM-01 ~ SM-06, 5.1(메인 메뉴 골격), 5.2.1, 5.2.2, 5.2.3

**비즈니스 규칙:**
- 이름 빈 값 → `ValueError: 시료 이름은 필수 입력값입니다.`
- avgProductionTime ≤ 0 → `ValueError: 평균 생산시간은 0보다 커야 합니다.`
- yield_ ≤ 0 또는 yield_ > 1 → `ValueError: 수율은 0 초과 1 이하여야 합니다.`
- ID 자동 부여: 현재 저장된 시료 수 + 1 기반으로 `S{순번:03d}` 생성
- 검색: 대소문자 무관 부분 일치

**MVC 역할 분리 원칙 (모든 Phase 공통):**
- **View**: `render_*()` 메서드만 보유. 서비스 호출 금지. 데이터를 받아 출력만 함
- **Controller**: 입력 수신 → 서비스 호출 → view.render_*() 로 결과 전달. 도메인 로직 구현 금지
- **display.py**: 공통 유틸 (헤더, 구분선, 컬러, 테이블). ANSI 색상 조건부 활성화 (TTY 감지)

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

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상, `python main.py` 및 `python dummy.py` 정상 동작 확인

---

### Phase 3: 시료 주문 서비스 + UI

**브랜치:** `feat/phase-3-order-service`

**목표:** 주문 접수 비즈니스 로직과 UI를 함께 구현한다.
Phase 3 완료 후 `python main.py` 실행 시 시료 관리 + 시료 주문 기능을 사용할 수 있다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/order_service.py` | `place_order()` |
| `src/views/order_view.py` | 주문 접수 결과 렌더링 |
| `src/controllers/order_controller.py` | 주문 입력 처리 → order_service → order_view |
| `main.py` (수정) | `(2) 시료 주문` 메뉴 활성화 |

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

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상, `python main.py` 실행 후 시료 주문 기능 정상 동작 확인

---

### Phase 4: 주문 승인 / 거절 서비스 + UI

**브랜치:** `feat/phase-4-approval-service`

**목표:** 주문 승인·거절 및 재고 기반 자동 상태 분기 로직과 UI를 함께 구현한다.
이 Phase가 시스템의 핵심 비즈니스 로직이다.
Phase 4 완료 후 `python main.py` 실행 시 시료 관리 + 주문 + 승인/거절 기능을 사용할 수 있다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/approval_service.py` | `approve_order()`, `reject_order()`, `_calculate_production_quantity()` |
| `src/views/approval_view.py` | RESERVED 주문 목록 + 승인/거절 결과 렌더링 |
| `src/controllers/approval_controller.py` | 승인/거절 입력 처리 → service → view |
| `main.py` (수정) | `(3) 주문 승인/거절` 메뉴 활성화 |

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

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상, `python main.py` 실행 후 승인/거절 기능 정상 동작 확인

---

### Phase 5: 모니터링 서비스 + UI

**브랜치:** `feat/phase-5-monitoring-service`

**목표:** 주문 현황 집계와 시료별 재고 현황 조회 로직과 UI를 함께 구현한다.
Phase 5 완료 후 `python main.py` 실행 시 모니터링 화면에서 주문/재고 현황을 실시간으로 확인할 수 있다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/monitoring_service.py` | `get_order_summary()`, `get_stock_status()`, `_classify_stock()` |
| `src/views/monitoring_view.py` | ANSI 색상 + 유니코드 테이블로 주문량/재고 현황 렌더링 |
| `src/controllers/monitoring_controller.py` | 모니터링 입력 처리 → service → view |
| `main.py` (수정) | `(4) 모니터링` 메뉴 활성화, 메인 메뉴 상단 요약 정보 표시 |

**PRD 대응 요구사항:** MN-01 ~ MN-04, 5.1(요약 정보), 5.5.1, 5.5.2

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

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상, `python main.py` 실행 후 모니터링 및 메인 메뉴 요약 정보 정상 표시 확인

---

### Phase 6: 생산 라인 서비스 + UI

**브랜치:** `feat/phase-6-production-service`

**목표:** 생산 라인 현황 조회·완료 처리 로직과 UI를 함께 구현한다.
Phase 6 완료 후 `python main.py` 실행 시 생산 라인 조회 및 완료 처리 기능을 사용할 수 있다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/production_service.py` | `get_production_status()`, `complete_production()` |
| `src/views/production_view.py` | 생산 현황 + 대기 큐 렌더링 |
| `src/controllers/production_controller.py` | 생산 조회/완료 입력 처리 → service → view |
| `main.py` (수정) | `(5) 생산 라인 조회` 메뉴 활성화 |

**PRD 대응 요구사항:** PL-01 ~ PL-05, 5.6

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

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상, `python main.py` 실행 후 생산 라인 조회 및 완료 처리 정상 동작 확인

---

### Phase 7: 출고 처리 서비스 + UI

**브랜치:** `feat/phase-7-shipment-service`

**목표:** CONFIRMED 상태 주문의 출고 처리 로직과 UI를 함께 구현한다.
Phase 7 완료 후 전체 시스템이 `python main.py`로 완전히 동작한다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `src/services/shipment_service.py` | `get_confirmed_orders()`, `release_order()` |
| `src/views/shipment_view.py` | 출고 대상 목록 + 처리 결과 렌더링 |
| `src/controllers/shipment_controller.py` | 출고 입력 처리 → service → view |
| `main.py` (수정) | `(6) 출고 처리` 메뉴 활성화 → 전체 메뉴 완성 |

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

**완료 기준:** 모든 단위 테스트 PASS, 커버리지 90% 이상, `python main.py` 실행 후 전체 플로우 (시료등록→주문→승인→생산완료→출고) 정상 동작 확인

---

### Phase 8: 전체 통합 테스트 및 완성

**브랜치:** `feat/phase-8-integration`

**목표:** Phase 7까지 구현된 전체 시스템에 대해 end-to-end 통합 테스트를 작성하고, 코드 품질을 최종 점검한다.
Phase 7 완료 시점에 이미 전체 시스템이 동작하므로, Phase 8은 신규 기능 구현 없이 검증·완성에 집중한다.

**구현 대상 파일:**

| 파일 | 구현 내용 |
|------|---------|
| `tests/phase8/test_integration.py` | 서비스 레이어 end-to-end 통합 시나리오 테스트 |

**테스트 대상 (`tests/phase8/test_integration.py`):**
- 전체 시나리오 A: 시료 등록 → 주문 → 승인(재고 부족) → 생산 완료 → 출고 처리
- 전체 시나리오 B: 시료 등록 → 주문 → 승인(재고 충분) → 출고 처리
- 전체 시나리오 C: 시료 등록 → 주문 → 거절 (REJECTED 상태 확인)
- 복수 주문 동시 존재 시 모니터링 집계 정확성
- 생산 큐 FIFO 순서 처리 end-to-end 검증
- 출고 후 재고 차감 및 모니터링 반영 정확성
- 잘못된 입력(미등록 시료 ID, CONFIRMED 아닌 주문 출고 시도 등) 예외 처리 — PRD OR-01, RL-02

**완료 기준:** 통합 시나리오 테스트 전체 PASS, 전체 커버리지 85% 이상

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

## 실행 명령

```bash
# 시스템 직접 실행 (Phase 2 이후 가능)
python main.py

# 전체 테스트 + HTML 커버리지 리포트
pytest

# 특정 Phase만 실행
pytest tests/phase1/ -v

# HTML 리포트 열기 (Windows)
start htmlcov/index.html
```

## Phase별 사용 가능 기능

| Phase 완료 시점 | `python main.py`에서 사용 가능한 메뉴 |
|----------------|--------------------------------------|
| Phase 2 완료 | (1) 시료 관리 |
| Phase 3 완료 | (1) 시료 관리, (2) 시료 주문 |
| Phase 4 완료 | (1)~(2) + (3) 주문 승인/거절 |
| Phase 5 완료 | (1)~(3) + (4) 모니터링 |
| Phase 6 완료 | (1)~(4) + (5) 생산 라인 조회 |
| Phase 7 완료 | 전체 메뉴 (1)~(6) + (0) 종료 |

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
