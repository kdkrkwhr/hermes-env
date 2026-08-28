#!/usr/bin/env bash
# hermes-env bootstrap — AGENT_BOOTSTRAP.md 의 1~7단계를 결정론적으로 실행.
#
# 무료/약한 모델에서도 안 깨지도록 절차·검증을 코드로 못 박는다.
# 에이전트의 역할은 "경로 3개 넘기고 이 스크립트 실행 → 출력 보고"로 축소된다.
# 판단이 필요한 부분(스킬 레거시 경로, SSoT URL, 시크릿 값, SOUL/coral)만 사람/모델 몫.
#
# 사용:
#   bash bootstrap.sh --project-root ~/develop/project --e2e-root ~/develop/e2e
#   bash bootstrap.sh --check          # doctor: 현재 상태만 검증 후 표 출력
#
# 멱등(idempotent): 여러 번 돌려도 기존 config/secret 을 덮어쓰지 않는다.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

PROJECT_ROOT=""
E2E_ROOT=""
HERMES_HOME=""
SSOT_URL=""
WITH_SOULS=0     # SOUL.md 덮어쓰기(동의) 필요 → opt-in
WITH_CORAL=0     # AgentRadio/Coral 실시간 peer(선택, Java24+/pip mcp 필요)
CHECK=0

usage() {
  cat <<'EOF'
사용: bash bootstrap.sh [옵션]
  --project-root PATH   프로젝트 코드 루트 (필수, 없으면 대화형 질문)
  --e2e-root PATH       ssot/reports 등 E2E 루트 (필수, 없으면 대화형 질문)
  --hermes-home PATH    Hermes 홈 (기본: $HOME/.hermes)
  --ssot-url URL        SSoT 레포 URL (있으면 ssot/ 가 비었을 때만 clone)
  --with-souls          역할별 SOUL.md 배치 (기존 SOUL 덮어씀 — 동의 의미)
  --with-coral          Coral 실시간 peer 연동 설치/셋업 (선택)
  --check               검증만 수행(doctor). 아무것도 설치/복사하지 않음
  -h, --help            도움말
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project-root) PROJECT_ROOT="${2:-}"; shift 2;;
    --e2e-root)     E2E_ROOT="${2:-}"; shift 2;;
    --hermes-home)  HERMES_HOME="${2:-}"; shift 2;;
    --ssot-url)     SSOT_URL="${2:-}"; shift 2;;
    --with-souls)   WITH_SOULS=1; shift;;
    --with-coral)   WITH_CORAL=1; shift;;
    --check)        CHECK=1; shift;;
    -h|--help)      usage; exit 0;;
    *) echo "알 수 없는 인자: $1"; usage; exit 2;;
  esac
done

: "${HERMES_HOME:=$HOME/.hermes}"

# ---- 0단계: 경로 확정 (비어있으면 대화형 질문 — 코드로 강제) ----
resolve_paths() {
  if [ -z "$PROJECT_ROOT" ]; then
    if [ -t 0 ]; then read -r -p "작업 루트 PROJECT_ROOT (예: $HOME/develop/project): " PROJECT_ROOT
    else echo "FAIL: --project-root 미지정 (비대화형). 플래그로 넘기세요"; exit 2; fi
  fi
  if [ -z "$E2E_ROOT" ]; then
    if [ -t 0 ]; then read -r -p "E2E 루트 E2E_ROOT (예: $HOME/develop/e2e): " E2E_ROOT
    else echo "FAIL: --e2e-root 미지정 (비대화형). 플래그로 넘기세요"; exit 2; fi
  fi
  [ -n "$PROJECT_ROOT" ] || { echo "FAIL: PROJECT_ROOT 필요"; exit 2; }
  [ -n "$E2E_ROOT" ]     || { echo "FAIL: E2E_ROOT 필요"; exit 2; }
}

# 복사된 파일의 플레이스홀더를 실제 경로로 치환 (GNU/BSD sed 양쪽 안전)
subst() {
  local f="$1" t
  t="$(mktemp)"
  sed -e "s|__E2E_ROOT__|$E2E_ROOT|g" \
      -e "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" \
      -e "s|__HERMES_HOME__|$HERMES_HOME|g" \
      "$f" > "$t" && mv "$t" "$f"
}

