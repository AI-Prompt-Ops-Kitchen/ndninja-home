# .claude/hooks/lib/test_context7_redis.py
import pytest
from context7_redis import RedisClient

# Redis password from /etc/redis/redis.conf
REDIS_PASSWORD = "8NsEZXThezZwCQe0nwjGMZErrWVLe666Yy4UMkFV6Z4="

def test_redis_connect():
    """Test Redis connection with auth."""
    client = RedisClient(
        host="localhost",
        port=6379,
        db=2,
        password=REDIS_PASSWORD
    )

    # Should connect without error
    assert client.ping() == True, "Redis ping failed"

    # Test basic operations
    client.set("test_key", "test_value", ttl=60)
    assert client.get("test_key") == "test_value"

    client.delete("test_key")
    assert client.get("test_key") is None

def test_redis_unavailable_graceful():
    """Test graceful handling when Redis unavailable."""
    client = RedisClient(host="invalid.host", port=6379, db=2)

    # Should not raise, just return None
    assert client.ping() == False
    assert client.get("any_key") is None
    assert client.set("key", "value") == False
