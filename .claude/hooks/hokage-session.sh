#!/usr/bin/env bash
# ============================================================================
# Hokage — SessionStart Hook
# Loads ALL edicts from edicts.yaml and injects them as additionalContext
# so Claude sees the full ruleset on every session boot.
#
# This is the wisdom layer — ensures no edict is forgotten between sessions.
# ============================================================================

set -euo pipefail

EDICTS_FILE="/home/ndninja/.claude/hokage/edicts.yaml"
LOG_FILE="/home/ndninja/.logs/hokage.log"

mkdir -p "$(dirname "$LOG_FILE")"

# If edicts file doesn't exist, pass through silently
if [ ! -f "$EDICTS_FILE" ]; then
  echo '{}'
  exit 0
fi

# Parse edicts and format as context injection
# Timeout protection: 300ms max (YAML parsing can be slow)
CONTEXT=$(timeout 0.3s python3 -c "
import yaml, json, sys

try:
    with open('$EDICTS_FILE') as f:
        data = yaml.safe_load(f)

    edicts = data.get('edicts', [])
    if not edicts:
        print('{}')
        sys.exit(0)

    # Group by domain
    domains = {}
    counts = {'BLOCK': 0, 'WARN': 0, 'PREFER': 0}
    for e in edicts:
        d = e.get('domain', 'unknown')
        domains.setdefault(d, []).append(e)
        sev = e.get('severity', 'PREFER')
        counts[sev] = counts.get(sev, 0) + 1

    # Build compact context string
    lines = []
    lines.append('=== HOKAGE EDICTS ({} rules: {} BLOCK, {} WARN, {} PREFER) ==='.format(
        len(edicts), counts['BLOCK'], counts['WARN'], counts['PREFER']))
    lines.append('')

    for domain, rules in sorted(domains.items()):
        lines.append(f'[{domain.upper()}]')
        for r in rules:
            sev = r.get('severity', 'PREFER')
            marker = '🚫' if sev == 'BLOCK' else ('⚠️' if sev == 'WARN' else '→')
            lines.append(f'  {marker} {r[\"id\"]}: {r[\"rule\"]}')
        lines.append('')

    lines.append('=== END HOKAGE EDICTS ===')

    result = {
        'additionalContext': '\n'.join(lines)
    }
    print(json.dumps(result))

except Exception as e:
    with open('$LOG_FILE', 'a') as f:
        f.write(f'hokage-session error: {e}\n')
    print('{}')
" 2>>"$LOG_FILE") || CONTEXT='{}'

echo "$CONTEXT"

# Fire-and-forget Rasengan event
(python3 -c "
import httpx, json
try:
    httpx.post('http://localhost:8050/events', json={
        'event_type': 'hokage.session_loaded',
        'source': 'hokage',
        'payload': {'hook': 'session_start'}
    }, timeout=2.0)
except: pass
" &>/dev/null &)

exit 0
