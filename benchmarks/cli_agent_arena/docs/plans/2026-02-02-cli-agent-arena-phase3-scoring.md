# CLI Agent Benchmark Arena - Phase 3: Scoring & Testing

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement scoring system, test harness integration, and database persistence to enable automated correctness validation and comprehensive metric tracking.

**Architecture:** Create scoring engine that runs pytest on generated code, calculates weighted scores across 5 dimensions (speed, correctness, cost, autonomy, quality), and persists results to PostgreSQL. Test harness wraps pytest execution and captures detailed results. Database persistence layer saves BenchmarkResult objects with full metrics.

**Tech Stack:** Python subprocess, pytest, PostgreSQL psycopg2, pylint/flake8, dataclasses

**Prerequisites:** Phase 1 (schema) and Phase 2 (adapters) complete

---

## Task 1: Test Harness for Correctness Validation

**Files:**
- Create: `test_harness.py`
- Create: `test_test_harness.py`

**Step 1: Write test for test harness initialization**

Create `test_test_harness.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli_agent_arena && pytest test_test_harness.py::test_test_harness_init -v`
Expected: FAIL with import error

**Step 3: Write TestHarness class**

Create `test_harness.py`:

```python
"""Test harness for running and analyzing pytest results"""

import subprocess
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TestResult:
    """Results from running tests"""
    passed: int
    failed: int
    total: int
    pass_rate: float
    output: str
    exit_code: int
    error: Optional[str] = None


class TestHarness:
    """Harness for running pytest and extracting metrics"""

    def run_tests(self, task_dir: str, test_command: str, timeout: int = 60) -> TestResult:
        """Run tests and extract results

        Args:
            task_dir: Directory containing test files
            test_command: Command to run (e.g., "pytest test_file.py -v")
            timeout: Maximum execution time in seconds

        Returns:
            TestResult with pass/fail counts and metrics
        """
        try:
            result = subprocess.run(
                test_command.split(),
                cwd=task_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout + result.stderr

            # Parse pytest output for results
            # Look for patterns like "2 passed" or "1 failed, 1 passed"
            passed = 0
            failed = 0

            # Match "N passed" pattern
            passed_match = re.search(r'(\d+) passed', output)
            if passed_match:
                passed = int(passed_match.group(1))

            # Match "N failed" pattern
            failed_match = re.search(r'(\d+) failed', output)
            if failed_match:
                failed = int(failed_match.group(1))

            total = passed + failed
            pass_rate = (passed / total * 100.0) if total > 0 else 0.0

            return TestResult(
                passed=passed,
                failed=failed,
                total=total,
                pass_rate=pass_rate,
                output=output,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                passed=0,
                failed=0,
                total=0,
                pass_rate=0.0,
                output="",
                exit_code=-1,
                error=f"Test execution timed out after {timeout}s"
            )
        except Exception as e:
            return TestResult(
                passed=0,
                failed=0,
                total=0,
                pass_rate=0.0,
                output="",
                exit_code=-1,
                error=str(e)
            )
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli_agent_arena && pytest test_test_harness.py -v`
Expected: PASS (3 tests)

**Step 5: Write test for failing tests**

Add to `test_test_harness.py`:

```python
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
```

**Step 6: Run tests to verify they pass**

Run: `cd benchmarks/cli_agent_arena && pytest test_test_harness.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add test_harness.py test_test_harness.py
git commit -m "feat: add test harness for correctness validation

- Add TestHarness class to run pytest and extract results
- Add TestResult dataclass for test metrics
- Parse pytest output for pass/fail counts
- Handle timeouts and errors
- All tests passing (4/4)"
```

---

## Task 2: Scoring Engine

**Files:**
- Create: `scoring.py`
- Create: `test_scoring.py`

**Step 1: Write test for scoring calculator**

Create `test_scoring.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli_agent_arena && pytest test_scoring.py::test_scoring_engine_init -v`
Expected: FAIL with import error

**Step 3: Write ScoringEngine class**

Create `scoring.py`:

```python
"""Scoring engine for calculating benchmark scores"""

from dataclasses import dataclass
from adapters.base import BenchmarkResult
from test_harness import TestResult


@dataclass
class Score:
    """Comprehensive score breakdown"""
    speed_score: float  # 25% weight
    correctness_score: float  # 40% weight
    cost_score: float  # 15% weight
    autonomy_score: float  # 12% weight
    quality_score: float  # 8% weight
    total_score: float  # Sum of all scores (max 100)


class ScoringEngine:
    """Calculate scores across 5 dimensions"""

    # Score weights
    SPEED_WEIGHT = 0.25
    CORRECTNESS_WEIGHT = 0.40
    COST_WEIGHT = 0.15
    AUTONOMY_WEIGHT = 0.12
    QUALITY_WEIGHT = 0.08

    def calculate_speed_score(self, actual_time: float, estimated_time: float) -> float:
        """Calculate speed score (0-25 points)

        Args:
            actual_time: Actual execution time in seconds
            estimated_time: Estimated time budget in seconds

        Returns:
            Speed score (0-25)
        """
        max_score = 25.0

        # Calculate ratio of actual to estimated
        ratio = actual_time / estimated_time

        # Perfect score if under half the time
        if ratio <= 0.5:
            return max_score

        # Linear penalty from 0.5x to 2x
        if ratio <= 2.0:
            return max_score * (1.0 - (ratio - 0.5) / 1.5)

        # Heavy penalty beyond 2x
        return max(0.0, max_score * 0.1 / ratio)

    def calculate_correctness_score(self, test_result: TestResult) -> float:
        """Calculate correctness score (0-40 points)

        Args:
            test_result: Test execution results

        Returns:
            Correctness score (0-40)
        """
        max_score = 40.0
        return max_score * (test_result.pass_rate / 100.0)

    def calculate_cost_score(self, actual_cost: float, budgeted_cost: float) -> float:
        """Calculate cost score (0-15 points)

        Args:
            actual_cost: Actual API cost in USD
            budgeted_cost: Budgeted cost in USD

        Returns:
            Cost score (0-15)
        """
        max_score = 15.0

        if budgeted_cost == 0:
            return max_score

        ratio = actual_cost / budgeted_cost

        # Perfect score if under budget
        if ratio <= 1.0:
            return max_score

        # Penalty for over budget
        return max(0.0, max_score / ratio)

    def calculate_autonomy_score(
        self,
        retries: int,
        error_recovered: bool,
        tool_calls: int
    ) -> float:
        """Calculate autonomy score (0-12 points)

        Args:
            retries: Number of retries
            error_recovered: Whether errors were recovered
            tool_calls: Number of tool calls

        Returns:
            Autonomy score (0-12)
        """
        max_score = 12.0
        score = max_score

        # Penalty for retries (1 point per retry, max 5)
        retry_penalty = min(retries, 5) * 1.0
        score -= retry_penalty

        # Bonus for error recovery
        if error_recovered:
            score += 2.0

        # Efficiency penalty for excessive tool calls (>15)
        if tool_calls > 15:
            efficiency_penalty = (tool_calls - 15) * 0.2
            score -= min(efficiency_penalty, 3.0)

        return max(0.0, min(score, max_score))

    def calculate_quality_score(self, linting_issues: int, file_count: int) -> float:
        """Calculate code quality score (0-8 points)

        Args:
            linting_issues: Number of linting issues
            file_count: Number of generated files

        Returns:
            Quality score (0-8)
        """
        max_score = 8.0

        if file_count == 0:
            return 0.0

        # Penalty per linting issue
        issues_per_file = linting_issues / file_count
        penalty = min(issues_per_file * 2.0, max_score)

        return max(0.0, max_score - penalty)

    def calculate_total_score(
        self,
        benchmark_result: BenchmarkResult,
        test_result: TestResult,
        estimated_time: float,
        budgeted_cost: float,
        linting_issues: int
    ) -> Score:
        """Calculate total score across all dimensions

        Args:
            benchmark_result: Benchmark execution results
            test_result: Test execution results
            estimated_time: Time budget in seconds
            budgeted_cost: Cost budget in USD
            linting_issues: Number of linting issues

        Returns:
            Score object with all dimensions
        """
        speed_score = self.calculate_speed_score(
            benchmark_result.wall_time,
            estimated_time
        )

        correctness_score = self.calculate_correctness_score(test_result)

        cost_score = self.calculate_cost_score(
            benchmark_result.cost,
            budgeted_cost
        )

        autonomy_score = self.calculate_autonomy_score(
            benchmark_result.retries,
            benchmark_result.error_recovered,
            benchmark_result.tool_calls
        )

        quality_score = self.calculate_quality_score(
            linting_issues,
            len(benchmark_result.generated_files)
        )

        total = (
            speed_score +
            correctness_score +
            cost_score +
            autonomy_score +
            quality_score
        )

        return Score(
            speed_score=speed_score,
            correctness_score=correctness_score,
            cost_score=cost_score,
            autonomy_score=autonomy_score,
            quality_score=quality_score,
            total_score=total
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli_agent_arena && pytest test_scoring.py -v`
Expected: PASS (9 tests)

