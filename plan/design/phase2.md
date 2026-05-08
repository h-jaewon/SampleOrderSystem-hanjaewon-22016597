# Phase 2 설계 문서: 시료 관리 서비스

> 기준 문서: plan.md (Phase 2), PRD.md v1.0 | 작성일: 2026-05-08

---

## 1. 개요

### 목표

시료 등록, 전체 조회, 이름 검색의 비즈니스 로직을 서비스 레이어로 구현한다.
Phase 1에서 구축한 `Sample` 데이터 클래스와 `SampleRepository` 위에 서비스 레이어를 추가하는 것이 이번 Phase의 전부이며, 새로운 모델이나 저장소는 추가하지 않는다.

### 브랜치명

```
feat/phase-2-sample-service
```

### PRD 대응 요구사항

| 요구사항 ID | 내용 요약 |
|------------|----------|
| SM-01 | 시료 ID는 시스템이 자동 부여하며 중복되지 않아야 한다. |
| SM-02 | 시료 이름은 필수 입력값이며 빈 값은 허용하지 않는다. |
| SM-03 | 평균 생산시간은 양수(0 초과)만 허용한다. |
| SM-04 | 수율은 0 초과 1 이하의 값이어야 한다. |
| SM-05 | 시료 조회 시 현재 재고 수량도 함께 반환된다. |
| SM-06 | 시료 검색은 이름 기준 부분 일치를 지원한다. |
| 5.2.1 | 시료 등록 기능 — 유효성 검사 후 ID 자동 부여 및 저장 |
| 5.2.2 | 시료 조회 기능 — 전체 시료 목록 반환 |
| 5.2.3 | 시료 검색 기능 — 이름 키워드 기반 부분 일치 검색 |

### Phase 1과의 의존 관계

Phase 2는 Phase 1이 완전히 완료(모든 테스트 PASS, 커버리지 90% 이상)된 상태를 전제로 진행한다.

| Phase 2가 의존하는 Phase 1 결과물 | 사용 목적 |
|----------------------------------|----------|
| `src/models/sample.py` — `Sample` 데이터 클래스 | 서비스에서 생성·반환하는 엔티티 타입 |
| `src/repositories/sample_repository.py` — `SampleRepository` | 시료 저장 및 조회의 실제 구현체 |

Phase 2에서 직접 수정하는 Phase 1 파일은 없다. `SampleRepository`의 `add`, `get_all`, `find_by_name` 메서드를 호출만 한다.

---

## 2. 디렉터리 및 파일 구조

Phase 2에서 생성하는 파일은 아래 1개뿐이다. 이 목록 외의 파일은 이번 Phase에서 생성하지 않는다.

```
sampleordersystem/
├── src/
│   └── services/
│       ├── __init__.py                  # 패키지 선언 (내용 없음) — Phase 2에서 신규 생성
│       └── sample_service.py            # 시료 관리 서비스 — Phase 2에서 신규 생성
└── tests/
    └── phase2/
        ├── __init__.py                  # 패키지 선언 (내용 없음) — Phase 2에서 신규 생성
        └── test_sample_service.py       # Phase 2 단위 테스트 — Phase 2에서 신규 생성
```

### 각 파일의 역할

| 파일 | 역할 |
|------|------|
| `src/services/__init__.py` | services 패키지 선언. 내용 없음. |
| `src/services/sample_service.py` | `SampleService` 클래스를 포함한다. 유효성 검사, ID 생성, 저장소 호출을 담당하는 비즈니스 로직 계층이다. |
| `tests/phase2/__init__.py` | phase2 테스트 패키지 선언. 내용 없음. |
| `tests/phase2/test_sample_service.py` | `SampleService`의 모든 퍼블릭 메서드에 대한 단위 테스트를 포함한다. |

---

## 3. 서비스 설계 (`sample_service.py`)

### 3.1 클래스 구조

**파일:** `src/services/sample_service.py`

**임포트:**
- `from src.models.sample import Sample`
- `from src.repositories.sample_repository import SampleRepository`

**클래스:** `SampleService`

`SampleService`는 생성자에서 `SampleRepository` 인스턴스를 주입받는다(의존성 주입). 저장소를 내부에서 직접 생성하지 않는다. 이 구조는 테스트 시 독립적인 저장소 인스턴스를 주입할 수 있게 하여 테스트 격리를 보장한다.

```
SampleService
├── __init__(self, sample_repository: SampleRepository) -> None
├── register_sample(self, name: str, avgProductionTime: float, yield_: float) -> Sample
├── get_all_samples(self) -> list[Sample]
└── search_samples_by_name(self, keyword: str) -> list[Sample]
```

**생성자 명세:**

