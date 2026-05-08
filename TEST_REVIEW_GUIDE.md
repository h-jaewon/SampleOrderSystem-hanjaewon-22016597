# TEST_REVIEW_GUIDE.md - 관리감독자 테스트 검토 가이드
> 대상: 각 Phase 완료 후 SubAgent3가 검토를 요청한 시점에 사용

---

## 0. 공통 준비사항

### 환경 확인 (최초 1회)

```powershell
# Python 버전 확인 (3.11 이상)
python --version

# 의존성 설치
pip install -r requirements.txt

# 설치 확인
pytest --version
```

### 테스트 실행 방법

```powershell
# 전체 테스트 + HTML 커버리지 리포트 생성
pytest

# 특정 Phase만 실행
pytest tests/phaseN/ -v

# HTML 커버리지 리포트 열기
start htmlcov/index.html
```

### 검토 판단 기준 (전 Phase 공통)

| 항목 | 합격 기준 | 불합격 시 조치 |
|------|-----------|--------------|
| 테스트 통과율 | **100%** (0 failed) | SubAgent2에 수정 요청 후 재검토 |
| 커버리지 | Phase 1~7: **90% 이상** / Phase 8: **85% 이상** | 미커버 항목 확인 후 판단 |
| 경고(warning) | 무시 가능한 수준 | 내용 확인 후 판단 |

---

## Phase 1: 도메인 모델 및 저장소 기반

**브랜치:** `feat/phase-1-domain-models`

### 테스트 실행

```powershell
pytest tests/phase1/ -v
```

### 커버리지 확인

```
htmlcov/index.html 열기 → 다음 파일의 커버리지 확인:
  - src/models/sample.py
  - src/models/order.py
  - src/models/production_job.py
  - src/repositories/sample_repository.py
  - src/repositories/order_repository.py
  - src/repositories/production_queue.py
```

### 핵심 체크포인트

**1) OrderStatus 열거형 — 5가지 상태 모두 존재하는가?**
```
RESERVED / REJECTED / PRODUCING / CONFIRMED / RELEASED
```
터미널에서 직접 확인:
```powershell
python -c "from src.models.order import OrderStatus; print(list(OrderStatus))"
```
기대 출력:
```
[<OrderStatus.RESERVED: ...>, <OrderStatus.REJECTED: ...>, ...]
```

**2) ID 자동 생성 형식이 맞는가?**
```powershell
python -c "
from src.repositories.sample_repository import SampleRepository
from src.models.sample import Sample
repo = SampleRepository()
s = Sample(id='', name='Test', avgProductionTime=1.0, yield_=0.9, stock=0)
repo.add(s)
print(repo.get_all()[0].id)  # 기대: S001
"
```

**3) ProductionQueue FIFO 순서가 보장되는가?**
```powershell
python -c "
from src.repositories.production_queue import ProductionQueue
q = ProductionQueue()
q.enqueue('A')
q.enqueue('B')
q.enqueue('C')
print(q.dequeue())  # 기대: A
print(q.dequeue())  # 기대: B
"
```

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed
- [ ] 커버리지: 90% 이상
- [ ] OrderStatus 5가지 상태 존재
- [ ] ID 형식 S001, ORD-001 패턴 확인
- [ ] FIFO 순서 보장 확인

---

## Phase 2: 시료 관리 서비스

**브랜치:** `feat/phase-2-sample-service`

### 테스트 실행

```powershell
pytest tests/phase1/ tests/phase2/ -v
```

> Phase 1 테스트도 함께 실행하여 회귀(regression) 여부 확인

### 커버리지 확인

```
src/services/sample_service.py 커버리지 집중 확인
```

### 핵심 체크포인트

**1) 유효성 검사 — 잘못된 입력에서 ValueError가 발생하는가?**
```powershell
python -c "
from src.services.sample_service import SampleService
from src.repositories.sample_repository import SampleRepository
svc = SampleService(SampleRepository())

# 이름 빈 값
try:
    svc.register_sample('', 2.5, 0.85)
except ValueError as e:
    print('OK:', e)

# 생산시간 0
try:
    svc.register_sample('GaAs', 0, 0.85)
except ValueError as e:
    print('OK:', e)

# 수율 1 초과
try:
    svc.register_sample('GaAs', 2.5, 1.1)
except ValueError as e:
    print('OK:', e)
"
```

