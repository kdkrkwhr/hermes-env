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
| `autostart/` | 재부팅 자동복구 런처 (Windows `.cmd.template` / mac·linux `.sh`) |

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

## ⚠️ 핵심 주의

- **세션 secret은 in-memory** — coral-server 재시작/재부팅 시 URL 무효 → `setup-hermes-coral.sh` **재실행**해야 5개 살아남. `autostart/` 가 이걸 자동화.
- 서버(:5555) 없으면 `mcp_coral_*` 는 조용히 비활성 — fleet 은 Kanban/Discord 로 정상 동작(best-effort).
- `mcp` 파이썬 패키지 필요(`pip install mcp`) — 없으면 Hermes MCP 조용히 비활성.
- SOUL 규칙은 `../profiles/<p>/SOUL.md.template` 의 `[COORD]` 섹션 참조.
