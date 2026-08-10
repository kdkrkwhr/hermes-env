# 쿵야 페르소나 워크플로우 (Kanban 기반 멀티에이전트)

> 이 문서는 `hermes-env` 부트스트랩 이후, **대장님(김동기)이 쿵야 페르소나 5인조로 일하는 방식**을 정리한다.
> Hermes Kanban(`hermes kanban`)을 허브로 두고, 각 페르소나가 프로필(모델)에 매핑되어 카드를 주고받는다.
> `kanban-fleet.md`(양송 플릿 dispatch 규칙)와 함께 읽는다.

## 1. 페르소나 ↔ 프로필 매핑

| 페르소나 | 정체성 | Kanban 담당자(assignee) | 실제 Hermes 프로필 | 모델 |
|----------|--------|--------------------------|---------------------|------|
| **마늘쫑쿵야** | PM / 아키텍트 (요구사항 분해) | `default` | (버섯이 대리 수행) | — |
| **양파쿵야** | **프론트엔드 + 백엔드 개발자** (실제 코딩 구현) | `default` | `default` (Cursor ACP 경유) | Cursor 구독 / ACP |
| **무시쿵야** | **인프라 개발자** (인프라 설정/구축/배포) | `claude-sonnet` | `claude-sonnet` | 무료모델(gemini/hy3) 전환 예정 |
| **샐러리쿵야** | QA 수문장 (검수 PASS/REJECT) | `claude` | `claude` | claude-1개 유지(유료) 또는 무료모델 |
| **버섯쿵야** | 비서 / 보고 (칸반 모니터링) | `nous-work` | `nous-work` | 오케(디스패처, hy3) |

> ⚠️ **중요**: 마늘쫑·양파·무시·샐러리·버섯은 **대화 컨텍스트에서만 존재하는 페르소나**다.
> 칸반의 `assignee` 값은 프로필명(`default`/`claude-sonnet`/`claude`/`nous-work`)이고,
> 페르소나 이름은 브리핑·보고용 라벨이다. config에 "마늘쫑" 같은 문자열은 없다.

> 📌 **역할 재정의 이력 (2026-08-10)**:
> - **양파쿵야**: 기존(인프라/API/터미널) → **프론트엔드+백엔드 개발자** (실제 코딩 구현 담당)
> - **무시쿵야**: 기존(알고리즘/로직/아키) → **인프라 개발자** (인프라 설정/구축/배포)
> - 코딩 구현은 양파가, 인프라 세팅은 무시가, QA는 샐러리가, 기획은 마늘쫑이, 비서는 버섯이 담당.

## 2. 흐름 (요구사항 1건 처리 기준)

