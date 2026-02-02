"""Reference implementation of quicksort"""


def quicksort(arr: list) -> list:
    """
    Sort a list using the quicksort algorithm.

    Args:
        arr: List to sort

    Returns:
        New sorted list

    Time Complexity: O(n log n) average, O(n^2) worst case
    Space Complexity: O(n) for the output list
    """
    if len(arr) <= 1:
        return arr.copy()

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quicksort(left) + middle + quicksort(right)