**2) 시료 등록 후 ID가 자동 부여되는가?**
```powershell
python -c "
from src.services.sample_service import SampleService
from src.repositories.sample_repository import SampleRepository
svc = SampleService(SampleRepository())
s = svc.register_sample('GaAs-100', 2.5, 0.85)
print(s.id)    # 기대: S001
print(s.name)  # 기대: GaAs-100
print(s.stock) # 기대: 0
"
```

**3) 검색이 부분 일치로 동작하는가?**
```powershell
python -c "
from src.services.sample_service import SampleService
from src.repositories.sample_repository import SampleRepository
svc = SampleService(SampleRepository())
svc.register_sample('GaAs-100', 2.5, 0.85)
svc.register_sample('SiC-300', 5.5, 0.80)
results = svc.search_samples_by_name('GaAs')
print(len(results))   # 기대: 1
print(results[0].name) # 기대: GaAs-100
"
```

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed (Phase 1 포함)
- [ ] 커버리지: 90% 이상
- [ ] 빈 이름 / 생산시간 0 / 수율 범위 위반 시 ValueError 발생
- [ ] ID 자동 부여 S001, S002 순서 확인
- [ ] 검색 부분 일치 동작 확인

---

## Phase 3: 시료 주문 서비스

**브랜치:** `feat/phase-3-order-service`

### 테스트 실행

```powershell
pytest tests/phase1/ tests/phase2/ tests/phase3/ -v
```

### 커버리지 확인

```
src/services/order_service.py 커버리지 집중 확인
```

### 핵심 체크포인트

**1) 주문 등록 후 상태가 RESERVED인가?**
```powershell
python -c "
from src.repositories.sample_repository import SampleRepository
from src.repositories.order_repository import OrderRepository
from src.services.sample_service import SampleService
from src.services.order_service import OrderService
from src.models.order import OrderStatus

sample_repo = SampleRepository()
order_repo = OrderRepository()
svc_s = SampleService(sample_repo)
svc_o = OrderService(order_repo, sample_repo)

svc_s.register_sample('GaAs-100', 2.5, 0.85)
order = svc_o.place_order('S001', '한국반도체연구소', 10)

print(order.status == OrderStatus.RESERVED)  # 기대: True
print(order.id)                              # 기대: ORD-001
print(order.customerName)                    # 기대: 한국반도체연구소
"
```

**2) 존재하지 않는 시료 ID 주문 시 ValueError가 발생하는가?**
```powershell
python -c "
from src.repositories.sample_repository import SampleRepository
from src.repositories.order_repository import OrderRepository
from src.services.order_service import OrderService

svc = OrderService(OrderRepository(), SampleRepository())
try:
    svc.place_order('S999', '고객', 5)
except ValueError as e:
    print('OK:', e)
"
```

**3) 주문 수량 0 이하 입력 시 ValueError가 발생하는가?**
```powershell
python -c "
from src.repositories.sample_repository import SampleRepository
from src.repositories.order_repository import OrderRepository
from src.services.sample_service import SampleService
from src.services.order_service import OrderService

sample_repo = SampleRepository()
SampleService(sample_repo).register_sample('GaAs', 2.5, 0.85)
svc = OrderService(OrderRepository(), sample_repo)

try:
    svc.place_order('S001', '고객', 0)
except ValueError as e:
    print('OK:', e)
"
```

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed (Phase 1~2 포함)
- [ ] 커버리지: 90% 이상
- [ ] 주문 등록 즉시 RESERVED 상태 확인
- [ ] 존재하지 않는 시료 ID 방어 확인
- [ ] 수량 경계값(0, 음수) 방어 확인
- [ ] createdAt 자동 설정 확인

---

## Phase 4: 주문 승인 / 거절 서비스 ⭐ (핵심 Phase)

**브랜치:** `feat/phase-4-approval-service`

