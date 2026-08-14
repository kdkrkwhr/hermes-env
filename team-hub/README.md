# team-hub — 5인조 멀티에이전트 팀 허브 (정적 사이트)

`hermes-env` 부트스트랩으로 세팅되는 5인조 플릿(PM/Dev/Infra/QA/Ops)을
한눈에 보여주는 정적 사이트. 빌드 단계 없음 — `index.html`을 열면 끝.

## 보는 법

- 로컬: `python3 -m http.server` 후 `http://127.0.0.1:8000/`
- GitHub Pages: 이 디렉토리를 Pages 소스로 지정 (`.nojekyll` 불필요)

## 구조

```
team-hub/
├── index.html   # 단일 페이지 셸 + 네비
├── styles.css   # 다크 테마 (slate-950 기반)
└── app.js       # 역할 데이터 + 뷰 렌더링 (vanilla JS, 의존성 0)
```

## 데이터 정본

역할별 매핑(PM↔pm, Dev↔dev, Infra↔infra, QA↔qa, Ops↔ops)과 Discord ID는
`../docs/workflow-cungya.md` §1을 단일 진실원으로 삼는다. 수정 시 양쪽을 맞춘다.

## 심화 문서

- `../docs/conventions.md` — 디렉토리 분리·산출물 규칙
- `../docs/kanban-fleet.md` — 5인조 멀티에이전트 dispatch / assignee
- `../docs/workflow-cungya.md` — 역할별 페르소나 5인조 워크플로우
- `../docs/agentradio-coral.md` — 실시간 peer 사이드채널 연동
