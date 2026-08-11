#!/bin/bash
# Coral이 각 에이전트 인스턴스마다 실행. 자기 MCP URL($CORAL_CONNECTION_URL)을
# 캡처 파일에 남기고 idle. Hermes가 그 URL로 붙어 실제 대화를 담당한다.
echo "$CORAL_AGENT_ID|$CORAL_CONNECTION_URL" >> "${CORAL_URLS_FILE:-/tmp/coral-urls.txt}"
sleep 86400
