import pytest
from tools_db.database import Database
from tools_db.tools.automation_hub import AutomationHub
from tools_db.models import AutomationEvent
from datetime import datetime, timezone
import sqlite3

def test_automation_events_table_created():
    """Test that automation_events table is created with correct schema"""
    db = Database("sqlite:///:memory:")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='automation_events'
        """)
        assert cursor.fetchone() is not None, "automation_events table not found"

        # Check columns exist
        cursor.execute("PRAGMA table_info(automation_events)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = {
            'id': 'INTEGER',
            'event_type': 'TEXT',
            'project_id': 'TEXT',
            'status': 'TEXT',
            'evidence': 'TEXT',
            'detected_from': 'TEXT',
            'created_at': 'DATETIME',
            'resolved_at': 'DATETIME',
            'metadata': 'TEXT'
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Column {col_name} not found"

def test_automation_events_indexes_created():
    """Test that indexes are created for performance"""
    db = Database("sqlite:///:memory:")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='automation_events'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'ix_automation_event_type_project',
            'ix_automation_created_at',
            'ix_automation_status'
        ]

        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} not found"


def test_automation_hub_store_event():
    """Test storing AutomationEvent to database"""
    db = Database("sqlite:///:memory:")
    hub = AutomationHub(db=db)

    event = AutomationEvent(
        event_type="production_check",
        project_id="test-project",
        status="success",
        evidence={"checks": 6, "passed": 6},
        detected_from="skill"
    )

    stored_id = hub.store_event(event)
    assert stored_id is not None
    assert isinstance(stored_id, int)

def test_automation_hub_get_project_status():
    """Test retrieving project status"""
    db = Database("sqlite:///:memory:")
    hub = AutomationHub(db=db)

    event = AutomationEvent(
        event_type="production_check",
        project_id="test-project",
        status="success",
        evidence={"checks": 6},
        detected_from="skill"
    )
    hub.store_event(event)

    status = hub.get_project_status("test-project")
    assert status is not None
    assert status["event_type"] == "production_check"
    assert status["status"] == "success"

def test_automation_hub_list_events_by_type():
    """Test listing events by type"""
    db = Database("sqlite:///:memory:")
    hub = AutomationHub(db=db)

    # Store multiple events
    for i in range(3):
        event = AutomationEvent(
            event_type="action_item_completed",
            project_id=f"project-{i}",
            status="success",
            evidence={"todo_id": f"item-{i}"},
            detected_from="hook"
        )
        hub.store_event(event)

    events = hub.get_events_by_type("action_item_completed")
    assert len(events) == 3
    assert all(e["event_type"] == "action_item_completed" for e in events)
