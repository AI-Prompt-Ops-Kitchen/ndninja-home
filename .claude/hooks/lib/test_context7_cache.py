# .claude/hooks/lib/test_context7_cache.py
import pytest
from context7_cache import CacheManager
from context7_fingerprint import generate_fingerprint

@pytest.fixture
def cache_manager():
    """Create cache manager for testing."""
    return CacheManager(
        redis_host="127.0.0.1",
        redis_port=6379,
        redis_db=2,
        redis_password="8NsEZXThezZwCQe0nwjGMZErrWVLe666Yy4UMkFV6Z4=",
        pg_config={
            'host': 'localhost',
            'database': 'claude_memory',
            'user': 'claude_mcp',
            'password': 'REDACTED'
        }
    )

def test_cache_miss_flow(cache_manager):
    """Test full cache miss flow: Redis -> PostgreSQL -> None."""
    fingerprint = generate_fingerprint("testlib", "1", "test query")

    # Clear any existing cache
    cache_manager.invalidate(fingerprint)

    # Cache miss should return None
    result = cache_manager.get(fingerprint)
    assert result is None

def test_cache_hit_redis(cache_manager):
    """Test cache hit from Redis (fast path)."""
    fingerprint = generate_fingerprint("testlib", "1", "test query")
    content = {"docs": "test content", "examples": []}

    # Store in both tiers
    cache_manager.set(fingerprint, "testlib", "1", "test", content, None)

    # Should retrieve from Redis
    result = cache_manager.get(fingerprint)
    assert result is not None
    assert result['content'] == content

    # Cleanup
    cache_manager.invalidate(fingerprint)

def test_cache_fallback_to_postgres(cache_manager):
    """Test fallback to PostgreSQL when Redis entry missing."""
    fingerprint = generate_fingerprint("testlib", "1", "fallback query")
    content = {"docs": "fallback content"}

    # Store in both tiers
    cache_manager.set(fingerprint, "testlib", "1", "test", content, None)

    # Remove from Redis only to simulate miss
    cache_manager.redis.delete(f"context7:cache:{fingerprint}")

    # Should still retrieve from PostgreSQL
    result = cache_manager.get(fingerprint)
    assert result is not None
    assert result['content'] == content

    # Cleanup
    cache_manager.invalidate(fingerprint)

def test_usage_tracking(cache_manager):
    """Test query count and last_accessed tracking."""
    fingerprint = generate_fingerprint("testlib", "1", "tracking query")
    content = {"docs": "tracking test"}

    # Store once
    cache_manager.set(fingerprint, "testlib", "1", "test", content, None)

    # Access multiple times
    for _ in range(3):
        cache_manager.get(fingerprint)

    # Check query count increased
    stats = cache_manager.get_stats(fingerprint)
    assert stats is not None
    assert stats['query_count'] >= 3

    # Cleanup
    cache_manager.invalidate(fingerprint)
