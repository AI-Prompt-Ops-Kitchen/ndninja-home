"""Test Claude Code adapter"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.claude import ClaudeCodeAdapter
from adapters.base import BenchmarkResult


def test_claude_adapter_creation():
    """Test Claude adapter can be instantiated"""
    adapter = ClaudeCodeAdapter()
    assert adapter is not None


def test_claude_adapter_setup():
    """Test Claude adapter setup"""
    adapter = ClaudeCodeAdapter()
    adapter.setup("/tmp/test-task")
    assert adapter.task_dir == "/tmp/test-task"


@pytest.mark.skip(reason="Requires Claude Code CLI and API key")
def test_claude_adapter_execute():
    """Test Claude adapter execution (integration test)"""
    adapter = ClaudeCodeAdapter()
    adapter.setup("../../shared-tasks/quicksort")

    result = adapter.execute_task("Implement quicksort", timeout=300)

    assert isinstance(result, BenchmarkResult)
    assert result.recording_path.endswith(".cast")