| 항목 | 내용 |
|------|------|
| 파라미터 | `sample_repository: SampleRepository` |
| 동작 | 전달받은 `sample_repository`를 인스턴스 변수(`self._sample_repository`)로 저장한다. |
| 예외 | 없음 |

---

### 3.2 `register_sample(name, avgProductionTime, yield_)`

#### 목적

입력값의 유효성을 검사한 후, ID를 자동 생성하여 `Sample` 엔티티를 만들고 저장소에 저장한다.

#### 시그니처

```
register_sample(self, name: str, avgProductionTime: float, yield_: float) -> Sample
```

#### 입력

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `name` | `str` | 시료 이름 |
| `avgProductionTime` | `float` | 시료 1개 생산에 소요되는 평균 시간 (단위: 시간) |
| `yield_` | `float` | 공정 성공률 (0 < yield_ <= 1). 파라미터명 끝의 언더스코어는 Python 예약어 `yield` 회피를 위한 것이다. |

#### 유효성 검사 순서 및 규칙

유효성 검사는 아래 순서대로 수행한다. 첫 번째 위반 항목에서 즉시 `ValueError`를 발생시키고 이후 검사는 진행하지 않는다.

1. `name`이 빈 문자열인지 확인한다. (`name.strip() == ""` 또는 `not name.strip()`)
2. `avgProductionTime`이 0 이하인지 확인한다. (`avgProductionTime <= 0`)
3. `yield_`이 0 이하이거나 1 초과인지 확인한다. (`yield_ <= 0 or yield_ > 1`)

각 위반 시 발생시킬 예외는 아래 "4. 유효성 검사 규칙 명세" 섹션에 정의한다.

#### 처리 흐름

```
1. name 유효성 검사 (빈 값 여부)
2. avgProductionTime 유효성 검사 (0 이하 여부)
3. yield_ 유효성 검사 (0 이하 또는 1 초과 여부)
4. ID 자동 생성: f"S{len(self._sample_repository.get_all()) + 1:03d}"
5. Sample 인스턴스 생성: Sample(id=생성된_id, name=name, avgProductionTime=avgProductionTime, yield_=yield_)
6. self._sample_repository.add(sample) 호출
7. 저장된 sample 인스턴스 반환
```

#### 반환값

등록이 완료된 `Sample` 인스턴스를 반환한다.

| 속성 | 값 |
|------|------|
| `id` | 자동 생성된 `S{순번:03d}` 형식 문자열 |
| `name` | 입력받은 `name` |
| `avgProductionTime` | 입력받은 `avgProductionTime` |
| `yield_` | 입력받은 `yield_` |
| `stock` | `0` (Sample 데이터 클래스의 기본값) |

#### 예외

| 조건 | 예외 타입 | 예외 메시지 |
|------|-----------|------------|
| `name`이 빈 문자열 | `ValueError` | `"시료 이름은 필수 입력값입니다."` |
| `avgProductionTime <= 0` | `ValueError` | `"평균 생산시간은 0보다 커야 합니다."` |
| `yield_ <= 0 or yield_ > 1` | `ValueError` | `"수율은 0 초과 1 이하여야 합니다."` |

---

### 3.3 `get_all_samples()`

#### 목적

저장소에 등록된 모든 시료를 반환한다.

#### 시그니처

```
get_all_samples(self) -> list[Sample]
```

#### 입력

없음

#### 처리 흐름

```
1. self._sample_repository.get_all() 호출
2. 반환된 list[Sample]을 그대로 반환
```

유효성 검사 및 추가 가공 없이 저장소의 반환값을 그대로 전달한다.

#### 반환값

| 상황 | 반환값 |
|------|--------|
| 등록된 시료가 있는 경우 | 등록 순서대로 정렬된 `list[Sample]` |
| 등록된 시료가 없는 경우 | 빈 리스트 `[]` |

#### 예외

없음

---

### 3.4 `search_samples_by_name(keyword)`

#### 목적

이름에 검색어(keyword)가 포함된 시료를 대소문자 무관하게 검색하여 반환한다.

#### 시그니처

```
search_samples_by_name(self, keyword: str) -> list[Sample]
```

#### 입력

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `keyword` | `str` | 검색할 이름 키워드. 빈 문자열도 허용되며, 빈 문자열이면 모든 시료가 반환된다. |

#### 처리 흐름

```
1. self._sample_repository.find_by_name(keyword) 호출
2. 반환된 list[Sample]을 그대로 반환
```

대소문자 무관 부분 일치 로직은 `SampleRepository.find_by_name()`에서 이미 구현되어 있으므로(Phase 1), 서비스는 이를 그대로 위임한다.

#### 반환값

| 상황 | 반환값 |
|------|--------|
| 검색어를 이름에 포함하는 시료가 있는 경우 | 해당 `Sample` 인스턴스들의 리스트 |
| 검색 결과가 없는 경우 | 빈 리스트 `[]` |

