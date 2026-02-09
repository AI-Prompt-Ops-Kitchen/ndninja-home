"""Tests for QualityAnalyzer."""

import tempfile
import os
import pytest
from .analyzer import QualityAnalyzer


def create_temp_file(content: str) -> str:
    """Helper to create a temporary Python file with given content.

    Args:
        content: Python code to write to file

    Returns:
        Path to temporary file
    """
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    except Exception:
        os.close(fd)
        raise


def test_quality_analyzer_perfect_code():
    """Test quality analysis on perfectly formatted code."""
    code = '''"""Example module."""


def hello_world():
    """Return a greeting."""
    return "Hello, world!"


def add_numbers(a, b):
    """Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b
'''
    test_file = create_temp_file(code)

    try:
        analyzer = QualityAnalyzer()
        score = analyzer.analyze([test_file])

        assert score >= 90, f"Expected score >= 90 for perfect code, got {score}"
        assert score <= 100, f"Score should not exceed 100, got {score}"
    finally:
        os.unlink(test_file)


def test_quality_analyzer_messy_code():
    """Test quality analysis on poorly formatted code."""
    code = '''def x():pass
import os;import sys
a=1+2+3+4
'''
    test_file = create_temp_file(code)

    try:
        analyzer = QualityAnalyzer()
        score = analyzer.analyze([test_file])

        assert score < 70, f"Expected score < 70 for messy code, got {score}"
        assert score >= 0, f"Score should not be negative, got {score}"
    finally:
        os.unlink(test_file)


def test_quality_analyzer_empty_file_list():
    """Test quality analysis with empty file list."""
    analyzer = QualityAnalyzer()
    score = analyzer.analyze([])

    # Empty file list should return a default score (100 or 0)
    assert score == 100, f"Expected 100 for empty file list, got {score}"


def test_quality_analyzer_nonexistent_file():
    """Test quality analysis with nonexistent file."""
    analyzer = QualityAnalyzer()
    score = analyzer.analyze(["/tmp/nonexistent_file_12345.py"])

    # Should handle gracefully and return low score or 0
    assert score >= 0, f"Score should not be negative, got {score}"
    assert score <= 100, f"Score should not exceed 100, got {score}"


def test_quality_analyzer_multiple_files():
    """Test quality analysis with multiple files."""
    # One good file, one bad file
    good_code = '''"""Good module."""


def good_function():
    """A well-formatted function."""
    return True
'''
    bad_code = '''def bad():pass
'''

    good_file = create_temp_file(good_code)
    bad_file = create_temp_file(bad_code)

    try:
        analyzer = QualityAnalyzer()
        score = analyzer.analyze([good_file, bad_file])

        # Score should be somewhere in the middle (average of good and bad)
        assert score >= 30, f"Expected score >= 30 for mixed quality, got {score}"
        assert score <= 95, f"Expected score <= 95 for mixed quality, got {score}"
    finally:
        os.unlink(good_file)
        os.unlink(bad_file)