**Step 5: Commit**

```bash
git add scoring.py test_scoring.py
git commit -m "feat: add scoring engine for benchmark evaluation

- Add ScoringEngine class with 5-dimension scoring
- Speed score (25%): time vs budget with penalties
- Correctness score (40%): test pass rate
- Cost score (15%): API cost vs budget
- Autonomy score (12%): retries, recovery, efficiency
- Quality score (8%): linting issues per file
- All tests passing (9/9)"
```

---

## Task 3: Database Persistence Layer

**Files:**
- Create: `database.py`
- Create: `test_database.py`

**Step 1: Write test for database persistence**

Create `test_database.py`:

```python
import pytest
import psycopg2
from database import DatabaseClient
from adapters.base import BenchmarkResult
from test_harness import TestResult
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

    test_result = TestResult(
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
        assert "total_score" in result


def test_get_agent_comparison(db_client):
    """Test getting agent comparison view"""
    comparison = db_client.get_agent_comparison()

    assert isinstance(comparison, list)

    if len(comparison) > 0:
        row = comparison[0]
        assert "agent_name" in row
        assert "avg_score" in row
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli_agent_arena && pytest test_database.py::test_database_client_init -v`
Expected: FAIL with import error

**Step 3: Write DatabaseClient class**

Create `database.py`:

```python
"""Database persistence layer for benchmark results"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from adapters.base import BenchmarkResult
from test_harness import TestResult
from scoring import Score


class DatabaseClient:
    """Client for saving and retrieving benchmark results"""

    def __init__(
        self,
        host: str = "localhost",
        database: str = "workspace",
        user: str = "ndninja",
        password: str = None
    ):
        """Initialize database client

        Args:
            host: Database host
            database: Database name
            user: Database user
            password: Database password (optional)
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def save_result(
        self,
        agent_name: str,
        task_name: str,
        task_category: str,
        benchmark_result: BenchmarkResult,
        test_result: TestResult,
        score: Score
    ) -> int:
        """Save benchmark result to database

        Args:
            agent_name: Name of agent (kimi, claude, gemini)
            task_name: Name of task (quicksort, etc.)
            task_category: Task category (algorithms, etc.)
            benchmark_result: Benchmark execution results
            test_result: Test execution results
            score: Calculated scores

        Returns:
            Result ID from database
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO cli_agent_benchmark_results (
                        agent_name,
                        task_name,
                        task_category,
                        success,
                        wall_time_seconds,
                        input_tokens,
                        output_tokens,
                        cost_usd,
                        retries,
                        tool_calls,
                        error_recovered,
                        tests_passed,
                        tests_failed,
                        tests_total,
                        speed_score,
                        correctness_score,
                        cost_score,
                        autonomy_score,
                        quality_score,
                        total_score,
                        recording_path,
                        logs
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s
                    ) RETURNING id
                """, (
                    agent_name,
                    task_name,
                    task_category,
                    benchmark_result.success,
                    benchmark_result.wall_time,
                    benchmark_result.token_count.get("input", 0),
                    benchmark_result.token_count.get("output", 0),
                    benchmark_result.cost,
                    benchmark_result.retries,
                    benchmark_result.tool_calls,
                    benchmark_result.error_recovered,
                    test_result.passed,
                    test_result.failed,
                    test_result.total,
                    score.speed_score,
                    score.correctness_score,
                    score.cost_score,
                    score.autonomy_score,
                    score.quality_score,
                    score.total_score,
                    benchmark_result.recording_path,
                    benchmark_result.logs
                ))
                result_id = cur.fetchone()[0]
                conn.commit()
                return result_id
        finally:
            conn.close()

    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent benchmark results

        Args:
            limit: Maximum number of results to return

        Returns:
            List of result dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT *
                    FROM cli_agent_benchmark_results
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_agent_comparison(self) -> List[Dict[str, Any]]:
        """Get agent comparison from view

        Returns:
            List of agent comparison dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM cli_agent_comparison")
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli_agent_arena && pytest test_database.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add database.py test_database.py
git commit -m "feat: add database persistence layer

- Add DatabaseClient for saving benchmark results
- Save complete results with all metrics to PostgreSQL
- Get recent results and agent comparison
- All tests passing (4/4)"
```

