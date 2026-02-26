#!/usr/bin/env bash
# Kuchiyose no Jutsu — Summoning System Hook
# Fires on SubagentStart / SubagentStop to make AI agents visible in the Dojo.
# Usage: echo '{"agent_id":"...","agent_type":"..."}' | bash kuchiyose.sh start|stop

set -euo pipefail

ACTION="${1:-}"  # "start" or "stop"
INPUT=$(cat)

# Parse fields from stdin JSON (jq if available, else python fallback)
if command -v jq &>/dev/null; then
  AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')
  AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty')
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
else
  AGENT_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_id',''))" 2>/dev/null || echo "")
  AGENT_TYPE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_type',''))" 2>/dev/null || echo "")
  SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || echo "")
fi

[ -z "$AGENT_ID" ] && exit 0

# --- Summon Roster ---
case "$AGENT_TYPE" in
  Explore)
    NAME="Gamakichi"; ANIMAL="toad"; COLOR="yellow-400"; SPECIALTY="Exploring codebase" ;;
  Plan)
    NAME="Gamabunta"; ANIMAL="toad"; COLOR="orange-400"; SPECIALTY="Designing strategy" ;;
  general-purpose)
    NAME="Manda"; ANIMAL="snake"; COLOR="purple-400"; SPECIALTY="Executing task" ;;
  claude-code-guide)
    NAME="Katsuyu"; ANIMAL="slug"; COLOR="green-400"; SPECIALTY="Consulting docs" ;;
  linux-security-auditor)
    NAME="Aoda"; ANIMAL="snake"; COLOR="red-400"; SPECIALTY="Auditing security" ;;
  *)
    NAME="Kuchiyose"; ANIMAL="scroll"; COLOR="cyan-400"; SPECIALTY="Summoned agent" ;;
esac

# Derive a roster key for the summon ID
ROSTER_KEY=$(echo "$NAME" | tr '[:upper:]' '[:lower:]')
SUMMON_ID="${ROSTER_KEY}-${AGENT_ID}"

DOJO_URL="${DOJO_URL:-http://localhost:8090}"
RASENGAN_URL="${RASENGAN_URL:-http://localhost:8050}"

if [ "$ACTION" = "start" ]; then
  EVENT_TYPE="agent.summoned"
  STATUS="active"
elif [ "$ACTION" = "stop" ]; then
  EVENT_TYPE="agent.dismissed"
  STATUS="done"
else
  exit 0
fi

# Fire-and-forget to Dojo (2s timeout, backgrounded)
curl -s -m 2 -X POST "${DOJO_URL}/api/summons/event" \
  -H 'Content-Type: application/json' \
  -d "{
    \"event_type\": \"${EVENT_TYPE}\",
    \"payload\": {
      \"summon_id\": \"${SUMMON_ID}\",
      \"name\": \"${NAME}\",
      \"animal\": \"${ANIMAL}\",
      \"color\": \"${COLOR}\",
      \"specialty\": \"${SPECIALTY}\",
      \"status\": \"${STATUS}\",
      \"agent_type\": \"${AGENT_TYPE}\",
      \"session_id\": \"${SESSION_ID}\"
    }
  }" &>/dev/null &

# Fire-and-forget to Rasengan (2s timeout, backgrounded)
curl -s -m 2 -X POST "${RASENGAN_URL}/events" \
  -H 'Content-Type: application/json' \
  -d "{
    \"event_type\": \"${EVENT_TYPE}\",
    \"source\": \"claude-code\",
    \"payload\": {
      \"summon_id\": \"${SUMMON_ID}\",
      \"name\": \"${NAME}\",
      \"animal\": \"${ANIMAL}\",
      \"agent_type\": \"${AGENT_TYPE}\",
      \"session_id\": \"${SESSION_ID}\"
    }
  }" &>/dev/null &

# Never block Claude Code
exit 0
