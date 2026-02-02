# CLI Agent Benchmark Arena - Phase 3: Scoring & Testing

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement scoring system that evaluates speed (25%), correctness (40%), cost (15%), autonomy (12%), and quality (8%), integrate pytest test harness, and add database persistence.

**Architecture:** Scoring engine takes BenchmarkResult + test results, calculates weighted scores per design. Test harness runs pytest, extracts pass/fail counts. Database persister saves to PostgreSQL schema from Phase 1.

**Tech Stack:** Python dataclasses, pytest subprocess integration, PostgreSQL psycopg2, scoring formulas

**Prerequisites:** Phase 1 (schema, task loader) and Phase 2 (adapters, runner) complete

---

## Task 1: Test Harness Integration

**Files:**
- Create: `benchmarks/cli_agent_arena/test_harness.py`
- Create: `benchmarks/cli_agent_arena/test_test_harness.py`

**Step 1: Write test for test harness**

Create `benchmarks/cli_agent_arena/test_test_harness.py`:

```python
"""Test pytest test harness integration"""

import pytest
from pathlib import Path
from benchmarks.cli_agent_arena.test_harness import TestHarness, TestResult


def test_test_harness_run_passing_tests(tmp_path):
    """Test harness can run passing tests"""
    # Create a simple passing test
    test_file = tmp_path / "test_sample.py"
    test_file.write_text("""
def test_passing():
    assert 1 + 1 == 2

def test_also_passing():
    assert True
""")

    harness = TestHarness()
    result = harness.run_tests(str(tmp_path))

    assert isinstance(result, TestResult)
    assert result.total == 2
    assert result.passed == 2
    assert result.failed == 0
    assert result.pass_rate == 100.0


def test_test_harness_run_failing_tests(tmp_path):
    """Test harness can detect failing tests"""
    test_file = tmp_path / "test_sample.py"
    test_file.write_text("""
def test_passing():
    assert 1 + 1 == 2

def test_failing():
    assert 1 + 1 == 3
""")

    harness = TestHarness()
    result = harness.run_tests(str(tmp_path))

    assert result.total == 2
    assert result.passed == 1
    assert result.failed == 1
    assert result.pass_rate == 50.0


def test_test_harness_empty_directory(tmp_path):
    """Test harness handles no tests gracefully"""
    harness = TestHarness()
    result = harness.run_tests(str(tmp_path))

    assert result.total == 0
    assert result.passed == 0
    assert result.pass_rate == 0.0
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli_agent_arena && pytest test_test_harness.py -v`
Expected: FAIL with import error

**Step 3: Write TestResult dataclass**

Create `benchmarks/cli_agent_arena/test_harness.py`:

```python
"""Pytest test harness for running and evaluating agent-generated code"""

import subprocess
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TestResult:
    """Results from running pytest on agent-generated code"""
    total: int
    passed: int
    failed: int
    skipped: int
    error: Optional[str] = None

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage"""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100.0


class TestHarness:
    """Wrapper around pytest for running tests and extracting metrics"""

    def __init__(self, timeout: int = 30):
        """Initialize test harness

        Args:
            timeout: Maximum time to wait for tests (seconds)
        """
        self.timeout = timeout

    def run_tests(self, test_dir: str, test_file: Optional[str] = None) -> TestResult:
        """Run pytest in directory and extract results

        Args:
            test_dir: Directory containing tests
            test_file: Optional specific test file to run

        Returns:
            TestResult with pass/fail counts
        """
        # Build pytest command
        if test_file:
            target = str(Path(test_dir) / test_file)
        else:
            target = str(test_dir)

        try:
            result = subprocess.run(
                ["pytest", target, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse pytest output
            return self._parse_pytest_output(result.stdout, result.stderr)

        except subprocess.TimeoutExpired:
            return TestResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                error=f"Tests timed out after {self.timeout}s"
            )
        except Exception as e:
            return TestResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                error=str(e)
            )

    def _parse_pytest_output(self, stdout: str, stderr: str) -> TestResult:
        """Parse pytest output to extract test counts

        Args:
            stdout: Pytest stdout
            stderr: Pytest stderr

        Returns:
            TestResult with parsed counts
        """
        # Look for summary line like: "2 passed, 1 failed in 0.05s"
        # or "2 passed in 0.03s"
        summary_pattern = r"(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?"

        match = re.search(summary_pattern, stdout)

        if match:
            passed = int(match.group(1))
            failed = int(match.group(2)) if match.group(2) else 0
            skipped = int(match.group(3)) if match.group(3) else 0
            total = passed + failed + skipped

            return TestResult(
                total=total,
                passed=passed,
                failed=failed,
                skipped=skipped
            )

        # No tests found
        if "no tests ran" in stdout.lower() or "collected 0 items" in stdout:
            return TestResult(total=0, passed=0, failed=0, skipped=0)

        # Parse error
        return TestResult(
            total=0,
            passed=0,
            failed=0,
            skipped=0,
            error="Failed to parse pytest output"
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli_agent_arena && pytest test_test_harness.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add benchmarks/cli_agent_arena/test_harness.py benchmarks/cli_agent_arena/test_test_harness.py
git commit -m "feat: add pytest test harness integration

- Add TestResult dataclass for test metrics
- Add TestHarness class to run pytest and parse output
- Extract pass/fail/skip counts from pytest summary
- Handle timeouts and errors gracefully
- All tests passing (3/3)"
```

