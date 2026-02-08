#!/bin/bash
# Daily Review Automation Shell Wrapper
# Runs nightly to analyze conversations and generate suggestions
# Logs: structured JSON → ~/.logs/daily-review.log (via structured_logger.py)

set -e

mkdir -p /home/ndninja/.logs

# Load API keys from LLM Council .env file
if [ -f /home/ndninja/projects/llm-council/.env ]; then
  export $(grep -v '^#' /home/ndninja/projects/llm-council/.env | xargs)
fi

# Run Python automation script (structured logger handles all log output)
cd /home/ndninja/scripts
python3 daily-review-automation.py 1

EXIT_CODE=$?

# Cleanup old logs (keep last 30 days)
find /home/ndninja/.logs -name "*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
