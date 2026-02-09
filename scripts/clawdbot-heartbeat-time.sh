#!/usr/bin/env bash
# clawdbot-heartbeat-time.sh — Inject current CST date/time into HEARTBEAT.md
# Cron: * * * * * /home/ndninja/scripts/clawdbot-heartbeat-time.sh

HEARTBEAT_FILE="/home/ndninja/clawd/HEARTBEAT.md"

CURRENT_TIME=$(TZ="America/Chicago" date '+%A, %B %-d, %Y at %I:%M %p %Z')

cat > "$HEARTBEAT_FILE" <<EOF
Current date and time: ${CURRENT_TIME}
EOF