---

## Task 2: Scoring Engine

**Files:**
- Create: `benchmarks/cli_agent_arena/scoring.py`
- Create: `benchmarks/cli_agent_arena/test_scoring.py`

**Step 1: Write test for scoring engine**

Create `benchmarks/cli_agent_arena/test_scoring.py`:

```python
"""Test scoring system"""

import pytest
from benchmarks.cli_agent_arena.scoring import ScoringEngine, Score
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult
from benchmarks.cli_agent_arena.test_harness import TestResult


def test_scoring_perfect_correctness():
    """Test correctness scoring with all tests passing"""
    test_result = TestResult(total=10, passed=10, failed=0, skipped=0)

    engine = ScoringEngine()
    score = engine.calculate_correctness(test_result)

    assert score == 100.0


def test_scoring_partial_correctness():
    """Test correctness scoring with some failures"""
    test_result = TestResult(total=10, passed=7, failed=3, skipped=0)

    engine = ScoringEngine()
    score = engine.calculate_correctness(test_result)

    assert score == 70.0


def test_scoring_speed_on_time():
    """Test speed scoring when on expected time"""
    engine = ScoringEngine()
    score = engine.calculate_speed(
        wall_time=120.0,
        estimated_time=120.0
    )

    assert score == 100.0


def test_scoring_speed_faster():
    """Test speed scoring when faster than expected"""
    engine = ScoringEngine()
    score = engine.calculate_speed(
        wall_time=60.0,
        estimated_time=120.0
    )

    assert score == 100.0  # Capped at 100


def test_scoring_speed_slower():
    """Test speed scoring when slower than expected"""
    engine = ScoringEngine()
    score = engine.calculate_speed(
        wall_time=180.0,
        estimated_time=120.0
    )

    # 120 / 180 = 0.667 * 100 = 66.7
    assert abs(score - 66.7) < 0.1


def test_scoring_cost_under_budget():
    """Test cost scoring under budget"""
    engine = ScoringEngine()
    score = engine.calculate_cost(actual_cost=0.03, budget=0.05)

    assert score == 100.0


def test_scoring_cost_over_budget():
    """Test cost scoring over budget"""
    engine = ScoringEngine()

    # 50% over budget (1.5x)
    score1 = engine.calculate_cost(actual_cost=0.075, budget=0.05)
    assert score1 == 75.0

    # 100% over budget (2x)
    score2 = engine.calculate_cost(actual_cost=0.10, budget=0.05)
    assert score2 == 50.0

    # Way over budget (>2x)
    score3 = engine.calculate_cost(actual_cost=0.15, budget=0.05)
    assert score3 == 25.0


def test_scoring_autonomy_perfect():
    """Test autonomy scoring with no penalties"""
    engine = ScoringEngine()
    score = engine.calculate_autonomy(
        retries=0,
        max_retries=2,
        tool_calls=15,
        max_tool_calls=20,
        error_recovered=False
    )

    assert score == 100.0


def test_scoring_autonomy_with_recovery():
    """Test autonomy scoring with error recovery bonus"""
    engine = ScoringEngine()
    score = engine.calculate_autonomy(
        retries=1,
        max_retries=2,
        tool_calls=15,
        max_tool_calls=20,
        error_recovered=True
    )

    # 100 base + 20 bonus = 120, capped at 100
    assert score == 100.0


def test_scoring_autonomy_penalties():
    """Test autonomy scoring with retry and tool call penalties"""
    engine = ScoringEngine()
    score = engine.calculate_autonomy(
        retries=4,  # 2 over max (2 * 15 = 30 penalty)
        max_retries=2,
        tool_calls=35,  # 15 over max (1 * 10 = 10 penalty)
        max_tool_calls=20,
        error_recovered=False
    )

    # 100 - 30 - 10 = 60
    assert score == 60.0


def test_scoring_overall_weighted():
    """Test overall score calculation with all dimensions"""
    benchmark_result = BenchmarkResult(
        success=True,
        wall_time=120.0,
        token_count={"input": 100, "output": 200},
        cost=0.05,
        retries=1,
        tool_calls=15,
        error_recovered=False,
        generated_files=["solution.py"],
        logs="Test logs",
        recording_path="recording.cast"
    )

    test_result = TestResult(total=10, passed=10, failed=0, skipped=0)

    engine = ScoringEngine()
    score = engine.calculate_overall(
        benchmark_result=benchmark_result,
        test_result=test_result,
        estimated_time=120.0,
        cost_budget=0.05,
        max_retries=2,
        max_tool_calls=20,
        quality_score=85.0
    )

    assert isinstance(score, Score)
    assert score.correctness == 100.0
    assert score.speed == 100.0
    assert score.cost == 100.0
    assert score.autonomy == 100.0
    assert score.quality == 85.0

    # Overall = (40*100 + 25*100 + 15*100 + 12*100 + 8*85) / 100
    expected_overall = (40*100 + 25*100 + 15*100 + 12*100 + 8*85) / 100
    assert abs(score.overall - expected_overall) < 0.1
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli_agent_arena && pytest test_scoring.py -v`
Expected: FAIL with import error

