#!/bin/bash
# Coral 런타임 설치 — coral-server.jar 및 (필요 시) JDK24+ 를 $CORAL_HOME 에 내려받는다.
# 바이너리는 repo에 넣지 않으므로(용량), 새 머신마다 이 스크립트로 확보한다.
#
# 필수 env: HERMES_HOME
# 선택 env: CORAL_HOME(기본 $HERMES_HOME/coral)
set -uo pipefail
: "${HERMES_HOME:?HERMES_HOME 를 지정하세요}"
CORAL_HOME="${CORAL_HOME:-$HERMES_HOME/coral}"
mkdir -p "$CORAL_HOME"

# coral-server.jar (AgentRadio 공식 배포 링크, ~106MB)
JAR="$CORAL_HOME/coral-server.jar"
JAR_URL="https://drive.usercontent.google.com/download?id=17b40_1kXFrAC0pnN8w_7PPY13O7pYVke&export=download&confirm=t"
if [ -f "$JAR" ] && [ "$(stat -c%s "$JAR" 2>/dev/null || stat -f%z "$JAR" 2>/dev/null || echo 0)" -gt 50000000 ]; then
  echo "coral-server.jar 이미 있음"
else
  echo "coral-server.jar 다운로드..."; curl -L -o "$JAR" "$JAR_URL"
fi

# Java 24+ 필요 (jar class file version 68). 시스템 java가 24 미만이면 안내.
JV=$(java -version 2>&1 | head -1 | grep -oE '[0-9]+' | head -1 || echo 0)
if [ "${JV:-0}" -ge 24 ]; then
  echo "시스템 java $JV OK (>=24)"
else
  echo "⚠️ 시스템 java=$JV (<24). coral-server 실행 불가."
  echo "   포터블 Temurin JDK25 를 받아 CORAL_JAVA 로 지정하세요:"
  echo "   OS별 zip/tar: https://adoptium.net/temurin/releases/?version=25"
  echo "   예) curl -L -o \"\$CORAL_HOME/jdk.zip\" \\"
  echo "        'https://api.adoptium.net/v3/binary/latest/25/ga/<os>/<arch>/jdk/hotspot/normal/eclipse?project=jdk'"
  echo "   압축 해제 후: export CORAL_JAVA=\"\$CORAL_HOME/<jdk>/bin/java\""
fi
echo "[done] jar=$JAR"
