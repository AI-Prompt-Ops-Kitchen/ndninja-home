"""Test Gemini CLI adapter"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.gemini import GeminiAdapter
from adapters.base import BenchmarkResult
from recording_manager import RecordingManager


def test_gemini_adapter_creation():
    """Test Gemini adapter can be instantiated"""
    adapter = GeminiAdapter()
    assert adapter is not None
    assert adapter.parser is not None
    assert adapter.quality_analyzer is not None


def test_gemini_adapter_creation_with_api_key():
    """Test Gemini adapter with API key"""
    adapter = GeminiAdapter(api_key="test-key-123")
    assert adapter.api_key == "test-key-123"


def test_gemini_adapter_setup():
    """Test Gemini adapter setup"""
    adapter = GeminiAdapter()
    adapter.setup("/tmp/test-task")
    assert adapter.task_dir == "/tmp/test-task"


@patch('adapters.gemini.subprocess.run')
def test_gemini_adapter_mocked_execution(mock_run):
    """Test Gemini adapter execution with mocked subprocess"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        gemini_output = json.dumps({
            "response": "Here is your solution",
            "stats": {
                "models": [
                    {"name": "gemini-2.0-flash", "tokens": {"input": 800, "output": 1200}}
                ],
                "tools": {"totalCalls": 5},
            },
        })

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = gemini_output
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        adapter = GeminiAdapter()
        adapter.setup(str(temp_dir))

        result = adapter.execute_task("Write quicksort", timeout=60)

        assert result.success is True
        assert result.token_count["input"] == 800
        assert result.token_count["output"] == 1200
        assert result.tool_calls == 5
        assert result.cost > 0
    finally:
        shutil.rmtree(temp_dir)


@patch('adapters.gemini.subprocess.run')
def test_gemini_adapter_timeout(mock_run):
    """Test Gemini adapter handles timeout"""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="gemini", timeout=60)

    adapter = GeminiAdapter()
    adapter.setup("/tmp/test")

    result = adapter.execute_task("test prompt", timeout=60)

    assert result.success is False
    assert "timed out" in result.logs


@patch('adapters.gemini.subprocess.run')
def test_gemini_check_available(mock_run):
    """Test check_available with gemini installed"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    assert GeminiAdapter.check_available() is True


@patch.object(RecordingManager, 'check_asciinema_available', return_value=False)
def test_gemini_command_construction(mock_asciinema):
    """Test that the correct command is built"""
    adapter = GeminiAdapter(api_key="test-key")
    adapter.setup("/tmp/test-task")

    with patch('adapters.gemini.subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "{}"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        adapter.execute_task("test prompt", timeout=60)

        # Verify command includes expected flags
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "gemini"
        assert "-p" in cmd
        assert "-o" in cmd
        assert "json" in cmd
        assert "--yolo" in cmd

        # Verify API key in environment
        if "env" in call_args[1]:
            assert call_args[1]["env"].get("GEMINI_API_KEY") == "test-key"


@pytest.mark.skip(reason="Requires Gemini CLI and API key")
def test_gemini_adapter_execute():
    """Test Gemini adapter execution (integration test)"""
    adapter = GeminiAdapter()
    adapter.setup("../../shared-tasks/quicksort")

    result = adapter.execute_task("Implement quicksort", timeout=300)

    assert isinstance(result, BenchmarkResult)
    assert result.recording_path.endswith(".cast")
