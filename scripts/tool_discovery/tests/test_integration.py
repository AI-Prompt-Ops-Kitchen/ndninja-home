import pytest
import subprocess
import os
from database import ToolDatabase
from session_start import SessionStartDiscovery
from realtime import RealtimeDiscovery

def test_end_to_end_session_start():
    """Test complete SessionStart flow"""
    discovery = SessionStartDiscovery()
    tools = discovery.get_relevant_tools(limit=3)

    assert isinstance(tools, list)
    assert len(tools) <= 3

    output = discovery.format_suggestions(tools)
    assert 'Suggested tools' in output or 'No tools' in output

def test_end_to_end_realtime():
    """Test complete real-time detection flow"""
    discovery = RealtimeDiscovery(state_file='/tmp/test-tool-discovery.json')

    # Test match
    prompt = "I need multi-model consensus analysis"
    tool = discovery.match_keywords(prompt)

    if tool:  # May be None if registry empty
        output = discovery.format_suggestion(tool)
        assert 'Detected tool suggestion' in output

    discovery.close()

def test_hooks_executable():
    """Test that hooks are executable"""
    session_hook = '/home/ndninja/.claude/hooks/on-session-start-tool-discovery.sh'
    prompt_hook = '/home/ndninja/.claude/hooks/on-user-prompt-tool-discovery.sh'

    assert os.path.exists(session_hook), f"SessionStart hook not found at {session_hook}"
    assert os.path.exists(prompt_hook), f"UserPromptSubmit hook not found at {prompt_hook}"
    assert os.access(session_hook, os.X_OK), f"SessionStart hook not executable"
    assert os.access(prompt_hook, os.X_OK), f"UserPromptSubmit hook not executable"

def test_database_has_tools():
    """Test that registry is seeded"""
    db = ToolDatabase()
    assert db.connect(), "Failed to connect to database"

    tools = db.get_all_tools()
    db.close()

    assert len(tools) >= 10, f"Expected at least 10 seeded tools, found {len(tools)}"

    # Verify tool structure
    if tools:
        tool = tools[0]
        assert 'key' in tool, "Tool missing 'key' field"
        assert 'data' in tool, "Tool missing 'data' field"
        assert 'description' in tool['data'], "Tool data missing 'description' field"