# Windows(git-bash) 한정: 경로 표기 사고(/d/ 를 d/ 로 써서 엉뚱한 폴더 검색) 방지 힌트를
# config 의 environment_hint 에 주입한다. mac/Linux 에선 아무것도 안 함.
is_windows() { case "$(uname -s 2>/dev/null)" in MINGW*|MSYS*|CYGWIN*) return 0;; *) return 1;; esac; }
ENV_HINT="Windows/git-bash 환경. 파일 경로는 항상 POSIX 절대경로 /d/... (맨 앞 슬래시 필수, 드라이브 소문자). 슬래시 없는 d/... 상대경로 및 드라이브 백슬래시 표기 금지. 경로 변환은 cygpath -u / cygpath -w 사용."
set_env_hint() { # $1 config 파일 — environment_hint 가 비어있을 때만 채움
  is_windows || return 0
  grep -q "environment_hint: ''" "$1" 2>/dev/null || return 0
  local t; t="$(mktemp)"
  sed "s|environment_hint: ''|environment_hint: '$ENV_HINT'|" "$1" > "$t" && mv "$t" "$1"
}

# ---- 7단계 / --check: 현재 상태 검증 표 (환각 방지: 실제 파일시스템만 본다) ----
doctor() {
  local fail=0
  chk() { # $1 라벨  $2 조건식
    if eval "$2" >/dev/null 2>&1; then printf '  [OK]   %s\n' "$1"
    else printf '  [FAIL] %s\n' "$1"; fail=$((fail+1)); fi
  }
  echo "=== hermes-env 검증 (PROJECT_ROOT=$PROJECT_ROOT E2E_ROOT=$E2E_ROOT HERMES_HOME=$HERMES_HOME) ==="
  chk "PROJECT_ROOT 존재"              "test -d '$PROJECT_ROOT'"
  chk "E2E reports 디렉토리"           "test -d '$E2E_ROOT/reports'"
  chk "hermes CLI (hermes --version)"  "command -v hermes"
  chk "config.yaml 배치"               "test -f '$HERMES_HOME/config.yaml'"
  chk "config 플레이스홀더 잔존 없음"  "! grep -q '__E2E_ROOT__\\|__PROJECT_ROOT__\\|__HERMES_HOME__' '$HERMES_HOME/config.yaml'"
  chk "스킬 배치 (E2E hermes/skills)"  "test -n \"\$(ls -A '$E2E_ROOT/hermes/skills' 2>/dev/null)\""
  chk ".env.local 생성"                "test -f '$E2E_ROOT/.env.local'"
  local p
  for p in pm dev infra qa ops; do
    chk "profiles/$p/config.yaml"      "test -f '$HERMES_HOME/profiles/$p/config.yaml'"
  done
  if [ "$fail" -gt 0 ]; then echo "결과: FAIL ($fail개 미충족) — '완료' 아님"; return 1; fi
  echo "결과: OK (전부 통과)"; return 0
}

# 스킬 안 레거시 절대경로 스캔 (자동수정 X — 판단은 사람 몫, 목록만 보고)
scan_legacy_paths() {
  local hits
  hits="$(grep -rIl 'D:\\\\develop\|/Users/[a-z]*/develop' "$E2E_ROOT/hermes/skills" 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    echo "주의: 스킬에 레거시 절대경로가 박힌 파일이 있습니다 (수동 확인 권장):"
    echo "$hits" | sed 's/^/  - /'
  fi
}

resolve_paths

if [ "$CHECK" = 1 ]; then
  doctor; exit $?
fi

echo "== 1단계: 선행 조건 =="
command -v git    >/dev/null 2>&1 || { echo "FAIL: git 설치 필요"; exit 1; }
command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || { echo "FAIL: python3 설치 필요"; exit 1; }
echo "  [OK] git / python"

