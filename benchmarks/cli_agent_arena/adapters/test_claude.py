import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.claude import ClaudeCodeAdapter


def test_adapter_initialization():
    """Test ClaudeCodeAdapter initialization"""
    adapter = ClaudeCodeAdapter(api_key="test-key")
    assert adapter.api_key == "test-key"
    assert adapter.task_dir is None


def test_setup():
    """Test adapter setup"""
    adapter = ClaudeCodeAdapter()
    adapter.setup("/tmp/task")
    assert adapter.task_dir == "/tmp/task"


@patch('adapters.claude.subprocess.run')
def test_check_available_installed(mock_run):
    """Test check_available when Claude is installed"""
    mock_run.return_value = MagicMock(returncode=0)

    assert ClaudeCodeAdapter.check_available() is True
    mock_run.assert_called_once()


@patch('adapters.claude.subprocess.run', side_effect=FileNotFoundError)
def test_check_available_not_installed(mock_run):
    """Test check_available when Claude is not installed"""
    assert ClaudeCodeAdapter.check_available() is False
