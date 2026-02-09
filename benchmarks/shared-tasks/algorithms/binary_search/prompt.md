Implement binary search in Python.

Requirements:
1. Function signature: def binary_search(arr: list, target: int) -> int
2. Input array is already sorted in ascending order
3. Return the index of the target if found, -1 if not found
4. Use iterative approach (not recursive)
5. Include type hints and docstring
6. Handle edge cases (empty list, target not in list)

Example:
>>> binary_search([1, 3, 5, 7, 9], 5)
2

>>> binary_search([1, 3, 5, 7, 9], 4)
-1

>>> binary_search([], 5)
-1

Time complexity should be O(log n).
