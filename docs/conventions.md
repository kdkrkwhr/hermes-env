# 컨벤션 — 이 구조를 유지하기 위한 규칙

## 디렉토리 분리

| 경로 | 용도 | Git |
|------|------|-----|
| `$PROJECT_ROOT/<repo>` | 제품 코드 | 각자 독립 레포 |
| `$E2E_ROOT/ssot` | 스펙/DDL/ADR (SSoT) | 별도 레포 1개 |
| `$E2E_ROOT/reports` | 에이전트 산출물 | 선택 |
| `$E2E_ROOT/.env.local` | 시크릿 | ❌ 절대 금지 |

## 규칙

1. **하드코딩 경로 금지** — 항상 `$PROJECT_ROOT` / `$E2E_ROOT` / `$HERMES_HOME`
2. **에이전트 리포트는 프로젝트 레포에 넣지 않음** → `$E2E_ROOT/reports`
3. **스펙 문서는 SSoT 레포에만** — 프로젝트에 사본 두지 않음
4. **시크릿은 .env.local 하나** — 새 머신에서는 수동 입력
5. **에이전트 완료 = complete + 결과 보고** (block/리뷰요청 금지)
6. **custom_providers는 list-of-dicts** — dict 형식으로 쓰면 config 날아감
7. **모델/프로바이더 정보는 이 repo에 넣지 않음** — 환경 의존/시크릿. `hermes setup` 또는 `.env`로 세팅
8. **경로 표기 — 항상 절대경로, 맨몸 상대경로 금지**
   - **Windows/git-bash**: 드라이브가 `/d/` 로 마운트됨. `/d/...`(맨 앞 슬래시 필수, 드라이브 소문자) 사용. `d/...`(슬래시 없는 상대경로 → cwd 기준 엉뚱한 폴더)·`D:` 백슬래시 **금지**. 변환은 `cygpath -u 'D:\dir'` / `cygpath -w /d/dir`.
   - **macOS/Linux**: `/Users/...` 또는 `$HOME/...` 절대경로. `Users/...` 같은 맨몸 상대경로 금지.
   - *bootstrap.sh 가 OS별(Windows·macOS)로 이 규칙을 config `environment_hint` 에 자동 주입한다.*

## Kanban 플릿 (5인조 멀티에이전트)

- 디스패처 `ops`만 `kanban.dispatch_in_gateway: true`
- 워커 `pm` / `dev` / `infra` / `qa`는 `false` (이중 디스패치 방지)
- `ops.kanban.default_assignee: pm`

상세: [`docs/kanban-fleet.md`](kanban-fleet.md)

## 역할별 페르소나 워크플로우

대장님이 5인조 멀티에이전트(PM/Dev/Infra/QA/Ops)로 일하는 멀티에이전트 흐름.
페르소나는 대화 컨텍스트 전용 라벨이고, 칸반 assignee는 프로필명(`pm`/`dev`/`infra`/`qa`/`ops`)이다.

| 페르소나 | 칸반 assignee | 프로필 |
|----------|---------------|--------|
| PM (PM) | `pm` | `pm` |
| Dev (개발 리드) | `dev` | `dev` |
| Infra (인프라) | `infra` | `infra` |
| QA (QA) | `qa` | `qa` |
| Ops (비서/디스패처) | `ops` | `ops` |

상세: [`docs/workflow-cungya.md`](workflow-cungya.md)
