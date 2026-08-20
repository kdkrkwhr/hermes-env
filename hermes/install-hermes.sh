#!/usr/bin/env bash
# Hermes Agent CLI 설치. 이미 있으면 건너뛴다.
# 모델/프로바이더 마법사는 생략 — 사용자는 나중에 `hermes setup`.
#
# 필수 env: HERMES_HOME (0단계에서 받은 값)
# Windows(git-bash)는 공식 설치기가 PowerShell이므로 install-hermes.ps1 로 위임한다.
#
# 사용:
#   HERMES_HOME="$HOME/.hermes" bash hermes/install-hermes.sh
set -euo pipefail
: "${HERMES_HOME:?HERMES_HOME 를 지정하세요}"

if command -v hermes >/dev/null 2>&1; then
  echo "hermes 이미 설치됨 — 건너뜀"
  hermes --version || true
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UNAME_S="$(uname -s 2>/dev/null || echo unknown)"

case "$UNAME_S" in
  MINGW*|MSYS*|CYGWIN*)
    echo "Windows 감지 — PowerShell 설치기로 위임"
    if command -v cygpath >/dev/null 2>&1; then
      PS1="$(cygpath -w "$SCRIPT_DIR/install-hermes.ps1")"
      HOME_WIN="$(cygpath -w "$HERMES_HOME")"
    else
      PS1="$SCRIPT_DIR/install-hermes.ps1"
      HOME_WIN="$HERMES_HOME"
    fi
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1" -HermesHome "$HOME_WIN"
    ;;
  *)
    echo "Hermes CLI 설치 중 (HERMES_HOME=$HERMES_HOME, setup 마법사 생략)"
    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- \
      --skip-setup --non-interactive --hermes-home "$HERMES_HOME"
    ;;
esac

# 설치기가 User PATH만 갱신하면 현재 셸에는 안 잡힐 수 있다.
if ! command -v hermes >/dev/null 2>&1; then
  export PATH="$HERMES_HOME/hermes-agent/bin:$HOME/.local/bin:$PATH"
fi

if command -v hermes >/dev/null 2>&1; then
  echo "[OK] Hermes CLI 설치 완료"
  hermes --version || true
else
  echo "FAIL: hermes 가 PATH에 없습니다. 터미널을 다시 연 뒤 hermes --version 으로 확인하세요."
  exit 1
fi
