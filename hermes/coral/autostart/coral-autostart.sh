#!/bin/bash
# [macOS/Linux] 로그온/부팅 자동복구. cron(@reboot) 또는 launchd/systemd 에 등록.
#   export HERMES_HOME=~/.hermes  (또는 실제 경로)
#   crontab:  @reboot HERMES_HOME=$HOME/.hermes bash $HERMES_HOME/coral/autostart/coral-autostart.sh
set -uo pipefail
: "${HERMES_HOME:?HERMES_HOME 를 지정하세요}"
bash "$HERMES_HOME/coral/setup-hermes-coral.sh" --inject pm,dev,infra,qa,ops
hermes gateway restart 2>&1 | tail -3 || true
