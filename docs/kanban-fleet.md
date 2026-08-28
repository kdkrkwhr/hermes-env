# Kanban 플릿 설정 (5인조 멀티에이전트)

출처: `hermes-kanban-fleet`에서 훔친 최소 설정. 프로필 이름 갈아엎지 말고 **dispatch / default_assignee만** 맞춘다.

## 역할

| 프로필 | 페르소나 | `dispatch_in_gateway` | `default_assignee` |
|--------|----------|------------------------|--------------------|
| `ops` | Ops(비서/디스패처) | **true** (유일) | **`pm`** |
| `pm` | PM(PM) | **false** | (미사용) |
| `dev` | Dev(개발) | **false** | (미사용) |
| `infra` | Infra(인프라) | **false** | (미사용) |
| `qa` | QA(QA) | **false** | (미사용) |

## 왜

- 게이트웨이 여러 개 켤 때 디스패처가 **이중 스윕**하면 claim/꼬임 난다.
- `default_assignee: ""`면 분해기가 이상한 assignee를 찍고 카드가 `ready`에 영원히 남을 수 있다.
- `ops`가 유일 디스패처 → **업무 성격에 따라 동적 라우팅**: 큰/복잡 → `pm` 분해, 소규모 개발 → `dev` 직행, 소규모 인프라 → `infra` 직행, 검증성 → `qa` 직행 (PM 우회). `default_assignee: pm` 은 미지정 카드용 fallback.
- **`ops` toolsets에 `kanban` 필수** — Ops이 dev/infra/qa에 직접 카드를 create/assign 하려면 필요. 상세 흐름: `workflow-cungya.md` §2.

## 적용

템플릿:

- `hermes/config.yaml.template` → `$HERMES_HOME/config.yaml` (default 워커)
- `hermes/profiles/ops/config.yaml.template` → `$HERMES_HOME/profiles/ops/config.yaml`의 `kanban:` 블록
- 기타 워커(`pm`/`dev`/`infra`/`qa`) 템플릿 → 각 프로필 config의 `kanban:` 블록

기존 config가 있으면 **`kanban:` 키만** 머지. 모델·시크릿·다른 섹션은 건드리지 말 것.

변경 후 해당 프로필 **gateway 재시작**.

## 선택

- `auto_decompose: false` — 디스패처가 채팅에서만 쪼개고 싶을 때. 기본은 `true` 유지.
- 하드 코딩 → `qa`(검수), 나머지 → `dev`/`infra` 라우팅은 SOUL/`workflow-cungya.md`에 한 줄로.

## 안 가져오는 것

- 프로필 rename (`orchestrator`/`generalist`/`coder`)
- fleet `install.ps1` 통설치