### 테스트 실행

```powershell
pytest tests/phase1/ tests/phase2/ tests/phase3/ tests/phase4/ -v
```

### 커버리지 확인

```
src/services/approval_service.py 커버리지 집중 확인
특히 재고 분기 로직(재고 충분/부족 두 경로) 모두 커버되었는지 확인
```

### 핵심 체크포인트

**1) 재고 충분 시 CONFIRMED로 전환되는가?**
```powershell
python -c "
from src.repositories.sample_repository import SampleRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.services.sample_service import SampleService
from src.services.order_service import OrderService
from src.services.approval_service import ApprovalService
from src.models.order import OrderStatus

sr, or_, pq = SampleRepository(), OrderRepository(), ProductionQueue()
ss = SampleService(sr)
os = OrderService(or_, sr)
aps = ApprovalService(or_, sr, pq)

s = ss.register_sample('GaAs-100', 2.5, 0.85)
s.stock = 20  # 재고 수동 설정

order = os.place_order('S001', '고객A', 5)
result = aps.approve_order('ORD-001')

print(result.status == OrderStatus.CONFIRMED)  # 기대: True
print(pq.is_empty())                           # 기대: True (생산 큐 미등록)
"
```

**2) 재고 부족 시 PRODUCING으로 전환되고 생산 큐에 등록되는가?**
```powershell
python -c "
from src.repositories.sample_repository import SampleRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.services.sample_service import SampleService
from src.services.order_service import OrderService
from src.services.approval_service import ApprovalService
from src.models.order import OrderStatus

sr, or_, pq = SampleRepository(), OrderRepository(), ProductionQueue()
ss = SampleService(sr)
os = OrderService(or_, sr)
aps = ApprovalService(or_, sr, pq)

s = ss.register_sample('SiC-300', 5.5, 0.80)
s.stock = 3  # 재고 3개

order = os.place_order('S001', '한국반도체연구소', 10)
result = aps.approve_order('ORD-001')

print(result.status == OrderStatus.PRODUCING)  # 기대: True
print(pq.is_empty())                           # 기대: False (생산 큐 등록됨)
job = pq.peek()
print(job.plannedQuantity)      # 기대: 10 (ceil(7 / (0.8 x 0.9)) = ceil(9.72) = 10)
print(job.totalProductionTime)  # 기대: 55.0 (5.5 x 10)
"
```

**3) 생산량 계산 공식을 직접 검증한다 — PRD 수치와 일치하는가?**

PRD 5.4 UI 예시 수치:
- 주문 수량 10개, 현재 재고 3개, 수율 0.80, 평균 생산시간 5.5h
- 부족분 = 10 - 3 = 7
- 실 생산량 = ceil(7 / (0.80 × 0.9)) = ceil(9.722...) = **10**
- 총 생산 시간 = 5.5 × 10 = **55.0h**

```powershell
python -c "
import math
shortage = 7
yield_ = 0.80
planned = math.ceil(shortage / (yield_ * 0.9))
total_time = 5.5 * planned
print(planned)    # 기대: 10
print(total_time) # 기대: 55.0
"
```

**4) 거절 시 REJECTED로 전환되는가?**
```powershell
# (환경 세팅 후)
result = aps.reject_order('ORD-001')
print(result.status == OrderStatus.REJECTED)  # 기대: True
```

**5) 재고 == 수량인 경계값에서 CONFIRMED로 처리되는가?**
```
stock = 10, quantity = 10 → CONFIRMED (기대)
stock = 9,  quantity = 10 → PRODUCING (기대)
```

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed (Phase 1~3 포함)
- [ ] 커버리지: 90% 이상
- [ ] 재고 충분 경로: CONFIRMED, 생산 큐 미등록
- [ ] 재고 부족 경로: PRODUCING, 생산 큐 등록
- [ ] 실 생산량 계산 수치 PRD 예시와 일치 (부족분 7 → 실 생산량 10)
- [ ] 총 생산 시간 계산 수치 PRD 예시와 일치 (55.0h)
- [ ] 재고 == 수량 경계값에서 CONFIRMED 처리
- [ ] 거절 → REJECTED 전환

