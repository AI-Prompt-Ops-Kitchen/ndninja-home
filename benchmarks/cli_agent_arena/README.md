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
- **40 tests passing, 4 skipped**

**Phase 2: Adapters** ✅ Complete
- asciinema recording manager ✅
- Mock adapter for testing ✅
- Kimi CLI adapter (stub) ✅
- Claude Code adapter (stub) ✅
- Gemini CLI adapter (stub) ✅
- Adapter factory ✅
- Runner integration ✅
- End-to-end execution with mock adapter ✅

**Phase 3: Scoring & Testing** ✅ Complete
- Test harness for correctness validation ✅
- Scoring engine (5 dimensions) ✅
- Database persistence layer ✅
- Runner integration with scoring ✅
- **55 tests passing, 4 skipped**

**Phase 4: Reporting & Analytics** ✅ Complete

**Milestone 1: Kimi + Basic Report** ✅ Complete
- Code quality analysis (pylint/flake8) ✅
- Output parsers (BaseOutputParser, KimiParser) ✅
- Real Kimi CLI adapter implementation ✅
- HTML report generator with dashboard ✅
- **85 tests passing, 4 skipped**

**Milestone 2: Claude + Comparison** ✅ Complete
- Claude Code adapter implementation ✅
- Claude output parser ✅
- Multi-agent comparison reports ✅
- **105+ tests passing, 4 skipped**

**Milestone 3: Gemini + Polish** ✅ Complete
- Gemini CLI adapter (GeminiParser + GeminiAdapter) ✅
- Three-way comparison dashboard with radar chart ✅
- Agent ranking with medal icons (1st/2nd/3rd) ✅
- Autonomy metric (retries + error recovery) ✅
- Path-dependent test failures fixed ✅
- Restored missing shared-tasks data files ✅
- **118 tests passing, 3 skipped**

## Quick Start

### Milestone 1 Usage Examples

```bash
# Run Kimi CLI on a task (requires kimi-cli installed)
python benchmarks/cli_agent_arena/run_cli_benchmarks.py --agent kimi --tasks algorithms/quicksort

# Generate HTML report from results
python -c "
from benchmarks.cli_agent_arena.reporting import HTMLGenerator
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult

result = BenchmarkResult(
    success=True, wall_time=45.2, token_count={'input': 1500, 'output': 2300},
    cost=0.038, retries=0, tool_calls=8, error_recovered=True,
    generated_files=['quicksort.py'], logs='...', recording_path='recording.cast',
    quality_score=87.5
)

generator = HTMLGenerator()
html = generator.generate({'kimi': result}, 'algorithms/quicksort')
generator.save(html, 'reports/latest.html')
print('Report saved to reports/latest.html')
"

# Analyze code quality
python -c "
from benchmarks.cli_agent_arena.quality import QualityAnalyzer

analyzer = QualityAnalyzer()
score = analyzer.analyze(['quicksort.py'])
print(f'Quality score: {score}/100')
"

# Parse Kimi CLI output
python -c "
from benchmarks.cli_agent_arena.adapters.parsers import KimiParser

parser = KimiParser()
metrics = parser.extract_metrics(
    'Executing tool: write_file\ninput=1500, output=2300', ''
)
print(f'Tokens: {metrics[\"tokens\"]}, Cost: ${metrics[\"cost\"]:.3f}')
"
```

### Milestone 2 Usage Examples

```bash
# Run both Kimi and Claude on same task for comparison
python benchmarks/cli_agent_arena/run_cli_benchmarks.py \
  --agent kimi,claude \
  --tasks algorithms/quicksort

# Generate comparison report from database
python -c "
from benchmarks.cli_agent_arena.reporting import HTMLGenerator
from benchmarks.cli_agent_arena.database import DatabaseClient

db = DatabaseClient()
results = db.get_results_for_task('algorithms/quicksort')

# results = {'kimi': BenchmarkResult(...), 'claude': BenchmarkResult(...)}
generator = HTMLGenerator()
html = generator.generate_comparison(results, 'algorithms/quicksort')
generator.save(html, 'reports/comparison.html')
print('Comparison report saved to reports/comparison.html')
"

# Parse Claude Code output
python -c "
from benchmarks.cli_agent_arena.adapters.parsers import ClaudeParser

parser = ClaudeParser()
output = '''
Using tool: Read
Using tool: Write
Input tokens: 1,234
Output tokens: 567
'''
metrics = parser.extract_metrics(output, '', exit_code=0)
print(f'Tokens: {metrics[\"token_count\"]}, Cost: ${metrics[\"cost\"]:.4f}')
print(f'Tool calls: {metrics[\"tool_calls\"]}, Retries: {metrics[\"retries\"]}')
"
```