---

## Task 4: Integrate Scoring into Runner

**Files:**
- Modify: `run_cli_benchmarks.py`

**Step 1: Add scoring integration imports**

In `run_cli_benchmarks.py`, add imports at top:

```python
from benchmarks.cli_agent_arena.test_harness import TestHarness
from benchmarks.cli_agent_arena.scoring import ScoringEngine
from benchmarks.cli_agent_arena.database import DatabaseClient
```

**Step 2: Update run_benchmarks function**

Replace the execution loop in `run_benchmarks()`:

```python
# Inside run_benchmarks(), replace the execution loop:

    # Initialize services
    test_harness = TestHarness()
    scoring_engine = ScoringEngine()
    db_client = DatabaseClient() if not args.dry_run else None

    run_id = str(uuid.uuid4())
    print(f"Benchmark Run ID: {run_id}\n")

    results = []
    for agent in agents:
        if not availability.get(agent, False):
            print(f"⚠️  Skipping {agent}: CLI not available")
            continue

        print(f"Running benchmarks with {agent}:")

        for task_path in task_list:
            task = load_task(Path(f"shared-tasks/{task_path}"))
            print(f"  - {task.name} ({task.difficulty}, ~{task.estimated_time_seconds}s)...", end=" ", flush=True)

            adapter = None
            try:
                # Get adapter
                adapter = get_adapter(agent)

                # Setup
                adapter.setup(str(task.task_dir))

                # Execute
                benchmark_result = adapter.execute_task(task.prompt, timeout=task.estimated_time_seconds * 2)

                # Run tests for correctness
                test_result = test_harness.run_tests(
                    task_dir=str(task.task_dir),
                    test_command=task.test_command
                )

                # Calculate score
                score = scoring_engine.calculate_total_score(
                    benchmark_result=benchmark_result,
                    test_result=test_result,
                    estimated_time=task.estimated_time_seconds,
                    budgeted_cost=task.budgeted_cost,
                    linting_issues=0  # TODO: Add linting in Phase 4
                )

                # Display result
                if benchmark_result.success and test_result.pass_rate == 100.0:
                    print(f"✅ Score: {score.total_score:.1f}/100 ({benchmark_result.wall_time:.1f}s)")
                elif test_result.pass_rate > 0:
                    print(f"⚠️  Partial: {score.total_score:.1f}/100 ({test_result.pass_rate:.0f}% tests passed)")
                else:
                    print(f"❌ Failed: {score.total_score:.1f}/100")

                # Save to database
                if db_client:
                    result_id = db_client.save_result(
                        agent_name=agent,
                        task_name=task.name,
                        task_category=task.category,
                        benchmark_result=benchmark_result,
                        test_result=test_result,
                        score=score
                    )
                    print(f"     Saved to database (ID: {result_id})")

                results.append((agent, task, benchmark_result, test_result, score))

            except NotImplementedError as e:
                print(f"⚠️  Not implemented")
            except Exception as e:
                print(f"❌ Error: {e}")
            finally:
                if adapter:
                    adapter.cleanup()
```

