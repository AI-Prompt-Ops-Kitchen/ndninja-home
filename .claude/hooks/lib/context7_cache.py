# .claude/hooks/lib/context7_cache.py
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from context7_redis import RedisClient

logger = logging.getLogger(__name__)


class CacheManager:
    """Two-tier cache manager (Redis + PostgreSQL).

    Fast path: Redis (hot cache, 24h TTL)
    Warm path: PostgreSQL (persistent, unlimited)
    """

    def __init__(self, redis_host: str, redis_port: int, redis_db: int,
                 pg_config: dict, redis_password: Optional[str] = None):
        self.redis = RedisClient(redis_host, redis_port, redis_db, redis_password)
        self.pg_config = pg_config

    def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get cached content (Redis -> PostgreSQL -> None).

        Returns: {'content': dict, 'citations': dict, 'query_count': int, ...}
        """
        # Fast path: Check Redis
        cache_key = f"context7:cache:{fingerprint}"
        cached = self.redis.get_json(cache_key)
        if cached:
            logger.debug(f"Cache HIT (Redis): {fingerprint}")
            self._log_query(fingerprint, None, True, 0)
            self._update_access_time(fingerprint)
            return cached

        # Warm path: Check PostgreSQL
        cached = self._get_postgres(fingerprint)
        if cached:
            logger.debug(f"Cache HIT (PostgreSQL): {fingerprint}")
            # Promote to Redis for next access
            self.redis.set_json(cache_key, cached, ttl=86400)
            self._log_query(fingerprint, None, True, 0)
            self._update_access_time(fingerprint)
            return cached

        # Cache miss
        logger.debug(f"Cache MISS: {fingerprint}")
        self._log_query(fingerprint, None, False, 0)
        return None

    def set(self, fingerprint: str, library_id: str, library_version: str,
            query_intent: str, content: dict, citations: Optional[dict]) -> bool:
        """Store content in both Redis and PostgreSQL."""
        data = {
            'content': content,
            'citations': citations,
            'query_count': 1,
            'last_accessed': datetime.now().isoformat()
        }

        # Store in Redis
        cache_key = f"context7:cache:{fingerprint}"
        self.redis.set_json(cache_key, data, ttl=86400)

        # Store in PostgreSQL
        return self._store_postgres(fingerprint, library_id, library_version,
                                    query_intent, content, citations)

    def invalidate(self, fingerprint: str) -> bool:
        """Remove entry from both cache tiers."""
        cache_key = f"context7:cache:{fingerprint}"
        self.redis.delete(cache_key)

        try:
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM context7_cache WHERE fingerprint = %s;",
                                (fingerprint,))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Invalidate failed: {e}")
            return False

    def get_stats(self, fingerprint: str) -> Optional[dict]:
        """Get cache statistics for fingerprint."""
        try:
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT query_count, last_accessed, created_at
                        FROM context7_cache WHERE fingerprint = %s;
                    """, (fingerprint,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return None

    def _get_postgres(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get cached content from PostgreSQL."""
        try:
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT content, citations, query_count, last_accessed
                        FROM context7_cache WHERE fingerprint = %s;
                    """, (fingerprint,))
                    row = cur.fetchone()
                    if row:
                        result = dict(row)
                        # Ensure content is dict, not string
                        if isinstance(result.get('content'), str):
                            result['content'] = json.loads(result['content'])
                        if isinstance(result.get('citations'), str):
                            result['citations'] = json.loads(result['citations'])
                        # Serialize datetime for JSON compatibility
                        if result.get('last_accessed'):
                            result['last_accessed'] = result['last_accessed'].isoformat()
                        return result
                    return None
        except Exception as e:
            logger.error(f"PostgreSQL GET failed: {e}")
            return None

    def _store_postgres(self, fingerprint: str, library_id: str, library_version: str,
                        query_intent: str, content: dict, citations: Optional[dict]) -> bool:
        """Store content in PostgreSQL with upsert."""
        try:
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO context7_cache
                        (fingerprint, library_id, library_version, query_intent, content, citations)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fingerprint) DO UPDATE SET
                            content = EXCLUDED.content,
                            citations = EXCLUDED.citations,
                            query_count = context7_cache.query_count + 1,
                            last_accessed = NOW();
                    """, (fingerprint, library_id, library_version, query_intent,
                          json.dumps(content),
                          json.dumps(citations) if citations else None))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL STORE failed: {e}")
            return False

    def _update_access_time(self, fingerprint: str):
        """Update last_accessed timestamp and increment query_count."""
        try:
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE context7_cache
                        SET last_accessed = NOW(), query_count = query_count + 1
                        WHERE fingerprint = %s;
                    """, (fingerprint,))
                    conn.commit()
        except Exception as e:
            logger.error(f"Update access time failed: {e}")

    def _log_query(self, fingerprint: str, original_query: Optional[str],
                   cache_hit: bool, response_time_ms: int):
        """Log query to analytics table."""
        try:
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO context7_query_log
                        (fingerprint, original_query, cache_hit, response_time_ms)
                        VALUES (%s, %s, %s, %s);
                    """, (fingerprint, original_query, cache_hit, response_time_ms))
                    conn.commit()
        except Exception as e:
            logger.error(f"Log query failed: {e}")

    def track_usage(self, project_path: str, library_id: str,
                    library_version: str, detection_source: str = 'manifest'):
        """Record or increment library usage for a project."""
        try:
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO context7_project_libraries
                        (project_path, library_id, library_version, detection_source, usage_count, last_used)
                        VALUES (%s, %s, %s, %s, 1, NOW())
                        ON CONFLICT (project_path, library_id) DO UPDATE SET
                            usage_count = context7_project_libraries.usage_count + 1,
                            last_used = NOW(),
                            library_version = COALESCE(EXCLUDED.library_version, context7_project_libraries.library_version);
                    """, (project_path, library_id, library_version, detection_source))
                    conn.commit()
        except Exception as e:
            logger.error(f"Track usage failed: {e}")
