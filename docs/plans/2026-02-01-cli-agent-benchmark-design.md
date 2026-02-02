# CLI Agent Benchmark Arena - Design Document

**Date:** 2026-02-01
**Status:** Design Approved
**Goal:** Comprehensive benchmark system comparing AI CLI coding agents (Kimi CLI, Claude Code, Gemini CLI) for YouTube/Substack content, personal decision-making, and community research

---

## Project Goals

1. **YouTube/Substack Content** - Entertaining head-to-head comparisons with clear winners/losers
2. **Personal Decision Making** - Help choose which CLI agent for different tasks
3. **Community Research** - Rigorous, reproducible data for other developers

## Key Metrics (Priority Order)

1. **Speed** - Wall-clock time from prompt to working solution
2. **Correctness** - Does it work? Pass tests? Handle edge cases?
3. **Cost** - API pricing per task (real-world usage concern)
4. **Autonomy** - Hand-holding needed, error recovery ability
5. **Code Quality** - Readability, maintainability, best practices

## Task Categories

- **Algorithm Challenges** - Quicksort, binary search, LRU cache, etc.
- **Feature Development** - "Add user auth", "Implement dark mode"
- **Debugging Tasks** - Fix broken code, diagnose issues
- **Multi-File Refactoring** - Split monoliths, add TypeScript
- **Real-World Patterns** - Config parsing, file I/O, API clients

## Execution Model

**Fully Automated** with screen recording:
- Script-driven benchmark execution
- Automated `asciinema` terminal recording
- Side-by-side comparison videos for YouTube B-roll
- GIF/MP4 export for Substack articles
- Reproducible, scientific rigor

## Autonomy Measurement

**Combination Score** weighted by:
- **Retry count** - How many attempts before success
- **Error recovery** - Successfully recovers from failures
- **Tool call efficiency** - No redundant reads/searches
- **Question asking** - Fewer clarifications = more autonomous (context-dependent)

---

## Architecture Overview

### Approach: Hybrid - Shared Tasks, Separate Execution

**Why this approach:**
- Reuses task definitions (DRY principle)
- Purpose-built CLI execution without compromising existing LLM benchmarks
- Unified reporting (compare LLMs vs CLI agents!)
- Incremental development (build CLI runner alongside existing)

### Directory Structure

```
benchmarks/
├── llm-suite/                    # Existing LLM benchmarks
│   ├── run_benchmarks.py         # LLM runner (unchanged)
│   └── ...
├── cli-agent-arena/              # New CLI agent benchmarks
│   ├── run_cli_benchmarks.py     # CLI agent runner
│   ├── adapters/                 # CLI-specific adapters
│   │   ├── base.py               # Abstract base adapter
│   │   ├── kimi.py               # Kimi CLI adapter
│   │   ├── claude.py             # Claude Code adapter
│   │   └── gemini.py             # Gemini CLI adapter
│   ├── recordings/               # asciinema recordings
│   ├── reporting/                # Report generators
│   │   ├── html_report.py
│   │   ├── substack_article.py
│   │   └── youtube_content.py
│   └── reports/                  # Generated HTML/JSON reports
└── shared-tasks/                 # Shared task definitions
    ├── algorithms/
    │   ├── quicksort/
    │   │   ├── task.yaml         # Task metadata
    │   │   ├── prompt.md         # Task description
    │   │   ├── starter/          # Starting code (if any)
    │   │   └── tests/            # Validation tests
    │   └── ...
    ├── features/                 # Feature development tasks
    ├── debugging/                # Debugging challenges
    └── refactoring/              # Refactoring tasks
```

### Execution Flow

1. `run_cli_benchmarks.py --agent kimi --tasks algorithms/quicksort`
2. Load task definition from `shared-tasks/`
3. Spin up CLI agent via adapter (spawn process)
4. Wrap execution with `asciinema` recording
5. Feed prompt, capture output, run tests
6. Calculate scores (speed, correctness, cost, autonomy, quality)
7. Save to PostgreSQL + JSON report
8. Generate visualization

---

## Task Definition Format

### Task Metadata (`task.yaml`)

```yaml
name: quicksort
category: algorithms
difficulty: medium
estimated_time: 180  # seconds
description: "Implement quicksort algorithm in Python"

# Scoring weights (total = 100)
weights:
  correctness: 40
  speed: 25
  cost: 15
  autonomy: 12
  code_quality: 8

# Cost expectations (for scoring)
cost_budget:
  kimi: 0.02      # $0.02 via NVIDIA free tier (estimated tokens)
  claude: 0.05    # $0.05 via Anthropic API
  gemini: 0.03    # $0.03 via Google API

# Files the agent should create/modify
expected_outputs:
  - path: "quicksort.py"
    type: "implementation"
  - path: "test_quicksort.py"
    type: "tests"  # optional - some tasks provide tests

# Autonomy scoring criteria
autonomy_criteria:
  max_retries: 2        # >2 retries = autonomy penalty
  max_tool_calls: 20    # Efficiency threshold
  error_recovery: true  # Should recover from failures
```

