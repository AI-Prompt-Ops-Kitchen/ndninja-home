"""Tests for GeminiParser."""

import json
import pytest
from .gemini_parser import GeminiParser


def test_gemini_parser_init():
    """Test GeminiParser initialization"""
    parser = GeminiParser()
    assert parser is not None


def test_extract_metrics_happy_path():
    """Test full extraction from valid Gemini JSON output"""
    parser = GeminiParser()

    data = {
        "response": "Here is your quicksort implementation...",
        "stats": {
            "models": [
                {"name": "gemini-2.0-flash", "tokens": {"input": 1500, "output": 2300}}
            ],
            "tools": {"totalCalls": 8},
        },
    }

    metrics = parser.extract_metrics(json.dumps(data), "")

    assert metrics["tokens"]["input"] == 1500
    assert metrics["tokens"]["output"] == 2300
    assert metrics["tool_calls"] == 8
    assert metrics["retries"] == 0
    assert metrics["error_recovered"] is False
    assert metrics["cost"] > 0


def test_multi_model_token_summing():
    """Test token summing across multiple models"""
    parser = GeminiParser()

    data = {
        "response": "done",
        "stats": {
            "models": [
                {"name": "gemini-2.0-flash", "tokens": {"input": 1000, "output": 500}},
                {"name": "gemini-2.0-pro", "tokens": {"input": 2000, "output": 1500}},
            ],
            "tools": {"totalCalls": 3},
        },
    }

    metrics = parser.extract_metrics(json.dumps(data), "")

    assert metrics["tokens"]["input"] == 3000
    assert metrics["tokens"]["output"] == 2000


def test_cost_calculation():
    """Test cost math matches Gemini pricing"""
    parser = GeminiParser()

    data = {
        "response": "done",
        "stats": {
            "models": [
                {"name": "gemini-2.0-flash", "tokens": {"input": 1000, "output": 1000}}
            ],
            "tools": {"totalCalls": 0},
        },
    }

    metrics = parser.extract_metrics(json.dumps(data), "")

    # $0.00025/1K input + $0.001/1K output
    expected = (1000 * 0.00025 / 1000) + (1000 * 0.001 / 1000)
    assert abs(metrics["cost"] - expected) < 0.0001


def test_tool_calls_extraction():
    """Test tool call count extraction"""
    parser = GeminiParser()

    data = {
        "response": "done",
        "stats": {
            "models": [{"name": "m", "tokens": {"input": 0, "output": 0}}],
            "tools": {"totalCalls": 15},
        },
    }

    metrics = parser.extract_metrics(json.dumps(data), "")
    assert metrics["tool_calls"] == 15


def test_error_recovery_detection():
    """Test error recovery when error and response both present"""
    parser = GeminiParser()

    data = {
        "error": "Rate limit exceeded",
        "response": "Here is the result after retry",
        "stats": {
            "models": [{"name": "m", "tokens": {"input": 100, "output": 200}}],
            "tools": {"totalCalls": 2},
            "retries": 1,
        },
    }

    metrics = parser.extract_metrics(json.dumps(data), "")
    assert metrics["error_recovered"] is True
    assert metrics["retries"] == 1


def test_malformed_json():
    """Test handling of malformed JSON"""
    parser = GeminiParser()

    metrics = parser.extract_metrics("this is not json {{{", "")

    assert metrics["tokens"] == {"input": 0, "output": 0}
    assert metrics["cost"] == 0.0
    assert metrics["tool_calls"] == 0
    assert metrics["retries"] == 0
    assert metrics["error_recovered"] is False


def test_missing_fields():
    """Test handling of JSON with missing expected fields"""
    parser = GeminiParser()

    metrics = parser.extract_metrics(json.dumps({"result": "ok"}), "")

    assert metrics["tokens"] == {"input": 0, "output": 0}
    assert metrics["cost"] == 0.0
    assert metrics["tool_calls"] == 0


def test_empty_output():
    """Test handling of empty output"""
    parser = GeminiParser()

    metrics = parser.extract_metrics("", "")

    assert metrics["tokens"] == {"input": 0, "output": 0}
    assert metrics["cost"] == 0.0
    assert metrics["tool_calls"] == 0
    assert metrics["retries"] == 0
    assert metrics["error_recovered"] is False