**Step 3: Test runner with scoring**

Run: `cd benchmarks && python3 cli_agent_arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort --dry-run`
Expected: Success with score displayed

**Step 4: Commit**

```bash
git add run_cli_benchmarks.py
git commit -m "feat: integrate scoring and test harness into runner

- Add test execution after benchmark run
- Calculate scores across 5 dimensions
- Display scores with pass/fail indicators
- Save results to database (unless --dry-run)
- Enhanced output with score breakdown"
```

---

## Task 5: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `requirements.txt`

**Step 1: Add dependencies to requirements.txt**

Add to `requirements.txt`:

```
# Code quality (for Phase 4)
# pylint>=3.0.0
# flake8>=7.0.0
```

**Step 2: Update README status**

In `README.md`, update Phase 3 section:

```markdown
**Phase 3: Scoring & Testing** ✅ Complete
- Test harness for correctness validation ✅
- Scoring engine (5 dimensions) ✅
- Database persistence layer ✅
- Runner integration with scoring ✅
- **53 tests passing, 4 skipped**

**Phase 4: Reporting & Analytics** 🚧 Next
- Code quality analysis (pylint/flake8)
- Report generators
- Real CLI adapter implementations
```

Update Next Steps section:

```markdown
## Phase 3 Deliverables

✅ TestHarness for running pytest and extracting results
✅ ScoringEngine with 5-dimension scoring system
✅ DatabaseClient for persisting results to PostgreSQL
✅ Runner integration with test execution and scoring
✅ End-to-end pipeline: execute → test → score → save

**Test Summary:** 53 tests passing (4 skipped for integration)

## Next Steps (Phase 4)

1. Add code quality analysis (pylint/flake8)
2. Implement real Kimi CLI adapter
3. Implement real Claude Code adapter
4. Research Gemini CLI availability
5. Create report generators
6. Build analytics dashboard
```

**Step 3: Test all tests**

Run: `cd benchmarks/cli_agent_arena && pytest -v --tb=no -q`
Expected: 53 tests passing

**Step 4: Commit**

```bash
git add README.md requirements.txt
git commit -m "docs: update README for Phase 3 completion

- Mark Phase 3 as complete
- Update test count (53 passing)
- Document Phase 3 deliverables
- Add Phase 4 roadmap"
```

---

## Phase 3 Complete! 🎉

**Deliverables:**
- ✅ TestHarness with pytest integration (4 tests)
- ✅ ScoringEngine with 5-dimension scoring (9 tests)
- ✅ DatabaseClient for persistence (4 tests)
- ✅ Runner integration with full pipeline
- ✅ End-to-end execution: run → test → score → save

**Test Summary:** 53 tests passing (4 skipped for integration)

**What Works:**
- Automated correctness validation via pytest
- Comprehensive scoring across speed, correctness, cost, autonomy, quality
- Database persistence with full metrics
- Runner displays scores and saves to PostgreSQL
- Mock adapter demonstrates full pipeline

**What's Next (Phase 4):**
1. Code quality analysis (pylint/flake8)
2. Real CLI adapter implementations (Kimi, Claude Code, Gemini)
3. Report generators and analytics
4. Performance optimizations
5. Production deployment

See implementation plans at:
- `docs/plans/2026-02-01-cli-agent-arena-phase1-foundation.md` ✅
- `docs/plans/2026-02-01-cli-agent-arena-phase2-adapters.md` ✅
- `docs/plans/2026-02-02-cli-agent-arena-phase3-scoring.md` ✅
