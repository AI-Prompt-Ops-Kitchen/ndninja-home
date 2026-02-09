"""Integration tests for Milestone 1 components.

Tests the complete pipeline:
1. KimiParser extracts metrics from CLI output
2. QualityAnalyzer scores generated code
3. BenchmarkResult includes quality_score
4. HTMLGenerator produces report
"""

import tempfile
import os
from pathlib import Path

from adapters.base import BenchmarkResult
from adapters.parsers.kimi_parser import KimiParser
from quality.analyzer import QualityAnalyzer
from reporting.html_generator import HTMLGenerator


def test_end_to_end_kimi_to_html():
    """Test complete flow: Parse Kimi output → Analyze quality → Generate HTML."""

    # Step 1: Parse Kimi CLI output
    kimi_output = """
Starting task...
Executing tool: write_file
Executing tool: bash
Executing tool: read_file
input=1500, output=2300
Error: File not found
Retrying...
Success: All tests passed
"""

    parser = KimiParser()
    metrics = parser.extract_metrics(kimi_output, "")

    assert metrics["tokens"]["input"] == 1500
    assert metrics["tokens"]["output"] == 2300
    assert metrics["tool_calls"] == 3
    assert metrics["error_recovered"] is True  # Has both "Error:" and "Success:"

    # Step 2: Analyze code quality
    # Create a temporary Python file
    test_code = '''"""Example quicksort implementation."""


def quicksort(arr):
    """Sort array using quicksort algorithm.

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quicksort(left) + middle + quicksort(right)
'''

    # Write to temp file
    fd, temp_file = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(test_code)

        analyzer = QualityAnalyzer()
        quality_score = analyzer.analyze([temp_file])

        assert quality_score > 70, f"Expected quality > 70, got {quality_score}"
    finally:
        os.unlink(temp_file)

    # Step 3: Build BenchmarkResult with quality score
    result = BenchmarkResult(
        success=True,
        wall_time=45.2,
        token_count=metrics["tokens"],
        cost=metrics["cost"],
        retries=metrics["retries"],
        tool_calls=metrics["tool_calls"],
        error_recovered=metrics["error_recovered"],
        generated_files=["quicksort.py"],
        logs=kimi_output,
        recording_path="/recordings/kimi_quicksort_20260202_abcd1234.cast",
        quality_score=quality_score,
    )

    assert result.quality_score == quality_score
    assert result.success is True

    # Step 4: Generate HTML report
    generator = HTMLGenerator()
    html = generator.generate(
        results={"kimi": result},
        task_name="algorithms/quicksort",
    )

    # Verify HTML contains expected content
    assert "<!DOCTYPE html>" in html
    assert "kimi" in html
    assert "algorithms/quicksort" in html
    assert "45.2" in html  # wall_time
    assert str(int(quality_score)) in html  # quality_score (formatted)
    assert "SUCCESS" in html
    assert "quicksort.py" not in html  # File list not shown in this version

    # Verify HTML can be written to file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        temp_html = f.name

    try:
        assert os.path.exists(temp_html)
        assert os.path.getsize(temp_html) > 1000  # Should be substantial
    finally:
        os.unlink(temp_html)


def test_integration_multiple_agents():
    """Test HTML generation with multiple agent results."""

    # Create mock results for multiple agents
    kimi_result = BenchmarkResult(
        success=True,
        wall_time=45.2,
        token_count={"input": 1500, "output": 2300},
        cost=0.038,
        retries=0,
        tool_calls=8,
        error_recovered=True,
        generated_files=["quicksort.py"],
        logs="Kimi logs",
        recording_path="/recordings/kimi.cast",
        quality_score=82.5,
    )

    claude_result = BenchmarkResult(
        success=True,
        wall_time=52.1,
        token_count={"input": 2000, "output": 1800},
        cost=0.042,
        retries=1,
        tool_calls=12,
        error_recovered=False,
        generated_files=["quicksort.py", "test_quicksort.py"],
        logs="Claude logs",
        recording_path="/recordings/claude.cast",
        quality_score=91.0,
    )

    # Generate comparison report
    generator = HTMLGenerator()
    html = generator.generate(
        results={"kimi": kimi_result, "claude": claude_result},
        task_name="algorithms/quicksort",
    )

    # Verify both agents appear
    assert "kimi" in html
    assert "claude" in html

    # Verify stats
    assert "45.2" in html  # Fastest time (kimi)
    assert "52.1" in html  # Claude time
    assert "91.0" in html  # Highest quality (claude)

    # Verify winner is determined
    assert "WINNER" in html


def test_integration_quality_analyzer_with_parser():
    """Test that quality analyzer works with parser output."""

    # Simulate parsing output from a real run
    parser = KimiParser()
    metrics = parser.extract_metrics(
        "Executing tool: write_file\ninput=500, output=300",
        ""
    )

    # Create a simple Python file
    fd, temp_file = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write("def hello(): return 'world'")

        analyzer = QualityAnalyzer()
        quality_score = analyzer.analyze([temp_file])

        # Create result
        result = BenchmarkResult(
            success=True,
            wall_time=10.0,
            token_count=metrics["tokens"],
            cost=metrics["cost"],
            retries=0,
            tool_calls=metrics["tool_calls"],
            error_recovered=False,
            generated_files=[temp_file],
            logs="test",
            recording_path="/test.cast",
            quality_score=quality_score,
        )

        assert result.quality_score >= 0
        assert result.quality_score <= 100
    finally:
        os.unlink(temp_file)
