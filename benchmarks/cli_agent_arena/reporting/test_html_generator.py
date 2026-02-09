"""Tests for HTMLGenerator."""

import tempfile
import os
from pathlib import Path
from .html_generator import HTMLGenerator
from adapters.base import BenchmarkResult


def test_html_generator_creation():
    """Test that HTMLGenerator can be instantiated."""
    generator = HTMLGenerator()
    assert generator is not None


def test_html_generator_single_result():
    """Test generating HTML for a single benchmark result."""
    result = BenchmarkResult(
        success=True,
        wall_time=42.5,
        token_count={"input": 1000, "output": 500},
        cost=0.05,
        retries=0,
        tool_calls=15,
        error_recovered=False,
        generated_files=["quicksort.py"],
        logs="Agent output here",
        recording_path="/path/to/recording.cast",
        quality_score=87.5,
    )

    generator = HTMLGenerator()
    html = generator.generate(
        results={"kimi": result},
        task_name="algorithms/quicksort",
    )

    # Verify HTML contains expected content
    assert "<!DOCTYPE html>" in html
    assert "algorithms/quicksort" in html
    assert "kimi" in html
    assert "42.5" in html  # wall_time
    assert "87.5" in html  # quality_score


def test_html_generator_output_to_file():
    """Test writing HTML to a file."""
    result = BenchmarkResult(
        success=True,
        wall_time=30.0,
        token_count={"input": 500, "output": 300},
        cost=0.02,
        retries=1,
        tool_calls=8,
        error_recovered=True,
        generated_files=["solution.py"],
        logs="Test logs",
        recording_path="/test/recording.cast",
        quality_score=92.0,
    )

    generator = HTMLGenerator()
    html = generator.generate(
        results={"claude": result},
        task_name="test_task",
    )

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        temp_path = f.name

    try:
        # Verify file exists and has content
        assert os.path.exists(temp_path)
        with open(temp_path, "r") as f:
            content = f.read()
            assert len(content) > 0
            assert "claude" in content
    finally:
        os.unlink(temp_path)


def test_generate_comparison_table():
    """Test generating comparison table for multiple agents"""
    from adapters.base import BenchmarkResult

    generator = HTMLGenerator()

    kimi_result = BenchmarkResult(
        success=True,
        wall_time=45.2,
        token_count={"input": 1500, "output": 2300},
        cost=0.038,
        retries=1,
        tool_calls=12,
        error_recovered=True,
        generated_files=["quicksort.py"],
        logs="Kimi execution log",
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
        generated_files=["quicksort.py"],
        logs="Claude execution log",
        recording_path="claude.cast",
        quality_score=92.3,
    )

    results = {"kimi": kimi_result, "claude": claude_result}

    html = generator.generate_comparison(results, "algorithms/quicksort")

    assert "kimi" in html.lower()
    assert "claude" in html.lower()
    assert "45.2" in html  # Kimi time
    assert "38.7" in html  # Claude time
    assert "comparison" in html.lower()


def test_determine_winner():
    """Test determining winner for a metric"""
    generator = HTMLGenerator()

    # Lower is better (time, cost)
    winner = generator.determine_winner({"kimi": 45.2, "claude": 38.7}, lower_is_better=True)
    assert winner == "claude"

    # Higher is better (score, quality)
    winner = generator.determine_winner({"kimi": 87.5, "claude": 92.3}, lower_is_better=False)
    assert winner == "claude"

    # Tie
    winner = generator.determine_winner({"kimi": 100.0, "claude": 100.0}, lower_is_better=False)
    assert winner == "tie"
