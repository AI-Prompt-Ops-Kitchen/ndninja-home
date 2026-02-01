#!/bin/bash
# Sync chat history to PostgreSQL
# Run periodically via cron or heartbeat

cd ~/clawd
python3 scripts/import_chat_history.py 2>&1 | tail -5