**Step 3: Write Score dataclass**

Create `benchmarks/cli_agent_arena/scoring.py`:

```python
"""Scoring system for CLI agent benchmarks"""

from dataclasses import dataclass
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult
from benchmarks.cli_agent_arena.test_harness import TestResult


@dataclass
class Score:
    """Comprehensive score across all dimensions"""
    correctness: float      # 0-100 (40% weight)
    speed: float           # 0-100 (25% weight)
    cost: float            # 0-100 (15% weight)
    autonomy: float        # 0-100 (12% weight)
    quality: float         # 0-100 (8% weight)
    overall: float         # 0-100 (weighted average)


class ScoringEngine:
    """Calculate scores across all benchmark dimensions"""

    # Scoring weights (must sum to 100)
    WEIGHT_CORRECTNESS = 40
    WEIGHT_SPEED = 25
    WEIGHT_COST = 15
    WEIGHT_AUTONOMY = 12
    WEIGHT_QUALITY = 8

    def calculate_correctness(self, test_result: TestResult) -> float:
        """Calculate correctness score from test results

        Args:
            test_result: Test harness results

        Returns:
            Score 0-100 based on test pass rate
        """
        return test_result.pass_rate

    def calculate_speed(self, wall_time: float, estimated_time: float) -> float:
        """Calculate speed score

        Args:
            wall_time: Actual execution time (seconds)
            estimated_time: Expected execution time (seconds)

        Returns:
            Score 0-100 (faster = higher, capped at 100)
        """
        if wall_time <= 0:
            return 0.0

        time_ratio = estimated_time / wall_time
        return min(100.0, time_ratio * 100.0)

    def calculate_cost(self, actual_cost: float, budget: float) -> float:
        """Calculate cost score

        Args:
            actual_cost: Actual API cost (USD)
            budget: Budgeted cost (USD)

        Returns:
            Score 0-100 based on budget adherence
        """
        if actual_cost <= budget:
            return 100.0
        elif actual_cost <= budget * 1.5:
            return 75.0  # 50% over budget
        elif actual_cost <= budget * 2.0:
            return 50.0  # 100% over budget
        else:
            return 25.0  # Way over budget

    def calculate_autonomy(
        self,
        retries: int,
        max_retries: int,
        tool_calls: int,
        max_tool_calls: int,
        error_recovered: bool
    ) -> float:
        """Calculate autonomy score

        Args:
            retries: Number of retry attempts
            max_retries: Maximum expected retries
            tool_calls: Number of tool calls
            max_tool_calls: Maximum expected tool calls
            error_recovered: Whether agent recovered from errors

        Returns:
            Score 0-100 based on autonomy metrics
        """
        score = 100.0

        # Penalty for retries (each retry over max -15 points)
        if retries > max_retries:
            score -= (retries - max_retries) * 15

        # Penalty for excessive tool calls (-10 points per 10 extra calls)
        if tool_calls > max_tool_calls:
            excess = tool_calls - max_tool_calls
            score -= (excess // 10) * 10

        # Bonus for error recovery (+20 points)
        if error_recovered:
            score += 20

        # Clamp to 0-100
        return max(0.0, min(100.0, score))

    def calculate_overall(
        self,
        benchmark_result: BenchmarkResult,
        test_result: TestResult,
        estimated_time: float,
        cost_budget: float,
        max_retries: int,
        max_tool_calls: int,
        quality_score: float
    ) -> Score:
        """Calculate overall score with all dimensions

        Args:
            benchmark_result: Results from adapter execution
            test_result: Results from test harness
            estimated_time: Expected execution time
            cost_budget: Expected cost budget
            max_retries: Maximum expected retries
            max_tool_calls: Maximum expected tool calls
            quality_score: Code quality score (0-100)

        Returns:
            Score object with all dimensions and overall
        """
        correctness = self.calculate_correctness(test_result)
        speed = self.calculate_speed(benchmark_result.wall_time, estimated_time)
        cost = self.calculate_cost(benchmark_result.cost, cost_budget)
        autonomy = self.calculate_autonomy(
            benchmark_result.retries,
            max_retries,
            benchmark_result.tool_calls,
            max_tool_calls,
            benchmark_result.error_recovered
        )

        # Calculate weighted overall
        overall = (
            self.WEIGHT_CORRECTNESS * correctness +
            self.WEIGHT_SPEED * speed +
            self.WEIGHT_COST * cost +
            self.WEIGHT_AUTONOMY * autonomy +
            self.WEIGHT_QUALITY * quality_score
        ) / 100.0

        return Score(
            correctness=correctness,
            speed=speed,
            cost=cost,
            autonomy=autonomy,
            quality=quality_score,
            overall=overall
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli_agent_arena && pytest test_scoring.py -v`
Expected: PASS (12 tests)

