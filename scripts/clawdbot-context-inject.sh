#!/usr/bin/env bash
# clawdbot-context-inject.sh — Inject PostgreSQL preferences into Clawdbot memory
# Cron: */5 * * * * /home/ndninja/scripts/clawdbot-context-inject.sh

STARTUP_FILE="/home/ndninja/clawd/memory/STARTUP.md"
LOG_FILE="/home/ndninja/.logs/clawdbot-context-inject.log"
CURRENT_TIME=$(TZ="America/Chicago" date '+%A, %B %-d, %Y at %I:%M %p %Z')

mkdir -p "$(dirname "$STARTUP_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# Query active preferences grouped by category
PREFS=$(sudo -u postgres psql -d workspace -t -A -F '|' -c "
    SELECT category, key, value, priority
    FROM clawdbot_preferences
    WHERE active = true
    ORDER BY priority DESC, category, key;
" 2>/dev/null)

if [ -z "$PREFS" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to query preferences" >> "$LOG_FILE"
    exit 1
fi

# Build STARTUP.md
{
    echo "# Startup Context (Auto-generated)"
    echo ""
    echo "**Last updated:** ${CURRENT_TIME}"
    echo ""
    echo "## Active Preferences"
    echo ""

    CURRENT_CATEGORY=""
    while IFS='|' read -r category key value priority; do
        if [ "$category" != "$CURRENT_CATEGORY" ]; then
            CURRENT_CATEGORY="$category"
            echo "### ${category^} (Priority ${priority}+)"
            echo ""
        fi
        echo "- **${key}**: ${value}"
    done <<< "$PREFS"

    echo ""
    echo "---"
    echo "*Source: workspace.clawdbot_preferences — $(echo "$PREFS" | wc -l) active rules*"
} > "$STARTUP_FILE"
