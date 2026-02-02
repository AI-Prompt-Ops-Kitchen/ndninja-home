"""Test suite for quicksort implementation"""

import pytest
import time


def test_import_quicksort():
    """Test that quicksort module and function can be imported"""
    from quicksort import quicksort
    assert callable(quicksort)


def test_empty_list():
    """Test quicksort with empty list"""
    from quicksort import quicksort
    assert quicksort([]) == []


def test_single_element():
    """Test quicksort with single element"""
    from quicksort import quicksort
    assert quicksort([42]) == [42]


def test_two_elements():
    """Test quicksort with two elements"""
    from quicksort import quicksort
    assert quicksort([2, 1]) == [1, 2]
    assert quicksort([1, 2]) == [1, 2]


def test_already_sorted():
    """Test quicksort with already sorted list"""
    from quicksort import quicksort
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]


def test_reverse_sorted():
    """Test quicksort with reverse-sorted list"""
    from quicksort import quicksort
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]


def test_duplicates():
    """Test quicksort with duplicate elements"""
    from quicksort import quicksort
    assert quicksort([3, 1, 3, 2, 1]) == [1, 1, 2, 3, 3]


def test_negative_numbers():
    """Test quicksort with negative numbers"""
    from quicksort import quicksort
    assert quicksort([-5, 3, -1, 7, 0]) == [-5, -1, 0, 3, 7]


def test_random_list():
    """Test quicksort with random unsorted list"""
    from quicksort import quicksort
    arr = [64, 34, 25, 12, 22, 11, 90]
    expected = [11, 12, 22, 25, 34, 64, 90]
    assert quicksort(arr) == expected


def test_immutability():
    """Test that input list is not modified"""
    from quicksort import quicksort
    original = [3, 1, 2]
    quicksort(original)
    assert original == [3, 1, 2], "Input list should not be modified"


def test_performance():
    """Test quicksort performance with large list"""
    from quicksort import quicksort
    import random

    # Generate large random list
    arr = [random.randint(0, 10000) for _ in range(10000)]
    expected = sorted(arr)

    start = time.time()
    result = quicksort(arr)
    duration = time.time() - start

    assert result == expected, "Large list should be sorted correctly"
    assert duration < 5.0, f"Quicksort took {duration:.2f}s, should be under 5s"


def test_strings():
    """Test quicksort with strings"""
    from quicksort import quicksort
    assert quicksort(["banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]