```
대장님 지시 (Discord #work)
   ↓
[마늘쫑] 요구사항 분석 → 칸반 카드 분해 + 담당 배정
   (실제: 버섯=오케가 hermes kanban create/assign 로 실행)
   ↓
[무시] 인프라 개발자 — 인프라 설정/구축 (claude-sonnet 프로필, 무료모델 전환 예정)
   ↓
[양파] 프론트엔드+백엔드 개발자 — 실제 코딩 구현 (Cursor ACP 경유)
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
| `claude-sonnet` (무시=인프라) | false | (미사용) | spawn only / 무료모델 전환 예정 |
| `claude` (샐러리=QA) | false | (미사용) | spawn only / claude-1개 유지 |
| `default` (양파=개발) | false | (미사용) | spawn only / Cursor ACP 경유 |

- 게이트웨이 여러 개 켜면 디스패처 이중 스윕 → claim 꼬임. 디스패처는 `nous-work` 하나만.
- `auto_decompose: true` 유지 → 버섯이 채팅에서 카드를 자동 분해.

## 5. 호칭 규칙

- 대장님(김동기)을 **"대장님"**으로 부른다. "대표님" 사용 금지.
- 모든 페르소나(마늘쫑/양파/무시/샐러리/버섯)가 동일하게 "대장님" 호칭 사용.

## 6. 알려진 리스크 / 운영 주의

- **②단계 폴링은 Discord 세션이 살아있을 때만 작동**. 끊기면 놓침 → `kanban daemon` 또는 cron으로 빼야 24h 모니터링.
- **양파(Cursor ACP)는 Hermes 토큰을 안 씀** — Cursor 구독비 별도. Hermes에서 ACP로 툴 등록만 함. 양파가 "코딩"하면 비용은 Cursor 측에서 감.
- **무시(인프라)는 무료 모델(gemini-2.0-flash / hy3)로 전환 예정** — claude-sonnet 요금 소진(2026-08-10)으로 인해. OpenRouter(`OPENROUTER_API_KEY`) 또는 Gemini(`GEMINI_API_KEY`) 키 발급 후 `config.yaml` model 교체.
- **샐러리(QA)는 claude 1개 유지 원칙** 이나, claude 요금 소진 시 무료 모델(gemini-2.0-flash)로 QA 우회 가능. 정밀 리뷰 필요시에만 claude 사용.
- **OpenRouter는 Hermes 공식 지원** — `.env`에 `OPENROUTER_API_KEY` 세팅 + `config.yaml` 에 `provider: openrouter`, `default: openrouter/<vendor>/<model>` 형식 사용. 무료 태그는 `:free`.
- SSoT 문서 커밋 전 **로컬 validator 필수 실행** (`python scripts/validate_ssot.py <file>` → PASS 필요). spec 타입은 frontmatter(`author`/`created`/`updated`/`status`/`tags:[scope:rws]`/`summary`) 필수.
- 칸반 서버: `http://127.0.0.1:9119/kanban`. CLI는 `hermes kanban <subcommand>`.

## 7. SOUL 템플릿 적용 (쿵야 페르소나를 실제 프로필에 박기)

`hermes/profiles/<name>/SOUL.md.template` 에 쿵야 페르소나 정의가 들어있다.
이걸 각 프로필의 `SOUL.md`로 복사하면 대화 컨텍스트 페르소나가 실제 시스템 프롬프트로 고정된다.

| 템플릿 | 대상 프로필 | 페르소나 |
|---------|-----------|----------|
| `profiles/default/SOUL.md.template` | `default` | 마늘쫑 (PM) |
| `profiles/default/SOUL-yangpa.md.template` | `default` | 양파 (인프라) — 마늘쫑과 같은 프로필 공용 |
| `profiles/claude-sonnet/SOUL.md.template` | `claude-sonnet` | 무시 (로직) |
| `profiles/claude/SOUL.md.template` | `claude` | 샐러리 (QA) |
| `profiles/nous-work/SOUL.md.template` | `nous-work` | 버섯 (비서) |

적용 명령 (부트스트랩 단계에서 사용자 동의 후):

```bash
cp "$BOOTSTRAP_REPO/hermes/profiles/default/SOUL.md.template"         "$HERMES_HOME/profiles/default/SOUL.md"
cp "$BOOTSTRAP_REPO/hermes/profiles/claude-sonnet/SOUL.md.template"  "$HERMES_HOME/profiles/claude-sonnet/SOUL.md"
cp "$BOOTSTRAP_REPO/hermes/profiles/claude/SOUL.md.template"         "$HERMES_HOME/profiles/claude/SOUL.md"
cp "$BOOTSTRAP_REPO/hermes/profiles/nous-work/SOUL.md.template"      "$HERMES_HOME/profiles/nous-work/SOUL.md"
```

> ⚠️ 주의: 실제 `claude` 프로필에는 이미 "친구 말투" SOUL이 적용되어 있을 수 있음.
> 쿵야(샐러리=QA) 템플릿으로 덮어쓰면 말투가 바뀜 — 적용 전 사용자에게 확인받을 것.
> 기존 SOUL을 유지하려면 템플릿을 참고용으로만 쓰고 복사하지 않는다.
