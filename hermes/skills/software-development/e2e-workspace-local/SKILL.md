---
name: e2e-workspace
description: "Cross-platform dev workspace: e2e layout, Hermes HERMES_HOME, ai-harness skill sync, Windows↔Mac bootstrap. Use when setting up, migrating, or replicating the develop/e2e tree."
version: 1.1.0
---

# E2E Workspace (nous-work local copy)

> ⚠️ Patched from shared skill. The shared copy in `skills.external_dirs` is read-only; this local copy carries nous-work-specific updates.

## Local additions (2026-07-14)

### `.env.local` 병합 패턴
- `$E2E_ROOT\.env.local` → Hermes `.env`에 `cat`으로 병합
- `hermes config env-path`로 프로필별 `.env` 경로 확인
- ⚠️ 보안: `.env` 값은 세션에서 모델에 접근 가능 — 게이트웨이 시작 시 source 방식이 더 안전

### AGENTS.md 통합
- `$E2E_ROOT\AGENTS.md` = single source of truth
- `$E2E_ROOT\index.md` → "→ AGENTS.md 참조"로 축소
- AGENTS.md: 디렉토리 맵 + Hermes 프로필 + 양송 워크플로우 + Key rules + Scripts(하단)
- 마이그레이션 이력은 git log에 위임, AGENTS.md에는 넣지 않음

### Kanban review convention (2026-07-14)
- `blocked` 상태 = review-required. 양파쿵야가 작업 완료 후 검토 요청 시 `kanban_block()` 호출
- `hermes kanban runs <id>`로 block 사유 확인 (예: "review-required: ... PRIOR/LOOK")
