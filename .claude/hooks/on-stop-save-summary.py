#!/usr/bin/env python3
"""
Auto-Save Conversation Summary Hook
Saves session summaries to claude_memory database at session end.

Event: Stop
Saves to: claude_memory.conversation_summaries via MCP
"""

import json
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
LOG_FILE = Path.home() / ".logs" / "conversation-summary-hook.log"
LOG_FILE.parent.mkdir(exist_ok=True)

def log(message: str):
    """Log to file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def read_transcript(transcript_path: str) -> str:
    """Read and return transcript content."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""

    try:
        with open(transcript_path, 'r') as f:
            return f.read()
    except Exception as e:
        log(f"Error reading transcript: {e}")
        return ""

def simple_transcript_analysis(transcript: str, session_id: str) -> dict:
    """Simple heuristic-based analysis when LLM analysis isn't available."""

    lines = transcript.split('\n')

    # Extract basic info
    user_messages = [l for l in lines if l.strip().startswith('User:')]
    assistant_messages = [l for l in lines if l.strip().startswith('Assistant:')]

    # Generate simple summary
    summary = f"Session with {len(user_messages)} user messages and {len(assistant_messages)} assistant responses"

    # Try to extract topics from user messages
    topics = []
    for msg in user_messages[:5]:  # First 5 messages
        # Simple keyword extraction
        words = msg.lower().split()
        keywords = [w for w in words if len(w) > 6 and w not in ['investigate', 'please', 'analyze']]
        topics.extend(keywords[:2])

    return {
        "summary": summary[:200],  # Truncate if too long
        "action_items": [],
        "key_decisions": [],
        "topics_discussed": list(set(topics))[:5],  # Unique topics, max 5
        "emotional_context": "session completed"
    }

def save_to_database(session_id: str, summary_data: dict) -> bool:
    """Save summary to database using MCP tool."""

    try:
        log("Saving to database via MCP...")

        # Prepare MCP tool call parameters
        mcp_params = {
            "session_id": session_id,
            "summary": summary_data.get("summary", "Session completed"),
            "app_source": "code",
            "action_items": summary_data.get("action_items", []),
            "key_decisions": summary_data.get("key_decisions", []),
            "topics_discussed": summary_data.get("topics_discussed", []),
            "emotional_context": summary_data.get("emotional_context", "")
        }

        # Call via psql directly (more reliable than MCP from hook)
        # Check if session already exists
        check_sql = f"SELECT COUNT(*) FROM conversation_summaries WHERE session_id = '{session_id}';"
        check_result = subprocess.run(
            [
                'psql',
                '-U', 'claude_mcp',
                '-d', 'claude_memory',
                '-h', 'localhost',
                '-t',  # Tuples only
                '-c', check_sql
            ],
            env={**os.environ, 'PGPASSWORD': 'REDACTED'},
            capture_output=True,
            text=True,
            timeout=5
        )

        exists = check_result.returncode == 0 and int(check_result.stdout.strip()) > 0

        if exists:
            log(f"Session {session_id} already exists, skipping")
            return True

        sql = f"""
INSERT INTO conversation_summaries (
    session_id,
    app_source,
    summary,
    action_items,
    key_decisions,
    topics_discussed,
    emotional_context,
    created_at
) VALUES (
    '{session_id}',
    'code',
    $${summary_data.get('summary', 'Session completed')}$$,
    '{json.dumps(summary_data.get('action_items', []))}'::jsonb,
    '{json.dumps(summary_data.get('key_decisions', []))}'::jsonb,
    '{json.dumps(summary_data.get('topics_discussed', []))}'::jsonb,
    '{summary_data.get('emotional_context', '')}',
    NOW()
);
"""

        result = subprocess.run(
            [
                'psql',
                '-U', 'claude_mcp',
                '-d', 'claude_memory',
                '-h', 'localhost',
                '-c', sql
            ],
            env={**os.environ, 'PGPASSWORD': 'REDACTED'},
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            log(f"✓ Successfully saved summary for session {session_id}")
            return True
        else:
            log(f"✗ Failed to save summary: {result.stderr}")
            return False

    except Exception as e:
        log(f"Error saving to database: {e}")
        return False

def main():
    """Main hook execution."""
    log("=" * 60)
    log("Auto-Save Conversation Summary Hook Started")

    try:
        # Get session info from environment
        session_id = os.environ.get('CLAUDE_SESSION_ID', f'session-{datetime.now().strftime("%Y-%m-%d-%H%M%S")}')
        transcript_path = os.environ.get('CLAUDE_TRANSCRIPT_PATH')

        log(f"Session ID: {session_id}")
        log(f"Transcript path: {transcript_path}")

        # Read transcript
        transcript = read_transcript(transcript_path)
        if not transcript or len(transcript.strip()) < 100:
            log("Transcript too short or empty, skipping")
            return 0

        log(f"Transcript size: {len(transcript)} chars")

        # Use simple analysis (fast, no API costs)
        log("Analyzing transcript with heuristics...")
        summary_data = simple_transcript_analysis(transcript, session_id)
        log(f"Analysis complete: {summary_data.get('summary', 'N/A')[:100]}")

        # Save to database
        success = save_to_database(session_id, summary_data)

        log("=" * 60)
        return 0 if success else 1

    except Exception as e:
        log(f"Fatal error: {e}")
        import traceback
        log(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())
