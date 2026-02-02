import pytest
from scoring import ScoringEngine, Score
from adapters.base import BenchmarkResult
from test_harness import TestResult


def test_scoring_engine_init():
    """Test ScoringEngine initialization"""
    engine = ScoringEngine()
    assert engine is not None


def test_calculate_speed_score():
    """Test speed score calculation"""
    engine = ScoringEngine()

    # Fast completion (under budget)
    score = engine.calculate_speed_score(
        actual_time=60.0,
        estimated_time=120.0
    )
    assert score > 20.0  # Should get high score

    # Slow completion (over budget)
    score = engine.calculate_speed_score(
        actual_time=180.0,
        estimated_time=120.0
    )
    assert score < 15.0  # Should get penalty


def test_calculate_correctness_score():
    """Test correctness score calculation"""
    engine = ScoringEngine()

    # All tests pass
    test_result = TestResult(
        passed=10,
        failed=0,
        total=10,
        pass_rate=100.0,
        output="",
        exit_code=0
    )
    score = engine.calculate_correctness_score(test_result)
    assert score == 40.0  # Max correctness score

    # Half tests pass
    test_result = TestResult(
        passed=5,
        failed=5,
        total=10,
        pass_rate=50.0,
        output="",
        exit_code=1
    )
    score = engine.calculate_correctness_score(test_result)
    assert score == 20.0  # Half of max score


def test_calculate_cost_score():
    """Test cost score calculation"""
    engine = ScoringEngine()

    # Under budget
    score = engine.calculate_cost_score(
        actual_cost=0.02,
        budgeted_cost=0.05
    )
    assert score > 12.0

    # Over budget
    score = engine.calculate_cost_score(
        actual_cost=0.10,
        budgeted_cost=0.05
    )
    assert score < 10.0


def test_calculate_autonomy_score():
    """Test autonomy score calculation"""
    engine = ScoringEngine()

    # Perfect autonomy (no retries, error recovered)
    score = engine.calculate_autonomy_score(
        retries=0,
        error_recovered=True,
        tool_calls=5
    )
    assert score > 10.0

    # Poor autonomy (many retries)
    score = engine.calculate_autonomy_score(
        retries=5,
        error_recovered=False,
        tool_calls=20
    )
    assert score < 8.0


def test_calculate_quality_score():
    """Test code quality score calculation"""
    engine = ScoringEngine()

    # No linting issues
    score = engine.calculate_quality_score(
        linting_issues=0,
        file_count=3
    )
    assert score == 8.0

    # Some linting issues
    score = engine.calculate_quality_score(
        linting_issues=5,
        file_count=3
    )
    assert score < 8.0


def test_calculate_total_score():
    """Test total score calculation"""
    engine = ScoringEngine()

    benchmark_result = BenchmarkResult(
        success=True,
        wall_time=60.0,
        token_count={"input": 1000, "output": 500},
        cost=0.03,
        retries=0,
        tool_calls=5,
        error_recovered=True,
        generated_files=["quicksort.py"],
        logs="",
        recording_path=""
    )

    test_result = TestResult(
        passed=10,
        failed=0,
        total=10,
        pass_rate=100.0,
        output="",
        exit_code=0
    )

    score = engine.calculate_total_score(
        benchmark_result=benchmark_result,
        test_result=test_result,
        estimated_time=120.0,
        budgeted_cost=0.05,
        linting_issues=0
    )

    assert isinstance(score, Score)
    assert score.total_score > 80.0  # Should be high score
    assert score.speed_score > 0
    assert score.correctness_score == 40.0
    assert score.cost_score > 0
    assert score.autonomy_score > 0
    assert score.quality_score > 0
