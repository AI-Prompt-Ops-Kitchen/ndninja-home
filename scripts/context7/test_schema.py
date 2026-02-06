# scripts/context7/test_schema.py
import psycopg2
import pytest

def test_context7_tables_exist():
    """Verify all Context7 tables exist with correct structure."""
    conn = psycopg2.connect(
        host="localhost",
        database="claude_memory",
        user="claude_mcp",
        password="REDACTED"
    )
    cur = conn.cursor()

    # Check context7_cache table
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'context7_cache'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()

    expected_columns = [
        ('id', 'uuid'),
        ('fingerprint', 'character varying'),
        ('library_id', 'character varying'),
        ('library_version', 'character varying'),
        ('query_intent', 'character varying'),
        ('content', 'jsonb'),
        ('citations', 'jsonb'),
        ('query_count', 'integer'),
        ('last_accessed', 'timestamp without time zone'),
        ('created_at', 'timestamp without time zone')
    ]

    assert len(columns) == len(expected_columns), f"Expected {len(expected_columns)} columns, got {len(columns)}"

    # Check unique constraint on fingerprint
    cur.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'context7_cache' AND constraint_type = 'UNIQUE';
    """)
    constraints = cur.fetchall()
    assert len(constraints) > 0, "Missing UNIQUE constraint on fingerprint"

    conn.close()
