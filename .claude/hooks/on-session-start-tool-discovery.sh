#!/bin/bash
#
# SessionStart hook for Memory-Assisted Tool Discovery
# Surfaces relevant tools based on recent conversation topics

SCRIPT_DIR="/home/ndninja/scripts/tool_discovery"
LOG_FILE="/home/ndninja/.logs/tool-discovery.log"

# Create log directory if needed
mkdir -p "$(dirname "$LOG_FILE")"

# Timeout protection (200ms)
timeout 0.2s python3 -c "
import sys
sys.path.insert(0, '/home/ndninja/scripts')

try:
    from tool_discovery.session_start import SessionStartDiscovery

    discovery = SessionStartDiscovery()
    tools = discovery.get_relevant_tools(limit=5)

    if tools:
        output = discovery.format_suggestions(tools)
        print(output)

except Exception as e:
    import traceback
    with open('$LOG_FILE', 'a') as f:
        f.write(f'SessionStart error: {e}\n')
        f.write(traceback.format_exc())
" 2>>"$LOG_FILE"

exit 0  # Never block session start
