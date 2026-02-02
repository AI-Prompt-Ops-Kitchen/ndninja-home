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