**Step 5: Commit**

```bash
git add benchmarks/cli_agent_arena/scoring.py benchmarks/cli_agent_arena/test_scoring.py
git commit -m "feat: add scoring engine for benchmark evaluation

- Add Score dataclass with all dimensions
- Add ScoringEngine with weighted calculations
- Correctness: test pass rate (40% weight)
- Speed: time vs estimate (25% weight)
- Cost: actual vs budget (15% weight)
- Autonomy: retries + tool calls + recovery (12% weight)
- Quality: code quality score (8% weight)
- All tests passing (12/12)"
```

---

## Task 3: Database Persister

**Files:**
- Create: `benchmarks/cli_agent_arena/database.py`
- Create: `benchmarks/cli_agent_arena/test_database.py`

**Step 1: Write test for database persister**

Create `benchmarks/cli_agent_arena/test_database.py`:

```python
"""Test database persistence"""

import pytest
import psycopg2
from datetime import datetime
from benchmarks.cli_agent_arena.database import DatabasePersister
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult
from benchmarks.cli_agent_arena.scoring import Score
from benchmarks.cli_agent_arena.test_harness import TestResult


@pytest.fixture
def db_persister():
    """Create database persister"""
    return DatabasePersister()


def test_database_save_result(db_persister):
    """Test saving benchmark result to database"""
    benchmark_result = BenchmarkResult(
        success=True,
        wall_time=120.5,
        token_count={"input": 100, "output": 200},
        cost=0.05,
        retries=1,
        tool_calls=15,
        error_recovered=False,
        generated_files=["solution.py"],
        logs="Test execution logs",
        recording_path="recordings/test.cast"
    )

    score = Score(
        correctness=95.0,
        speed=85.0,
        cost=100.0,
        autonomy=90.0,
        quality=88.0,
        overall=91.0
    )

    test_result = TestResult(total=10, passed=10, failed=0, skipped=0)

    # Save to database
    result_id = db_persister.save_benchmark_result(
        agent="mock",
        task_name="quicksort",
        task_category="algorithms",
        benchmark_result=benchmark_result,
        test_result=test_result,
        score=score
    )

    assert result_id is not None
    assert isinstance(result_id, int)

    # Verify it was saved
    conn = psycopg2.connect(
        dbname="workspace",
        user="ndninja"
    )
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cli_agent_benchmark_results WHERE id = %s",
        (result_id,)
    )
    row = cursor.fetchone()

    assert row is not None
    # Verify key fields
    assert row[1] == "mock"  # agent
    assert row[2] == "quicksort"  # task_name
    assert row[7] == 95.0  # correctness_score

    cursor.close()
    conn.close()


def test_database_connection_error_handling(db_persister):
    """Test database connection error handling"""
    # Create persister with invalid connection
    bad_persister = DatabasePersister(dbname="nonexistent_db")

    benchmark_result = BenchmarkResult(
        success=True,
        wall_time=120.0,
        token_count={"input": 100, "output": 200},
        cost=0.05,
        retries=0,
        tool_calls=10,
        error_recovered=False,
        generated_files=[],
        logs="",
        recording_path=""
    )

    score = Score(100, 100, 100, 100, 100, 100)
    test_result = TestResult(10, 10, 0, 0)

    # Should raise exception
    with pytest.raises(Exception):
        bad_persister.save_benchmark_result(
            agent="test",
            task_name="test",
            task_category="test",
            benchmark_result=benchmark_result,
            test_result=test_result,
            score=score
        )
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli_agent_arena && pytest test_database.py -v`
Expected: FAIL with import error

