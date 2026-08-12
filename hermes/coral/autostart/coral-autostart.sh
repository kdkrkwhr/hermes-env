#!/bin/bash
# [macOS/Linux] 로그온/부팅 자동복구. cron(@reboot) 또는 launchd/systemd 에 등록.
#   export HERMES_HOME=~/.hermes  (또는 실제 경로)
#   crontab:  @reboot HERMES_HOME=$HOME/.hermes bash $HERMES_HOME/coral/autostart/coral-autostart.sh
set -uo pipefail
: "${HERMES_HOME:?HERMES_HOME 를 지정하세요}"
bash "$HERMES_HOME/coral/setup-hermes-coral.sh" --inject pm,dev,infra,qa,ops
hermes gateway restart 2>&1 | tail -3 || true
# Coral -> Discord 실시간 미러 브리지 (10초 폴링). BRIDGE_CHANNEL 로 채널 변경 가능.
CORAL_HOME="$HERMES_HOME/coral" nohup python3 -u "$HERMES_HOME/coral/coral-discord-bridge.py" --loop 10 \
  > "$HERMES_HOME/coral/coral-bridge.log" 2>&1 &
echo "[autostart] coral-discord-bridge 시작"
# Coral 자동응답 데몬 (12초 폴링): idle 에이전트가 coral 멘션에 자율 응답. AUTORESP_ENABLED=0 이면 감지만(드라이런).
CORAL_HOME="$HERMES_HOME/coral" nohup python3 -u "$HERMES_HOME/coral/coral-autoresponder.py" --loop 12 \
  > "$HERMES_HOME/coral/coral-autoresp.log" 2>&1 &
echo "[autostart] coral-autoresponder 시작"
