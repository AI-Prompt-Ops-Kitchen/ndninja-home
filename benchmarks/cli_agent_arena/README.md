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

**Phase 2: Adapters** 🚧 In Progress
- Kimi CLI adapter (stub ✅)
- Claude Code adapter
- Gemini CLI adapter
- asciinema recording integration (✅)
- Mock adapter (✅)

## Quick Start

### List Available Tasks

```bash
python benchmarks/cli_agent_arena/run_cli_benchmarks.py --list-tasks
```

### Run Tests

```bash
cd benchmarks/cli_agent_arena
python3 -m pytest -v
```

### Check Database Schema

```bash
psql -U ndninja -d workspace -c "SELECT * FROM cli_agent_comparison LIMIT 5"
```

## Architecture

- `adapters/` - CLI agent-specific adapters (base interface ✅, mock ✅, kimi stub ✅)
- `recording_manager.py` - asciinema wrapper ✅
- `task_loader.py` - Task definition loader ✅
- `run_cli_benchmarks.py` - Main runner ✅
- `schema.sql` - PostgreSQL schema ✅
- `recordings/` - Terminal recordings (Phase 2)
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

## Next Steps (Phase 2)

1. Implement Kimi CLI adapter (fill in stub)
2. Implement Claude Code adapter
3. Implement Gemini CLI adapter
4. Test execution pipeline end-to-end with real agents

See implementation plans at:
- `docs/plans/2026-02-01-cli-agent-arena-phase1-foundation.md` ✅
- `docs/plans/2026-02-01-cli-agent-arena-phase2-adapters.md`
