# AgentRadio/Coral 실시간 peer 연동 (5인조 fleet)

> 5인조 멀티에이전트(PM/Dev/Infra/QA/Ops)에 **실시간 peer 메시징**을 더하는 방법.
> 구현 세트는 [`../hermes/coral/`](../hermes/coral/), 워크플로우는 [`workflow-cungya.md`](workflow-cungya.md) 와 함께 읽는다.

## 무엇 / 왜

- **AgentRadio**(arXiv 2607.28430, repo `Coral-Protocol/AgentRadio`) = 장기 멀티에이전트 협업용 **passive awareness** 프레임워크. 핵심은 **Coral 메시지 서버**(MCP over Streamable HTTP).
- 현재 fleet 조율 = **Kanban(:9119) 카드 + Discord**, Ops 단일 디스패처(비동기·카드 기반).
- Coral은 그 위에 **실시간 peer 사이드채널**을 더한다 — Dev↔Infra↔QA 가 작업 중 findings·질문·블로커를 즉시 주고받고, 상대는 작업을 멈추지 않고 스텝 경계에서 받는다.
- **배치 원칙 = 보완(augment), 대체 아님.** Kanban 이 작업 상태의 단일 진실원(SoT)으로 남고, Coral 은 실시간 협업 대화용.

## 어떻게 붙는가 (아키텍처)

```
coral-server(:5555, 상시)  ──  세션 "hermes-fleet" (agents: pm,dev,infra,qa,ops)
        │ 각 에이전트 MCP URL = /mcp/v1/<secret>/mcp   (probe spawn 시 $CORAL_CONNECTION_URL 로 캡처)
        ▼
프로필별 config.yaml:  mcp_servers.coral.url = <그 에이전트의 URL>   (Hermes 네이티브 MCP, HTTP)
        ▼
Hermes 시작 → 각 에이전트가 mcp_coral_* 툴 8개 획득
   (create_thread / close_thread / add·remove_participant / send_message /
    wait_for_message / wait_for_mention / wait_for_agent)
        ▼
SOUL.md 의 [COORD] 섹션이 "언제/어떻게 쓸지" 규칙 제공
```

Hermes 는 MCP HTTP transport 를 지원하므로 **URL 한 줄**이면 붙는다. Coral 이 에이전트를 spawn 하는 원본 모델과 달리, 여기선 **Hermes 가 프로세스 소유** — probe 로 URL만 발급받아 Hermes 가 그 URL에 client 로 붙는다.

## 설치 (부트스트랩 이후 선택 단계)

```bash
export HERMES_HOME=~/.hermes                        # 0단계 값
bash hermes/coral/install-coral.sh                  # coral-server.jar 확보 (Java 24+)
bash hermes/coral/setup-hermes-coral.sh --inject pm,dev,infra,qa,ops --restart-gateway
```

SOUL 규칙 적용(동의 후 — 기존 SOUL 덮어씀에 주의):
```bash
for p in pm dev infra qa ops; do
  cp "hermes/profiles/$p/SOUL.md.template" "$HERMES_HOME/profiles/$p/SOUL.md"
done
```

검증:
```bash
for p in pm dev infra qa ops; do hermes mcp test coral --profile $p; done
# 각 ✓ Connected / Tools discovered: 8
```

## 운영 주의 (반드시)

1. **세션 secret 은 in-memory** — coral-server 재시작/재부팅 시 URL 무효. `setup-hermes-coral.sh` **재실행**이 복구 절차. `hermes/coral/autostart/` 로 로그온 자동복구(Windows Startup 폴더 / mac·linux cron·launchd).
2. **best-effort** — 서버(:5555) 없거나 `mcp_coral_*` 안 보이면 fleet 은 Kanban/Discord 로 정상 동작. SOUL 이 폴백을 지시.
3. **경계** — 카드 상태 전이·배정은 Kanban. Coral 로 결정 트래픽을 흘리지 말 것.
4. **의존성** — `pip install mcp`(Hermes MCP client), Java 24+(coral-server), Node/uv(불필요, HTTP transport 라).

### 2026-08-20 실전 학습 (Windows, 반드시 확인)
5. **probe 에이전트 bash 경로 (Windows 치명적)** — `agents/probe/coral-agent.toml` 의 `path = "bash"` 는 mac/linux 에선 정상이나, **Windows 예약작업/서비스 컨텍스트에서 `bash` 가 WSL 로 풀려 `execvpe(/bin/bash) failed` → probe 5개 즉시 사망 → 세션 close (probe URL 미기록)**. Windows 상시화 시 probe 런타임 경로를 **git-bash 절대경로**(예: `C:/Program Files/Git/bin/bash.exe`)로 고정할 것. (대화형 셸에선 우연히 되므로 오진 쉽다.)
6. **toolsets 누락 함정** — `setup-hermes-coral.sh`/`upsert_coral_mcp.py` 는 `mcp_servers.coral` 블록만 주입하고 **`toolsets` 에 `coral` 을 넣지 않는다**. toolset 에 `coral` 이 없으면 `mcp test` 는 Connected 라도 에이전트에게 `mcp_coral_*` 가 **노출되지 않아 무전 불가**. 설치 후 5프로필 `toolsets` 에 `coral` 포함 여부를 반드시 확인/추가.
7. **probe URL 함정** — probe 가 쓴 **distinct-UUID URL 만 유효**. `sessionId` 로 조립한 URL 은 401. 또한 probe URL 은 setup 의 동기 라인 **이후 async 로 기록**되므로, 재주입 전 `/tmp/coral-urls.txt` 에 distinct UUID(>1)가 들어올 때까지 **대기**할 것.
8. **`GET /api/v1/local/session/<SID>` 는 활성 세션에도 404** — 세션 생존 판정에 쓰지 말 것. keepalive ping 은 응답코드를 무시하고 보내기만 한다.
9. **상시 유지 패턴(Windows)** — coral-server 를 예약작업(로그온, `Start-Process`, 재시작 PT1M) 으로 서비스화 + hermes cron `--no-agent` 헬스 잡(1h)으로 서버/세션 감시. cron 은 게이트웨이 재시작 명령을 **금지**(lifecycle guard)하므로, URL 변경 후 게이트웨이 재시작은 별도 로그온 태스크(`autostart`)가 담당.
10. **한글(비-ASCII) 깨짐 — JVM 인코딩** — 한국어 Windows 는 JVM 기본 인코딩이 MS949 라, coral-server 가 메시지의 한글을 **U+FFFD(대체문자)로 저장·반환**한다(전송 바이트는 정상 UTF-8인데 서버가 깨뜨림; `Content-Type; charset=utf-8` 로는 안 고쳐짐). 서버 기동 java 인자에 `-Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8` 를 넣어야 한다. → `setup-hermes-coral.sh` 의 `start_server()` 에 반영됨(2026-08-20). 검증: 한글 메시지 송신 후 서버 echo 가 원문과 완전 일치.

## 요구사항 체크

- [ ] `hermes mcp test coral --profile <p>` 5개 전부 Connected
- [ ] coral-server 상시화(autostart) 등록
- [ ] SOUL `[COORD]` 규칙 적용 여부 사용자 확인
