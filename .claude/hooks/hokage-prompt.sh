#!/usr/bin/env bash
# ============================================================================
# Hokage — UserPromptSubmit Hook
# Keyword-scans user prompt and injects relevant domain edicts as context.
# Only injects edicts for domains that match — not the full ruleset.
#
# Input (stdin): {"user_prompt":"..."}
# Output: {"additionalContext":"..."} or empty
# ============================================================================

set -euo pipefail

EDICTS_FILE="/home/ndninja/.claude/hokage/edicts.yaml"
LOG_FILE="/home/ndninja/.logs/hokage.log"

mkdir -p "$(dirname "$LOG_FILE")"

# Read input from stdin
INPUT=$(cat)

# If edicts file doesn't exist, pass through
if [ ! -f "$EDICTS_FILE" ]; then
  echo '{}'
  exit 0
fi

# Keyword scan — timeout 50ms (matches existing pattern)
RESULT=$(timeout 0.05s python3 -c "
import json, sys, yaml

try:
    input_data = json.loads(sys.argv[1])
    prompt = input_data.get('user_prompt', '').lower()

    if not prompt or len(prompt) < 3:
        print('{}')
        sys.exit(0)

    # Load edicts
    with open('$EDICTS_FILE') as f:
        data = yaml.safe_load(f)

    edicts = data.get('edicts', [])

    # Find matching domains by keyword
    matched_edicts = []
    matched_domains = set()

    for edict in edicts:
        keywords = edict.get('keywords', [])
        for kw in keywords:
            if kw.lower() in prompt:
                matched_edicts.append(edict)
                matched_domains.add(edict.get('domain', 'unknown'))
                break  # One match per edict is enough

    if not matched_edicts:
        print('{}')
        sys.exit(0)

    # Build context — only matched domains
    lines = []
    lines.append(f'[HOKAGE — {len(matched_edicts)} relevant edicts for: {\", \".join(sorted(matched_domains))}]')

    for e in matched_edicts:
        sev = e.get('severity', 'PREFER')
        marker = '🚫' if sev == 'BLOCK' else ('⚠️' if sev == 'WARN' else '→')
        lines.append(f'{marker} {e[\"id\"]}: {e[\"rule\"]}')
        if sev in ('BLOCK', 'WARN'):
            lines.append(f'  Reason: {e.get(\"rationale\", \"\")}')

    result = {
        'additionalContext': '\n'.join(lines)
    }
    print(json.dumps(result))

except Exception as e:
    with open('$LOG_FILE', 'a') as f:
        f.write(f'hokage-prompt error: {e}\n')
    print('{}')
" "$INPUT" 2>>"$LOG_FILE") || RESULT='{}'

echo "$RESULT"
exit 0
