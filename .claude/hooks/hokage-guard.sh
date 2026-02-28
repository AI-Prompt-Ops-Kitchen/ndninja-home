#!/usr/bin/env bash
# ============================================================================
# Hokage — PreToolUse Guard Hook
# Pattern-matches Bash commands against BLOCK/WARN trigger patterns.
# This is the enforcement layer — the critical piece.
#
# Input (stdin): {"tool_name":"Bash","tool_input":{"command":"..."}}
# Output: {"decision":"block","reason":"..."} or {"decision":"allow"} or empty
# ============================================================================

set -euo pipefail

EDICTS_FILE="/home/ndninja/.claude/hokage/edicts.yaml"
LOG_FILE="/home/ndninja/.logs/hokage.log"

mkdir -p "$(dirname "$LOG_FILE")"

# Read input from stdin
INPUT=$(cat)

# If edicts file doesn't exist, allow everything
if [ ! -f "$EDICTS_FILE" ]; then
  echo '{}'
  exit 0
fi

# Extract command from tool_input — timeout 100ms
RESULT=$(timeout 0.1s python3 -c "
import json, sys, re, yaml

try:
    input_data = json.loads(sys.argv[1])

    # Only guard Bash tool calls
    tool_name = input_data.get('tool_name', '')
    if tool_name != 'Bash':
        print('{}')
        sys.exit(0)

    command = input_data.get('tool_input', {}).get('command', '')
    if not command:
        print('{}')
        sys.exit(0)

    # Load edicts
    with open('$EDICTS_FILE') as f:
        data = yaml.safe_load(f)

    edicts = data.get('edicts', [])
    cmd_lower = command.lower()

    for edict in edicts:
        patterns = edict.get('trigger_patterns', [])
        if not patterns:
            continue

        severity = edict.get('severity', 'PREFER')
        if severity not in ('BLOCK', 'WARN'):
            continue

        for pattern in patterns:
            try:
                if re.search(pattern, cmd_lower):
                    edict_id = edict.get('id', 'unknown')
                    rule = edict.get('rule', '')
                    rationale = edict.get('rationale', '')

                    if severity == 'BLOCK':
                        result = {
                            'decision': 'block',
                            'reason': f'[HOKAGE {edict_id}] {rule}. {rationale}'
                        }
                    else:  # WARN
                        result = {
                            'decision': 'ask',
                            'message': f'[HOKAGE {edict_id}] {rule}. {rationale}'
                        }

                    print(json.dumps(result))

                    # Log the enforcement
                    import datetime
                    with open('$LOG_FILE', 'a') as f:
                        f.write(f'{datetime.datetime.now().isoformat()} {severity} {edict_id}: matched \"{pattern}\" in: {command[:100]}\\n')

                    sys.exit(0)
            except re.error:
                continue

    # No match — allow
    print('{}')

except Exception as e:
    import traceback
    with open('$LOG_FILE', 'a') as f:
        f.write(f'hokage-guard error: {e}\\n')
        f.write(traceback.format_exc())
    # Never block Claude if Hokage breaks
    print('{}')
" "$INPUT" 2>>"$LOG_FILE") || RESULT='{}'

echo "$RESULT"

# If we blocked something, fire Rasengan event (backgrounded)
if echo "$RESULT" | grep -q '"block"' 2>/dev/null; then
  (python3 -c "
import httpx, json, sys
try:
    result = json.loads(sys.argv[1])
    input_data = json.loads(sys.argv[2])
    cmd = input_data.get('tool_input', {}).get('command', '')[:200]
    httpx.post('http://localhost:8050/events', json={
        'event_type': 'hokage.blocked',
        'source': 'hokage',
        'payload': {
            'reason': result.get('reason', ''),
            'command_preview': cmd
        }
    }, timeout=2.0)
except: pass
" "$RESULT" "$INPUT" &>/dev/null &)
fi

exit 0
