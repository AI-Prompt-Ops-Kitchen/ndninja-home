"""Test cases for binary search"""

import pytest
from pathlib import Path
import importlib.util


# Load generated code
spec = importlib.util.spec_from_file_location(
    "generated",
    Path(__file__).parent / ".generated_code.py"
)
if spec and spec.loader:
    generated = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generated)
    binary_search = generated.binary_search
else:
    raise ImportError("Could not load generated code")


def test_found_middle():
    """Test finding element in middle"""
    assert binary_search([1, 3, 5, 7, 9], 5) == 2


def test_found_start():
    """Test finding element at start"""
    assert binary_search([1, 3, 5, 7, 9], 1) == 0


def test_found_end():
    """Test finding element at end"""
    assert binary_search([1, 3, 5, 7, 9], 9) == 4


def test_not_found():
    """Test element not in list"""
    assert binary_search([1, 3, 5, 7, 9], 4) == -1


def test_empty_list():
    """Test with empty list"""
    assert binary_search([], 5) == -1


def test_single_element_found():
    """Test single element - found"""
    assert binary_search([5], 5) == 0


def test_single_element_not_found():
    """Test single element - not found"""
    assert binary_search([5], 3) == -1


def test_large_list():
    """Test with large list"""
    arr = list(range(0, 10000, 2))  # Even numbers 0 to 9998
    assert binary_search(arr, 5000) == 2500
    assert binary_search(arr, 5001) == -1
