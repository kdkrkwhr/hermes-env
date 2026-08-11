#!/bin/bash
# Hermes 5인조(pm/dev/infra/qa/ops) <-> Coral(AgentRadio) 연동 — 이식 가능, 재실행 가능.
#
# 하는 일:
#   1) coral-server(:$CORAL_PORT) 안 떠 있으면 기동 (probe 레지스트리)
#   2) hermes-fleet 세션 생성(5 agents) → 각 에이전트 MCP URL 캡처
#   3) 각 Hermes 프로필 config.yaml 의 mcp_servers.coral.url 을 upsert
#
# ⚠️ 세션 secret은 서버 재시작마다 바뀜(in-memory) → 서버 재기동/재부팅 후 이 스크립트를
#    다시 돌려야 5개 프로필의 mcp_coral_* 가 되살아난다. (autostart/ 참고)
#
# 필수 env (부트스트랩 0단계 변수):
#   HERMES_HOME   Hermes 설치 경로 (profiles/<p>/config.yaml 위치)
# 선택 env:
#   CORAL_HOME    jar·jdk 위치      (기본: $HERMES_HOME/coral)
#   CORAL_JAVA    java 실행 파일    (기본: java; ⚠️ Java 24+ 필요)
#   CORAL_JAR     coral-server.jar  (기본: $CORAL_HOME/coral-server.jar)
#   CORAL_PORT    서버 포트         (기본: 5555)
#   CORAL_AUTH    auth key          (기본: test)
#
#   usage: bash setup-hermes-coral.sh [--inject pm,dev,infra,qa,ops] [--restart-gateway]
#          --inject 없으면 URL 캡처까지만(드라이런).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${HERMES_HOME:?HERMES_HOME 를 지정하세요 (예: export HERMES_HOME=~/.hermes)}"
CORAL_HOME="${CORAL_HOME:-$HERMES_HOME/coral}"
CORAL_JAVA="${CORAL_JAVA:-java}"
CORAL_JAR="${CORAL_JAR:-$CORAL_HOME/coral-server.jar}"
CORAL_PORT="${CORAL_PORT:-5555}"
CORAL_AUTH="${CORAL_AUTH:-test}"
PROBE_DIR="$SCRIPT_DIR/agents/probe"
HERMES_PROFILES="$HERMES_HOME/profiles"
export CORAL_URLS_FILE="${CORAL_URLS_FILE:-$CORAL_HOME/coral-urls.txt}"
BASE="http://localhost:$CORAL_PORT"
AUTHH="Authorization: Bearer $CORAL_AUTH"

INJECT=""; RESTART=""
while [ $# -gt 0 ]; do
  case "$1" in
    --inject) INJECT="${2:-}"; shift 2;;
    --restart-gateway) RESTART="1"; shift;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done

mkdir -p "$CORAL_HOME"

# --- 1) 서버 기동 ---
if curl -s -m3 "$BASE/api/v1/local/namespace" -H "$AUTHH" >/dev/null 2>&1; then
  echo "[1] coral-server 이미 UP ($BASE)"
else
  [ -f "$CORAL_JAR" ] || { echo "FAIL: $CORAL_JAR 없음 → 먼저 install-coral.sh 실행"; exit 1; }
  echo "[1] coral-server 기동..."
  ( cd "$PROBE_DIR" && nohup "$CORAL_JAVA" -jar "$CORAL_JAR" \
      --auth.keys="$CORAL_AUTH" --network.bind_port="$CORAL_PORT" --network.allow_any_host=true \
      --session.defaultWaitTimeout=300000 --registry.include_debug_agents=true \
      --registry.local_agents="$PROBE_DIR" > "$CORAL_HOME/coral-server.log" 2>&1 & )
  for i in $(seq 1 30); do
    curl -s -m3 "$BASE/api/v1/local/namespace" -H "$AUTHH" >/dev/null 2>&1 && { echo "    ready ($i)"; break; }
    sleep 2
  done
fi

# --- 2) 세션 생성 + URL 캡처 ---
echo "[2] hermes-fleet 세션 생성..."
rm -f "$CORAL_URLS_FILE"
AG=""
for name in pm dev infra qa ops; do
  AG="$AG{\"id\":{\"name\":\"probe\",\"version\":\"0.1.0\",\"registrySourceId\":{\"type\":\"local\"}},\"name\":\"$name\",\"provider\":{\"type\":\"local\",\"runtime\":\"executable\"},\"description\":\"$name\",\"options\":{},\"blocking\":false},"
done
AG="${AG%,}"
cat > "$CORAL_HOME/fleet.json" <<JSON
{"agentGraphRequest":{"agents":[$AG],"groups":[["pm","dev","infra","qa","ops"]]},
"namespaceProvider":{"type":"create_if_not_exists","namespaceRequest":{"name":"hermes-fleet","deleteOnLastSessionExit":false}},
"execution":{"mode":"immediate","runtimeSettings":{"ttl":86400000}}}
JSON
curl -s -m20 -X POST "$BASE/api/v1/local/session" -H "$AUTHH" -H "Content-Type: application/json" -d @"$CORAL_HOME/fleet.json"; echo
for i in $(seq 1 10); do [ "$(grep -c '|' "$CORAL_URLS_FILE" 2>/dev/null || echo 0)" -ge 5 ] && break; sleep 1; done
echo "[2] 캡처된 URL:"; cat "$CORAL_URLS_FILE"

# --- 3) 주입 ---
if [ -z "$INJECT" ]; then
  echo "[3] --inject 없음 → 주입 생략(드라이런)."
  exit 0
fi
echo "[3] 프로필 주입: $INJECT"
IFS=',' read -ra TARGETS <<< "$INJECT"
for name in "${TARGETS[@]}"; do
  url=$(grep -E "^$name\|" "$CORAL_URLS_FILE" | head -1 | cut -d'|' -f2)
  cfg="$HERMES_PROFILES/$name/config.yaml"
  [ -z "$url" ] && { echo "  ! $name: URL 없음, skip"; continue; }
  [ ! -f "$cfg" ] && { echo "  ! $name: $cfg 없음, skip"; continue; }
  [ -f "$cfg.bak.coral" ] || cp "$cfg" "$cfg.bak.coral"
  CORAL_URL="$url" CORAL_PROFILE="$name" "${CORAL_PY:-python3}" "$SCRIPT_DIR/upsert_coral_mcp.py" "$cfg" \
    && echo "  ✓ $name ← ...${url##*/mcp/v1/}"
done

# --- 4) 선택: gateway 재시작해 새 config 로드 ---
if [ -n "$RESTART" ]; then
  echo "[4] gateway 재시작..."
  hermes gateway restart 2>&1 | tail -3 || echo "  (gateway restart 실패 — 수동 재시작 필요)"
fi
echo "[done] 서버/세션 재생성 시 이 스크립트 재실행."
