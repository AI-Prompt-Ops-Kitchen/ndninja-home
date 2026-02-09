"""Test PostgreSQL schema creation and views"""

import pytest
import psycopg2
import os


@pytest.fixture
def db_connection():
    """Connect to workspace database via Unix socket"""
    conn = psycopg2.connect(
        dbname="workspace",
        user=os.getenv("DB_USER", "ndninja")
    )
    yield conn
    conn.close()


def test_schema_tables_exist(db_connection):
    """Verify table was created"""
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'cli_agent_benchmark_results'
    """)
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == 'cli_agent_benchmark_results'


def test_schema_indexes_exist(db_connection):
    """Verify indexes were created"""
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'cli_agent_benchmark_results'
    """)
    indexes = [row[0] for row in cursor.fetchall()]

    assert 'idx_cli_agent_name' in indexes
    assert 'idx_cli_task_name' in indexes
    assert 'idx_cli_timestamp' in indexes
    assert 'idx_cli_run_id' in indexes


def test_schema_views_exist(db_connection):
    """Verify views were created"""
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_name IN ('cli_agent_comparison', 'cli_agent_strengths', 'cli_recent_benchmarks')
    """)
    views = [row[0] for row in cursor.fetchall()]

    assert 'cli_agent_comparison' in views
    assert 'cli_agent_strengths' in views
    assert 'cli_recent_benchmarks' in views


def test_insert_sample_result(db_connection):
    """Test inserting a sample benchmark result"""
    cursor = db_connection.cursor()

    cursor.execute("""
        INSERT INTO cli_agent_benchmark_results (
            task_name, task_category, task_difficulty,
            agent_name, agent_version,
            overall_score, correctness_score, speed_score, cost_score, autonomy_score, code_quality_score,
            wall_time_seconds, actual_cost_usd, budgeted_cost_usd,
            token_count_input, token_count_output,
            retries, tool_calls, error_recovered,
            tests_total, tests_passed, tests_failed,
            recording_path, generated_files,
            benchmark_run_id
        ) VALUES (
            'quicksort', 'algorithms', 'medium',
            'test-agent', '1.0.0',
            95.5, 100.0, 90.0, 95.0, 98.0, 85.0,
            42.5, 0.05, 0.05,
            1000, 500,
            0, 15, false,
            10, 10, 0,
            '/path/to/recording.cast', '["quicksort.py"]'::jsonb,
            '00000000-0000-0000-0000-000000000000'::uuid
        )
        RETURNING id
    """)

    result_id = cursor.fetchone()[0]
    assert result_id is not None

    # Clean up test data
    cursor.execute("DELETE FROM cli_agent_benchmark_results WHERE id = %s", (result_id,))
    db_connection.commit()
