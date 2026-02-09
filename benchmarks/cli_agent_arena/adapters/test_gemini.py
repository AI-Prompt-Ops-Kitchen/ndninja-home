"""Test Gemini CLI adapter"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.gemini import GeminiAdapter
from adapters.base import BenchmarkResult


def test_gemini_adapter_creation():
    """Test Gemini adapter can be instantiated"""
    adapter = GeminiAdapter()
    assert adapter is not None


def test_gemini_adapter_setup():
    """Test Gemini adapter setup"""
    adapter = GeminiAdapter()
    adapter.setup("/tmp/test-task")
    assert adapter.task_dir == "/tmp/test-task"


@pytest.mark.skip(reason="Requires Gemini CLI and API key")
def test_gemini_adapter_execute():
    """Test Gemini adapter execution (integration test)"""
    adapter = GeminiAdapter()
    adapter.setup("../../shared-tasks/quicksort")

    result = adapter.execute_task("Implement quicksort", timeout=300)

    assert isinstance(result, BenchmarkResult)
    assert result.recording_path.endswith(".cast")
