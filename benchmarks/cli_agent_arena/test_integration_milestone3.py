"""Integration tests for Milestone 3: Gemini adapter + three-way comparison"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from adapters.gemini import GeminiAdapter
from adapters.parsers.gemini_parser import GeminiParser
from reporting.html_generator import HTMLGenerator
from adapters.base import BenchmarkResult


def test_gemini_parser_full_extraction():
    """Test GeminiParser extracts all metrics from real-format JSON"""
    parser = GeminiParser()

    data = {
        "response": "Here is quicksort:\n\ndef quicksort(arr):\n    ...",
        "stats": {
            "models": [
                {"name": "gemini-2.0-flash", "tokens": {"input": 2500, "output": 3100}},
            ],
            "tools": {"totalCalls": 12},
            "retries": 1,
        },
        "error": "Rate limit hit",
    }

    metrics = parser.extract_metrics(json.dumps(data), "")

    assert metrics["tokens"]["input"] == 2500
    assert metrics["tokens"]["output"] == 3100
    assert metrics["tool_calls"] == 12
    assert metrics["retries"] == 1
    assert metrics["error_recovered"] is True  # error + response both present
    assert metrics["cost"] > 0


@patch('adapters.gemini.subprocess.run')
def test_gemini_adapter_execution_flow(mock_run):
    """Test GeminiAdapter end-to-end mocked execution"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        gemini_output = json.dumps({
            "response": "Implementation complete",
            "stats": {
                "models": [
                    {"name": "gemini-2.0-flash", "tokens": {"input": 1800, "output": 2200}}
                ],
                "tools": {"totalCalls": 7},
            },
        })

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = gemini_output
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        adapter = GeminiAdapter()
        adapter.setup(str(temp_dir))

        result = adapter.execute_task("Write quicksort in Python", timeout=120)

        assert result.success is True
        assert result.token_count["input"] == 1800
        assert result.token_count["output"] == 2200
        assert result.tool_calls == 7
        assert result.cost > 0
        assert result.wall_time > 0
    finally:
        shutil.rmtree(temp_dir)


def _make_result(wall_time, cost, tool_calls, quality, retries=0, error_recovered=False):
    """Helper to create BenchmarkResult"""
    return BenchmarkResult(
        success=True,
        wall_time=wall_time,
        token_count={"input": 1000, "output": 1000},
        cost=cost,
        retries=retries,
        tool_calls=tool_calls,
        error_recovered=error_recovered,
        generated_files=["solution.py"],
        logs="logs",
        recording_path="recording.cast",
        quality_score=quality,
    )


def test_three_way_comparison_generation():
    """Test HTML comparison report with three agents"""
    generator = HTMLGenerator()

    results = {
        "kimi": _make_result(45.2, 0.038, 12, 87.5, retries=1, error_recovered=True),
        "claude": _make_result(38.7, 0.042, 8, 92.3),
        "gemini": _make_result(32.1, 0.0012, 10, 89.0),
    }

    html = generator.generate_comparison(results, "algorithms/quicksort")

    # All three agents present
    assert "kimi" in html.lower()
    assert "claude" in html.lower()
    assert "gemini" in html.lower()

    # Key values present
    assert "45.2" in html
    assert "38.7" in html
    assert "32.1" in html

    # Comparison elements
    assert "winner" in html.lower()
    assert "Autonomy" in html
    assert "radarChart" in html
    assert "Chart" in html


def test_three_way_winner_determination():
    """Test overall winner is correctly determined with 3 agents"""
    generator = HTMLGenerator()

    # Gemini: fastest and cheapest
    # Claude: highest quality
    # Kimi: middle of the road
    results = {
        "kimi": _make_result(45.2, 0.038, 12, 87.5),
        "claude": _make_result(38.7, 0.042, 8, 92.3),
        "gemini": _make_result(32.1, 0.0012, 10, 89.0),
    }

    rankings = generator._rank_agents(results)

    # All three agents should be ranked
    assert len(rankings) == 3
    assert set(rankings.values()) == {1, 2, 3}

    # Gemini should rank well (fastest + cheapest)
    assert rankings["gemini"] == 1


def test_three_way_ranking_accuracy():
    """Test 1st/2nd/3rd ranking is correct"""
    generator = HTMLGenerator()

    # Clear ordering: agent_a best in everything
    results = {
        "agent_a": _make_result(10.0, 0.001, 3, 95.0),
        "agent_b": _make_result(30.0, 0.010, 8, 80.0),
        "agent_c": _make_result(50.0, 0.050, 15, 60.0),
    }

    rankings = generator._rank_agents(results)

    assert rankings["agent_a"] == 1
    assert rankings["agent_b"] == 2
    assert rankings["agent_c"] == 3
