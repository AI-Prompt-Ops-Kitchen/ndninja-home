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

    # Initialize with fixed state file for session persistence
    discovery = RealtimeDiscovery(state_file='/tmp/tool-discovery-claude-session.json')

    # Use suggest_tool which handles rate limiting and state
    # Safely get prompt from sys.argv to prevent injection attacks
    suggestion = discovery.suggest_tool(sys.argv[1]) if len(sys.argv) > 1 else None

    if suggestion:
        print(suggestion)

except Exception as e:
    import traceback
    with open('$LOG_FILE', 'a') as f:
        f.write(f'UserPromptSubmit error: {e}\n')
        f.write(traceback.format_exc())

finally:
    # Ensure database connection is closed to prevent connection leaks
    if 'discovery' in locals():
        discovery.close()
" "$PROMPT" 2>>"$LOG_FILE"

exit 0  # Never block prompt submission
