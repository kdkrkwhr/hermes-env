# hermes-env

어떤 PC든 `git clone` 한 번. 경로 3개 넣고 `bootstrap.sh` 실행하면 끝.

Hermes 에이전트 작업 환경(디렉토리 구조, 스킬, config, 워크플로우 규칙)을 그대로 옮기는 bootstrap repo다.
프로젝트 코드·SSoT 본문·메모리·시크릿 값은 안 넣는다.

![bootstrap flow](docs/images/flow.png)

## Quick Start

```bash
git clone <이 레포 URL> hermes-env
cd hermes-env

# 경로 3개만 넣으면 디렉토리·config·스킬 배치 + 검증까지 결정론적으로 실행 (git-bash/bash)
bash bootstrap.sh --project-root ~/develop/project --e2e-root ~/develop/e2e
bash bootstrap.sh --check --project-root ~/develop/project --e2e-root ~/develop/e2e   # 검증만
```

절차·검증이 스크립트에 박혀 있어 **무료/약한 모델에서도 안 깨진다.** 에이전트에게 시키려면:

> `AGENT_BOOTSTRAP.md` 대로 경로 3개 물어보고 `bootstrap.sh` 실행해줘.

`hermes` CLI가 없으면 스크립트가 공식 설치기로 설치한다 (모델/API 키 마법사는 생략). 멱등이라 여러 번 돌려도 기존 config·시크릿을 덮어쓰지 않는다.

| # | 질문 | 변수 |
|---|------|------|
| 1 | 프로젝트 코드가 모일 루트 | `PROJECT_ROOT` |
| 2 | ssot / reports 등 E2E 루트 | `E2E_ROOT` |
| 3 | Hermes 설치 경로 (기본 `$HOME/.hermes`) | `HERMES_HOME` |

## 한눈에

![repo → machine layout](docs/images/architecture.png)

## 구조

```
├── bootstrap.sh                # 결정론 세팅 실행기 (1~7단계 + --check doctor)
├── AGENT_BOOTSTRAP.md          # 스크립트 실행 가이드 + 판단 필요한 마무리
├── README.md
├── .env.example                # 시크릿 이름만 (값 없음)
├── hermes/
│   ├── install-hermes.sh       # Hermes CLI 설치 (없으면, Unix/mac/WSL; Win은 ps1 위임)
│   ├── install-hermes.ps1      # Hermes CLI 설치 (없으면, Windows native)
│   ├── config.yaml.template    # default 워커 (워크플로우 전용, 모델/프로바이더 제외)
│   ├── profiles/
│   │   ├── pm/                 # PM(프로젝트 매니저) — SOUL + kanban 템플릿
│   │   ├── dev/                # Dev(개발 리드) — SOUL + config 템플릿
│   │   ├── infra/              # Infra(인프라) — SOUL + config 템플릿
│   │   ├── qa/                 # QA(검수) — SOUL + config 템플릿(토론 규칙 포함)
│   │   └── ops/                # Ops(비서/디스패처) — SOUL + kanban 템플릿
│   ├── coral/                  # AgentRadio/Coral 실시간 peer 연동 (설치·셋업·autostart)
│   └── skills/                 # 이식용 스킬 (경로 정규화됨)
└── docs/
    ├── conventions.md          # 디렉토리 / 워크플로우 규칙
    ├── kanban-fleet.md         # 5인조 멀티에이전트 dispatch / assignee
    ├── workflow-cungya.md      # 역할별 페르소나 5인조 워크플로우
    ├── agentradio-coral.md     # 실시간 peer 사이드채널 연동 (선택)
    └── images/
        ├── flow.png
        └── architecture.png
```

## 포함 / 미포함

| 포함 | 미포함 |
|------|--------|
| 부트스트랩 체크리스트 | 프로젝트 코드 |
| Hermes CLI 설치 래퍼 (없으면 공식 설치기 호출) | 모델명·프로바이더·API키 |
| config 워크플로우 템플릿(kanban/discord/SOUL 등) | 에이전트 메모리 |
| 이식용 스킬 세트 | `.env` 실제 값 |
| 컨벤션 문서 / 다이어그램 | 특정 PC 하드코딩 경로 |

## 포함 스킬 (요약)

- `hermes-agent` — Hermes 설정·확장
- `ponytail` 계열 — 최소 구현 / 과설계 리뷰
- `e2e-workspace` — E2E 레이아웃 컨벤션
- `code-flow-audit` — 엔트리→스토어 추적
- `hermes-credential-discovery` — 자격증명 탐색
- `kanban-worker` / `kanban-orchestrator`
- `ocr-and-documents`
- GitHub 워크플로 스킬 묶음 (auth, issues, PR, review, repo, inspection)

## 대상

- Hermes Agent를 새 머신에 다시 깔 사람
- 팀 온보딩 (같은 디렉토리·스킬·규칙으로 맞추고 싶을 때)

## 다음 문서

1. [`AGENT_BOOTSTRAP.md`](AGENT_BOOTSTRAP.md) — 실제 세팅 순서
2. [`docs/conventions.md`](docs/conventions.md) — 디렉토리 분리·산출물 규칙
3. [`docs/kanban-fleet.md`](docs/kanban-fleet.md) — 양송 Kanban dispatch / assignee
4. [`docs/workflow-cungya.md`](docs/workflow-cungya.md) — 역할별 페르소나 5인조 워크플로우 (대장님 멀티에이전트)
5. [`team-hub/`](team-hub/) — 5인조 플릿 팀 허브 (정적 사이트, 역할별 메뉴 + 부트스트랩 연계)