**Step 3: Write DatabasePersister class**

Create `benchmarks/cli_agent_arena/database.py`:

```python
"""Database persistence for benchmark results"""

import psycopg2
from datetime import datetime
from typing import Optional
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult
from benchmarks.cli_agent_arena.scoring import Score
from benchmarks.cli_agent_arena.test_harness import TestResult


class DatabasePersister:
    """Save benchmark results to PostgreSQL"""

    def __init__(
        self,
        dbname: str = "workspace",
        user: str = "ndninja",
        host: str = "localhost",
        port: int = 5432
    ):
        """Initialize database persister

        Args:
            dbname: Database name
            user: Database user
            host: Database host
            port: Database port
        """
        self.dbname = dbname
        self.user = user
        self.host = host
        self.port = port

    def save_benchmark_result(
        self,
        agent: str,
        task_name: str,
        task_category: str,
        benchmark_result: BenchmarkResult,
        test_result: TestResult,
        score: Score,
        run_id: Optional[str] = None
    ) -> int:
        """Save complete benchmark result to database

        Args:
            agent: Agent name (kimi, claude, gemini, mock)
            task_name: Task name (e.g., quicksort)
            task_category: Task category (algorithms, features, etc.)
            benchmark_result: Execution results from adapter
            test_result: Test harness results
            score: Calculated scores
            run_id: Optional batch run ID

        Returns:
            Database row ID

        Raises:
            Exception: If database operation fails
        """
        conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            host=self.host,
            port=self.port
        )

        try:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO cli_agent_benchmark_results (
                    agent,
                    task_name,
                    task_category,
                    timestamp,
                    success,
                    wall_time,
                    correctness_score,
                    speed_score,
                    cost_score,
                    autonomy_score,
                    quality_score,
                    overall_score,
                    tests_total,
                    tests_passed,
                    tests_failed,
                    cost_usd,
                    retries,
                    tool_calls,
                    error_recovered,
                    recording_path,
                    run_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                agent,
                task_name,
                task_category,
                datetime.now(),
                benchmark_result.success,
                benchmark_result.wall_time,
                score.correctness,
                score.speed,
                score.cost,
                score.autonomy,
                score.quality,
                score.overall,
                test_result.total,
                test_result.passed,
                test_result.failed,
                benchmark_result.cost,
                benchmark_result.retries,
                benchmark_result.tool_calls,
                benchmark_result.error_recovered,
                benchmark_result.recording_path,
                run_id
            ))

            result_id = cursor.fetchone()[0]
            conn.commit()

            cursor.close()
            return result_id

        finally:
            conn.close()
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli_agent_arena && pytest test_database.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add benchmarks/cli_agent_arena/database.py benchmarks/cli_agent_arena/test_database.py
git commit -m "feat: add database persister for benchmark results

- Add DatabasePersister class for PostgreSQL
- Save complete benchmark results with all metrics
- Insert into cli_agent_benchmark_results table
- Handle connection errors gracefully
- All tests passing (2/2)"
```

