"""Integration tests for Milestone 2: Claude adapter + comparison reports"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from adapters.claude import ClaudeCodeAdapter
from adapters.parsers.claude_parser import ClaudeParser
from reporting.html_generator import HTMLGenerator
from adapters.base import BenchmarkResult


@pytest.fixture
def temp_task_dir():
    """Create temporary task directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_claude_parser_full_extraction():
    """Test ClaudeParser extracts all metrics correctly"""
    parser = ClaudeParser()

    output = """
Task execution started.

Using tool: Read
Using tool: Bash
Using tool: Write

Error: File not found
Retrying...
Attempting again...

Task completed successfully!

Input tokens: 1,234
Output tokens: 567
Total: 1,801 tokens
"""

    metrics = parser.extract_metrics(output, "", exit_code=0)

    assert metrics["token_count"]["input"] == 1234
    assert metrics["token_count"]["output"] == 567
    assert metrics["cost"] > 0  # Should calculate cost
    assert metrics["tool_calls"] == 3
    assert metrics["retries"] == 2
    assert metrics["error_recovered"] is True  # Errors but successful exit


@patch('adapters.claude.subprocess.run')
def test_claude_adapter_execution_flow(mock_run, temp_task_dir):
    """Test ClaudeAdapter end-to-end execution flow"""
    # Mock successful claude execution
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = """
Using tool: Read
Using tool: Write
Task completed.
Input tokens: 1000
Output tokens: 500
"""
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    adapter = ClaudeCodeAdapter(api_key="test-key")
    adapter.setup(str(temp_task_dir))

    result = adapter.execute_task("Write a hello world script", timeout=60)

    assert result.success is True
    assert result.token_count["input"] == 1000
    assert result.token_count["output"] == 500
    assert result.cost > 0
    assert result.tool_calls == 2


def test_comparison_report_generation():
    """Test generating comparison report for Kimi vs Claude"""
    generator = HTMLGenerator()

    kimi_result = BenchmarkResult(
        success=True,
        wall_time=45.2,
        token_count={"input": 1500, "output": 2300},
        cost=0.038,
        retries=1,
        tool_calls=12,
        error_recovered=True,
        generated_files=["solution.py"],
        logs="Kimi logs",
        recording_path="kimi.cast",
        quality_score=87.5,
    )

    claude_result = BenchmarkResult(
        success=True,
        wall_time=38.7,
        token_count={"input": 1200, "output": 1800},
        cost=0.042,
        retries=0,
        tool_calls=8,
        error_recovered=False,
        generated_files=["solution.py"],
        logs="Claude logs",
        recording_path="claude.cast",
        quality_score=92.3,
    )

    results = {"kimi": kimi_result, "claude": claude_result}
    html = generator.generate_comparison(results, "test-task")

    # Verify comparison elements present
    assert "kimi" in html.lower()
    assert "claude" in html.lower()
    assert "45.2" in html  # Kimi time
    assert "38.7" in html  # Claude time
    assert "winner" in html.lower()
    assert "✓" in html  # Winner checkmarks
