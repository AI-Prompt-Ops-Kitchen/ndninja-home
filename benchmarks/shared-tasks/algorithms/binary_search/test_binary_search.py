"""Test cases for binary search"""

import pytest


def test_found_middle():
    """Test finding element in middle"""
    from binary_search import binary_search
    assert binary_search([1, 3, 5, 7, 9], 5) == 2


def test_found_start():
    """Test finding element at start"""
    from binary_search import binary_search
    assert binary_search([1, 3, 5, 7, 9], 1) == 0


def test_found_end():
    """Test finding element at end"""
    from binary_search import binary_search
    assert binary_search([1, 3, 5, 7, 9], 9) == 4


def test_not_found():
    """Test element not in list"""
    from binary_search import binary_search
    assert binary_search([1, 3, 5, 7, 9], 4) == -1


def test_empty_list():
    """Test with empty list"""
    from binary_search import binary_search
    assert binary_search([], 5) == -1


def test_single_element_found():
    """Test single element - found"""
    from binary_search import binary_search
    assert binary_search([5], 5) == 0


def test_single_element_not_found():
    """Test single element - not found"""
    from binary_search import binary_search
    assert binary_search([5], 3) == -1


def test_large_list():
    """Test with large list"""
    from binary_search import binary_search
    arr = list(range(0, 10000, 2))  # Even numbers 0 to 9998
    assert binary_search(arr, 5000) == 2500
    assert binary_search(arr, 5001) == -1
