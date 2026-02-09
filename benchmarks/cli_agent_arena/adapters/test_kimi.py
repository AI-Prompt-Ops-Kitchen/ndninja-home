"""Test Kimi CLI adapter"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.kimi import KimiAdapter
from adapters.base import BenchmarkResult


def test_kimi_adapter_creation():
    """Test Kimi adapter can be instantiated"""
    adapter = KimiAdapter()
    assert adapter is not None


def test_kimi_adapter_setup():
    """Test Kimi adapter setup"""
    adapter = KimiAdapter()
    adapter.setup("/tmp/test-task")
    assert adapter.task_dir == "/tmp/test-task"


@pytest.mark.skip(reason="Requires Kimi CLI to be installed and configured")
def test_kimi_adapter_execute():
    """Test Kimi adapter execution (integration test)"""
    adapter = KimiAdapter()
    adapter.setup("../../shared-tasks/quicksort")

    result = adapter.execute_task("Implement quicksort", timeout=300)

    assert isinstance(result, BenchmarkResult)
    assert result.recording_path.endswith(".cast")


def test_kimi_adapter_has_parser():
    """Test that Kimi adapter has parser and quality analyzer"""
    adapter = KimiAdapter()
    assert adapter.parser is not None
    assert adapter.quality_analyzer is not None


def test_kimi_adapter_find_generated_files_empty():
    """Test finding generated files with no task_dir"""
    adapter = KimiAdapter()
    files = adapter._find_generated_files()
    assert files == []


def test_kimi_adapter_not_installed_error():
    """Test that RuntimeError is raised when Kimi CLI not installed"""
    adapter = KimiAdapter()
    adapter.setup("/tmp/nonexistent")

    # This should raise RuntimeError if kimi not installed
    # Only test if kimi is actually not available
    if not KimiAdapter.check_available():
        with pytest.raises(RuntimeError, match="Kimi CLI not found"):
            adapter.execute_task("test", timeout=5)
