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

**Phase 4: Reporting & Analytics** 🚧 Next
- Code quality analysis (pylint/flake8)
- Report generators
- Real CLI adapter implementations

## Quick Start

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
```

### Check Database Schema

```bash
psql -U ndninja -d workspace -c "SELECT * FROM cli_agent_comparison LIMIT 5"
```

## Architecture

- `adapters/` - CLI agent adapters ✅
  - `base.py` - Abstract interface
  - `mock.py` - Testing adapter
  - `kimi.py` - Kimi CLI (stub)
  - `claude.py` - Claude Code (stub)
  - `gemini.py` - Gemini (stub)
- `recording_manager.py` - asciinema wrapper ✅
- `adapter_factory.py` - Adapter registry ✅
- `task_loader.py` - Task definition loader ✅
- `test_harness.py` - pytest execution wrapper ✅
- `scoring.py` - 5-dimension scoring engine ✅
- `database.py` - PostgreSQL persistence ✅
- `run_cli_benchmarks.py` - Main runner ✅
- `recordings/` - Terminal recordings
- `reporting/` - Report generators (Phase 4)
- `reports/` - Generated reports (Phase 4)

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

## Next Steps (Phase 4)

1. Add code quality analysis (pylint/flake8)
2. Implement real Kimi CLI adapter
3. Implement real Claude Code adapter
4. Research Gemini CLI availability
5. Create report generators
6. Build analytics dashboard

See plans at:
- `docs/plans/2026-02-01-cli-agent-arena-phase1-foundation.md` ✅
- `docs/plans/2026-02-01-cli-agent-arena-phase2-adapters.md` ✅
- `docs/plans/2026-02-02-cli-agent-arena-phase3-scoring.md` ✅