---

## Phase 5: 모니터링 서비스

**브랜치:** `feat/phase-5-monitoring-service`

### 테스트 실행

```powershell
pytest tests/phase1/ tests/phase2/ tests/phase3/ tests/phase4/ tests/phase5/ -v
```

### 커버리지 확인

```
src/services/monitoring_service.py 커버리지 집중 확인
재고 상태 분류(여유/부족/고갈) 3가지 경로 모두 커버되었는지 확인
```

### 핵심 체크포인트

**1) REJECTED 주문이 집계에서 제외되는가?**
```powershell
python -c "
# (시료, 주문 3건 생성: 1건 거절, 2건 RESERVED 유지 후)
summary = svc.get_order_summary()
rejected_count = summary.get('REJECTED', 0)
print(rejected_count)  # 기대: 0 (REJECTED는 집계 제외)
"
```

**2) 재고 상태 3단계가 올바르게 분류되는가?**

| 시나리오 | 기대 상태 |
|---------|---------|
| stock = 0 | 고갈 |
| stock > 0 이고 해당 시료 PRODUCING 주문 존재 | 부족 |
| stock > 0 이고 PRODUCING 주문 없음 | 여유 |

```powershell
python -c "
stock_status = svc.get_stock_status()
for item in stock_status:
    print(item['sample'].name, item['status'])
# GaAs-100(stock=0)  → 고갈
# SiC-300(stock=3, PRODUCING 주문 있음) → 부족
# Si-Wafer(stock=45, 주문 없음) → 여유
"
```

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed (Phase 1~4 포함)
- [ ] 커버리지: 90% 이상
- [ ] REJECTED 주문 집계 제외 확인
- [ ] 상태별 카운트 정확성 확인
- [ ] 재고 고갈/부족/여유 3단계 분류 확인

---

## Phase 6: 생산 라인 서비스

**브랜치:** `feat/phase-6-production-service`

### 테스트 실행

```powershell
pytest tests/phase1/ tests/phase2/ tests/phase3/ tests/phase4/ tests/phase5/ tests/phase6/ -v
```

### 커버리지 확인

```
src/services/production_service.py 커버리지 집중 확인
complete_production의 재고 증가 및 상태 전환 경로 확인
```

### 핵심 체크포인트

**1) 생산 완료 후 PRODUCING → CONFIRMED 전환과 재고 증가가 모두 발생하는가?**
```powershell
python -c "
# PRODUCING 상태 주문 1건 준비 후 (재고 3개, 주문 10개, 실 생산량 10개)
before_stock = sample.stock   # = 3

svc.complete_production()

print(order.status)     # 기대: CONFIRMED
print(sample.stock)     # 기대: 3 + 10 = 13
print(pq.is_empty())    # 기대: True
"
```

**2) 복수 작업이 큐에 있을 때 FIFO 순서로 처리되는가?**
```powershell
python -c "
# 큐에 ORD-001, ORD-002, ORD-003 순서로 등록 후
status = svc.get_production_status()
print(status['current'].orderId)   # 기대: ORD-001
print(status['queue'][0].orderId)  # 기대: ORD-002
print(status['queue'][1].orderId)  # 기대: ORD-003

svc.complete_production()
status2 = svc.get_production_status()
print(status2['current'].orderId)  # 기대: ORD-002
"
```

**3) 빈 큐에서 생산 완료 시도 시 ValueError가 발생하는가?**
```powershell
python -c "
try:
    svc.complete_production()
except ValueError as e:
    print('OK:', e)
"
```

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed (Phase 1~5 포함)
- [ ] 커버리지: 90% 이상
- [ ] 생산 완료 시 CONFIRMED 전환 확인
- [ ] 생산 완료 시 재고 증가(plannedQuantity만큼) 확인
- [ ] FIFO 순서 처리 확인
- [ ] 빈 큐 예외 처리 확인

---

## Phase 7: 출고 처리 서비스

**브랜치:** `feat/phase-7-shipment-service`

### 테스트 실행

