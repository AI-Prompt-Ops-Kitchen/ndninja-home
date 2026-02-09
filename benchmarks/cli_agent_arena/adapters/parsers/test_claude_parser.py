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
