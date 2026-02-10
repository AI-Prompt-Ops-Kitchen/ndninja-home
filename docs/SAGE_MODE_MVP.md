# Sage Mode MVP - Decision Journal Feature

## Overview

Sage Mode MVP is a Decision Journal system for neurodivergent developers who enter hyperfocus and make brilliant technical decisions that get lost.

**Problem:** ADHD hyperfocus cycle loses decisions
**Solution:** Decision Journal captures decisions non-intrusively

## Architecture

- **Decision Journal**: In-memory CRUD storage (MVP Phase 1)
- **Team Simulator**: 7 specialized agent types (MVP: 3 core)
- **API Endpoints**: REST API for decision management
- **Team Coordination**: Sequential execution (MVP), parallel Phase 2

## MVP Scope (Phase 1)

- ✅ Decision Journal CRUD
- ✅ 3 Core agents (Frontend, Backend, Architect)
- ✅ Sequential team execution
- ✅ API endpoints
- ⏸️ Kage Bunshin parallel execution (Phase 2)
- ⏸️ 4 Additional agents (Phase 2)
- ⏸️ UI Dashboard (Phase 3)

## Testing

```bash
python3 -m pytest tests/ -v
```

## Quick Start

Create a decision:
```bash
curl -X POST http://localhost:8000/api/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-id",
    "title": "Use async/await everywhere",
    "description": "Convert all blocking calls to async",
    "category": "architecture",
    "decision_type": "technical",
    "confidence_level": 95
  }'
```

## Next Steps (Phase 2)

- Kage Bunshin integration for parallel execution
- 4 remaining agents (UI/UX, DBA, IT Admin, Security)
- Frontend dashboard
- Decision linking and dependencies
- Celery worker integration
