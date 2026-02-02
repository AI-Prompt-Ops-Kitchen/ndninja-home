Implement an LRU (Least Recently Used) Cache in Python.

Requirements:
1. Class name: LRUCache
2. Constructor: __init__(self, capacity: int)
3. Methods:
   - get(self, key: int) -> int: Return value if key exists, -1 otherwise
   - put(self, key: int, value: int) -> None: Insert or update value
4. When capacity is reached, evict the least recently used item
5. Both get() and put() should update recency (move item to most recent)
6. Use OrderedDict or dict to implement
7. Include type hints and docstrings

Example usage:
>>> cache = LRUCache(capacity=2)
>>> cache.put(1, 1)
>>> cache.put(2, 2)
>>> cache.get(1)
1
>>> cache.put(3, 3)  # Evicts key 2
>>> cache.get(2)
-1
>>> cache.put(4, 4)  # Evicts key 1
>>> cache.get(1)
-1
>>> cache.get(3)
3
>>> cache.get(4)
4

Important edge cases:
- Updating an existing key should not evict anything
- Getting a key should mark it as recently used
- Capacity of 1 should work correctly