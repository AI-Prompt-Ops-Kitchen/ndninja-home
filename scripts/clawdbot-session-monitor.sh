#!/usr/bin/env bash
# clawdbot-session-monitor.sh — Monitor session JSONL files and prevent context overflow
# Cron: */30 * * * * /home/ndninja/scripts/clawdbot-session-monitor.sh
#
# Tiers:
#   >5MB  — Warning (log only)
#   >10MB — Attempt compaction via SIGUSR1 restart
#   >25MB — Emergency: archive file and restart

SESSION_DIR="/home/ndninja/.clawdbot/agents/main/sessions"
ARCHIVE_DIR="${SESSION_DIR}/archive"
LOG_FILE="/home/ndninja/.logs/clawdbot-session-monitor.log"
SERVICE_NAME="clawdbot-gateway.service"

WARN_BYTES=$((5 * 1024 * 1024))       # 5MB
COMPACT_BYTES=$((10 * 1024 * 1024))    # 10MB
EMERGENCY_BYTES=$((25 * 1024 * 1024))  # 25MB

log() {
    echo "[$(TZ='America/Chicago' date '+%Y-%m-%d %H:%M:%S %Z')] $1" >> "$LOG_FILE"
}

mkdir -p "$ARCHIVE_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Find all session JSONL files (skip archive directory)
shopt -s nullglob
SESSION_FILES=("${SESSION_DIR}"/*.jsonl)
shopt -u nullglob

if [ ${#SESSION_FILES[@]} -eq 0 ]; then
    exit 0
fi

ACTION_TAKEN=""

for FILE in "${SESSION_FILES[@]}"; do
    FILENAME=$(basename "$FILE")
    SIZE=$(stat -c%s "$FILE" 2>/dev/null || echo 0)
    SIZE_MB=$(awk "BEGIN {printf \"%.1f\", ${SIZE}/1024/1024}")

    if [ "$SIZE" -ge "$EMERGENCY_BYTES" ]; then
        log "EMERGENCY: ${FILENAME} is ${SIZE_MB}MB (>${EMERGENCY_BYTES}B). Archiving."
        ARCHIVE_NAME="${FILENAME%.jsonl}_$(date +%Y%m%d_%H%M%S).jsonl"
        mv "$FILE" "${ARCHIVE_DIR}/${ARCHIVE_NAME}"
        log "EMERGENCY: Archived to ${ARCHIVE_DIR}/${ARCHIVE_NAME}"
        ACTION_TAKEN="emergency"

    elif [ "$SIZE" -ge "$COMPACT_BYTES" ]; then
        log "COMPACT: ${FILENAME} is ${SIZE_MB}MB (>${COMPACT_BYTES}B). Triggering restart for compaction."
        ACTION_TAKEN="compact"

    elif [ "$SIZE" -ge "$WARN_BYTES" ]; then
        log "WARNING: ${FILENAME} is ${SIZE_MB}MB — approaching compaction threshold."
    fi
done

# If any action was taken, restart the service
if [ "$ACTION_TAKEN" = "emergency" ] || [ "$ACTION_TAKEN" = "compact" ]; then
    # Try SIGUSR1 first (hot restart), fall back to systemctl
    GATEWAY_PID=$(pgrep -f "clawdbot.*gateway" | head -1)
    if [ -n "$GATEWAY_PID" ]; then
        kill -USR1 "$GATEWAY_PID" 2>/dev/null
        log "Sent SIGUSR1 to gateway PID ${GATEWAY_PID}"
    else
        systemctl --user restart "$SERVICE_NAME" 2>/dev/null
        log "Restarted ${SERVICE_NAME} via systemctl"
    fi
fi