#### 예외

없음

---

## 4. 유효성 검사 규칙 명세

아래 표의 예외 메시지 문자열은 정확히 일치해야 한다. 공백, 구두점, 조사 하나도 다르면 테스트가 실패한다.

| 입력값 | 허용 범위 | 위반 조건 | 예외 타입 | 예외 메시지 (정확한 문자열) |
|--------|-----------|-----------|-----------|--------------------------|
| `name` | 비어있지 않은 문자열 | `name.strip() == ""` | `ValueError` | `"시료 이름은 필수 입력값입니다."` |
| `avgProductionTime` | 0 초과의 실수 | `avgProductionTime <= 0` | `ValueError` | `"평균 생산시간은 0보다 커야 합니다."` |
| `yield_` | 0 초과 1 이하의 실수 | `yield_ <= 0 or yield_ > 1` | `ValueError` | `"수율은 0 초과 1 이하여야 합니다."` |

**경계값 정리:**

| 입력값 | 허용되지 않음 (ValueError) | 허용됨 |
|--------|--------------------------|--------|
| `name` | `""`, `"   "` (공백만 있는 경우) | `"A"`, `"GaAs-100"` 등 |
| `avgProductionTime` | `0`, `-1`, `-0.001` | `0.001`, `1.0`, `2.5` |
| `yield_` | `0`, `-0.1`, `1.001`, `2.0` | `0.001`, `0.5`, `0.85`, `1.0` |

---

## 5. ID 자동 생성 로직

### 형식

```
S{순번:03d}
```

| 순번 | 생성된 ID |
|------|-----------|
| 1 | `S001` |
| 2 | `S002` |
| 3 | `S003` |
| ... | ... |
| 999 | `S999` |

### 생성 방법

`register_sample()` 내부에서 저장소의 현재 크기에 1을 더하여 순번을 결정한다.

```
순번 = len(self._sample_repository.get_all()) + 1
sample_id = f"S{순번:03d}"
```

### 중복 방지 방법

Phase 2 서비스와 Phase 1 저장소가 각각 책임을 분담하여 중복을 방지한다.

| 계층 | 역할 |
|------|------|
| 서비스 (`SampleService`) | `get_all()` 결과의 길이 기반으로 순번을 결정하므로, 시료가 삭제되지 않는 이 시스템에서는 동일 순번이 두 번 생성되지 않는다. |
| 저장소 (`SampleRepository`) | `add()` 호출 시 이미 동일 ID가 존재하면 `ValueError("이미 존재하는 시료 ID입니다: {id}")`를 발생시킨다 (Phase 1 구현). |

시료 삭제 기능은 PRD 범위 밖이므로, `len(get_all()) + 1` 방식으로 순번이 단조 증가함이 보장된다.

---

## 6. 테스트 명세

### 테스트 파일 위치

```
tests/phase2/test_sample_service.py
```

### 테스트 픽스처 설계

각 테스트는 독립적인 `SampleRepository`와 `SampleService` 인스턴스를 사용해야 한다. pytest의 `@pytest.fixture`를 이용하여 `service` 픽스처를 정의하고, 각 테스트 함수의 파라미터로 주입한다.

픽스처 예시 (의사코드):
```
@pytest.fixture
def service():
    repo = SampleRepository()
    return SampleService(repo)
```

### 테스트 케이스 목록

---

#### TC-2-01: 정상 시료 등록 및 반환값 검증 [Happy Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=2.5`, `yield_=0.85` |
| 기대 결과 | 반환된 `Sample` 인스턴스의 `name == "GaAs-100"`, `avgProductionTime == 2.5`, `yield_ == 0.85`, `stock == 0` |
| 추가 검증 | `sample.id`가 `"S001"` 형식임을 확인한다 (`sample.id == "S001"`). |

---

#### TC-2-02: 이름 빈 문자열 입력 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name=""`, `avgProductionTime=2.5`, `yield_=0.85` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"시료 이름은 필수 입력값입니다."` 와 일치한다. |

---

#### TC-2-03: 이름 공백만 있는 경우 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="   "` (공백 문자열), `avgProductionTime=2.5`, `yield_=0.85` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"시료 이름은 필수 입력값입니다."` 와 일치한다. |

---

#### TC-2-04: avgProductionTime = 0 일 때 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=0`, `yield_=0.85` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"평균 생산시간은 0보다 커야 합니다."` 와 일치한다. |

---

#### TC-2-05: avgProductionTime 음수 입력 시 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=-1.0`, `yield_=0.85` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"평균 생산시간은 0보다 커야 합니다."` 와 일치한다. |

---

#### TC-2-06: avgProductionTime 정상값 허용 [Happy Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=0.001`, `yield_=0.85` |
| 기대 결과 | `ValueError` 미발생. `Sample` 인스턴스 반환. `sample.avgProductionTime == 0.001`. |

