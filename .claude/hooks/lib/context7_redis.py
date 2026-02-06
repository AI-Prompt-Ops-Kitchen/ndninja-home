# .claude/hooks/lib/context7_redis.py
import redis
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client with graceful degradation."""

    def __init__(self, host: str, port: int, db: int, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None
        self._connect()

    def _connect(self):
        """Establish Redis connection."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=2
            )
            self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port} DB{self.db}")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            self._client = None

    def ping(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        try:
            return self._client.ping()
        except:
            return False

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self._client:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = 86400) -> bool:
        """Set value in Redis with TTL (default 24h)."""
        if not self._client:
            return False
        try:
            self._client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except:
            return False

    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return None
        return None

    def set_json(self, key: str, value: dict, ttl: int = 86400) -> bool:
        """Set JSON value in Redis."""
        try:
            return self.set(key, json.dumps(value), ttl)
        except:
            return False
