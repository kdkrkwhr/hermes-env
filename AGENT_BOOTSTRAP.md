# AGENT_BOOTSTRAP.md — 에이전트 환경 세팅 순서

> 이 문서는 **새 PC에서 Hermes 에이전트가 읽고 그대로 실행**하는 부트스트랩 체크리스트다.
> 각 단계 끝의 검증 명령이 통과해야 다음으로 진행한다. 실패 시 사용자에게 멈추고 보고할 것.
>
> **이 repo는 구조와 워크플로우만 이관한다.** 프로젝트 코드, SSoT 문서 내용, 메모리는 포함하지 않는다.

---

## 0단계: 사용자에게 경로 질문 (필수, 건너뛰기 금지)

에이전트는 세팅 전에 사용자에게 아래를 **반드시** 질문한다. 추측으로 진행 금지.

| # | 질문 | 예시 | 저장 변수 |
|---|------|------|-----------|
| 1 | 작업 루트 디렉토리는? (프로젝트 코드들이 모일 곳) | Windows: `D:\develop\project` / Mac: `~/develop/project` | `PROJECT_ROOT` |
| 2 | E2E 루트는? (ssot, reports 등 에이전트 작업물) | `D:\develop\e2e` / `~/develop/e2e` | `E2E_ROOT` |
| 3 | Hermes 설치 경로는? (기본: `$HOME/.hermes`) | 기본값 엔터 시 `$HOME/.hermes` | `HERMES_HOME` |

**이 질문 없이 세팅을 시작하면 안 된다.** 이 repo의 모든 스크립트와 컨벤션은 이 3개 변수 기준으로 동작한다.

---

## 1단계: 선행 조건 확인

아래 명령을 실행하고 전부 통과하는지 확인:

```bash
# Git
git --version || echo "FAIL: git 설치 필요"

# Python 3.10+
python3 --version || echo "FAIL: python3 설치 필요"

# OS 확인
uname -s   # Linux / Darwin / MINGW64_NT (git-bash)
```

- [ ] git 존재
- [ ] python3 존재
- [ ] OS 파악 완료 (이후 단계에서 분기)

**Windows 주의:** 기본 셸 명령은 **git-bash** 기준. PowerShell이 아니다.
예외는 **1-1단계 Hermes CLI 설치**뿐 — 공식 Windows 설치기는 PowerShell이다.

---

## 1-1단계: Hermes CLI 설치 (없으면)

`hermes` 가 PATH에 없으면 공식 설치 스크립트를 돌린다. 이미 있으면 건너뛴다.

- 모델/프로바이더 마법사는 **대화형**이므로 생략한다. 사용자는 나중에 `hermes setup` 또는 `.env`로 설정.
- Windows 공식 기본 데이터 경로는 `%LOCALAPPDATA%\hermes`다. 이 repo는 0단계 `$HERMES_HOME`(기본 `$HOME/.hermes`)을 쓰므로 **반드시 `-HermesHome` / `--hermes-home`을 넘긴다.**
- 설치 후 현재 셸 PATH에 `hermes`가 안 잡히면 터미널을 다시 열고 재검증한다.

```bash
export HERMES_HOME   # 0단계에서 받은 값
bash "$BOOTSTRAP_REPO/hermes/install-hermes.sh"
```

Windows에서 에이전트가 PowerShell을 쓰는 경우:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "$BOOTSTRAP_REPO\hermes\install-hermes.ps1" `
  -HermesHome $env:HERMES_HOME
```

**검증:**
```bash
command -v hermes && hermes --version && echo OK || echo FAIL
```

- [ ] `hermes` 명령 존재 (또는 이번 단계에서 설치 완료)
- [ ] `hermes --version` 출력됨

---

## 2단계: 디렉토리 구조 생성

0단계에서 받은 변수로 구조를 만든다:

```bash
mkdir -p "$PROJECT_ROOT"          # 프로젝트 코드 (repo당 1개 디렉토리)
mkdir -p "$E2E_ROOT/ssot"         # SSoT 레포 클론 위치
mkdir -p "$E2E_ROOT/reports"      # 에이전트 산출물 (프로젝트 레포에 넣지 않음!)
mkdir -p "$HERMES_HOME/profiles"  # Hermes 프로필
```

**검증:**
```bash
test -d "$PROJECT_ROOT" && test -d "$E2E_ROOT/reports" && echo OK || echo FAIL
```

### 디렉토리 분리 규칙 (컨벤션)

