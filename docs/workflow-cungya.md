# 역할별 페르소나 워크플로우 (Kanban 기반 멀티에이전트)

> 이 문서는 `hermes-env` 부트스트랩 이후, **대장님(김동기)이 역할별 페르소나 5인조로 일하는 방식**을 정리한다.
> Hermes Kanban(`hermes kanban`)을 허브로 두고, 각 페르소나가 프로필(모델)에 매핑되어 카드를 주고받는다.
> `kanban-fleet.md`(플릿 dispatch 규칙)와 함께 읽는다.

## 1. 페르소나 ↔ 프로필 매핑

| 페르소나 | 정체성 | Kanban 담당자(assignee) | 실제 Hermes 프로필 | Discord 봇 ID |
|----------|--------|--------------------------|---------------------|---------------|
| **PM** | PM / 아키텍트 (요구사항 분해·배정) | `pm` | `pm` | 1534806088762003476 |
| **Dev** | **개발 리드** (전반적 개발 구현) | `dev` | `dev` | 1513699678556782703 |
| **Infra** | **인프라 개발자** (인프라 설정/구축/배포) | `infra` | `infra` | 1535078180077965354 |
| **QA** | QA 수문장 (검수 PASS/REJECT) | `qa` | `qa` | 1513768982472032266 |
| **Ops** | 비서 / 보고 (칸반 모니터링·디스패처) | `ops` | `ops` | 1526011878281842728 |

> ⚠️ **중요**: PM·Dev·Infra·QA·Ops은 **대화 컨텍스트에서만 존재하는 페르소나**다.
> 칸반의 `assignee` 값은 프로필명(`pm`/`dev`/`infra`/`qa`/`ops`)이고,
> 페르소나 이름은 브리핑·보고용 라벨이다.

> 📌 **역할 재정의 이력 (2026-08-10)**:
> - **Dev**: 기존(인프라/API/터미널) → **개발 리드** (전반적 개발 구현 담당)
> - **Infra**: 기존(알고리즘/로직/아키) → **인프라 개발자** (인프라 설정/구축/배포)
> - 코딩 구현은 Dev가, 인프라 세팅은 Infra가, QA는 QA가, 기획은 PM이, 비서는 Ops이 담당.

## 2. 흐름 — OPS 허브 동적 라우팅

낡은 "무조건 PM 거치는 일렬"을 버리고, **Ops(비서·디스패처)가 대장님 유일 창구로서
업무 성격에 따라 경로를 고른다.** 조율은 Coral 이벤트, 상태는 Kanban, 사람 통신은 Discord.

```
대장님 (Discord #work) — 목표 제시 · 게이트 승인만
   ↓  유일 창구
[Ops/ops] 접수 → 업무 성격 판단 → 동적 라우팅 (칸반 카드 create/assign)
   ├─① 큰/복잡 업무    → [PM/pm] 기획·분해 → [Dev]+[Infra] 병렬 → [QA]
   ├─② 소규모 개발     → [Dev/dev] 직행       (PM 우회, Ops 판단)
   ├─③ 소규모 인프라   → [Infra/infra] 직행   (PM 우회, Ops 판단)
   ├─④ 검증성·소규모   → [QA/qa] 직행         (PM 우회, Ops 판단)
   └─⑤ 통지·관리       → Ops 자체 처리
        ↑ 조율은 🪸Coral 이벤트로 서로 반응
[QA/qa] 지속 검증·게이트: PASS → Done / REJECT → 담당자 In Progress 복귀
   ↓
[Ops/ops] 완료 취합 → 대장님께 보고 (게이트 승인 필요 건만 상신)
```

- **Ops**: 대장님 유일 창구. 라우팅 판단 + 카드 create/assign + 통지·관리 직접 처리.
  → 이를 위해 `ops` 프로필 toolsets에 **`kanban` 포함 필수** (dev/infra/qa에 직접 배정하려면).
- **PM**: 큰/복잡 업무만 기획·분해. 소규모는 Ops이 PM을 우회한다.
- **Dev·Infra**: 병렬 실행. Ops이 소규모 건은 PM 없이 직접 배정 가능.
- **QA**: 지속 검증·게이트. 소규모·검증성은 Ops에서 직접 수령.
- **대장님**: 목표 제시 + 게이트 승인(A)만. 실행 조율엔 개입하지 않는다.