---

#### TC-2-07: yield_ = 0 일 때 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=2.5`, `yield_=0` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"수율은 0 초과 1 이하여야 합니다."` 와 일치한다. |

---

#### TC-2-08: yield_ > 1 일 때 ValueError [Error Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=2.5`, `yield_=1.001` |
| 기대 결과 | `ValueError` 발생. 예외 메시지가 `"수율은 0 초과 1 이하여야 합니다."` 와 일치한다. |

---

#### TC-2-09: yield_ = 1.0 허용 (경계값) [Happy Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=2.5`, `yield_=1.0` |
| 기대 결과 | `ValueError` 미발생. `Sample` 인스턴스 반환. `sample.yield_ == 1.0`. |

---

#### TC-2-10: yield_ 소수 정상값 허용 [Happy Path]

| 항목 | 내용 |
|------|------|
| 입력 | `name="GaAs-100"`, `avgProductionTime=2.5`, `yield_=0.001` |
| 기대 결과 | `ValueError` 미발생. `Sample` 인스턴스 반환. `sample.yield_ == 0.001`. |

---

#### TC-2-11: 전체 조회 — 등록된 시료 수 일치 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `register_sample`으로 시료 3개를 등록한다. |
| 입력 | `get_all_samples()` 호출 |
| 기대 결과 | 반환된 리스트의 길이가 `3`이다. |

---

#### TC-2-12: 전체 조회 — 등록된 시료 없을 때 빈 리스트 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 아무 시료도 등록하지 않은 상태 |
| 입력 | `get_all_samples()` 호출 |
| 기대 결과 | 반환값이 `[]` (빈 리스트)이다. |

---

#### TC-2-13: 이름 검색 — 부분 일치 결과 반환 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `name="GaAs-100"`, `name="GaAs-200"`, `name="SiC-300"` 3개를 등록한다. |
| 입력 | `search_samples_by_name("GaAs")` 호출 |
| 기대 결과 | 반환된 리스트의 길이가 `2`이다. 반환된 시료의 `name`이 각각 `"GaAs-100"`, `"GaAs-200"`이다. |

---

#### TC-2-14: 이름 검색 — 대소문자 무관 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `name="GaAs-100"`, `name="SiC-300"` 2개를 등록한다. |
| 입력 | `search_samples_by_name("gaas")` 호출 (소문자) |
| 기대 결과 | 반환된 리스트의 길이가 `1`이다. 반환된 시료의 `name == "GaAs-100"`이다. |

---

#### TC-2-15: 이름 검색 — 결과 없을 때 빈 리스트 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | `name="GaAs-100"` 시료 1개를 등록한다. |
| 입력 | `search_samples_by_name("존재하지않는이름")` 호출 |
| 기대 결과 | 반환값이 `[]` (빈 리스트)이다. |

---

#### TC-2-16: 복수 시료 등록 시 ID 중복 없음 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 없음 |
| 입력 | 유효한 시료 3개를 순서대로 등록한다. |
| 기대 결과 | 3개 시료의 `id`가 각각 `"S001"`, `"S002"`, `"S003"`이며, 모두 서로 다르다. |

---

#### TC-2-17: 복수 시료 등록 시 ID 순번 연속 증가 [Happy Path]

| 항목 | 내용 |
|------|------|
| 사전 조건 | 없음 |
| 입력 | 유효한 시료 2개를 등록한 뒤 각각 반환된 `Sample`의 `id`를 확인한다. |
| 기대 결과 | 첫 번째 등록: `id == "S001"`. 두 번째 등록: `id == "S002"`. |

---

## 7. 완료 기준

### PASS 조건

- `tests/phase2/test_sample_service.py` 내 모든 테스트 케이스가 PASS 상태여야 한다.
- 테스트 실행 명령: `pytest tests/phase2/ -v`
- 단 하나의 FAILED 또는 ERROR도 허용하지 않는다.

### 커버리지 기준

- Phase 2 구현 대상 파일(`src/services/sample_service.py`)의 라인 커버리지가 **90% 이상**이어야 한다.
- 커버리지 측정 명령: `pytest tests/phase2/ --cov=src/services/sample_service --cov-report=term-missing`
- HTML 리포트: `pytest tests/phase2/ --cov=src/services/sample_service --cov-report=html:htmlcov` 실행 후 `htmlcov/index.html`에서 확인.

### 참고: pytest.ini 전역 설정

`pytest.ini`에 아래 설정이 적용되어 있으므로 `pytest` 단독 실행 시 `src` 전체에 대한 커버리지 리포트가 자동 생성된다.

```ini
[pytest]
testpaths = tests
addopts = --cov=src --cov-report=html:htmlcov --cov-report=term-missing -v
```