### Milestone 3 Usage Examples

```bash
# Run all three agents on the same task
python benchmarks/cli_agent_arena/run_cli_benchmarks.py --all --tasks algorithms/quicksort --dry-run

# Generate three-way comparison with radar chart
python -c "
from benchmarks.cli_agent_arena.reporting import HTMLGenerator
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult

# Example results for all three agents
results = {
    'kimi': BenchmarkResult(success=True, wall_time=45.2, token_count={'input': 1500, 'output': 2300}, cost=0.038, retries=1, tool_calls=12, error_recovered=True, generated_files=['quicksort.py'], logs='...', recording_path='', quality_score=87.5),
    'claude': BenchmarkResult(success=True, wall_time=38.7, token_count={'input': 1200, 'output': 1800}, cost=0.042, retries=0, tool_calls=8, error_recovered=False, generated_files=['quicksort.py'], logs='...', recording_path='', quality_score=92.3),
    'gemini': BenchmarkResult(success=True, wall_time=32.1, token_count={'input': 2000, 'output': 2500}, cost=0.0012, retries=0, tool_calls=10, error_recovered=False, generated_files=['quicksort.py'], logs='...', recording_path='', quality_score=89.0),
}

generator = HTMLGenerator()
html = generator.generate_comparison(results, 'algorithms/quicksort')
generator.save(html, 'reports/three-way-comparison.html')
print('Three-way comparison saved to reports/three-way-comparison.html')
"

# Parse Gemini CLI JSON output
python -c "
from benchmarks.cli_agent_arena.adapters.parsers import GeminiParser

parser = GeminiParser()
import json
output = json.dumps({
    'response': 'done',
    'stats': {'models': [{'name': 'gemini-2.0-flash', 'tokens': {'input': 2000, 'output': 2500}}], 'tools': {'totalCalls': 10}}
})
metrics = parser.extract_metrics(output, '')
print(f'Tokens: {metrics[\"tokens\"]}, Cost: \${metrics[\"cost\"]:.4f}')
print(f'Tool calls: {metrics[\"tool_calls\"]}')
"
```

### Check Adapter Availability

```bash
python benchmarks/cli_agent_arena/run_cli_benchmarks.py --list-tasks
python -c "from benchmarks.cli_agent_arena.adapter_factory import check_adapter_availability; print(check_adapter_availability())"
```

### Run Mock Benchmark

```bash
# Test with mock adapter (no real CLI needed)
python benchmarks/cli_agent_arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort --dry-run
```

### Run All Tests

```bash
cd benchmarks/cli_agent_arena
python3 -m pytest -v
# Expected: 118 tests passing, 3 skipped
```

### Check Database Schema

```bash
psql -U ndninja -d workspace -c "SELECT * FROM cli_agent_comparison LIMIT 5"
```

## Architecture

- `adapters/` - CLI agent adapters ✅
  - `base.py` - Abstract interface with BenchmarkResult dataclass
  - `mock.py` - Testing adapter
  - `kimi.py` - Kimi CLI (real implementation) ✅
  - `claude.py` - Claude Code (real implementation) ✅
  - `gemini.py` - Gemini CLI (real implementation) ✅
  - `parsers/` - Output parsers for CLI tools ✅
    - `base_parser.py` - BaseOutputParser interface
    - `kimi_parser.py` - KimiParser implementation
    - `claude_parser.py` - ClaudeParser implementation ✅
    - `gemini_parser.py` - GeminiParser (JSON) implementation ✅
