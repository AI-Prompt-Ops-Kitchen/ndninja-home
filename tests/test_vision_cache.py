import pytest
from tools_db.tools.vision_cache import VisionCache
from tools_db.models import VisionCacheEntry
import hashlib
import json
from datetime import datetime, timedelta


def test_vision_cache_stores_and_retrieves():
    """Should store and retrieve cached vision analysis"""
    cache = VisionCache(test_mode=True)

    image_hash = hashlib.sha256(b"test_image").hexdigest()
    data = {"keywords": ["sunset", "landscape"], "style": "photography"}

    cache.store(
        image_hash=image_hash,
        extracted_data=data,
        confidence_score=0.92,
        model_version="gpt-vision-1.0"
    )

    result = cache.get(image_hash)
    assert result is not None
    assert result["extracted_data"]["keywords"] == ["sunset", "landscape"]


def test_vision_cache_respects_ttl():
    """Should respect TTL and mark expired entries"""
    cache = VisionCache(test_mode=True)

    image_hash = "expired_hash"
    cache.store(
        image_hash=image_hash,
        extracted_data={"keywords": []},
        confidence_score=0.8,
        model_version="v1.0",
        ttl_hours=0  # Immediate expiration
    )

    result = cache.get(image_hash)
    # Should return None or mark as expired
    assert result is None or result.get("expired") is True


def test_vision_cache_tracks_hits():
    """Should track cache hits for analytics"""
    cache = VisionCache(test_mode=True)

    image_hash = "popular_hash"
    cache.store(
        image_hash=image_hash,
        extracted_data={"keywords": ["test"]},
        confidence_score=0.9,
        model_version="v1.0"
    )

    for _ in range(4):
        cache.get(image_hash)  # Record hits

    stats = cache.get_stats(image_hash)
    assert stats["hit_count"] >= 4  # At least 4 hits