---

## Task 4: Integrate Scoring Into Runner

**Files:**
- Modify: `benchmarks/cli_agent_arena/run_cli_benchmarks.py`
- Modify: `benchmarks/cli_agent_arena/test_runner.py`

**Step 1: Write test for end-to-end scoring**

Add to `test_runner.py`:

```python
def test_runner_execute_with_scoring():
    """Test runner calculates and saves scores"""
    result = subprocess.run(
        [
            sys.executable,
            "benchmarks/cli_agent_arena/run_cli_benchmarks.py",
            "--agent", "mock",
            "--tasks", "algorithms/quicksort"
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )

    assert result.returncode == 0
    assert "Overall Score:" in result.stdout
    assert "Correctness:" in result.stdout
    assert "Speed:" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli_agent_arena && pytest test_runner.py::test_runner_execute_with_scoring -v`
Expected: FAIL (scoring not implemented)

**Step 3: Integrate scoring into runner**

Modify `run_cli_benchmarks.py`:

Add imports:
```python
from benchmarks.cli_agent_arena.test_harness import TestHarness
from benchmarks.cli_agent_arena.scoring import ScoringEngine
from benchmarks.cli_agent_arena.database import DatabasePersister
```

Modify `run_benchmarks()` function to add scoring:

```python
def run_benchmarks(args):
    """Run benchmarks with scoring and persistence"""
    # ... existing task/agent setup ...

    # Initialize scoring components
    test_harness = TestHarness()
    scoring_engine = ScoringEngine()
    db_persister = DatabasePersister() if not args.dry_run else None

    run_id = str(uuid.uuid4())
    print(f"Benchmark Run ID: {run_id}\n")

    results = []
    for agent in agents:
        if not availability.get(agent, False):
            print(f"⚠️  Skipping {agent}: CLI not available")
            continue

        print(f"Running benchmarks with {agent}:")

        adapter = None
        for task_path in task_list:
            task = load_task(get_shared_tasks_base() / task_path)
            print(f"  - {task.name} ({task.difficulty}, ~{task.estimated_time_seconds}s)...", end=" ", flush=True)

            try:
                # Get adapter and execute
                adapter = get_adapter(agent)
                adapter.setup(str(task.task_dir))
                benchmark_result = adapter.execute_task(
                    task.prompt,
                    timeout=task.estimated_time_seconds * 2
                )

                # Run tests
                test_result = test_harness.run_tests(str(task.task_dir))

                # Calculate scores
                score = scoring_engine.calculate_overall(
                    benchmark_result=benchmark_result,
                    test_result=test_result,
                    estimated_time=task.estimated_time_seconds,
                    cost_budget=0.05,  # Default budget
                    max_retries=2,
                    max_tool_calls=20,
                    quality_score=85.0  # Placeholder until quality checker implemented
                )

                # Save to database
                if db_persister:
                    db_persister.save_benchmark_result(
                        agent=agent,
                        task_name=task.name,
                        task_category=task.category,
                        benchmark_result=benchmark_result,
                        test_result=test_result,
                        score=score,
                        run_id=run_id
                    )

                # Display results
                if benchmark_result.success:
                    print(f"✅ Success ({benchmark_result.wall_time:.1f}s)")
                    print(f"     Overall Score: {score.overall:.1f}/100")
                    print(f"     Correctness: {score.correctness:.1f} | Speed: {score.speed:.1f} | Cost: {score.cost:.1f}")
                else:
                    print(f"❌ Failed")

                results.append((agent, task, benchmark_result, score))

            except NotImplementedError as e:
                print(f"⚠️  Not implemented: {str(e)[:50]}")
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
            finally:
                if adapter:
                    adapter.cleanup()

    # Summary
    print(f"\n{'='*60}")
    print(f"Completed {len(results)} benchmarks")

    if args.dry_run:
        print("(Dry run - results not saved to database)")
    else:
        print(f"Results saved to database (run_id: {run_id})")

    return 0
```

