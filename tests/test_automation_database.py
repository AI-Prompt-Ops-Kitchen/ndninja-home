import pytest
from tools_db.database import Database
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
