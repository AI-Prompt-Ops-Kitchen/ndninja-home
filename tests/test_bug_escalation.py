import pytest
from tools_db.tools.bug_escalation import BugEscalation
from datetime import datetime


def test_bug_escalation_records_issue():
    """Should record and escalate bugs"""
    escalator = BugEscalation(test_mode=True)

    escalator.report_bug(
        bug_id="bug_vision_prompt_001",
        error_type="OutputFormatError",
        error_message="Vision model produced narrative instead of keywords",
        stack_trace="...",
        user_impact="critical"
    )

    bugs = escalator.get_escalations(status="pending")
    assert len(bugs) == 1
    assert bugs[0]["user_impact"] == "critical"


def test_bug_escalation_determines_priority():
    """Should automatically determine escalation priority"""
    escalator = BugEscalation(test_mode=True)

    priority = escalator.calculate_priority(
        error_type="DatabaseConnectionError",
        user_impact="high",
        frequency=10,
        deadline_hours=2
    )

    assert priority in ["low", "medium", "high", "critical"]
    # High impact + soon deadline should be critical or high
    assert priority in ["high", "critical"]


def test_bug_escalation_tracks_resolution():
    """Should track bug resolution"""
    escalator = BugEscalation(test_mode=True)

    bug_id = "bug_resolution_test"
    escalator.report_bug(
        bug_id=bug_id,
        error_type="TestError",
        error_message="Test error",
        user_impact="low"
    )

    escalator.mark_resolved(bug_id, resolution="Fixed in commit abc123")

    resolved = escalator.get_escalations(status="resolved")
    assert any(b["bug_id"] == bug_id for b in resolved)
