# hermes/coral — AgentRadio/Coral 실시간 peer 연동

5인조 Hermes fleet(pm/dev/infra/qa/ops)에 **실시간 peer 메시징**을 붙이는 이식용 세트.
Kanban(작업 상태 SoT)은 그대로 두고 그 위에 **보완 사이드채널**로 얹는다.

> 배경·원리·운영주의는 [`../../docs/agentradio-coral.md`](../../docs/agentradio-coral.md) 참조.

## 파일

| 파일 | 역할 |
|------|------|
| `install-coral.sh` | coral-server.jar(+JDK24 안내) 를 `$CORAL_HOME` 에 확보 (바이너리는 repo 미포함) |
| `setup-hermes-coral.sh` | 서버 기동 + hermes-fleet 세션 생성 + 5프로필 `mcp_servers.coral` upsert (재실행 가능) |
| `upsert_coral_mcp.py` | config.yaml 에 coral MCP 블록 idempotent 주입(주석/포맷 보존) |
| `agents/probe/` | Coral 로컬 레지스트리용 no-op 프로브(세션 에이전트 URL 캡처용) |
| `coral-discord-bridge.py` | Coral 대화를 Discord 채널(기본 #agent-multi)로 실시간 미러링 — 대장님 가시성 |
| `coral-autoresponder.py` | idle 에이전트가 coral 멘션에 자율 응답(헤드리스 `hermes -z` 턴). 루프 가드 내장 |
| `autostart/` | 재부팅 자동복구 런처 (setup + gateway restart + 브리지, Windows `.cmd.template` / mac·linux `.sh`) |

## 빠른 시작

```bash
export HERMES_HOME=~/.hermes            # 부트스트랩 0단계 값
bash hermes/coral/install-coral.sh      # jar 확보 (Java 24+ 필요; 없으면 안내대로 JDK25)
bash hermes/coral/setup-hermes-coral.sh --inject pm,dev,infra,qa,ops --restart-gateway
```

검증:
```bash
for p in pm dev infra qa ops; do hermes mcp test coral --profile $p; done
# 각각 ✓ Connected / Tools discovered: 8 (coral_*)
```

## 가시성 — Coral 대화를 Discord에서 보기

Coral은 에이전트 간 **사이드채널**이라 그 대화는 기본적으로 Discord에 안 뜬다. 두 층으로 보이게 한다:

- **A. 미러 브리지** — `coral-discord-bridge.py`가 coral 전체 스레드를 폴링해 새 메시지를 **#agent-multi** 채널로 실시간 복사. autostart가 `--loop 10`으로 상시 기동.
  - 첫 실행은 기존 메시지를 baseline으로 기록만(과거 도배 방지), 이후 새 것만 미러.
  - 채널 변경: `BRIDGE_CHANNEL=discord:#원하는채널`. `hermes send`가 discord 타겟을 인식하려면 프로필 지정 필요(브리지는 `BRIDGE_PROFILE=ops` 기본).
  - ⚠️ Windows: 브리지는 git-bash를 명시 호출(`BRIDGE_BASH`) — bare `bash`는 WSL이 잡혀 멈춤.
  - **멘션 매핑**: coral은 프로필명(`dev`)으로 멘션하지만 Discord는 봇 ID(`<@123...>`)라야 진짜 멘션이 된다.
    `mention-map.json.template` 을 복사해 실제 봇 ID를 채우고 `mention-map.json` 으로 저장하면(위치: `$CORAL_HOME` 또는 `BRIDGE_MENTION_MAP`),
    브리지가 미러 시 `@dev`·멘션목록을 `<@봇ID>` 로 변환한다. 매핑 파일이 없으면 평문 `@name` 유지(무해).
- **B. ops 하이라이트** — ops SOUL이 결정적 순간(수신·블로커·합의·완료)만 **#work**에 한 줄 요약. 전문은 A, 사람용 요약은 B.

## 자율 협업 — idle 에이전트가 coral 멘션에 자동 응답

`coral-autoresponder.py`가 coral을 폴링해 "에이전트 X가 동료에게 멘션됨"을 감지하면, 헤드리스 `hermes --profile X -z` 턴을 띄워 X가 coral로 응답하게 한다. 에이전트가 작업 중이 아니어도(=상시 watcher 없이도) 멘션에 반응한다.

- **전제**: 각 프로필 SOUL의 `[COORD]`에 **"coral 동료 멘션에는 응답하라(Discord 봇 침묵 규칙의 예외)"** 카브아웃이 있어야 함(SOUL 템플릿에 포함). 없으면 에이전트가 "봇 멘션 침묵" 규칙으로 no-action 처리.
- **루프 가드**: 스레드당 자동응답 상한(`AUTORESP_THREAD_CAP=4`) + 프롬프트의 "조치 무의미하면 응답 안 함(no action)" 이스케이프 → 잡담성 핑백은 자연 종료.
- **킬스위치**: `AUTORESP_ENABLED=0` 이면 감지만 하고 스폰 안 함(드라이런).
- **비용**: 멘션 1건 = 헤드리스 LLM 턴 1회. 상한으로 폭주 방지.

## ⚠️ 핵심 주의

- **세션 secret은 in-memory** — coral-server 재시작/재부팅 시 URL 무효 → `setup-hermes-coral.sh` **재실행**해야 5개 살아남. `autostart/` 가 이걸 자동화.
- 서버(:5555) 없으면 `mcp_coral_*` 는 조용히 비활성 — fleet 은 Kanban/Discord 로 정상 동작(best-effort).
- `mcp` 파이썬 패키지 필요(`pip install mcp`) — 없으면 Hermes MCP 조용히 비활성.
- SOUL 규칙은 `../profiles/<p>/SOUL.md.template` 의 `[COORD]` 섹션 참조.
