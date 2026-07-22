# 컨벤션 — 이 구조를 유지하기 위한 규칙

## 디렉토리 분리

| 경로 | 용도 | Git |
|------|------|-----|
| `$PROJECT_ROOT/<repo>` | 제품 코드 | 각자 독립 레포 |
| `$E2E_ROOT/ssot` | 스펙/DDL/ADR (SSoT) | 별도 레포 1개 |
| `$E2E_ROOT/reports` | 에이전트 산출물 | 선택 |
| `$E2E_ROOT/.env.local` | 시크릿 | ❌ 절대 금지 |

## 규칙

1. **하드코딩 경로 금지** — 항상 `$PROJECT_ROOT` / `$E2E_ROOT` / `$HERMES_HOME`
2. **에이전트 리포트는 프로젝트 레포에 넣지 않음** → `$E2E_ROOT/reports`
3. **스펙 문서는 SSoT 레포에만** — 프로젝트에 사본 두지 않음
4. **시크릿은 .env.local 하나** — 새 머신에서는 수동 입력
5. **에이전트 완료 = complete + 결과 보고** (block/리뷰요청 금지)
6. **custom_providers는 list-of-dicts** — dict 형식으로 쓰면 config 날아감
