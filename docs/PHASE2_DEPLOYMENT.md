# Phase 2 Deployment Guide

## Overview

Phase 2 MVP extends Sage Mode with:
- 4 additional specialist agents (UI/UX, DBA, IT Admin, Security)
- Kage Bunshin parallel execution framework
- Comprehensive 80+ test suite
- Dashboard API for monitoring decisions
- Full 7-member development team simulator

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│   Sage Mode Control Layer               │
│   (Planning + Decision Journal)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────v──────────────────────────┐
│   Development Team Simulator            │
│   7 Specialized Agents                  │
│   (3 Phase 1 + 4 Phase 2)               │
└──────────────┬──────────────────────────┘
               │
┌──────────────v──────────────────────────┐
│   Kage Bunshin Execution Engine         │
│   Parallel Task Grouping & Execution    │
│   (Sequential Phase 1 → Parallel P2)    │
└──────────────┬──────────────────────────┘
               │
┌──────────────v──────────────────────────┐
│   Dashboard API                         │
│   Decision Journal Visualization        │
│   Team Statistics & Monitoring          │
└─────────────────────────────────────────┘
```

## Running Phase 2

### Start Server
```bash
cd /home/ndninja/.worktrees/sage-mode-framework
python3 -m uvicorn sage_mode.api.app:app --reload
```

### Access Dashboard
```
http://localhost:8000/dashboard
```

### Execute Full Team Task
```python
from sage_mode.coordination.parallel_coordinator import ParallelCoordinator
from sage_mode.agents.architect_agent import ArchitectAgent
# ... initialize all 7 agents
coordinator = ParallelCoordinator(team_lead=architect)
result = coordinator.execute_feature_parallel(
    feature_name="My Feature",
    description="Feature description"
)
```

## Testing

### Run all Phase 2 tests
```bash
python3 -m pytest tests/test_additional_agents.py tests/test_kage_bunshin_parallel.py tests/test_full_team_integration.py tests/test_dashboard_api.py tests/test_phase2_final_integration.py -v
```

### Expected Result
80+ tests passing, full team simulation ready

## Next Steps (Phase 3)

- Integrate with Kage Bunshin cluster for true parallel execution
- Add React frontend for dashboard UI
- Implement Celery workers for distributed task execution
- Add database persistence layer for PostgreSQL
