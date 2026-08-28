# AGENT_BOOTSTRAP.md — 에이전트 환경 세팅

> 새 PC에서 Hermes 에이전트가 읽고 세팅하는 부트스트랩.
> **결정론적 단계(디렉토리·config·스킬·검증)는 전부 `bootstrap.sh` 가 실행한다.**
> 에이전트는 경로 3개를 받아 스크립트를 돌리고 출력을 보고할 뿐이다. 절차를 손으로 재현하지 않는다.
>
> 이 repo는 구조와 워크플로우만 이관한다. 프로젝트 코드·SSoT 본문·메모리·시크릿 값은 포함하지 않는다.
>
> **셸:** 모든 명령은 **git-bash**(Windows) / bash(mac·Linux) 기준. Hermes CLI 설치의 native-Windows 부분만 스크립트가 PowerShell로 위임한다.

---

## 0단계: 사용자에게 경로 질문 (필수)

세팅 전에 아래 3개를 사용자에게 묻는다. 추측 금지.

| # | 질문 | 예시 | 변수 |
|---|------|------|------|
| 1 | 작업 루트 (프로젝트 코드가 모일 곳) | `~/develop/project`, `D:\develop\project` | `PROJECT_ROOT` |
| 2 | E2E 루트 (ssot, reports 등 산출물) | `~/develop/e2e`, `D:\develop\e2e` | `E2E_ROOT` |
| 3 | Hermes 홈 (기본 `$HOME/.hermes`) | 엔터 시 기본값 | `HERMES_HOME` |

> 스크립트도 값이 비면 스스로 되묻지만, 에이전트가 먼저 물어 플래그로 넘기는 게 정석이다.
> 경로는 **git-bash 표기(`/c/...`)나 슬래시(`/`)** 로 넘긴다. 백슬래시 경로는 치환에서 깨질 수 있다.

---

## 1단계: 한 줄 실행

```bash
bash bootstrap.sh \
  --project-root "$PROJECT_ROOT" \
  --e2e-root     "$E2E_ROOT" \
  --hermes-home  "$HERMES_HOME"     # 생략 시 $HOME/.hermes
```

스크립트가 순서대로, **각 단계 검증 실패 시 즉시 중단**하며 실행한다:

| 스크립트 단계 | 내용 | 멱등성 |
|------|------|--------|
| 1 | 선행조건(git·python3) 확인 | — |
| 1-1 | Hermes CLI 설치 (없으면; 모델/키 마법사 생략) | 이미 있으면 건너뜀 |
| 2 | 디렉토리 구조 생성 (`$PROJECT_ROOT`, `$E2E_ROOT/{ssot,reports,hermes/skills}`, `$HERMES_HOME/profiles`) | mkdir -p |
| 3 | `config.yaml` + 5인조 프로필 config 배치, 플레이스홀더(`__E2E_ROOT__` 등) 실제 경로 치환 | 기존 config 덮어쓰지 않음 |
| 4 | 스킬 복사 → **`$E2E_ROOT/hermes/skills`** (config `skills.external_dirs` 가 읽는 위치) | — |
| 5 | `.env.example` → `$E2E_ROOT/.env.local` (이름만, 값은 사용자 몫) | 기존 파일 보존 |
| 끝 | 검증표 출력 (`doctor`). 하나라도 FAIL 이면 exit 1 | — |

**선택 플래그:**

| 플래그 | 효과 |
|--------|------|
| `--with-souls` | 역할별 `SOUL.md` 배치. **기존 SOUL 덮어씀** → 사용자 동의 후에만 |
| `--with-coral` | AgentRadio/Coral 실시간 peer 연동 설치·셋업 (Java 24+, `pip install mcp` 필요). 상세: [`docs/agentradio-coral.md`](docs/agentradio-coral.md) |
| `--ssot-url URL` | `ssot/` 가 비어있을 때만 clone |

---

## 2단계: 검증 (완료 판단은 스크립트가)

```bash
bash bootstrap.sh --check --project-root "$PROJECT_ROOT" --e2e-root "$E2E_ROOT" --hermes-home "$HERMES_HOME"
```

`doctor` 가 실제 파일시스템만 보고 표를 출력한다. **에이전트는 이 출력을 그대로 보고한다 — 완료 여부를 지어내지 않는다.** FAIL 이 있으면 "완료"라고 보고하지 않는다.

---

## 3단계: 사람/모델 판단이 필요한 마무리 (스크립트가 대신 못 하는 것)

1. **시크릿 값 입력** — `$E2E_ROOT/.env.local` 에 실제 토큰을 채운다 (`NOTION_TOKEN` 등, `.env.example` 주석 참조).
   **절대 금지:** `.env.local` 을 어떤 Git 레포에도 커밋하지 않는다. 커밋 시도 발견 시 즉시 경고.
2. **스킬 레거시 경로 검토** — 스크립트가 스킬 안 레거시 절대경로(`D:\develop`, `/Users/*/develop`)를 스캔해 목록만 보고한다.
   판단이 애매한 파일은 건드리지 말고 사용자에게 목록만 전달. 확실한 것만 `$E2E_ROOT` 기준으로 수정.
3. **SSoT clone** — 레포 URL 을 사용자에게 확인 후 `--ssot-url` 로 재실행 (아직 없으면 건너뜀).
4. **SOUL/coral** — 필요 시 사용자 동의 하에 `--with-souls` / `--with-coral`.

---

## 워크플로우 컨벤션 (세팅 후에도 유지 — 이 repo의 본질)

1. **경로 변수**: 하드코딩 금지. 항상 `$PROJECT_ROOT` / `$E2E_ROOT` / `$HERMES_HOME` 기준.
2. **산출물 분리**: 에이전트 리포트 → `$E2E_ROOT/reports`. 프로젝트 레포 안에 넣지 않음.
3. **SSoT 원칙**: 스펙/DDL/API 문서는 `$E2E_ROOT/ssot` 레포에서만 관리. 프로젝트 레포에 사본 두지 않음.
4. **시크릿**: `.env.local` 단일 파일. Git 커밋 금지. 새 머신에서는 수동 입력.
5. **에이전트 완료 보고**: block/리뷰요청 대신 complete + 결과 보고.

---

## 5인조 멀티에이전트 워크플로우 (참고)

대장님이 **PM/Dev/Infra/QA/Ops** 5인조로 일하는 흐름:

- 페르소나는 대화 라벨. 칸반 `assignee` 는 프로필명(`pm`/`dev`/`infra`/`qa`/`ops`).
- 흐름: 대장님 지시 → PM 분해·배정(Ops 이 kanban 대리) → Dev+Infra 구현 → QA 검수(PASS→Done) → Ops 이 대장님께 보고.
- `ops` 만 디스패처(`dispatch_in_gateway: true`, `default_assignee: pm`), 나머지는 `false`.
- 호칭: **"대장님"** (대표님 금지).

상세: [`docs/workflow-cungya.md`](docs/workflow-cungya.md), [`docs/kanban-fleet.md`](docs/kanban-fleet.md)
