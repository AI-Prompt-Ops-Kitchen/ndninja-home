"""Test cases for LRU Cache"""

import pytest


def test_basic_operations():
    """Test basic get and put"""
    from lru_cache import LRUCache
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)  # Evicts key 2
    assert cache.get(2) == -1
    cache.put(4, 4)  # Evicts key 1
    assert cache.get(1) == -1
    assert cache.get(3) == 3
    assert cache.get(4) == 4


def test_capacity_one():
    """Test with capacity of 1 - Common edge case"""
    from lru_cache import LRUCache
    cache = LRUCache(1)
    cache.put(1, 1)
    assert cache.get(1) == 1
    cache.put(2, 2)  # Should evict 1
    assert cache.get(1) == -1
    assert cache.get(2) == 2


def test_update_existing():
    """Test updating existing key doesn't evict"""
    from lru_cache import LRUCache
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.put(1, 10)  # Update, not insert
    cache.put(3, 3)   # Should evict 2, not 1
    assert cache.get(1) == 10
    assert cache.get(2) == -1
    assert cache.get(3) == 3


def test_get_updates_recency():
    """Test that get() marks item as recently used"""
    from lru_cache import LRUCache
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.get(1)      # Access 1, making it most recent
    cache.put(3, 3)   # Should evict 2
    assert cache.get(1) == 1
    assert cache.get(2) == -1


def test_repeated_access():
    """Test repeatedly accessing same key"""
    from lru_cache import LRUCache
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.get(1)
    cache.get(1)
    cache.get(1)
    cache.put(3, 3)  # Should evict 2
    assert cache.get(1) == 1
    assert cache.get(2) == -1


def test_empty_cache():
    """Test get on empty cache"""
    from lru_cache import LRUCache
    cache = LRUCache(5)
    assert cache.get(1) == -1


def test_larger_capacity():
    """Test with larger capacity"""
    from lru_cache import LRUCache
    cache = LRUCache(5)
    for i in range(1, 6):
        cache.put(i, i * 10)

    # All should be present
    for i in range(1, 6):
        assert cache.get(i) == i * 10

    # Add one more - should evict 1 (least recently used after gets)
    cache.put(6, 60)
    assert cache.get(1) == -1
    assert cache.get(6) == 60
