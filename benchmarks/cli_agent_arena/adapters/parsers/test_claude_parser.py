import pytest
from .claude_parser import ClaudeParser


def test_claude_parser_init():
    """Test ClaudeParser initialization"""
    parser = ClaudeParser()
    assert parser is not None


def test_extract_tokens_from_output():
    """Test extracting token counts from Claude output"""
    parser = ClaudeParser()

    output = """
Task completed successfully.

Input tokens: 1,234
Output tokens: 567
Total: 1,801 tokens
"""

    result = parser.extract_tokens(output)

    assert result["input"] == 1234
    assert result["output"] == 567


def test_calculate_cost_correctly():
    """Test cost calculation from token counts"""
    parser = ClaudeParser()

    tokens = {"input": 1000, "output": 500}
    cost = parser.calculate_cost(tokens)

    # Sonnet pricing: $3/MTok input, $15/MTok output
    expected_cost = (1000 * 0.003 / 1000) + (500 * 0.015 / 1000)
    assert abs(cost - expected_cost) < 0.0001  # Float comparison


def test_calculate_cost_zero_tokens():
    """Test cost calculation with zero tokens"""
    parser = ClaudeParser()

    tokens = {"input": 0, "output": 0}
    cost = parser.calculate_cost(tokens)

    assert cost == 0.0


def test_count_tool_calls():
    """Test counting tool usage from output"""
    parser = ClaudeParser()

    output = """
Running task...
Using tool: Read
Using tool: Bash
Using tool: Write
Task complete.
"""

    tool_calls = parser.count_tool_calls(output)
    assert tool_calls == 3


def test_detect_retries():
    """Test detecting retry attempts"""
    parser = ClaudeParser()

    output = """
Attempting operation...
Error occurred
Retrying...
Attempting again...
Success!
"""

    retries = parser.detect_retries(output)
    assert retries == 2


def test_detect_error_recovery():
    """Test detecting error recovery"""
    parser = ClaudeParser()

    # Errors present but successful exit
    output_with_recovery = "Error: File not found\nRetrying...\nSuccess!"
    assert parser.detect_error_recovery(output_with_recovery, exit_code=0) is True

    # Errors and failed exit
    output_failed = "Error: File not found\nFailed."
    assert parser.detect_error_recovery(output_failed, exit_code=1) is False

    # No errors
    output_clean = "Task completed successfully"
    assert parser.detect_error_recovery(output_clean, exit_code=0) is False