echo "== 1-1단계: Hermes CLI (없으면 설치) =="
HERMES_HOME="$HERMES_HOME" bash "$SCRIPT_DIR/hermes/install-hermes.sh"

echo "== 2단계: 디렉토리 구조 =="
mkdir -p "$PROJECT_ROOT" \
         "$E2E_ROOT/ssot" "$E2E_ROOT/reports" "$E2E_ROOT/hermes/skills" \
         "$HERMES_HOME/profiles"
echo "  [OK] 디렉토리 생성"

echo "== 3단계: Hermes config 배치 =="
if [ -f "$HERMES_HOME/config.yaml" ]; then
  echo "  [SKIP] config.yaml 이미 존재 — 덮어쓰지 않음"
else
  cp "$SCRIPT_DIR/hermes/config.yaml.template" "$HERMES_HOME/config.yaml"
  subst "$HERMES_HOME/config.yaml"
  set_env_hint "$HERMES_HOME/config.yaml"
  echo "  [OK] config.yaml 배치 + 경로 치환"
fi
for p in pm dev infra qa ops; do
  mkdir -p "$HERMES_HOME/profiles/$p"
  if [ -f "$HERMES_HOME/profiles/$p/config.yaml" ]; then
    echo "  [SKIP] profiles/$p/config.yaml 존재"
  else
    cp "$SCRIPT_DIR/hermes/profiles/$p/config.yaml.template" "$HERMES_HOME/profiles/$p/config.yaml"
    subst "$HERMES_HOME/profiles/$p/config.yaml"
    set_env_hint "$HERMES_HOME/profiles/$p/config.yaml"
    echo "  [OK] profiles/$p/config.yaml"
  fi
  if [ "$WITH_SOULS" = 1 ]; then
    cp "$SCRIPT_DIR/hermes/profiles/$p/SOUL.md.template" "$HERMES_HOME/profiles/$p/SOUL.md"
    subst "$HERMES_HOME/profiles/$p/SOUL.md"
    echo "  [OK] profiles/$p/SOUL.md (덮어씀)"
  fi
done

echo "== 4단계: 스킬 배치 (config 가 읽는 위치 = \$E2E_ROOT/hermes/skills) =="
cp -r "$SCRIPT_DIR/hermes/skills/." "$E2E_ROOT/hermes/skills/"
echo "  [OK] 스킬 복사 → $E2E_ROOT/hermes/skills"
scan_legacy_paths

echo "== 5단계: 시크릿 파일 =="
if [ -f "$E2E_ROOT/.env.local" ]; then
  echo "  [SKIP] .env.local 존재 — 시크릿 보존"
else
  cp "$SCRIPT_DIR/.env.example" "$E2E_ROOT/.env.local"
  echo "  [OK] .env.local 생성 — 실제 토큰 값은 사용자가 채워야 함"
fi

if [ "$WITH_CORAL" = 1 ]; then
  echo "== 3-2단계: Coral 실시간 peer 연동 =="
  bash "$SCRIPT_DIR/hermes/coral/install-coral.sh"
  cp -r "$SCRIPT_DIR/hermes/coral" "$HERMES_HOME/coral"
  bash "$HERMES_HOME/coral/setup-hermes-coral.sh" --inject pm,dev,infra,qa,ops --restart-gateway
fi

if [ -n "$SSOT_URL" ]; then
  echo "== 6단계: SSoT clone =="
  if [ -z "$(ls -A "$E2E_ROOT/ssot" 2>/dev/null)" ]; then
    git clone "$SSOT_URL" "$E2E_ROOT/ssot"
    echo "  [OK] SSoT clone"
  else
    echo "  [SKIP] ssot/ 비어있지 않음"
  fi
fi

echo
doctor || { echo "일부 항목 미완료 — 위 [FAIL] 확인 후 재실행하세요."; exit 1; }
echo
echo "다음(사람/모델 몫): (1) .env.local 토큰 채우기  (2) 위 레거시 경로 경고 있으면 검토"
echo "  (3) SSoT URL 있으면 --ssot-url 로 재실행  (4) SOUL/coral 필요 시 --with-souls/--with-coral"