## 3. Ops(ops) 보고 트리거

1. **① 라우팅·배정 완료 시** → 카드 ID · 담당자(pm/dev/infra/qa) · 경로 · 제목 브리핑
2. **② 작업 시작/종료 시** → 누가 무슨 카드 건드리는지 브리핑 (`hermes kanban watch`/`tail` 폴링)
3. **③ 완료 시** → Done 전환 브리핑 (게이트 승인 필요 건은 대장님께 상신)

## 4. 프로필 설정 규칙 (kanban-fleet.md 와 중복되나 요약)

| 프로필 | `dispatch_in_gateway` | `default_assignee` | 역할 |
|--------|----------------------|--------------------|------|
| `ops` | **true** (유일) | `pm` (fallback) | 유일 디스패처 · **동적 라우팅** · `kanban` 툴셋 필수 |
| `pm` | false | (미사용) | 큰/복잡 업무 분해 |
| `dev` | false | (미사용) | 실행 (Ops 직행 배정 가능) |
| `infra` | false | (미사용) | 실행 (Ops 직행 배정 가능) |
| `qa` | false | (미사용) | 검증·게이트 (Ops 직행 수령 가능) |

- 게이트웨이 여러 개 켜면 디스패처 이중 스윕 → claim 꼬임. 디스패처는 `ops` 하나만.
- `default_assignee: pm` 은 **fallback** — Ops이 라우팅에서 담당자를 명시하므로 평소엔 미사용. 미지정 카드만 pm으로.
- `auto_decompose: true` 유지 → Ops이 채팅에서 카드를 자동 분해·라우팅.
- **Ops이 dev/infra/qa에 직접 배정하려면 `ops` toolsets에 `kanban` 이 있어야 한다** (없으면 게이트웨이 자동디스패치만 되고 수동 라우팅 불가).

## 5. 호칭 규칙

- 대장님(김동기)을 **"대장님"**으로 부른다. "대표님" 사용 금지.
- 모든 페르소나(PM/Dev/Infra/QA/Ops)가 동일하게 "대장님" 호칭 사용.

## 6. 알려진 리스크 / 운영 주의

- **②단계 폴링은 Discord 세션이 살아있을 때만 작동**. 끊기면 놓침 → `kanban daemon` 또는 cron으로 빼야 24h 모니터링.
- 칸반 서버: `http://127.0.0.1:9119/kanban`. CLI는 `hermes kanban <subcommand>`.
- 프로필별 모델/프로바이더는 이 repo에 넣지 않음(시크릿·환경 의존). 새 머신에서는 `hermes setup` 또는 `.env`로 세팅.
- SSoT 문서 커밋 전 **로컬 validator 필수 실행** (`python scripts/validate_ssot.py <file>` → PASS 필요).
- Discord 채널 규칙(토론 규칙 등)은 `channel_prompts`로 프로필 config에 박힘 — `hermes/profiles/{dev,qa}/config.yaml.template` 참조.

## 7. SOUL 템플릿 적용 (역할별 페르소나를 실제 프로필에 박기)

`hermes/profiles/<name>/SOUL.md.template` 에 역할별 페르소나 정의가 들어있다.
이걸 각 프로필의 `SOUL.md`로 복사하면 대화 컨텍스트 페르소나가 실제 시스템 프롬프트로 고정된다.

| 템플릿 | 대상 프로필 | 페르소나 |
|---------|-----------|----------|
| `profiles/pm/SOUL.md.template` | `pm` | PM (PM) |
| `profiles/dev/SOUL.md.template` | `dev` | Dev (개발 리드) |
| `profiles/infra/SOUL.md.template` | `infra` | Infra (인프라) |
| `profiles/qa/SOUL.md.template` | `qa` | QA (QA) |
| `profiles/ops/SOUL.md.template` | `ops` | Ops (비서) |

적용 명령 (부트스트랩 단계에서 사용자 동의 후):

```bash
for p in pm dev infra qa ops; do
  cp "$BOOTSTRAP_REPO/hermes/profiles/$p/SOUL.md.template" "$HERMES_HOME/profiles/$p/SOUL.md"
done
```

> ⚠️ 주의: 기존 SOUL을 덮어쓰므로 적용 전 사용자에게 확인받을 것.
> 기존 SOUL을 유지하려면 템플릿을 참고용으로만 쓰고 복사하지 않는다.
