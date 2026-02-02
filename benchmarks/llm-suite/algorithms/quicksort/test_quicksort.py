"""Test cases for quicksort implementation"""

import pytest
import sys
from pathlib import Path

# Import generated code
try:
    from .generated_code import quicksort
except ImportError:
    # Load from .generated_code.py file
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generated",
        Path(__file__).parent / ".generated_code.py"
    )
    generated = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generated)
    quicksort = generated.quicksort


def test_empty_list():
    """Test with empty list"""
    assert quicksort([]) == []


def test_single_element():
    """Test with single element"""
    assert quicksort([5]) == [5]


def test_sorted_list():
    """Test with already sorted list"""
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]


def test_reverse_sorted():
    """Test with reverse sorted list"""
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]


def test_duplicates():
    """Test with duplicate elements"""
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6, 5]) == [1, 1, 2, 3, 4, 5, 5, 6, 9]


def test_negative_numbers():
    """Test with negative numbers"""
    assert quicksort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1, -1]


def test_mixed_positive_negative():
    """Test with mixed positive and negative numbers"""
    assert quicksort([3, -1, 4, -5, 2, 0]) == [-5, -1, 0, 2, 3, 4]


def test_large_list():
    """Test with larger list"""
    import random
    random.seed(42)
    arr = [random.randint(-100, 100) for _ in range(100)]
    result = quicksort(arr)
    assert result == sorted(arr)


def test_does_not_modify_original():
    """Test that original list is not modified"""
    original = [3, 1, 4, 1, 5]
    copy_of_original = original.copy()
    quicksort(original)
    assert original == copy_of_original