### Task Prompt (`prompt.md`)

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
```

## Tests Provided
See `tests/test_quicksort.py` for full test suite.
```

---

## CLI Agent Execution Pipeline

### Base Adapter Interface (`adapters/base.py`)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class BenchmarkResult:
    success: bool
    wall_time: float              # seconds
    token_count: dict             # {input: N, output: M}
    cost: float                   # USD
    retries: int                  # autonomy metric
    tool_calls: int               # autonomy metric
    error_recovered: bool         # autonomy metric
    generated_files: list[str]
    logs: str                     # Full interaction log
    recording_path: str           # asciinema file

class CLIAgentAdapter(ABC):
    @abstractmethod
    def setup(self, task_dir: str):
        """Prepare agent environment (cwd, context)"""
        pass

    @abstractmethod
    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Run task, return metrics"""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up agent process"""
        pass
```

### Adapter Implementation Pattern

Each CLI agent (Kimi, Claude, Gemini) gets a concrete adapter that:

1. **Spawns the CLI process** wrapped in `asciinema` recording
2. **Sends the task prompt** via stdin or API
3. **Monitors output** to track:
   - Retries (re-attempting failed operations)
   - Tool calls (file reads, searches, command execution)
   - Errors and recovery attempts
   - Token usage (parse from agent output)
4. **Waits for completion** or timeout
5. **Returns BenchmarkResult** with all metrics

### Execution Wrapper (`run_cli_benchmarks.py`)

```python
# Load task
task = load_task("shared-tasks/algorithms/quicksort")

# Initialize adapter
adapter = get_adapter("kimi")  # KimiCLIAdapter, ClaudeCodeAdapter, etc.

# Execute
adapter.setup(task.dir)
result = adapter.execute_task(task.prompt, timeout=task.estimated_time * 2)

# Run tests
test_results = run_pytest(task.tests_dir, result.generated_files)

# Calculate scores
scores = calculate_scores(task, result, test_results)

