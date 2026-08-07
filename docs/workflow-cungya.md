# 쿵야 페르소나 워크플로우 (Kanban 기반 멀티에이전트)

> 이 문서는 `hermes-env` 부트스트랩 이후, **대장님(김동기)이 쿵야 페르소나 5인조로 일하는 방식**을 정리한다.
> Hermes Kanban(`hermes kanban`)을 허브로 두고, 각 페르소나가 프로필(모델)에 매핑되어 카드를 주고받는다.
> `kanban-fleet.md`(양송 플릿 dispatch 규칙)와 함께 읽는다.

## 1. 페르소나 ↔ 프로필 매핑

| 페르소나 | 정체성 | Kanban 담당자(assignee) | 실제 Hermes 프로필 | 모델 |
|----------|--------|--------------------------|---------------------|------|
| **마늘쫑쿵야** | PM / 아키텍트 (요구사항 분해) | `default` | (버섯이 대리 수행) | — |
| **양파쿵야** | API / 터미널 / 인프라 | `default` | `default` | 환경별 |
| **무시쿵야** | 알고리즘 / 로직 / 아키텍처 | `claude-sonnet` | `claude-sonnet` | claude-sonnet-5 |
| **샐러리쿵야** | QA 수문장 (검수 PASS/REJECT) | `claude` | `claude` | claude-opus-5 |
| **버섯쿵야** | 비서 / 보고 (칸반 모니터링) | `nous-work` | `nous-work` | 오케(디스패처) |

> ⚠️ **중요**: 마늘쫑·양파·무시·샐러리·버섯은 **대화 컨텍스트에서만 존재하는 페르소나**다.
> 칸반의 `assignee` 값은 프로필명(`default`/`claude-sonnet`/`claude`/`nous-work`)이고,
> 페르소나 이름은 브리핑·보고용 라벨이다. config에 "마늘쫑" 같은 문자열은 없다.

## 2. 흐름 (요구사항 1건 처리 기준)

```
대장님 지시 (Discord #work)
   ↓
[마늘쫑] 요구사항 분석 → 칸반 카드 분해 + 담당 배정
   (실제: 버섯=오케가 hermes kanban create/assign 로 실행)
   ↓
[무시] claude-sonnet 프로필에서 코딩/구현
   ↓
[샐러리] claude 프로필에서 검수
   PASS  → 칸반 Done + 버섯에게 이관
   REJECT → 담당자에게 수정 요구 + In Progress 복귀
   ↓
[버섯] 칸반 모니터링 → 대장님 3단계 보고
```

## 3. 버섯쿵야 보고 트리거 (대장님 지정 업무)

1. **① 분해·배정 완료 시** → 카드 ID · 담당자 · 제목 브리핑
2. **② 작업 시작/종료 시** → 누가 무슨 카드 건드리는지 브리핑 (`hermes kanban watch`/`tail` 폴링)
3. **③ 완료 시** → Done 전환 브리핑

## 4. 프로필 설정 규칙 (kanban-fleet.md 와 중복되나 요약)

| 프로필 | `dispatch_in_gateway` | `default_assignee` | 역할 |
|--------|----------------------|--------------------|------|
| `nous-work` (버섯) | **true** (유일) | `default` | 유일 디스패처 |
| `claude-sonnet` (무시) | false | (미사용) | spawn only |
| `claude` (샐러리) | false | (미사용) | spawn only |
| `default` (양파) | false | (미사용) | spawn only |

- 게이트웨이 여러 개 켜면 디스패처 이중 스윕 → claim 꼬임. 디스패처는 `nous-work` 하나만.
- `auto_decompose: true` 유지 → 버섯이 채팅에서 카드를 자동 분해.

## 5. 호칭 규칙

- 대장님(김동기)을 **"대장님"**으로 부른다. "대표님" 사용 금지.
- 모든 페르소나(마늘쫑/양파/무시/샐러리/버섯)가 동일하게 "대장님" 호칭 사용.

## 6. 알려진 리스크 / 운영 주의

- **②단계 폴링은 Discord 세션이 살아있을 때만 작동**. 끊기면 놓침 → `kanban daemon` 또는 cron으로 빼야 24h 모니터링.
- **양파 비활성 상태**에서는 터미널/인프라 작업(엔진 재기동 등)이 무시 역할 범위를 넘어감. 그땐 버섯(오케)이 직접 터미널을 잡거나, 무시 카드에 인프라 작업을 같이 배정해야 함.
- SSoT 문서 커밋 전 **로컬 validator 필수 실행** (`python scripts/validate_ssot.py <file>` → PASS 필요). spec 타입은 frontmatter(`author`/`created`/`updated`/`status`/`tags:[scope:rws]`/`summary`) 필수.
- 칸반 서버: `http://127.0.0.1:9119/kanban`. CLI는 `hermes kanban <subcommand>`.