```powershell
pytest tests/phase1/ tests/phase2/ tests/phase3/ tests/phase4/ tests/phase5/ tests/phase6/ tests/phase7/ -v
```

### 커버리지 확인

```
src/services/shipment_service.py 커버리지 집중 확인
```

### 핵심 체크포인트

**1) 출고 처리 후 CONFIRMED → RELEASED 전환과 재고 차감이 모두 발생하는가?**
```powershell
python -c "
# CONFIRMED 상태 주문 (수량 5개), 시료 재고 12개 준비 후
before_stock = sample.stock  # = 12

svc.release_order('ORD-001')

print(order.status)   # 기대: RELEASED
print(sample.stock)   # 기대: 12 - 5 = 7
"
```

**2) CONFIRMED 아닌 주문 출고 시도 시 ValueError가 발생하는가?**
```powershell
python -c "
# RESERVED 상태의 주문에 대해 출고 시도
try:
    svc.release_order('ORD-001')  # RESERVED 상태
except ValueError as e:
    print('OK:', e)
"
```

**3) 존재하지 않는 주문 ID 입력 시 ValueError가 발생하는가?**
```powershell
python -c "
try:
    svc.release_order('ORD-999')
except ValueError as e:
    print('OK:', e)
"
```

### 전체 상태 흐름 최종 검증

Phase 1~7을 모두 사용하여 전체 생명주기를 직접 확인한다.

**시나리오 A: 재고 충분 경로**
```
시료 등록(stock=20) → 주문 등록 → 승인(CONFIRMED) → 출고(RELEASED)
```

**시나리오 B: 재고 부족 경로**
```
시료 등록(stock=3) → 주문 등록(수량 10) → 승인(PRODUCING) → 생산 완료(CONFIRMED) → 출고(RELEASED)
```

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed (Phase 1~6 포함)
- [ ] 커버리지: 90% 이상
- [ ] 출고 후 RELEASED 전환 확인
- [ ] 출고 후 재고 차감 확인
- [ ] 잘못된 상태 주문 출고 방어 확인
- [ ] 시나리오 A (재고 충분 전체 흐름) 정상 동작 확인
- [ ] 시나리오 B (재고 부족 전체 흐름) 정상 동작 확인

---

## Phase 8: UI 레이어 및 시스템 통합

**브랜치:** `feat/phase-8-ui-integration`

### 테스트 실행

```powershell
# 전체 테스트 실행
pytest -v

# 통합 테스트만 실행
pytest tests/phase8/ -v
```

### 직접 실행 테스트 (가장 중요)

```powershell
python main.py
```

Phase 8은 UI 화면을 직접 눈으로 확인하는 것이 핵심이다.
아래 시나리오를 순서대로 직접 실행하며 검토한다.

---

#### 시나리오 1: 메인 메뉴 표시 및 기본 탐색

1. `python main.py` 실행
2. 메인 메뉴 화면 확인:
   - [ ] 시스템 타이틀(`S-Semi 반도체 시료 생산 주문 관리 시스템`) 표시
   - [ ] 시료 현황 요약 표시 (시료 수, 총 재고, RESERVED 건수, PRODUCING 건수)
   - [ ] 메뉴 1~6 및 0 표시
3. 잘못된 번호(`9`) 입력:
   - [ ] 오류 메시지 출력 후 재입력 요청 (종료되지 않음)
4. `0` 입력:
   - [ ] 시스템 정상 종료

---

#### 시나리오 2: 시료 등록 및 조회

1. 메인 메뉴 `(1)` 선택 → 시료 관리
2. 시료 등록:
   - 이름: `GaAs-100`, 생산시간: `2.5`, 수율: `0.85`
   - [ ] 등록 완료 메시지 + ID `S001` 표시
3. 빈 이름으로 등록 시도:
   - [ ] 오류 메시지 + 재입력 요청 (종료되지 않음)
4. 수율 `1.5` 입력 시도:
   - [ ] 오류 메시지 + 재입력 요청
5. 시료 조회:
   - [ ] 등록된 시료 목록 표시 (ID, 이름, 생산시간, 수율, 재고)
6. 시료 검색 (`GaAs`):
   - [ ] 부분 일치 결과 표시

