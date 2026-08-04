# Kanban 플릿 설정 (양송)

출처: `hermes-kanban-fleet`에서 훔친 최소 설정. 프로필 이름 갈아엎지 말고 **dispatch / default_assignee만** 맞춘다.

## 역할

| 프로필 | 역할 | `dispatch_in_gateway` | `default_assignee` |
|--------|------|------------------------|--------------------|
| `nous-work` | 오케(버섯) | **true** (유일) | **`default`** |
| `default` | 워커(양파) | **false** | (미사용) |
| `claude` | 워커(선택) | **false** | (미사용) |

## 왜

- 게이트웨이 여러 개 켤 때 디스패처가 **이중 스윕**하면 claim/꼬임 난다.
- `default_assignee: ""`면 분해기가 이상한 assignee를 찍고 카드가 `ready`에 영원히 남을 수 있다.

## 적용

템플릿:

- `hermes/config.yaml.template` → `$HERMES_HOME/config.yaml` (default 워커)
- `hermes/profiles/nous-work/config.yaml.template` → `$HERMES_HOME/profiles/nous-work/config.yaml`의 `kanban:` 블록
- `hermes/profiles/claude/config.yaml.template` → `$HERMES_HOME/profiles/claude/config.yaml`의 `kanban:` 블록

기존 config가 있으면 **`kanban:` 키만** 머지. 모델·시크릿·다른 섹션은 건드리지 말 것.

변경 후 해당 프로필 **gateway 재시작**.

## 선택

- `auto_decompose: false` — 오케가 채팅에서만 쪼개고 싶을 때 (플릿 원본). 양송 기본은 `true` 유지해도 됨.
- 하드 코딩 → `claude`, 나머지 → `default` 라우팅은 SOUL/`yangsong-workflow`에 한 줄로.

## 안 가져오는 것

- 프로필 rename (`orchestrator`/`generalist`/`coder`)
- fleet `install.ps1` 통설치
