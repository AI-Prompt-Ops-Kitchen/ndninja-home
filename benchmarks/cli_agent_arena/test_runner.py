"""Test benchmark runner CLI"""

import pytest
import subprocess
import sys
from pathlib import Path


def test_runner_help():
    """Test --help flag"""
    runner_path = Path(__file__).parent / "run_cli_benchmarks.py"
    result = subprocess.run(
        [sys.executable, str(runner_path), "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent  # Run from benchmarks/ directory
    )
    assert result.returncode == 0
    assert "CLI Agent Benchmark Runner" in result.stdout
    assert "--agent" in result.stdout
    assert "--tasks" in result.stdout


def test_runner_list_tasks():
    """Test --list-tasks flag"""
    runner_path = Path(__file__).parent / "run_cli_benchmarks.py"
    result = subprocess.run(
        [sys.executable, str(runner_path), "--list-tasks"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent  # Run from benchmarks/ directory
    )
    assert result.returncode == 0
    assert "quicksort" in result.stdout
    assert "binary_search" in result.stdout
    assert "lru_cache" in result.stdout


def test_runner_execute_single_task_mock():
    """Test executing a single task with mock adapter"""
    result = subprocess.run(
        [
            sys.executable,
            "benchmarks/cli_agent_arena/run_cli_benchmarks.py",
            "--agent", "mock",
            "--tasks", "algorithms/quicksort",
            "--dry-run"
        ],
        capture_output=True,
        text=True
    )

    # Should succeed
    assert result.returncode == 0
    assert "quicksort" in result.stdout
    assert "mock" in result.stdout