| 경로 | 용도 | 규칙 |
|------|------|------|
| `$PROJECT_ROOT/<repo>` | 제품 코드 (각자 자기 Git 레포) | 에이전트 산출물(리포트/분석)을 여기 두지 않음 |
| `$E2E_ROOT/ssot` | SSoT 레포 (specs, ddl, adr) | 별도 Git 레포를 클론 |
| `$E2E_ROOT/reports` | 에이전트 작업 리포트 | Git 관리 선택 |
| `$E2E_ROOT/.env.local` | 공통 시크릿 | **절대 Git에 커밋 금지** |

---

## 3단계: Hermes config 배치

```bash
# default 워커 템플릿 (모델/프로바이더는 hermes setup 또는 .env로 세팅)
cp "$BOOTSTRAP_REPO/hermes/config.yaml.template" "$HERMES_HOME/config.yaml"

# 5인조 멀티에이전트 플릿: 프로필별 kanban 블록 (기존 config가 있으면 kanban: 키만 머지)
for p in pm dev infra qa ops; do
  mkdir -p "$HERMES_HOME/profiles/$p"
  test -f "$HERMES_HOME/profiles/$p/config.yaml" || \
    cp "$BOOTSTRAP_REPO/hermes/profiles/$p/config.yaml.template" \
       "$HERMES_HOME/profiles/$p/config.yaml"
done
```

규칙 요약:

- `ops` (Ops) → `dispatch_in_gateway: true`, `default_assignee: pm` (유일 디스패처)
- `pm` / `dev` / `infra` / `qa` → `dispatch_in_gateway: false`
- 모델/프로바이더는 이 repo에 없음. 새 머신에서 `hermes setup` 또는 `.env`(`OPENROUTER_API_KEY` 등)로 세팅.

상세: `docs/kanban-fleet.md`, `docs/workflow-cungya.md`

## 3-1단계: 역할별 페르소나 SOUL 배치 (선택)

워크플로우 문서(`docs/workflow-cungya.md` §7)의 역할별 페르소나를 실제 시스템 프롬프트로 박으려면, 각 프로필의 `SOUL.md`에 템플릿을 복사한다. **기존 SOUL을 덮어쓰므로 적용 전 사용자 동의 필수** (특히 `claude` 프로필은 이미 "친구 말투" SOUL일 수 있음).

```bash
for p in pm dev infra qa ops; do
  cp "$BOOTSTRAP_REPO/hermes/profiles/$p/SOUL.md.template" "$HERMES_HOME/profiles/$p/SOUL.md"
done
```

`config.yaml.template` 안의 플레이스홀더(`__E2E_ROOT__`, `__PROJECT_ROOT__`)가 **주석이 아닌 실제 설정 라인에만** 있는지 확인 후 치환한다. 현재 템플릿은 모든 경로 설정이 선택 사항(주석 처리)이라, 기본 배치는 치환 없이 복사만 합니다.

**검증:**
```bash
test -f "$HERMES_HOME/config.yaml" && echo OK || echo FAIL
grep -n "dispatch_in_gateway" "$HERMES_HOME/config.yaml" || true
```

---

## 3-2단계: AgentRadio/Coral 실시간 peer 연동 (선택)

5인조에 **실시간 peer 메시징 사이드채널**을 붙인다(Kanban 은 그대로 SoT, Coral 은 보완). 상세: [`docs/agentradio-coral.md`](docs/agentradio-coral.md).

```bash
bash "$BOOTSTRAP_REPO/hermes/coral/install-coral.sh"        # coral-server.jar 확보 (Java 24+ 필요)
cp -r "$BOOTSTRAP_REPO/hermes/coral" "$HERMES_HOME/coral"    # 스크립트 이관
bash "$HERMES_HOME/coral/setup-hermes-coral.sh" --inject pm,dev,infra,qa,ops --restart-gateway
```

- `mcp` 파이썬 패키지 필요(`pip install mcp`) — 없으면 Hermes MCP 조용히 비활성.
- **세션 secret 은 서버 재시작마다 바뀜** → 재부팅 자동복구는 `hermes/coral/autostart/` 등록(Windows Startup 폴더 / mac·linux cron).
- SOUL `[COORD]` 규칙은 3-1단계에서 SOUL 템플릿을 복사하면 함께 적용됨.

**검증:**
```bash
for p in pm dev infra qa ops; do hermes mcp test coral --profile $p; done   # 각 ✓ Connected / Tools: 8
```

---

## 4단계: 스킬 배치

```bash
mkdir -p "$HERMES_HOME/skills"
cp -r "$BOOTSTRAP_REPO/hermes/skills/"* "$HERMES_HOME/skills/"
```

### 4-1. 스킬 내 경로 정규화