---

#### 시나리오 3: 주문 등록

1. 메뉴 `(2)` → 시료 주문
2. 시료 ID `S001`, 고객명 `ABC 팹리스`, 수량 `5` 입력:
   - [ ] 주문 완료 메시지 + `ORD-001`, `RESERVED` 상태 표시
3. 존재하지 않는 ID `S999` 입력:
   - [ ] 오류 메시지 + 재입력 요청

---

#### 시나리오 4: 주문 승인 (재고 부족 경로)

1. 시료 추가 등록: `SiC-300`, 생산시간 `5.5`, 수율 `0.80`
2. 주문 등록: `S002`, `한국반도체연구소`, 수량 `10` (재고 0개이므로 부족)
3. 메뉴 `(3)` → 주문 승인/거절
4. `ORD-002` 선택 → `(1) 승인`:
   - [ ] 재고 부족 메시지 표시
   - [ ] 부족분 10개, 실 생산량 `ceil(10 / (0.8 × 0.9)) = 14` 표시
   - [ ] 상태 변경 `RESERVED → PRODUCING` 확인

---

#### 시나리오 5: 생산 라인 조회

1. 메뉴 `(5)` → 생산 라인 조회:
   - [ ] 현재 생산 중인 항목 표시 (ORD-002, SiC-300, 총 생산 시간)
   - [ ] 생산 대기 큐 표시 (비어있으면 빈 큐 안내)

---

#### 시나리오 6: 전체 흐름 (재고 충분 경로)

1. 시료 `Si-Wafer-200` 등록 (생산시간 `3.0`, 수율 `0.90`)
2. 재고 설정 필요 시 직접 확인 (stock이 0이면 부족 경로)
3. 주문 등록 → 승인(CONFIRMED) → 출고 처리:
   - [ ] 메뉴 `(6)` → CONFIRMED 목록 표시
   - [ ] 출고 처리 후 `CONFIRMED → RELEASED` 메시지 확인

---

#### UI 형식 체크리스트

| 항목 | 확인 |
|------|------|
| 화면 헤더 형식 `[ 메뉴명 > 서브메뉴명 ]` | [ ] |
| 구분선(`---` 또는 `===`) 일관성 | [ ] |
| 입력 프롬프트 `>> ` 형식 | [ ] |
| 작업 완료 후 "엔터를 누르면 메인 메뉴로 돌아갑니다." 메시지 | [ ] |
| 잘못된 입력 시 시스템 비정상 종료 없음 | [ ] |

### 진행 여부 결정 기준

- [ ] pytest 결과: 0 failed (전체)
- [ ] 커버리지: 85% 이상
- [ ] `python main.py` 정상 실행
- [ ] 시나리오 1~6 직접 실행 완료
- [ ] UI 형식 체크리스트 전항목 통과
- [ ] 비정상 입력에서 시스템 종료 없음

---

## 커버리지 리포트 읽는 법

`start htmlcov/index.html` 실행 후:

1. **Module 별 커버리지 확인**: 각 파일의 `Cover %` 컬럼 확인
2. **미커버 라인 확인**: 파일 클릭 → 빨간색(미커버) 라인 확인
3. **판단 기준**:
   - 빨간 라인이 **예외 처리 경로**라면 → 해당 경계값 테스트 추가 요청
   - 빨간 라인이 **정상 흐름 핵심 로직**이라면 → 반드시 수정 요청
   - 빨간 라인이 **UI/출력 전용 코드**라면 → 허용 가능 (Phase 8에서 커버)

---

## 검토 결과 전달 방법

### 합격 (다음 Phase 진행)

```
Phase N 검토 완료. 테스트 및 커버리지 기준 충족. 다음 Phase 진행해.
```

### 불합격 (수정 요청)

```
Phase N 검토 결과:
- [실패 항목 1]: <구체적 내용>
- [실패 항목 2]: <구체적 내용>
수정 후 재검토 요청.
```

### commit & push 승인 (SubAgent5 호출)

```
Phase N 테스트 PASS. repository-governance로 commit과 push 진행해.
```
