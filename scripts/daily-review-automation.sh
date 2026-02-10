#!/bin/bash
# Daily Review Automation Shell Wrapper
# Runs nightly to analyze conversations and generate suggestions
# Logs: structured JSON → ~/.logs/daily-review.log (via structured_logger.py)

set -e

mkdir -p /home/ndninja/.logs

# Load API keys for LLM Council (cron doesn't inherit shell env)
# Priority: project .env → user .env → bashrc grep
if [ -f /home/ndninja/projects/llm-council/.env ]; then
  export $(grep -v '^#' /home/ndninja/projects/llm-council/.env | xargs)
fi
if [ -f /home/ndninja/.env ]; then
  export $(grep -E 'API_KEY=' /home/ndninja/.env | grep -v '^#' | xargs)
fi
# Fallback: extract API key exports from bashrc (safe — only grabs export lines)
if [ -z "$OPENAI_API_KEY" ] || [ -z "$GEMINI_API_KEY" ] || [ -z "$PERPLEXITY_API_KEY" ]; then
  eval "$(grep -E '^export\s+\w+_API_KEY=' /home/ndninja/.bashrc 2>/dev/null || true)"
fi

# Run Python automation script (structured logger handles all log output)
cd /home/ndninja/scripts
python3 daily-review-automation.py 1

EXIT_CODE=$?

# Cleanup old logs (keep last 30 days)
find /home/ndninja/.logs -name "*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE
