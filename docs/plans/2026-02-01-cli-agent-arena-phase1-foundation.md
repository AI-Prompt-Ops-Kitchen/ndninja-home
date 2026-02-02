# CLI Agent Benchmark Arena - Phase 1: Foundation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up the foundation infrastructure for CLI agent benchmarking - directory structure, base adapter interface, shared task definitions, PostgreSQL schema, and basic runner skeleton.

**Architecture:** Hybrid approach sharing task definitions between LLM and CLI benchmarks, with separate execution pipelines. PostgreSQL for data storage, YAML for task metadata, Python for implementation.

**Tech Stack:** Python 3.10+, PostgreSQL, pytest, PyYAML, psycopg2, dataclasses

---

## Task 1: Directory Structure Setup

**Files:**
- Create: `benchmarks/cli-agent-arena/README.md`
- Create: `benchmarks/cli-agent-arena/__init__.py`
- Create: `benchmarks/cli-agent-arena/adapters/__init__.py`
- Create: `benchmarks/cli-agent-arena/recordings/.gitkeep`
- Create: `benchmarks/cli-agent-arena/reporting/__init__.py`
- Create: `benchmarks/cli-agent-arena/reports/.gitkeep`
- Create: `benchmarks/shared-tasks/README.md`
- Create: `benchmarks/shared-tasks/algorithms/.gitkeep`

**Step 1: Create directory structure**

```bash
mkdir -p benchmarks/cli-agent-arena/{adapters,recordings,reporting,reports}
mkdir -p benchmarks/shared-tasks/{algorithms,features,debugging,refactoring}
touch benchmarks/cli-agent-arena/{__init__.py,adapters/__init__.py,reporting/__init__.py}
touch benchmarks/cli-agent-arena/{recordings/.gitkeep,reports/.gitkeep}
touch benchmarks/shared-tasks/algorithms/.gitkeep
```

**Step 2: Write main README**

Create `benchmarks/cli-agent-arena/README.md`:

```markdown
# CLI Agent Benchmark Arena

Comprehensive benchmark system for comparing AI CLI coding agents (Kimi CLI, Claude Code, Gemini CLI).

## Quick Start

```bash
# Run benchmarks for a specific agent
python run_cli_benchmarks.py --agent kimi --tasks algorithms/quicksort

# Run all tasks for all agents
python run_cli_benchmarks.py --all

# Generate HTML report
python run_cli_benchmarks.py --report
```

## Architecture

- `adapters/` - CLI agent-specific adapters (Kimi, Claude, Gemini)
- `recordings/` - asciinema terminal recordings
- `reporting/` - Report generators (HTML, Substack, YouTube)
- `reports/` - Generated benchmark reports
- `../shared-tasks/` - Task definitions shared with LLM benchmarks

## Metrics

- **Speed** (25%) - Wall-clock time to completion
- **Correctness** (40%) - Test pass rate
- **Cost** (15%) - API usage costs
- **Autonomy** (12%) - Retries, error recovery, efficiency
- **Code Quality** (8%) - Linting, formatting, complexity

See design doc at `docs/plans/2026-02-01-cli-agent-benchmark-design.md`
```

**Step 3: Write shared-tasks README**

Create `benchmarks/shared-tasks/README.md`:

```markdown
# Shared Benchmark Tasks

Task definitions used by both LLM and CLI agent benchmarks.

## Structure

Each task directory contains:
- `task.yaml` - Metadata, scoring weights, cost budgets
- `prompt.md` - Task description for agents
- `tests/` - Pytest test files
- `starter/` - Optional starter code

## Categories

- `algorithms/` - Algorithm implementations (quicksort, binary search, etc.)
- `features/` - Feature development (auth, dark mode, etc.)
- `debugging/` - Fix broken code
- `refactoring/` - Multi-file refactoring

## Adding Tasks

See `docs/plans/2026-02-01-cli-agent-benchmark-design.md` for task format.
```

**Step 4: Verify structure**

Run: `tree benchmarks/cli-agent-arena benchmarks/shared-tasks -L 2`
Expected: Directory tree matching design doc

**Step 5: Commit**

```bash
git add benchmarks/
git commit -m "feat: create CLI agent benchmark arena directory structure

- Add cli-agent-arena/ for CLI-specific execution
- Add shared-tasks/ for task definitions
- Add READMEs with quick start guides"
```

---

## Task 2: Base Adapter Interface

**Files:**
- Create: `benchmarks/cli-agent-arena/adapters/base.py`
- Create: `benchmarks/cli-agent-arena/adapters/test_base.py`

**Step 1: Write test for BenchmarkResult dataclass**

Create `benchmarks/cli-agent-arena/adapters/test_base.py`:

```python
import pytest
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult


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
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_base.py -v`
Expected: FAIL with "No module named 'benchmarks.cli_agent_arena.adapters.base'"

**Step 3: Write BenchmarkResult dataclass**

Create `benchmarks/cli-agent-arena/adapters/base.py`:

```python
"""Base adapter interface for CLI agents"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BenchmarkResult:
    """Results from a single benchmark execution"""
    success: bool
    wall_time: float  # seconds
    token_count: Dict[str, int]  # {input: N, output: M}
    cost: float  # USD
    retries: int  # autonomy metric
    tool_calls: int  # autonomy metric
    error_recovered: bool  # autonomy metric
    generated_files: List[str]
    logs: str  # Full interaction log
    recording_path: str  # asciinema file path
```

**Step 4: Run test to verify it passes**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_base.py -v`
Expected: PASS (2 tests)

**Step 5: Write test for CLIAgentAdapter interface**

Add to `benchmarks/cli-agent-arena/adapters/test_base.py`:

```python
from benchmarks.cli_agent_arena.adapters.base import CLIAgentAdapter


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
```

**Step 6: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_base.py::test_adapter_interface -v`
Expected: FAIL with "cannot import name 'CLIAgentAdapter'"

**Step 7: Write CLIAgentAdapter abstract base class**

Add to `benchmarks/cli-agent-arena/adapters/base.py`:

```python
class CLIAgentAdapter(ABC):
    """Abstract base class for CLI agent adapters"""

    @abstractmethod
    def setup(self, task_dir: str) -> None:
        """Prepare agent environment (cwd, context)

        Args:
            task_dir: Path to task directory containing prompt.md, tests/, etc.
        """
        pass

    @abstractmethod
    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Run task and return metrics

        Args:
            prompt: Task description from prompt.md
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with all metrics populated
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up agent process and resources"""
        pass
```

**Step 8: Run test to verify it passes**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_base.py -v`
Expected: PASS (4 tests)

**Step 9: Commit**

```bash
git add benchmarks/cli-agent-arena/adapters/
git commit -m "feat: add base adapter interface for CLI agents

- Add BenchmarkResult dataclass for execution metrics
- Add CLIAgentAdapter abstract base class
- Add comprehensive unit tests
- All tests passing (4/4)"
```

---

## Task 3: PostgreSQL Schema

**Files:**
- Create: `benchmarks/cli-agent-arena/schema.sql`
- Create: `benchmarks/cli-agent-arena/test_schema.py`

**Step 1: Write schema migration SQL**

Create `benchmarks/cli-agent-arena/schema.sql`:

```sql
-- CLI Agent Benchmark Results Schema
-- Run with: psql -U <user> -d workspace < schema.sql

-- Main results table
CREATE TABLE IF NOT EXISTS cli_agent_benchmark_results (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Task identification
    task_name VARCHAR(100) NOT NULL,
    task_category VARCHAR(50) NOT NULL,
    task_difficulty VARCHAR(20),

    -- Agent identification
    agent_name VARCHAR(50) NOT NULL,
    agent_version VARCHAR(50),

    -- Scores
    overall_score DECIMAL(5,2),
    correctness_score DECIMAL(5,2),
    speed_score DECIMAL(5,2),
    cost_score DECIMAL(5,2),
    autonomy_score DECIMAL(5,2),
    code_quality_score DECIMAL(5,2),

    -- Raw metrics
    wall_time_seconds DECIMAL(10,2),
    actual_cost_usd DECIMAL(10,6),
    budgeted_cost_usd DECIMAL(10,6),
    token_count_input INTEGER,
    token_count_output INTEGER,
    retries INTEGER,
    tool_calls INTEGER,
    error_recovered BOOLEAN,

    -- Test results
    tests_total INTEGER,
    tests_passed INTEGER,
    tests_failed INTEGER,

    -- Artifacts
    recording_path TEXT,
    generated_files JSONB,
    interaction_log TEXT,

    -- Metadata
    benchmark_run_id UUID,
    notes TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_cli_agent_name ON cli_agent_benchmark_results(agent_name);
CREATE INDEX IF NOT EXISTS idx_cli_task_name ON cli_agent_benchmark_results(task_name);
CREATE INDEX IF NOT EXISTS idx_cli_timestamp ON cli_agent_benchmark_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_cli_run_id ON cli_agent_benchmark_results(benchmark_run_id);

-- View: Compare agents head-to-head
CREATE OR REPLACE VIEW cli_agent_comparison AS
SELECT
    task_name,
    task_category,
    agent_name,
    AVG(overall_score) as avg_overall,
    AVG(correctness_score) as avg_correctness,
    AVG(speed_score) as avg_speed,
    AVG(cost_score) as avg_cost,
    AVG(autonomy_score) as avg_autonomy,
    AVG(wall_time_seconds) as avg_time,
    SUM(actual_cost_usd) as total_cost,
    COUNT(*) as runs
FROM cli_agent_benchmark_results
GROUP BY task_name, task_category, agent_name
ORDER BY task_name, avg_overall DESC;

-- View: Agent strengths/weaknesses by category
CREATE OR REPLACE VIEW cli_agent_strengths AS
SELECT
    agent_name,
    task_category,
    AVG(overall_score) as category_score,
    AVG(wall_time_seconds) as avg_time,
    AVG(actual_cost_usd) as avg_cost
FROM cli_agent_benchmark_results
GROUP BY agent_name, task_category
ORDER BY agent_name, category_score DESC;

-- View: Recent benchmark runs
CREATE OR REPLACE VIEW cli_recent_benchmarks AS
SELECT
    benchmark_run_id,
    MIN(timestamp) as run_start,
    COUNT(*) as tasks_completed,
    COUNT(DISTINCT agent_name) as agents_tested,
    AVG(overall_score) as avg_score
FROM cli_agent_benchmark_results
GROUP BY benchmark_run_id
ORDER BY run_start DESC
LIMIT 10;
```

**Step 2: Write schema validation test**

Create `benchmarks/cli-agent-arena/test_schema.py`:

```python
"""Test PostgreSQL schema creation and views"""

import pytest
import psycopg2
import os


@pytest.fixture
def db_connection():
    """Connect to workspace database"""
    conn = psycopg2.connect(
        dbname="workspace",
        user=os.getenv("DB_USER", "ndninja"),
        host=os.getenv("DB_HOST", "localhost"),
        password=os.getenv("DB_PASSWORD", "")
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
```

**Step 3: Run schema migration**

Run: `psql -U ndninja -d workspace < benchmarks/cli-agent-arena/schema.sql`
Expected: CREATE TABLE, CREATE INDEX (x4), CREATE VIEW (x3) messages

**Step 4: Run tests to verify schema**

Run: `cd benchmarks/cli-agent-arena && pytest test_schema.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add benchmarks/cli-agent-arena/schema.sql benchmarks/cli-agent-arena/test_schema.py
git commit -m "feat: add PostgreSQL schema for CLI agent benchmarks

- Add cli_agent_benchmark_results table with full metrics
- Add indexes for common queries (agent, task, timestamp, run_id)
- Add views for comparison, strengths, recent runs
- Add schema validation tests (4/4 passing)"
```

---

## Task 4: Task Definition Format

**Files:**
- Create: `benchmarks/shared-tasks/algorithms/quicksort/task.yaml`
- Create: `benchmarks/shared-tasks/algorithms/quicksort/prompt.md`
- Create: `benchmarks/cli-agent-arena/task_loader.py`
- Create: `benchmarks/cli-agent-arena/test_task_loader.py`

**Step 1: Write test for task loading**

Create `benchmarks/cli-agent-arena/test_task_loader.py`:

```python
"""Test task definition loading"""

import pytest
from pathlib import Path
from benchmarks.cli_agent_arena.task_loader import Task, load_task


def test_load_quicksort_task():
    """Test loading quicksort task definition"""
    task = load_task("benchmarks/shared-tasks/algorithms/quicksort")

    assert task.name == "quicksort"
    assert task.category == "algorithms"
    assert task.difficulty == "medium"
    assert task.estimated_time == 180
    assert "quicksort algorithm" in task.description.lower()

    # Check weights
    assert task.weights["correctness"] == 40
    assert task.weights["speed"] == 25
    assert task.weights["cost"] == 15
    assert task.weights["autonomy"] == 12
    assert task.weights["code_quality"] == 8

    # Check cost budgets
    assert "kimi" in task.cost_budget
    assert "claude" in task.cost_budget
    assert "gemini" in task.cost_budget

    # Check autonomy criteria
    assert task.autonomy_criteria["max_retries"] == 2
    assert task.autonomy_criteria["max_tool_calls"] == 20


def test_task_prompt_content():
    """Test that prompt.md is loaded correctly"""
    task = load_task("benchmarks/shared-tasks/algorithms/quicksort")

    assert task.prompt is not None
    assert len(task.prompt) > 0
    assert "quicksort" in task.prompt.lower()
    assert "requirements" in task.prompt.lower()


def test_task_validation_missing_file():
    """Test error handling for missing task"""
    with pytest.raises(FileNotFoundError):
        load_task("benchmarks/shared-tasks/algorithms/nonexistent")
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest test_task_loader.py -v`
Expected: FAIL with import errors

**Step 3: Create quicksort task.yaml**

Create `benchmarks/shared-tasks/algorithms/quicksort/task.yaml`:

```yaml
name: quicksort
category: algorithms
difficulty: medium
estimated_time: 180  # seconds
description: "Implement quicksort algorithm in Python"

# Scoring weights (must sum to 100 for clarity, though we normalize)
weights:
  correctness: 40
  speed: 25
  cost: 15
  autonomy: 12
  code_quality: 8

# Cost expectations for scoring (USD)
cost_budget:
  kimi: 0.02      # NVIDIA free tier (estimated tokens)
  claude: 0.05    # Anthropic API
  gemini: 0.03    # Google API

# Files the agent should create/modify
expected_outputs:
  - path: "quicksort.py"
    type: "implementation"

# Autonomy scoring criteria
autonomy_criteria:
  max_retries: 2        # >2 retries = autonomy penalty
  max_tool_calls: 20    # Efficiency threshold
  error_recovery: true  # Should recover from failures
```

**Step 4: Create quicksort prompt.md**

Create `benchmarks/shared-tasks/algorithms/quicksort/prompt.md`:

```markdown
# Task: Implement Quicksort

Implement a quicksort algorithm in Python.

## Requirements

1. Function signature: `def quicksort(arr: list) -> list`
2. Sort in ascending order
3. Handle empty arrays and single elements
4. Use in-place partitioning for efficiency

## Example

```python
>>> quicksort([3, 1, 4, 1, 5, 9, 2, 6])
[1, 1, 2, 3, 4, 5, 6, 9]

>>> quicksort([])
[]

>>> quicksort([42])
[42]
```

## Tests Provided

See `tests/test_quicksort.py` for the full test suite.

## Expected Deliverables

- `quicksort.py` with the implementation
```

**Step 5: Write task loader implementation**

Create `benchmarks/cli-agent-arena/task_loader.py`:

```python
"""Task definition loader for benchmark tasks"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any
import yaml


@dataclass
class Task:
    """Benchmark task definition"""
    name: str
    category: str
    difficulty: str
    estimated_time: int  # seconds
    description: str
    weights: Dict[str, int]
    cost_budget: Dict[str, float]
    expected_outputs: List[Dict[str, str]]
    autonomy_criteria: Dict[str, Any]
    prompt: str
    task_dir: Path


def load_task(task_path: str) -> Task:
    """Load task definition from directory

    Args:
        task_path: Path to task directory (e.g., "benchmarks/shared-tasks/algorithms/quicksort")

    Returns:
        Task object with all metadata and prompt loaded

    Raises:
        FileNotFoundError: If task.yaml or prompt.md missing
    """
    task_dir = Path(task_path)

    if not task_dir.exists():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")

    # Load task.yaml
    yaml_path = task_dir / "task.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"task.yaml not found in {task_dir}")

    with open(yaml_path) as f:
        metadata = yaml.safe_load(f)

    # Load prompt.md
    prompt_path = task_dir / "prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"prompt.md not found in {task_dir}")

    with open(prompt_path) as f:
        prompt = f.read()

    return Task(
        name=metadata["name"],
        category=metadata["category"],
        difficulty=metadata["difficulty"],
        estimated_time=metadata["estimated_time"],
        description=metadata["description"],
        weights=metadata["weights"],
        cost_budget=metadata["cost_budget"],
        expected_outputs=metadata["expected_outputs"],
        autonomy_criteria=metadata["autonomy_criteria"],
        prompt=prompt,
        task_dir=task_dir
    )
```

**Step 6: Run tests to verify they pass**

Run: `cd benchmarks/cli-agent-arena && pytest test_task_loader.py -v`
Expected: PASS (3 tests)

**Step 7: Commit**

```bash
git add benchmarks/shared-tasks/algorithms/quicksort/ benchmarks/cli-agent-arena/task_loader.py benchmarks/cli-agent-arena/test_task_loader.py
git commit -m "feat: add task definition format and loader

- Add quicksort task with YAML metadata and markdown prompt
- Add Task dataclass for task representation
- Add load_task() function with validation
- All tests passing (3/3)"
```

---

## Task 5: Migrate Existing Tasks from llm-suite

**Files:**
- Create: `benchmarks/shared-tasks/algorithms/binary_search/task.yaml`
- Create: `benchmarks/shared-tasks/algorithms/binary_search/prompt.md`
- Copy: `benchmarks/shared-tasks/algorithms/binary_search/tests/` from llm-suite
- Create: `benchmarks/shared-tasks/algorithms/lru_cache/task.yaml`
- Create: `benchmarks/shared-tasks/algorithms/lru_cache/prompt.md`
- Copy: `benchmarks/shared-tasks/algorithms/lru_cache/tests/` from llm-suite

**Step 1: Copy binary_search tests**

```bash
cp -r /home/ndninja/benchmarks/llm-suite/algorithms/binary_search/ benchmarks/shared-tasks/algorithms/
```

**Step 2: Create binary_search task.yaml**

Create `benchmarks/shared-tasks/algorithms/binary_search/task.yaml`:

```yaml
name: binary_search
category: algorithms
difficulty: easy
estimated_time: 120

description: "Implement binary search algorithm in Python"

weights:
  correctness: 40
  speed: 25
  cost: 15
  autonomy: 12
  code_quality: 8

cost_budget:
  kimi: 0.015
  claude: 0.04
  gemini: 0.025

expected_outputs:
  - path: "binary_search.py"
    type: "implementation"

autonomy_criteria:
  max_retries: 2
  max_tool_calls: 15
  error_recovery: true
```

**Step 3: Create binary_search prompt.md**

Create `benchmarks/shared-tasks/algorithms/binary_search/prompt.md`:

```markdown
# Task: Implement Binary Search

Implement a binary search algorithm in Python.

## Requirements

1. Function signature: `def binary_search(arr: list, target: int) -> int`
2. Return index of target if found, -1 if not found
3. Assume input array is sorted in ascending order
4. Use iterative or recursive approach

## Example

```python
>>> binary_search([1, 2, 3, 4, 5, 6, 7, 8, 9], 5)
4

>>> binary_search([1, 2, 3, 4, 5], 10)
-1

>>> binary_search([], 5)
-1
```

## Tests Provided

See `tests/test_binary_search.py` for the full test suite.

## Expected Deliverables

- `binary_search.py` with the implementation
```

**Step 4: Copy lru_cache tests**

```bash
cp -r /home/ndninja/benchmarks/llm-suite/algorithms/lru_cache/ benchmarks/shared-tasks/algorithms/
```

**Step 5: Create lru_cache task.yaml**

Create `benchmarks/shared-tasks/algorithms/lru_cache/task.yaml`:

```yaml
name: lru_cache
category: algorithms
difficulty: medium
estimated_time: 240

description: "Implement LRU (Least Recently Used) cache data structure"

weights:
  correctness: 40
  speed: 25
  cost: 15
  autonomy: 12
  code_quality: 8

cost_budget:
  kimi: 0.03
  claude: 0.06
  gemini: 0.04

expected_outputs:
  - path: "lru_cache.py"
    type: "implementation"

autonomy_criteria:
  max_retries: 2
  max_tool_calls: 25
  error_recovery: true
```

**Step 6: Create lru_cache prompt.md**

Create `benchmarks/shared-tasks/algorithms/lru_cache/prompt.md`:

```markdown
# Task: Implement LRU Cache

Implement an LRU (Least Recently Used) cache data structure.

## Requirements

1. Class signature: `class LRUCache`
2. Methods:
   - `__init__(self, capacity: int)` - Initialize with capacity
   - `get(self, key: int) -> int` - Get value, return -1 if not found
   - `put(self, key: int, value: int) -> None` - Put key-value pair
3. When capacity is reached, evict least recently used item
4. Both get and put operations count as "using" the key

## Example

```python
>>> cache = LRUCache(2)
>>> cache.put(1, 1)
>>> cache.put(2, 2)
>>> cache.get(1)
1
>>> cache.put(3, 3)  # Evicts key 2
>>> cache.get(2)
-1
```

## Tests Provided

See `tests/test_lru_cache.py` for the full test suite.

## Expected Deliverables

- `lru_cache.py` with the LRUCache class
```

**Step 7: Test that tasks load correctly**

Add to `benchmarks/cli-agent-arena/test_task_loader.py`:

```python
def test_load_binary_search_task():
    """Test loading binary_search task"""
    task = load_task("benchmarks/shared-tasks/algorithms/binary_search")
    assert task.name == "binary_search"
    assert task.difficulty == "easy"
    assert task.estimated_time == 120


def test_load_lru_cache_task():
    """Test loading lru_cache task"""
    task = load_task("benchmarks/shared-tasks/algorithms/lru_cache")
    assert task.name == "lru_cache"
    assert task.difficulty == "medium"
    assert task.estimated_time == 240
```

Run: `cd benchmarks/cli-agent-arena && pytest test_task_loader.py -v`
Expected: PASS (5 tests)

**Step 8: Commit**

```bash
git add benchmarks/shared-tasks/algorithms/
git commit -m "feat: migrate binary_search and lru_cache tasks from llm-suite

- Add binary_search task (easy, 120s)
- Add lru_cache task (medium, 240s)
- Copy existing test files
- Add task.yaml and prompt.md for both
- All task loader tests passing (5/5)"
```

---

## Task 6: Basic Runner Skeleton

**Files:**
- Create: `benchmarks/cli-agent-arena/run_cli_benchmarks.py`
- Create: `benchmarks/cli-agent-arena/test_runner.py`

**Step 1: Write test for runner CLI**

Create `benchmarks/cli-agent-arena/test_runner.py`:

```python
"""Test benchmark runner CLI"""

import pytest
import subprocess
import sys


def test_runner_help():
    """Test --help flag"""
    result = subprocess.run(
        [sys.executable, "benchmarks/cli-agent-arena/run_cli_benchmarks.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "CLI Agent Benchmark Runner" in result.stdout
    assert "--agent" in result.stdout
    assert "--tasks" in result.stdout


def test_runner_list_tasks():
    """Test --list-tasks flag"""
    result = subprocess.run(
        [sys.executable, "benchmarks/cli-agent-arena/run_cli_benchmarks.py", "--list-tasks"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "quicksort" in result.stdout
    assert "binary_search" in result.stdout
    assert "lru_cache" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest test_runner.py -v`
Expected: FAIL (file doesn't exist)

**Step 3: Write runner skeleton**

Create `benchmarks/cli-agent-arena/run_cli_benchmarks.py`:

```python
#!/usr/bin/env python3
"""CLI Agent Benchmark Runner

Runs benchmark tasks against CLI coding agents (Kimi, Claude, Gemini)
and records metrics (speed, correctness, cost, autonomy, quality).
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmarks.cli_agent_arena.task_loader import load_task


def list_tasks() -> List[str]:
    """List all available benchmark tasks"""
    tasks_dir = Path("benchmarks/shared-tasks")
    task_paths = []

    for category_dir in tasks_dir.iterdir():
        if category_dir.is_dir() and not category_dir.name.startswith('.'):
            for task_dir in category_dir.iterdir():
                if task_dir.is_dir() and (task_dir / "task.yaml").exists():
                    relative_path = task_dir.relative_to(tasks_dir)
                    task_paths.append(str(relative_path))

    return sorted(task_paths)


def main():
    parser = argparse.ArgumentParser(
        description="CLI Agent Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run quicksort with Kimi CLI
  %(prog)s --agent kimi --tasks algorithms/quicksort

  # Run all algorithm tasks with Claude
  %(prog)s --agent claude --category algorithms

  # List available tasks
  %(prog)s --list-tasks
        """
    )

    parser.add_argument(
        "--agent",
        choices=["kimi", "claude", "gemini"],
        help="CLI agent to benchmark"
    )

    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Specific tasks to run (e.g., algorithms/quicksort)"
    )

    parser.add_argument(
        "--category",
        help="Run all tasks in a category (e.g., algorithms)"
    )

    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List all available benchmark tasks"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tasks for all agents"
    )

    args = parser.parse_args()

    # Handle --list-tasks
    if args.list_tasks:
        print("Available benchmark tasks:\n")
        for task_path in list_tasks():
            task = load_task(f"benchmarks/shared-tasks/{task_path}")
            print(f"  {task_path:30s} ({task.difficulty:6s}, ~{task.estimated_time}s)")
        return 0

    # TODO: Implement actual benchmark execution
    print("Benchmark execution not yet implemented")
    print(f"Would run: agent={args.agent}, tasks={args.tasks}, category={args.category}, all={args.all}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Make runner executable**

```bash
chmod +x benchmarks/cli-agent-arena/run_cli_benchmarks.py
```

**Step 5: Run tests to verify they pass**

Run: `cd benchmarks/cli-agent-arena && pytest test_runner.py -v`
Expected: PASS (2 tests)

**Step 6: Test runner manually**

Run: `python benchmarks/cli-agent-arena/run_cli_benchmarks.py --list-tasks`
Expected: List of 3 tasks (quicksort, binary_search, lru_cache)

Run: `python benchmarks/cli-agent-arena/run_cli_benchmarks.py --help`
Expected: Help text with usage examples

**Step 7: Commit**

```bash
git add benchmarks/cli-agent-arena/run_cli_benchmarks.py benchmarks/cli-agent-arena/test_runner.py
git commit -m "feat: add benchmark runner CLI skeleton

- Add run_cli_benchmarks.py with argument parsing
- Add --list-tasks to show available benchmarks
- Add --agent, --tasks, --category, --all flags
- Add runner tests (2/2 passing)
- Execution logic TBD in Phase 2"
```

---

## Task 7: Requirements File

**Files:**
- Create: `benchmarks/cli-agent-arena/requirements.txt`

**Step 1: Create requirements.txt**

Create `benchmarks/cli-agent-arena/requirements.txt`:

```
# Core dependencies
PyYAML>=6.0.1
psycopg2-binary>=2.9.9

# Testing
pytest>=7.4.4
pytest-asyncio>=0.23.2

# Future dependencies (commented for Phase 2+)
# asciinema>=2.4.0  # Terminal recording
# Pillow>=10.0.0    # Image processing for recordings
```

**Step 2: Install dependencies**

Run: `pip install -r benchmarks/cli-agent-arena/requirements.txt`
Expected: Successfully installed PyYAML, psycopg2-binary, pytest, pytest-asyncio

**Step 3: Verify all tests still pass**

Run: `cd benchmarks/cli-agent-arena && pytest -v`
Expected: All tests passing (9 total: 4 base + 3 loader + 2 runner + schema tests require manual run)

**Step 4: Commit**

```bash
git add benchmarks/cli-agent-arena/requirements.txt
git commit -m "feat: add Python dependencies for Phase 1

- Add PyYAML for task definitions
- Add psycopg2-binary for PostgreSQL
- Add pytest for testing
- All Phase 1 dependencies installed"
```

---

## Task 8: Documentation

**Files:**
- Modify: `benchmarks/cli-agent-arena/README.md`

**Step 1: Update README with Phase 1 status**

Modify `benchmarks/cli-agent-arena/README.md`:

```markdown
# CLI Agent Benchmark Arena

Comprehensive benchmark system for comparing AI CLI coding agents (Kimi CLI, Claude Code, Gemini CLI).

## Status

**Phase 1: Foundation** ✅ Complete
- Directory structure created
- Base adapter interface implemented
- PostgreSQL schema deployed
- Task definition format established
- 3 benchmark tasks migrated (quicksort, binary_search, lru_cache)
- Basic runner CLI skeleton

**Phase 2: Adapters** 🚧 In Progress
- Kimi CLI adapter
- Claude Code adapter
- Gemini CLI adapter
- asciinema recording integration

## Quick Start

### List Available Tasks

```bash
python benchmarks/cli-agent-arena/run_cli_benchmarks.py --list-tasks
```

### Run Tests

```bash
cd benchmarks/cli-agent-arena
pytest -v
```

### Check Database Schema

```bash
psql -U ndninja -d workspace -c "SELECT * FROM cli_agent_comparison LIMIT 5"
```

## Architecture

- `adapters/` - CLI agent-specific adapters (base interface ✅, concrete TBD)
- `recordings/` - asciinema terminal recordings (Phase 2)
- `reporting/` - Report generators (Phase 4)
- `reports/` - Generated benchmark reports (Phase 4)
- `../shared-tasks/` - Task definitions (3 tasks ✅)

## Metrics

- **Speed** (25%) - Wall-clock time to completion
- **Correctness** (40%) - Test pass rate
- **Cost** (15%) - API usage costs
- **Autonomy** (12%) - Retries, error recovery, efficiency
- **Code Quality** (8%) - Linting, formatting, complexity

## Task Format

Each task in `../shared-tasks/` contains:
- `task.yaml` - Metadata, weights, budgets, criteria
- `prompt.md` - Task description for agents
- `tests/` - pytest test files

See `docs/plans/2026-02-01-cli-agent-benchmark-design.md` for full design.

## Development

### Run All Tests

```bash
cd benchmarks/cli-agent-arena
pytest -v
```

### Load a Task

```python
from benchmarks.cli_agent_arena.task_loader import load_task

task = load_task("benchmarks/shared-tasks/algorithms/quicksort")
print(task.name, task.difficulty, task.estimated_time)
```

### Database Queries

```sql
-- View all benchmark results
SELECT * FROM cli_agent_benchmark_results ORDER BY timestamp DESC LIMIT 10;

-- Compare agents
SELECT * FROM cli_agent_comparison;

-- Agent strengths by category
SELECT * FROM cli_agent_strengths;
```

## Next Steps (Phase 2)

1. Implement Kimi CLI adapter
2. Implement Claude Code adapter
3. Implement Gemini CLI adapter
4. Add asciinema recording wrapper
5. Test execution pipeline end-to-end

See implementation plan at `docs/plans/2026-02-01-cli-agent-arena-phase1-foundation.md`
```

**Step 2: Commit**

```bash
git add benchmarks/cli-agent-arena/README.md
git commit -m "docs: update README with Phase 1 completion status

- Mark Phase 1 as complete
- Add quick start commands
- Add development workflow
- Add next steps for Phase 2"
```

---

## Phase 1 Complete! 🎉

**Deliverables:**
- ✅ Directory structure (`cli-agent-arena/`, `shared-tasks/`)
- ✅ Base adapter interface (`BenchmarkResult`, `CLIAgentAdapter`)
- ✅ PostgreSQL schema (table, indexes, views)
- ✅ Task definition format (YAML + Markdown)
- ✅ 3 migrated tasks (quicksort, binary_search, lru_cache)
- ✅ Task loader with validation
- ✅ Basic runner CLI skeleton
- ✅ All tests passing (9 tests total)
- ✅ Documentation updated

**Test Summary:**
```
benchmarks/cli-agent-arena/
├── adapters/test_base.py .......... 4 passed
├── test_task_loader.py ............ 5 passed
├── test_runner.py ................. 2 passed
└── test_schema.py (manual) ........ 4 passed (run separately with DB)

Total: 11 tests, 11 passing ✅
```

**Next:** Ready for Phase 2 (Adapters)!