- `quality/` - Code quality analysis ✅
  - `analyzer.py` - QualityAnalyzer (pylint/flake8)
- `reporting/` - Report generators ✅
  - `html_generator.py` - HTMLGenerator class
  - `templates/dashboard.html` - Jinja2 template
- `recording_manager.py` - asciinema wrapper ✅
- `adapter_factory.py` - Adapter registry ✅
- `task_loader.py` - Task definition loader ✅
- `test_harness.py` - pytest execution wrapper ✅
- `scoring.py` - 5-dimension scoring engine ✅
- `database.py` - PostgreSQL persistence ✅
- `run_cli_benchmarks.py` - Main runner ✅
- `recordings/` - Terminal recordings
- `reports/` - Generated HTML reports

## Metrics

- **Speed** (25%) - Wall-clock time to completion
- **Correctness** (40%) - Test pass rate
- **Cost** (15%) - API usage costs
- **Autonomy** (12%) - Retries, error recovery, efficiency
- **Code Quality** (8%) - Linting, formatting, complexity

## Task Format

Each task in `../shared-tasks/` contains:
- `task.yaml` - Metadata, scoring criteria, validation
- `prompt.md` - Task description for agents
- Test files for validation

See `docs/plans/2026-02-01-cli-agent-benchmark-design.md` for full design.

## Development

### Run All Tests

```bash
cd benchmarks/cli_agent_arena
python3 -m pytest -v
```

### Load a Task

```python
from benchmarks.cli_agent_arena.task_loader import load_task

task = load_task("benchmarks/shared-tasks/algorithms/quicksort")
print(task.name, task.difficulty, task.estimated_time_seconds)
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

## Phase 3 Deliverables

✅ TestHarness for running pytest and extracting results
✅ ScoringEngine with 5-dimension scoring system
✅ DatabaseClient for persisting results to PostgreSQL
✅ Runner integration with test execution and scoring
✅ End-to-end pipeline: execute → test → score → save

**Test Summary:** 55 tests passing (14 new Phase 3 tests: 3 test harness, 7 scoring, 4 database)

## Phase 4 Milestone 1 Deliverables

✅ BaseOutputParser interface for CLI output parsing
✅ KimiParser for extracting metrics from Kimi CLI output
✅ QualityAnalyzer using pylint (70%) + flake8 (30%) scoring with fallback heuristics
✅ BenchmarkResult.quality_score field (0-100 code quality metric)
✅ Real Kimi CLI adapter with subprocess execution, recording, and quality analysis
✅ HTMLGenerator with Jinja2 dashboard template
✅ Responsive HTML reports with winner determination, stats, and color-coded results
✅ Integration tests for full pipeline: parse → analyze → score → report

**Test Summary:** 85 tests passing, 4 skipped (30 new Milestone 1 tests)

## Phase 4 Milestone 3 Deliverables

✅ GeminiParser for JSON output extraction (`-o json`)
✅ GeminiAdapter with subprocess execution, cwd-based isolation, quality analysis
✅ Three-way comparison dashboard with rank-based color coding
✅ Agent ranking system with medal icons (1st/2nd/3rd)
✅ Autonomy metric row (retries + error recovery scoring)
✅ Radar chart (Chart.js) for visual performance comparison
✅ Path-dependent test failures fixed (RecordingManager, runner shared-tasks)
✅ Restored missing shared-tasks files (task.yaml, prompt.md, tests)
✅ Integration tests for Gemini parser, adapter, three-way comparison, ranking

**Test Summary:** 118 tests passing, 3 skipped (23 new Milestone 3 tests: 9 gemini parser, 7 gemini adapter, 5 integration, 2 path fixes)

See plans at:
- `docs/plans/2026-02-01-cli-agent-arena-phase1-foundation.md` ✅
- `docs/plans/2026-02-01-cli-agent-arena-phase2-adapters.md` ✅
- `docs/plans/2026-02-02-cli-agent-arena-phase3-scoring.md` ✅
- `docs/plans/2026-02-02-cli-agent-arena-phase4-adapters-reporting.md` ✅