# Save to DB
save_benchmark_result(task, "kimi", scores, result)
```

---

## Scoring System

### Score Calculation

```python
def calculate_scores(task: Task, result: BenchmarkResult, test_results: TestResults) -> dict:
    """Calculate weighted scores across all dimensions"""

    # 1. CORRECTNESS (40% weight)
    correctness = (test_results.passed / test_results.total) * 100

    # 2. SPEED (25% weight)
    # Normalize against expected time (faster = higher score)
    time_ratio = task.estimated_time / result.wall_time
    speed = min(100, time_ratio * 100)  # Cap at 100

    # 3. COST (15% weight)
    # Compare actual cost vs budget
    budget = task.cost_budget[result.agent]
    if result.cost <= budget:
        cost = 100
    elif result.cost <= budget * 1.5:
        cost = 75  # 50% over budget
    elif result.cost <= budget * 2:
        cost = 50  # 100% over budget
    else:
        cost = 25  # Way over budget

    # 4. AUTONOMY (12% weight)
    autonomy_score = 100

    # Penalty for retries (each retry -15 points)
    if result.retries > task.autonomy_criteria.max_retries:
        autonomy_score -= (result.retries - task.autonomy_criteria.max_retries) * 15

    # Penalty for excessive tool calls (-10 points per 10 extra calls)
    if result.tool_calls > task.autonomy_criteria.max_tool_calls:
        excess = result.tool_calls - task.autonomy_criteria.max_tool_calls
        autonomy_score -= (excess // 10) * 10

    # Bonus for error recovery (+20 points)
    if result.error_recovered:
        autonomy_score += 20

    autonomy = max(0, min(100, autonomy_score))  # Clamp 0-100

    # 5. CODE QUALITY (8% weight)
    quality = run_quality_checks(result.generated_files)
    # Uses existing validation pipeline (flake8, black, complexity)

    # OVERALL SCORE (weighted average)
    overall = (
        correctness * task.weights.correctness / 100 +
        speed * task.weights.speed / 100 +
        cost * task.weights.cost / 100 +
        autonomy * task.weights.autonomy / 100 +
        quality * task.weights.code_quality / 100
    )

    return {
        "overall": overall,
        "correctness": correctness,
        "speed": speed,
        "cost": cost,
        "autonomy": autonomy,
        "code_quality": quality,
        "breakdown": {
            "test_pass_rate": test_results.passed / test_results.total,
            "wall_time": result.wall_time,
            "actual_cost": result.cost,
            "budget": budget,
            "retries": result.retries,
            "tool_calls": result.tool_calls,
            "error_recovered": result.error_recovered
        }
    }
```

### Score Interpretation

**Overall Ranges:**
- **90-100:** Excellent - Production ready
- **75-89:** Good - Minor issues, usable
- **60-74:** Fair - Significant issues, needs review
- **0-59:** Poor - Major problems, not usable

---

## Data Schema

### PostgreSQL Schema Extension

```sql
-- New table for CLI agent benchmarks
CREATE TABLE cli_agent_benchmark_results (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Task identification
    task_name VARCHAR(100) NOT NULL,
    task_category VARCHAR(50) NOT NULL,  -- algorithms, features, debugging, refactoring
    task_difficulty VARCHAR(20),         -- easy, medium, hard

    -- Agent identification
    agent_name VARCHAR(50) NOT NULL,     -- kimi, claude, gemini
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
    recording_path TEXT,                 -- asciinema file
    generated_files JSONB,               -- List of files created
    interaction_log TEXT,                -- Full conversation log

    -- Metadata
    benchmark_run_id UUID,               -- Group results from same run
    notes TEXT
);

-- Indexes for common queries
CREATE INDEX idx_cli_agent_name ON cli_agent_benchmark_results(agent_name);
CREATE INDEX idx_cli_task_name ON cli_agent_benchmark_results(task_name);
CREATE INDEX idx_cli_timestamp ON cli_agent_benchmark_results(timestamp);
CREATE INDEX idx_cli_run_id ON cli_agent_benchmark_results(benchmark_run_id);

-- View: Compare agents head-to-head
CREATE VIEW cli_agent_comparison AS
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

-- View: Agent strengths/weaknesses
CREATE VIEW cli_agent_strengths AS
SELECT
    agent_name,
    task_category,
    AVG(overall_score) as category_score,
    AVG(wall_time_seconds) as avg_time,
    AVG(actual_cost_usd) as avg_cost
FROM cli_agent_benchmark_results
GROUP BY agent_name, task_category
ORDER BY agent_name, category_score DESC;
```

---

## Screen Recording Integration

### Recording Strategy

All benchmark runs automatically recorded using `asciinema`:

1. **Start recording** before agent execution
2. **Capture full terminal session** (commands, output, timing)
3. **Save to `.cast` file** (JSON format, lightweight)
4. **Export to multiple formats** for content creation:
   - **GIF** - Quick previews for Substack
   - **MP4** - High-quality YouTube B-roll
   - **Web player** - Interactive embeds in articles

### Recording Manager

```python
class RecordingManager:
    """Handles asciinema recording for all benchmark runs"""

    def start_recording(self, agent: str, task: str, run_id: str) -> str:
        """Start asciinema recording, return path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent}_{task}_{timestamp}_{run_id}.cast"
        filepath = self.output_dir / filename
        return str(filepath)

    def export_to_gif(self, cast_file: str, max_duration: int = 60) -> str:
        """Convert .cast to GIF for YouTube B-roll"""
        gif_file = cast_file.replace(".cast", ".gif")
        subprocess.run([
            "agg", cast_file, gif_file,
            "--speed", "2",           # 2x speed for highlights
            "--cols", "120",
            "--rows", "30",
            "--theme", "monokai"
        ])
        return gif_file

    def export_to_mp4(self, cast_file: str) -> str:
        """Convert .cast to MP4 for high-quality YouTube footage"""
        mp4_file = cast_file.replace(".cast", ".mp4")
        subprocess.run(["asciinema", "render", cast_file, mp4_file])
        return mp4_file

    def create_highlight_reel(self, cast_files: list[str], task: str) -> str:
        """Create side-by-side comparison video"""
        mp4s = [self.export_to_mp4(f) for f in cast_files]
        output = f"highlights/{task}_comparison_{timestamp}.mp4"

        # Use ffmpeg to create split-screen (3 agents side-by-side)
        subprocess.run([
            "ffmpeg",
            "-i", mp4s[0],  # Kimi (left)
            "-i", mp4s[1],  # Claude (center)
            "-i", mp4s[2],  # Gemini (right)
            "-filter_complex", "[0:v][1:v][2:v]hstack=inputs=3[v]",
            "-map", "[v]",
            output
        ])
        return output
```

### Content Assets Generated

- **Individual recordings** (`.cast`) - Full session replay
- **GIF highlights** - Quick task previews
- **MP4 videos** - High-quality footage
- **Side-by-side comparisons** - Head-to-head showdowns
- **Embedded players** - Interactive terminal in articles

---

## Reporting & Visualization

### HTML Report Generator

Interactive HTML reports with:

1. **Overall Leaderboard Table**
   - Sort by any metric
   - Highlight winners/losers
   - Filter by task category

2. **Radar Chart** - Multi-dimensional comparison across all metrics

3. **Speed vs Cost Scatter Plot** - Find the sweet spot (fast + cheap)

4. **Category Performance** - Which agent excels at algorithms vs debugging vs features?

5. **Autonomy Breakdown** - Retries, tool calls, error recovery per agent

6. **Task-by-Task Breakdown** - Detailed results for each benchmark

7. **Embedded asciinema Players** - Watch agents work in-browser

### Substack Article Generator

Automated markdown article generation with:

- **TL;DR summary** with category winners
- **Embedded charts** (static images + interactive iframes)
- **GIF highlights** showing agents in action
- **Cost analysis** with running totals
- **Recommendations** - "When to use each agent"
- **Link to full interactive dashboard**

### YouTube Content Strategy

- **Intro** - Side-by-side comparison B-roll
- **Speed Test** - Timelapse with countdown timer
- **Debugging Challenge** - Watch each agent struggle/succeed
- **Cost Breakdown** - Animated charts
- **Winner Reveal** - Leaderboard with confetti

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- Set up `cli-agent-arena/` directory structure
- Create base adapter interface
- Migrate 3-5 tasks from `llm-suite` to `shared-tasks/`
- Set up PostgreSQL schema
- Implement basic `run_cli_benchmarks.py` skeleton

### Phase 2: Adapters (Week 2)
- Implement Kimi CLI adapter
- Implement Claude Code adapter
- Implement Gemini CLI adapter
- Add `asciinema` recording wrapper
- Test with 1-2 simple tasks

### Phase 3: Scoring & Testing (Week 3)
- Implement full scoring system
- Add test harness integration
- Validate autonomy metrics tracking
- Run full benchmark suite (20+ tasks)
- Debug and refine

### Phase 4: Content Generation (Week 4)
- HTML report generator
- Substack article generator
- Video export (GIF, MP4, side-by-side)
- Create first comparison article
- Record first YouTube video

### Phase 5: Polish & Launch (Week 5)
- Add remaining task categories
- Performance optimization
- Documentation
- Public GitHub repo
- Launch YouTube video + Substack article

---

## Success Metrics

**Technical:**
- ✅ 20+ benchmark tasks across all categories
- ✅ All three CLI agents integrated (Kimi, Claude, Gemini)
- ✅ Full automation (no manual intervention)
- ✅ <5% variance between runs (reproducibility)

**Content:**
- ✅ 1 comprehensive Substack article with embedded visualizations
- ✅ 1 YouTube video (10-15 min) with B-roll comparisons
- ✅ Public GitHub repo with results + methodology

**Community:**
- ✅ Reproducible by others (clear docs, open source)
- ✅ Useful for decision-making (recommendations per use case)
- ✅ Entertaining (clear winners, dramatic showdowns)

---

## Open Questions / Future Work

1. **How to handle different CLI interfaces?**
   - Some use stdin, some use API, some have interactive prompts
   - May need custom adapters per agent

2. **Token usage tracking**
   - Not all CLIs expose token counts
   - May need to parse logs or estimate from output

3. **Multi-turn tasks**
   - Some tasks may require back-and-forth conversation
   - Need to decide: allow unlimited turns or set max?

4. **Human evaluation**
   - Automated scoring might miss subjective quality
   - Consider adding manual review for top-scoring tasks?

5. **Continuous benchmarking**
   - Set up cron job to re-run benchmarks weekly?
   - Track performance over time as agents update?

---

## Related Projects

- Existing `benchmarks/llm-suite/` - LLM code generation benchmarks
- `scripts/llm-code-validator.py` - Code quality validation pipeline
- Vengeance server (RTX 4090) - Local LLM inference infrastructure
- PostgreSQL workspace database - Centralized data storage

---

## Conclusion

This benchmark system provides:

✅ **Entertainment value** - YouTube/Substack content with clear winners
✅ **Practical utility** - Data-driven decisions on which agent to use
✅ **Scientific rigor** - Reproducible, automated, comprehensive testing

Win-win-win! 🎉
