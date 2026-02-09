import pytest
import psycopg2
from database import DatabaseClient
from adapters.base import BenchmarkResult
from test_harness import HarnessResult
from scoring import Score


@pytest.fixture
def db_client():
    """Create database client"""
    client = DatabaseClient(
        host="localhost",
        database="workspace",
        user="ndninja"
    )
    yield client


def test_database_client_init(db_client):
    """Test DatabaseClient initialization"""
    assert db_client is not None


def test_save_benchmark_result(db_client):
    """Test saving benchmark result to database"""
    benchmark_result = BenchmarkResult(
        success=True,
        wall_time=65.5,
        token_count={"input": 1000, "output": 500},
        cost=0.03,
        retries=0,
        tool_calls=5,
        error_recovered=True,
        generated_files=["quicksort.py"],
        logs="Test logs",
        recording_path="/path/to/recording.cast"
    )

    test_result = HarnessResult(
        passed=10,
        failed=0,
        total=10,
        pass_rate=100.0,
        output="All tests passed",
        exit_code=0
    )

    score = Score(
        speed_score=23.5,
        correctness_score=40.0,
        cost_score=15.0,
        autonomy_score=12.0,
        quality_score=8.0,
        total_score=98.5
    )

    result_id = db_client.save_result(
        agent_name="mock",
        task_name="quicksort",
        task_category="algorithms",
        benchmark_result=benchmark_result,
        test_result=test_result,
        score=score
    )

    assert result_id is not None
    assert isinstance(result_id, int)


def test_get_recent_results(db_client):
    """Test retrieving recent results"""
    results = db_client.get_recent_results(limit=5)

    assert isinstance(results, list)
    assert len(results) <= 5

    if len(results) > 0:
        result = results[0]
        assert "agent_name" in result
        assert "task_name" in result
        assert "overall_score" in result


def test_get_agent_comparison(db_client):
    """Test getting agent comparison view"""
    comparison = db_client.get_agent_comparison()

    assert isinstance(comparison, list)

    if len(comparison) > 0:
        row = comparison[0]
        assert "agent_name" in row
        assert "avg_overall" in row
