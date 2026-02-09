import pytest
from base import BenchmarkResult, CLIAgentAdapter


class MockAdapter(CLIAgentAdapter):
    """Mock implementation for testing"""

    def setup(self, task_dir: str):
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        return BenchmarkResult(
            success=True,
            wall_time=1.0,
            token_count={"input": 10, "output": 10},
            cost=0.01,
            retries=0,
            tool_calls=5,
            error_recovered=False,
            generated_files=[],
            logs="mock logs",
            recording_path="/mock/path.cast"
        )

    def cleanup(self):
        pass


def test_benchmark_result_creation():
    """Test BenchmarkResult dataclass instantiation"""
    result = BenchmarkResult(
        success=True,
        wall_time=42.5,
        token_count={"input": 1000, "output": 500},
        cost=0.05,
        retries=0,
        tool_calls=15,
        error_recovered=False,
        generated_files=["quicksort.py", "test_quicksort.py"],
        logs="Agent output here",
        recording_path="/path/to/recording.cast"
    )

    assert result.success is True
    assert result.wall_time == 42.5
    assert result.token_count["input"] == 1000
    assert result.cost == 0.05
    assert len(result.generated_files) == 2


def test_benchmark_result_required_fields():
    """Test that all fields are required"""
    with pytest.raises(TypeError):
        BenchmarkResult(success=True)


def test_adapter_interface():
    """Test adapter interface methods"""
    adapter = MockAdapter()
    adapter.setup("/path/to/task")

    result = adapter.execute_task("Test prompt", timeout=60)
    assert isinstance(result, BenchmarkResult)
    assert result.success is True

    adapter.cleanup()


def test_adapter_is_abstract():
    """Test that CLIAgentAdapter cannot be instantiated directly"""
    with pytest.raises(TypeError):
        CLIAgentAdapter()


def test_benchmark_result_with_quality_score():
    """Test BenchmarkResult with quality_score field"""
    result = BenchmarkResult(
        success=True,
        wall_time=30.0,
        token_count={"input": 500, "output": 300},
        cost=0.02,
        retries=1,
        tool_calls=8,
        error_recovered=True,
        generated_files=["solution.py"],
        logs="Agent logs with quality analysis",
        recording_path="/path/to/recording.cast",
        quality_score=87.5
    )

    assert result.quality_score == 87.5
    assert result.success is True
    assert result.error_recovered is True


def test_benchmark_result_quality_score_defaults_to_zero():
    """Test that quality_score defaults to 0.0 when not provided"""
    result = BenchmarkResult(
        success=True,
        wall_time=20.0,
        token_count={"input": 200, "output": 100},
        cost=0.01,
        retries=0,
        tool_calls=3,
        error_recovered=False,
        generated_files=["output.py"],
        logs="Logs",
        recording_path="/path/to/file.cast"
    )

    assert result.quality_score == 0.0
