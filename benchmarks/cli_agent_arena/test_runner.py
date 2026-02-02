"""Test benchmark runner CLI"""

import pytest
import subprocess
import sys


def test_runner_help():
    """Test --help flag"""
    result = subprocess.run(
        [sys.executable, "benchmarks/cli_agent_arena/run_cli_benchmarks.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "CLI Agent Benchmark Runner" in result.stdout
    assert "--agent" in result.stdout
    assert "--tasks" in result.stdout


def test_runner_list_tasks():
    """Test --list-tasks flag"""
    result = subprocess.run(
        [sys.executable, "benchmarks/cli_agent_arena/run_cli_benchmarks.py", "--list-tasks"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "quicksort" in result.stdout
    assert "binary_search" in result.stdout
    assert "lru_cache" in result.stdout
