#!/bin/bash
# Weekly Evolution Digest Automation
# Run weekly to generate evolution digest and check attention alerts
#
# Usage: ./weekly-evolution.sh [--json]
#
# Can be triggered by:
# - n8n workflow (cron schedule)
# - Manual execution
# - Cron job: 0 9 * * 0 /home/ndninja/scripts/reflection_engine/weekly-evolution.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/home/ndninja/.logs/weekly-evolution.log"
mkdir -p "$(dirname "$LOG_FILE")"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check for JSON output flag
OUTPUT_JSON=false
if [[ "$1" == "--json" ]]; then
    OUTPUT_JSON=true
fi

if [ "$OUTPUT_JSON" = false ]; then
    echo "[$TIMESTAMP] Starting weekly evolution digest..." >> "$LOG_FILE"
fi

# Run automation script
cd "$SCRIPT_DIR"
if [ "$OUTPUT_JSON" = true ]; then
    python3 -c "
from evolution.automation import run_weekly_automation
import json
result = run_weekly_automation()
print(json.dumps(result))
"
else
    python3 -c "
from evolution.automation import run_weekly_automation
import json
result = run_weekly_automation()
print(json.dumps(result, indent=2))
" 2>&1 | tee -a "$LOG_FILE"
fi

EXIT_CODE=${PIPESTATUS[0]}

if [ "$OUTPUT_JSON" = false ]; then
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$TIMESTAMP] Weekly evolution completed successfully" >> "$LOG_FILE"
    else
        echo "[$TIMESTAMP] Weekly evolution failed with exit code $EXIT_CODE" >> "$LOG_FILE"
    fi
fi

exit $EXIT_CODE
