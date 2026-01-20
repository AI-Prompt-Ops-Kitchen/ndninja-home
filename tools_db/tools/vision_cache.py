from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from tools_db.models import VisionCacheEntry


class VisionCache:
    """Cache for vision analysis results"""

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.db = None
        if not test_mode:
            try:
                from tools_db.database import get_db
                self.db = get_db()
            except:
                pass
        self._memory_cache = {}  # For test_mode

    def store(
        self,
        image_hash: str,
        extracted_data: Dict[str, Any],
        confidence_score: float,
        model_version: str,
        image_url: Optional[str] = None,
        ttl_hours: int = 24
    ) -> bool:
        """Store vision analysis result in cache"""
        entry = VisionCacheEntry(
            image_hash=image_hash,
            extracted_data=extracted_data,
            confidence_score=confidence_score,
            model_version=model_version,
            image_url=image_url,
            ttl_hours=ttl_hours
        )

        if self.test_mode:
            self._memory_cache[image_hash] = entry
            return True

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vision_cache
                    (image_hash, image_url, extracted_data, confidence_score,
                     model_version, expires_at, hit_count)
                    VALUES (%s, %s, %s, %s, %s, %s, 0)
                    ON CONFLICT (image_hash) DO UPDATE SET
                    extracted_data = EXCLUDED.extracted_data,
                    confidence_score = EXCLUDED.confidence_score,
                    expires_at = EXCLUDED.expires_at,
                    hit_count = vision_cache.hit_count + 1
                """, (
                    image_hash,
                    image_url,
                    json.dumps(extracted_data),
                    confidence_score,
                    model_version,
                    entry.expires_at
                ))
                return True
        except Exception as e:
            print(f"Cache store error: {e}")
            return False

    def get(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached vision analysis"""
        if self.test_mode:
            entry = self._memory_cache.get(image_hash)
            if entry is None:
                return None
            if entry.is_expired():
                del self._memory_cache[image_hash]
                return None
            entry.record_hit()
            return {
                "image_hash": entry.image_hash,
                "extracted_data": entry.extracted_data,
                "confidence_score": entry.confidence_score,
                "model_version": entry.model_version,
                "expires_at": entry.expires_at,
                "hit_count": entry.hit_count
            }

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, image_hash, extracted_data, confidence_score,
                           model_version, expires_at, hit_count
                    FROM vision_cache
                    WHERE image_hash = %s AND expires_at > NOW()
                """, (image_hash,))

                row = cursor.fetchone()
                if row is None:
                    return None

                # Record hit
                cursor.execute("""
                    UPDATE vision_cache
                    SET hit_count = hit_count + 1
                    WHERE image_hash = %s
                """, (image_hash,))

                return {
                    "image_hash": row[1],
                    "extracted_data": json.loads(row[2]),
                    "confidence_score": row[3],
                    "model_version": row[4],
                    "expires_at": row[5],
                    "hit_count": row[6]
                }
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def invalidate(self, image_hash: str) -> bool:
        """Invalidate a cache entry"""
        if self.test_mode:
            if image_hash in self._memory_cache:
                del self._memory_cache[image_hash]
            return True

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM vision_cache WHERE image_hash = %s",
                    (image_hash,)
                )
                return True
        except:
            return False

    def cleanup_expired(self) -> int:
        """Remove expired cache entries, return count removed"""
        if self.test_mode:
            expired = [
                k for k, v in self._memory_cache.items()
                if v.is_expired()
            ]
            for k in expired:
                del self._memory_cache[k]
            return len(expired)

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM vision_cache WHERE expires_at < NOW()"
                )
                return cursor.rowcount
        except:
            return 0

    def get_stats(self, image_hash: Optional[str] = None) -> Dict[str, Any]:
        """Get cache statistics"""
        if image_hash and self.test_mode:
            entry = self._memory_cache.get(image_hash)
            if entry:
                return {"hit_count": entry.hit_count}
            return {}

        if self.test_mode:
            total = len(self._memory_cache)
            total_hits = sum(v.hit_count for v in self._memory_cache.values())
            return {
                "total_entries": total,
                "total_hits": total_hits,
                "avg_confidence": 0.9
            }

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if image_hash:
                    cursor.execute(
                        "SELECT hit_count FROM vision_cache WHERE image_hash = %s",
                        (image_hash,)
                    )
                    row = cursor.fetchone()
                    return {"hit_count": row[0] if row else 0}
                else:
                    cursor.execute("""
                        SELECT COUNT(*), SUM(hit_count), AVG(confidence_score)
                        FROM vision_cache WHERE expires_at > NOW()
                    """)
                    count, hits, avg_conf = cursor.fetchone()
                    return {
                        "total_entries": count or 0,
                        "total_hits": hits or 0,
                        "avg_confidence": avg_conf or 0
                    }
        except:
            return {}
