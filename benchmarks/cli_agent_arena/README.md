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
- **29 tests passing, 2 skipped**

**Phase 2: Adapters** ✅ Complete
- asciinema recording manager ✅
- Mock adapter (fully functional) ✅
- Kimi CLI adapter (stub) ✅
- Claude Code adapter (stub) ✅
- Gemini CLI adapter (stub) ✅
- Adapter factory pattern ✅
- Runner integration with dry-run ✅
- End-to-end execution pipeline ✅
- **40 tests passing, 4 skipped**

**Phase 3: Scoring & Testing** 🚧 Next
- Implement scoring system
- Test harness integration
- Real CLI adapter implementations
- Validate autonomy metrics

## Quick Start

### Check Adapter Availability

```bash
python3 -c "from benchmarks.cli_agent_arena.adapter_factory import check_adapter_availability; print(check_adapter_availability())"
```

### Run Mock Benchmark

```bash
# Test with mock adapter (no real CLI needed)
cd benchmarks
python3 cli_agent_arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort --dry-run
```

### List Available Tasks

```bash
cd benchmarks
python3 cli_agent_arena/run_cli_benchmarks.py --list-tasks
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
  - `base.py` - Abstract interface ✅
  - `mock.py` - Testing adapter ✅
  - `kimi.py` - Kimi CLI (stub) ✅
  - `claude.py` - Claude Code (stub) ✅
  - `gemini.py` - Gemini (stub) ✅
- `recording_manager.py` - asciinema wrapper ✅
- `adapter_factory.py` - Adapter registry ✅
- `task_loader.py` - Task definition loader ✅
- `run_cli_benchmarks.py` - Main runner ✅
- `schema.sql` - PostgreSQL schema ✅
- `recordings/` - Terminal recordings
- `reporting/` - Report generators (Phase 4)
- `reports/` - Generated reports (Phase 4)
- `../shared-tasks/` - Task definitions (3 tasks ✅)

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

## Phase 2 Deliverables

✅ asciinema RecordingManager with path generation
✅ Mock adapter (fully functional for testing)
✅ Adapter stubs (Kimi, Claude, Gemini)
✅ Adapter factory pattern
✅ Runner integration with dry-run support
✅ End-to-end execution pipeline

**Test Summary:** 40 tests passing (4 skipped for integration)

## Next Steps (Phase 3)

1. Implement scoring system (speed, correctness, cost, autonomy, quality)
2. Integrate pytest test harness
3. Implement real Kimi CLI adapter
4. Implement real Claude Code adapter
5. Research Gemini CLI availability
6. Add database persistence
7. Validate metrics tracking

See implementation plans at:
- `docs/plans/2026-02-01-cli-agent-arena-phase1-foundation.md` ✅
- `docs/plans/2026-02-01-cli-agent-arena-phase2-adapters.md` ✅
- `docs/plans/2026-02-01-cli-agent-arena-phase3-scoring.md` (TBD)
