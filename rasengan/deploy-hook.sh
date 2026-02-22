#!/usr/bin/env bash
# Rasengan deploy wrapper — wraps any deploy script with event tracking
# Usage: rasengan-deploy <service> <script> [args...]
# Emits: deploy.started, deploy.completed or deploy.failed

set -euo pipefail

RASENGAN_URL="${RASENGAN_URL:-http://127.0.0.1:8050}"

if [ $# -lt 2 ]; then
  echo "Usage: rasengan-deploy <service> <script> [args...]"
  echo "Example: rasengan-deploy sage_mode /home/ndninja/sage_mode/swarm-deploy.sh"
  exit 1
fi

SERVICE="$1"
SCRIPT="$2"
shift 2

_emit() {
  local event_type="$1"
  local payload="$2"
  curl -s -X POST "${RASENGAN_URL}/events" \
    -H "Content-Type: application/json" \
    -d "{\"event_type\": \"${event_type}\", \"source\": \"deploy-hook\", \"payload\": ${payload}}" \
    --connect-timeout 2 --max-time 5 \
    >/dev/null 2>&1 || true
}

START_TS=$(date +%s)

# Emit deploy.started (sync — we want this recorded before running)
_emit "deploy.started" "{\"service\": \"${SERVICE}\", \"script\": \"${SCRIPT}\"}"

echo "[rasengan-deploy] Starting deploy: ${SERVICE}"
echo "[rasengan-deploy] Script: ${SCRIPT} $*"

# Run the actual deploy script, capture exit code
set +e
"$SCRIPT" "$@"
EXIT_CODE=$?
set -e

END_TS=$(date +%s)
DURATION=$((END_TS - START_TS))

if [ $EXIT_CODE -eq 0 ]; then
  _emit "deploy.completed" "{\"service\": \"${SERVICE}\", \"script\": \"${SCRIPT}\", \"duration_seconds\": ${DURATION}, \"exit_code\": 0}"
  echo "[rasengan-deploy] Deploy completed (${DURATION}s)"
else
  _emit "deploy.failed" "{\"service\": \"${SERVICE}\", \"script\": \"${SCRIPT}\", \"duration_seconds\": ${DURATION}, \"exit_code\": ${EXIT_CODE}}"
  echo "[rasengan-deploy] Deploy FAILED with exit code ${EXIT_CODE} (${DURATION}s)" >&2
fi

exit $EXIT_CODE
