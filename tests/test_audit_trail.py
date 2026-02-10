import pytest
from tools_db.tools.audit_trail import AuditTrail
from datetime import datetime, timedelta


def test_audit_trail_records_event():
    """Should record audit trail events"""
    trail = AuditTrail(test_mode=True)

    trail.record_event(
        event_type="permission_changed",
        entity_type="permission",
        entity_id="perm_bash",
        old_value={"status": "pending"},
        new_value={"status": "approved"},
        user="test_user",
        context={"reason": "development"}
    )

    events = trail.get_events(entity_type="permission")
    assert len(events) == 1
    assert events[0]["entity_id"] == "perm_bash"


def test_audit_trail_supports_rollback():
    """Should support rolling back to previous state"""
    trail = AuditTrail(test_mode=True)

    # Record multiple changes
    trail.record_event(
        event_type="config_changed",
        entity_type="config",
        entity_id="setting_1",
        old_value={"value": "old"},
        new_value={"value": "new1"},
        user="user1"
    )

    trail.record_event(
        event_type="config_changed",
        entity_type="config",
        entity_id="setting_1",
        old_value={"value": "new1"},
        new_value={"value": "new2"},
        user="user2"
    )

    # Get rollback info
    rollback = trail.get_rollback_info("config", "setting_1")
    assert rollback is not None
    assert len(rollback) >= 2
