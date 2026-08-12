#!/bin/bash
# Coral이 각 에이전트 인스턴스마다 실행. 자기 MCP URL($CORAL_CONNECTION_URL)을
# 캡처 후 무기한 idle(세션 유지). 짧은 sleep은 세션 조기 소멸 → while 루프로 durable.
echo "$CORAL_AGENT_ID|$CORAL_CONNECTION_URL" >> "${CORAL_URLS_FILE:-/tmp/coral-urls.txt}"
while true; do sleep 86400; done