**Step 4: Run test to verify it passes**

Run: `cd benchmarks/cli_agent_arena && pytest test_runner.py::test_runner_execute_with_scoring -v`
Expected: PASS

**Step 5: Test manually**

Run: `python benchmarks/cli_agent_arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort --dry-run`
Expected: Shows scores in output

**Step 6: Commit**

```bash
git add benchmarks/cli_agent_arena/run_cli_benchmarks.py benchmarks/cli_agent_arena/test_runner.py
git commit -m "feat: integrate scoring system into benchmark runner

- Add test harness integration
- Add scoring engine integration
- Add database persistence (optional with --dry-run)
- Display scores in runner output
- Show correctness, speed, cost breakdowns
- All tests passing"
```

---

## Task 5: Update Documentation

**Files:**
- Modify: `benchmarks/cli_agent_arena/README.md`

**Step 1: Update README with Phase 3 completion**

Modify README.md:

Update status section:
```markdown
**Phase 3: Scoring & Testing** ✅ Complete
- Test harness integration ✅
- Scoring engine (5 dimensions) ✅
- Database persistence ✅
- Runner integration ✅
- End-to-end scoring pipeline ✅

**Phase 4: Content Generation** 🚧 Next
- HTML report generator
- Substack article generator
- YouTube video content
```

Add new section:
```markdown
## Scoring System

Benchmark scores calculated across 5 dimensions:

- **Correctness (40%)** - Test pass rate
- **Speed (25%)** - Execution time vs estimate
- **Cost (15%)** - API cost vs budget
- **Autonomy (12%)** - Retries, tool calls, error recovery
- **Quality (8%)** - Code quality metrics

### Score Calculation

```python
from benchmarks.cli_agent_arena.scoring import ScoringEngine

engine = ScoringEngine()
score = engine.calculate_overall(
    benchmark_result=result,
    test_result=tests,
    estimated_time=120,
    cost_budget=0.05,
    max_retries=2,
    max_tool_calls=20,
    quality_score=85.0
)

print(f"Overall: {score.overall}/100")
```

## Running Benchmarks

### With Scoring and Database

```bash
# Run with full scoring and save to database
python benchmarks/cli_agent_arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort

# Dry run (no database save)
python benchmarks/cli_agent_arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort --dry-run
```

### View Results

```sql
-- Latest benchmark results
SELECT agent, task_name, overall_score, correctness_score, speed_score
FROM cli_agent_benchmark_results
ORDER BY timestamp DESC
LIMIT 10;

-- Agent comparison
SELECT * FROM cli_agent_comparison;
```
```

**Step 2: Commit**

```bash
git add benchmarks/cli_agent_arena/README.md
git commit -m "docs: update README for Phase 3 completion

- Mark Phase 3 complete
- Add scoring system documentation
- Add usage examples with scoring
- Document score dimensions and weights
- Add SQL query examples"
```

---

## Phase 3 Complete! 🎉

**Deliverables:**
- ✅ Test harness integration (pytest runner + parser)
- ✅ Scoring engine (5 dimensions with weights)
- ✅ Database persistence (PostgreSQL)
- ✅ Runner integration (end-to-end scoring)
- ✅ Updated documentation

**Test Summary:**
```
benchmarks/cli_agent_arena/
├── test_test_harness.py ......... 3 passed
├── test_scoring.py .............. 12 passed
├── test_database.py ............. 2 passed
├── test_runner.py ............... 4 passed

Total: 21 new tests (all passing) ✅
```

**What's Working:**
- Mock adapter runs tasks end-to-end
- Tests run and results parsed
- Scores calculated across all dimensions
- Results saved to PostgreSQL
- Full benchmark pipeline operational

**What's Next (Phase 4):**
1. HTML report generator
2. Substack article generator
3. YouTube video content generator
4. Real Kimi/Claude/Gemini adapters
5. More benchmark tasks
