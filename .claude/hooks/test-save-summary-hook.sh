#!/bin/bash
echo "Testing conversation summary hook..."
TEST_TRANSCRIPT=$(mktemp)
echo "User: investigate database sessions" > "$TEST_TRANSCRIPT"
echo "Assistant: investigating..." >> "$TEST_TRANSCRIPT"
export CLAUDE_SESSION_ID="test-hook-$(date +%s)"
export CLAUDE_TRANSCRIPT_PATH="$TEST_TRANSCRIPT"
echo "Session ID: $CLAUDE_SESSION_ID"
echo "Transcript: $TEST_TRANSCRIPT"
echo
python3 /home/ndninja/.claude/hooks/on-stop-save-summary.py
EXIT_CODE=$?
echo
echo "Hook exit code: $EXIT_CODE"
echo "Check log: tail ~/.logs/conversation-summary-hook.log"
rm "$TEST_TRANSCRIPT"
