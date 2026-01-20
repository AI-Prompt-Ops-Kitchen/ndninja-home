import pytest
from tools_db.models import AuditTrailEvent, VisionCacheEntry
from datetime import datetime


def test_audit_trail_event_creation():
    """Should create and record audit events"""
    event = AuditTrailEvent(
        event_type="permission_changed",
        entity_type="permission",
        entity_id="perm_123",
        old_value={"status": "denied"},
        new_value={"status": "approved"},
        user="test_user",
        context={"reason": "user request"}
    )

    assert event.event_type == "permission_changed"
    assert event.entity_id == "perm_123"
    assert event.old_value["status"] == "denied"


def test_vision_cache_entry_with_expiry():
    """Should calculate and track cache expiry"""
    entry = VisionCacheEntry(
        image_hash="abc123",
        extracted_data={"keywords": ["landscape", "sunset"]},
        confidence_score=0.95,
        model_version="v1.0",
        ttl_hours=24
    )

    assert entry.confidence_score == 0.95
    assert entry.expires_at is not None
