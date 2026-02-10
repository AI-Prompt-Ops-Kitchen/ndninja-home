import pytest
from datetime import datetime, timezone
from tools_db.models import AutomationEvent

def test_automation_event_creation():
    """Test AutomationEvent dataclass creation and defaults"""
    event = AutomationEvent(
        event_type="production_check",
        project_id="my-project",
        status="success",
        evidence={"checks": ["tests", "security"]},
        detected_from="skill"
    )

    assert event.event_type == "production_check"
    assert event.project_id == "my-project"
    assert event.status == "success"
    assert event.detected_from == "skill"
    assert event.created_at is not None
    assert isinstance(event.created_at, datetime)
    assert event.resolved_at is None

def test_automation_event_resolve():
    """Test marking event as resolved"""
    event = AutomationEvent(
        event_type="n8n_fallback_routed",
        project_id="content-pipeline",
        status="success",
        evidence={"method": "celery"},
        detected_from="hook"
    )

    event.resolved_at = datetime.now(timezone.utc)
    assert event.resolved_at is not None
