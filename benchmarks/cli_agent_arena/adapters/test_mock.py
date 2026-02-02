"""Test mock adapter for development and testing"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.mock import MockAdapter
from adapters.base import BenchmarkResult


def test_mock_adapter_setup():
    """Test mock adapter setup"""
    adapter = MockAdapter()
    adapter.setup("/tmp/test-task")

    assert adapter.task_dir == "/tmp/test-task"


def test_mock_adapter_execute_success():
    """Test mock adapter successful execution"""
    adapter = MockAdapter(simulate_success=True)
    adapter.setup("/tmp/test-task")

    result = adapter.execute_task("Test prompt", timeout=60)

    assert isinstance(result, BenchmarkResult)
    assert result.success is True
    assert result.wall_time > 0
    assert result.cost >= 0
    assert result.retries == 0
    assert result.tool_calls > 0
    assert result.recording_path.endswith(".cast")


def test_mock_adapter_execute_failure():
    """Test mock adapter failure simulation"""
    adapter = MockAdapter(simulate_success=False)
    adapter.setup("/tmp/test-task")

    result = adapter.execute_task("Test prompt", timeout=60)

    assert isinstance(result, BenchmarkResult)
    assert result.success is False
    assert result.retries > 0


def test_mock_adapter_configurable_metrics():
    """Test mock adapter with custom metrics"""
    adapter = MockAdapter(
        simulate_wall_time=42.5,
        simulate_cost=0.05,
        simulate_retries=1,
        simulate_tool_calls=15
    )
    adapter.setup("/tmp/test-task")

    result = adapter.execute_task("Test prompt", timeout=60)

    assert result.wall_time == 42.5
    assert result.cost == 0.05
    assert result.retries == 1
    assert result.tool_calls == 15
