# Claude Sub-Agent 구성

이 프로젝트는 5개의 전문화된 Sub-Agent로 구성된 워크플로우를 사용합니다.

## 에이전트 구성

| 에이전트 | 파일 | 역할 |
|---------|------|------|
| SubAgent1 | `subAgent1-document-consistency.md` | 문서 정합성 검증 |
| SubAgent2 | `subAgent2-code-implementation.md` | 코드 구현 |
| SubAgent3 | `subAgent3-test-verify.md` | 테스트 검증 |
| SubAgent4 | `subAgent4-compliance-verify.md` | 컴플라이언스 검증 |
| SubAgent5 | `subAgent5-repository-governance.md` | 저장소 거버넌스 (최종 Commit Gate) |

## 권장 실행 순서

```
[1단계] SubAgent1 — 문서 정합성 검증
          ↓ (문서 이상 없음 확인 후)
[2단계] SubAgent2 — 코드 구현
          ↓ (구현 완료 후)
[3단계] SubAgent3 + SubAgent4 — 병렬 실행 가능
         ├── SubAgent3: 테스트 검증
         └── SubAgent4: 컴플라이언스 검증
          ↓ (모두 PASS 시)
[4단계] SubAgent5 — 저장소 거버넌스 (Commit Gate)
          ↓ (APPROVED 시)
[완료] Commit 및 배포 승인
```

## 피드백 루프

- SubAgent3(테스트) 또는 SubAgent4(컴플라이언스)에서 문제 발견 시 → SubAgent2로 수정 요청
- SubAgent1(문서 정합성)에서 문제 발견 시 → 문서 수정 후 SubAgent1 재실행
- Critical·High 컴플라이언스 항목 존재 시 → SubAgent5가 BLOCKED 판정, SubAgent2 수정 후 재검증
- SubAgent5(저장소 거버넌스)에서 BLOCKED 판정 시 → 차단 사유 해소 후 SubAgent5 재실행

## SubAgent5 Commit Gate 규칙

SubAgent5는 아래 조건을 **모두** 충족해야만 APPROVED를 발행한다.

| 조건 | 설명 |
|------|------|
| 테스트 PASS | SubAgent3 보고서에 PASS 판정 필수 |
| 컴플라이언스 PASS | SubAgent4 보고서에 PASS 판정 필수 |
| Diff 검토 완료 | `git diff --staged` 분석 없이 commit 금지 |
| Atomic Commit | 단일 commit에 무관한 변경 혼재 금지 |
| 문서 동기화 | `CURRENT_STATE.md` / `TASKS.md` / `DECISIONS.md` 업데이트 필수 |
| Conventional Commit | commit message는 Conventional Commits 형식 사용 |
| 안전한 브랜치 | main/master 직접 commit 금지 |
| 위험 명령 차단 | `force push`, `reset --hard` 등 비가역 명령 금지 |

## 입력 파일 위치

프로젝트 루트에 다음 파일이 있어야 합니다:

- `PRD.md` — 제품 요구사항 문서
- `plan.md` — 구현 계획 문서

SubAgent5 실행 후 자동 생성·갱신되는 파일:

- `CURRENT_STATE.md` — 현재 시스템 상태
- `TASKS.md` — 태스크 진행 현황
- `DECISIONS.md` — 아키텍처·설계 결정 이력
