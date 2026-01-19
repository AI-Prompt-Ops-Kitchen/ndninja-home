#!/bin/bash
#
# UserPromptSubmit hook for Memory-Assisted Tool Discovery
# Real-time keyword detection for high-value tools

SCRIPT_DIR="/home/ndninja/scripts/tool_discovery"
LOG_FILE="/home/ndninja/.logs/tool-discovery.log"

# Get user prompt from stdin or args
PROMPT="${CLAUDE_USER_PROMPT:-$*}"

# Skip if prompt is empty
if [ -z "$PROMPT" ]; then
    exit 0
fi

# Timeout protection (50ms)
timeout 0.05s python3 -c "
import sys
import os
sys.path.insert(0, '/home/ndninja/scripts')

try:
    from tool_discovery.realtime import RealtimeDiscovery

    # Override state file to use fixed path for session persistence
    # Using claude-session instead of PID for cross-invocation state
    discovery = RealtimeDiscovery()
    discovery.state_file = '/tmp/tool-discovery-claude-session.json'
    discovery._load_state()

    # Use suggest_tool which handles rate limiting and state
    suggestion = discovery.suggest_tool('''$PROMPT''')

    if suggestion:
        print(suggestion)

except Exception as e:
    import traceback
    with open('$LOG_FILE', 'a') as f:
        f.write(f'UserPromptSubmit error: {e}\n')
        f.write(traceback.format_exc())
" 2>>"$LOG_FILE"

exit 0  # Never block prompt submission
