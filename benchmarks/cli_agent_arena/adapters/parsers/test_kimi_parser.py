"""Tests for Kimi CLI output parser."""

import pytest
from .kimi_parser import KimiParser


class TestKimiParser:
    """Test suite for KimiParser."""

    @pytest.fixture
    def parser(self):
        """Create a KimiParser instance."""
        return KimiParser()

    def test_kimi_parser_extract_tokens(self, parser):
        """Test parsing token counts from Kimi output."""
        stdout = """
Processing task...
Tokens used: input=150, output=320
Task completed successfully.
"""
        stderr = ""

        metrics = parser.extract_metrics(stdout, stderr)

        assert metrics["tokens"]["input"] == 150
        assert metrics["tokens"]["output"] == 320

    def test_kimi_parser_extract_tool_calls(self, parser):
        """Test counting tool call occurrences."""
        stdout = """
Starting task...
Executing tool: read_file
File content retrieved.
Executing tool: write_file
File written successfully.
Executing tool: bash_command
Command completed.
Task finished.
"""
        stderr = ""

        metrics = parser.extract_metrics(stdout, stderr)

        assert metrics["tool_calls"] == 3

    def test_kimi_parser_extract_retries(self, parser):
        """Test counting retry attempts in stderr."""
        stdout = "Task execution..."
        stderr = """
Warning: API call failed, retrying...
Warning: Connection timeout, retrying...
Error: Rate limit hit, retrying...
"""

        metrics = parser.extract_metrics(stdout, stderr)

        assert metrics["retries"] == 3

    def test_kimi_parser_calculate_cost(self, parser):
        """Test cost calculation using Moonshot pricing."""
        stdout = """
Task execution...
Tokens used: input=1000, output=2000
Task completed.
"""
        stderr = ""

        metrics = parser.extract_metrics(stdout, stderr)

        # Total tokens: 3000, cost = 3000 / 1000 * $0.01 = $0.03
        assert metrics["cost"] == 0.03

    def test_kimi_parser_detect_error_recovery(self, parser):
        """Test detection of error recovery patterns."""
        stdout = """
Starting task...
Error: Connection failed
Retrying connection...
Success: Connection established
Task completed.
"""
        stderr = ""

        metrics = parser.extract_metrics(stdout, stderr)

        assert metrics["error_recovered"] is True

    def test_kimi_parser_missing_metrics(self, parser):
        """Test fallback to zero values when metrics not found."""
        stdout = "Simple output with no metrics"
        stderr = ""

        metrics = parser.extract_metrics(stdout, stderr)

        # Should fallback to default values
        assert metrics["tokens"]["input"] == 0
        assert metrics["tokens"]["output"] == 0
        assert metrics["cost"] == 0.0
        assert metrics["retries"] == 0
        assert metrics["tool_calls"] == 0
        assert metrics["error_recovered"] is False

    def test_kimi_parser_no_error_recovery(self, parser):
        """Test that error without success doesn't trigger recovery flag."""
        stdout = """
Starting task...
Error: Something went wrong
Task failed.
"""
        stderr = ""

        metrics = parser.extract_metrics(stdout, stderr)

        assert metrics["error_recovered"] is False

    def test_kimi_parser_partial_token_data(self, parser):
        """Test handling of malformed token output."""
        stdout = "Tokens used: input=100"  # Missing output tokens
        stderr = ""

        metrics = parser.extract_metrics(stdout, stderr)

        # Should fallback to zeros if pattern doesn't fully match
        assert metrics["tokens"]["input"] == 0
        assert metrics["tokens"]["output"] == 0
