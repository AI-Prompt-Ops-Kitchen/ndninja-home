import pytest
from pathlib import Path
import tempfile
import shutil
from test_harness import TestHarness, TestResult


@pytest.fixture
def temp_task_dir():
    """Create temporary task directory with test file"""
    temp_dir = Path(tempfile.mkdtemp())
    test_file = temp_dir / "test_example.py"
    test_file.write_text("""
import pytest

def test_passing():
    assert 1 + 1 == 2

def test_another_passing():
    assert True
""")
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_test_harness_init():
    """Test TestHarness initialization"""
    harness = TestHarness()
    assert harness is not None


def test_run_tests_success(temp_task_dir):
    """Test running tests that pass"""
    harness = TestHarness()
    result = harness.run_tests(
        task_dir=str(temp_task_dir),
        test_command="pytest test_example.py -v"
    )

    assert isinstance(result, TestResult)
    assert result.passed == 2
    assert result.failed == 0
    assert result.total == 2
    assert result.pass_rate == 100.0


def test_run_tests_failure(temp_task_dir):
    """Test running tests that fail"""
    # Create test file with failures
    test_file = temp_task_dir / "test_failing.py"
    test_file.write_text("""
import pytest

def test_failing():
    assert 1 + 1 == 3

def test_passing():
    assert True
""")

    harness = TestHarness()
    result = harness.run_tests(
        task_dir=str(temp_task_dir),
        test_command="pytest test_failing.py -v"
    )

    assert result.passed == 1
    assert result.failed == 1
    assert result.total == 2
    assert result.pass_rate == 50.0
    assert result.exit_code != 0