스킬 파일들에 레거시 절대경로(예: `D:\develop\e2e`)가 박혀 있을 수 있다. 아래 스캔으로 찾아 사용자에게 보고하고, `$E2E_ROOT` 기준으로 치환할지 확인받는다:

```bash
grep -rln "D:\\\\develop\|/Users/[a-z]*/develop" "$HERMES_HOME/skills/" 2>/dev/null
```

결과가 있으면 → 각 파일을 열어 `$E2E_ROOT` 상대 표현(또는 설명 텍스트)으로 바꾼다.
**판단이 애매한 파일은 건드리지 말고 목록만 사용자에게 전달.**

---

## 5단계: 환경변수 / 시크릿

```bash
cp "$BOOTSTRAP_REPO/.env.example" "$E2E_ROOT/.env.local"
```

그리고 사용자에게 안내:
> `.env.local`에 실제 토큰 값을 채워주세요. 목록:
> - `NOTION_TOKEN` — Notion integration 토큰
> - (기타 프로젝트에서 쓰는 키들은 .env.example 주석 참조)

**검증 (값이 채워졌는지가 아니라 파일 존재만):**
```bash
test -f "$E2E_ROOT/.env.local" && echo OK || echo FAIL
```

**절대 금지:** `.env.local`을 어떤 Git 레포에도 커밋하지 않는다. 커밋하려는 시도를 발견하면 사용자에게 즉시 경고.

---

## 6단계: SSoT 클론 (선택)

SSoT 레포 URL을 사용자에게 확인 후:

```bash
cd "$E2E_ROOT/ssot" && git clone <SSO_REPO_URL> .
```

SSoT 레포가 아직 없으면 이 단계는 건너뛰고, 디렉토리 규칙만 유지한다.

---

## 7단계: 최종 검증 리포트

에이전트는 아래 표를 사용자에게 출력하고 마무리한다:

| 항목 | 상태 |
|------|------|
| 경로 변수 3개 설정됨 | ✅/❌ |
| Hermes CLI 설치 (`hermes --version`) | ✅/이미 있음/❌ |
| 디렉토리 구조 생성 | ✅/❌ |
| config.yaml 배치 + 플레이스홀더 치환 | ✅/❌ |
| 스킬 배치 | ✅/❌ |
| 스킬 내 레거시 경로 스캔 결과 | N개 파일 발견, 처리 여부 |
| .env.local 생성 (값 입력은 사용자 몫) | ✅/❌ |
| SSoT 클론 | ✅/⏭️ 건너뜀 |

**미완료 항목이 있으면 "완료"라고 보고하지 않는다.**

---

## 워크플로우 컨벤션 요약 (세팅 후에도 유지)

이 repo의 본질은 구조가 아니라 이 규칙들이다:

1. **경로 변수**: 하드코딩 금지. 항상 `$PROJECT_ROOT` / `$E2E_ROOT` / `$HERMES_HOME` 기준.
2. **산출물 분리**: 에이전트 리포트 → `$E2E_ROOT/reports`. 프로젝트 레포 안에 넣지 않음.
3. **SSoT 원칙**: 스펙/DDL/API 문서는 `$E2E_ROOT/ssot` 레포에서만 관리. 프로젝트 레포에 스펙 문서 사본 두지 않음.
4. **시크릿**: `.env.local` 단일 파일. Git 커밋 금지. 새 머신에서는 수동 입력.
5. **에이전트 완료 보고**: block/리뷰요청 대신 complete + 결과 보고.

---

## 8단계: 역할별 페르소나 워크플로우 안내 (선택)

세팅 후 대장님이 **5인조 멀티에이전트(PM/Dev/Infra/QA/Ops)** 멀티에이전트로 일하려면 아래를 숙지한다.

- 페르소나는 대화 컨텍스트용 라벨. 칸반 `assignee`는 프로필명(`pm`/`dev`/`infra`/`qa`/`ops`).
- 매핑: PM(PM)→`pm`, Dev(개발)→`dev`, Infra(인프라)→`infra`, QA(QA)→`qa`, Ops(비서/디스패처)→`ops`.
- 흐름: 대장님 지시 → PM(pm) 분해·배정(Ops이 kanban create/assign 대리) → Dev(dev)+Infra(infra) 구현 → QA(qa) 검수(PASS→Done, REJECT→수정) → Ops(ops)이 대장님께 3단계 보고.
- 호칭: 대장님을 **"대장님"**으로 부른다 ("대표님" 금지).

상세: [`docs/workflow-cungya.md`](docs/workflow-cungya.md)
