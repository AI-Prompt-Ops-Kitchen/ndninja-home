# Claude Tools Database Layer

Production-ready database infrastructure for 4 core developer tools:
- Database Schema Validator
- Vision Analysis Cache
- Permission Audit Trail
- Critical Bug Escalation

## Architecture

```
┌─ PostgreSQL Database (shared persistence)
│
├─ Migration System (Alembic)
│  └─ Automatic schema creation/versioning
│
├─ Connection Pool (psycopg2)
│  └─ 1-20 connections, auto-retry
│
└─ MCP Server
   ├─ Schema Validator Tool
   ├─ Vision Cache Tool
   ├─ Audit Trail Tool
   └─ Bug Escalation Tool
```

## Quick Start

### 1. Setup Database

```bash
# Set PostgreSQL connection
export TOOLS_DB_URL="postgresql://user:pass@localhost/claude_tools"

# Run migrations
python3 -c "from tools_db.database import get_db; get_db()"
```

### 2. Use Individual Tools

```python
from tools_db.tools.schema_validator import SchemaValidator
from tools_db.tools.vision_cache import VisionCache
from tools_db.tools.audit_trail import AuditTrail
from tools_db.tools.bug_escalation import BugEscalation

# Schema validation
validator = SchemaValidator()
result = validator.validate_create_statement("""
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255)
    )
""")

# Vision caching
cache = VisionCache()
cache.store(
    image_hash="abc123",
    extracted_data={"keywords": ["sunset"]},
    confidence_score=0.95,
    model_version="v1.0"
)
result = cache.get("abc123")

# Audit trail
audit = AuditTrail()
audit.record_event(
    event_type="permission_changed",
    entity_type="permission",
    entity_id="perm_bash",
    new_value={"status": "approved"},
    user="admin"
)
events = audit.get_events(entity_type="permission")

# Bug escalation
escalator = BugEscalation()
escalator.report_bug(
    bug_id="bug_001",
    error_type="CriticalError",
    error_message="Application crashed",
    user_impact="critical"
)
bugs = escalator.get_escalations(status="pending")
```

## Testing

```bash
# Unit tests
pytest tests/test_*.py -v

# Integration tests
pytest tests/integration_tests.py -v

# With coverage
pytest --cov=tools_db tests/ -v
```

## Database Schema

### audit_trail_events
Tracks all permission/configuration changes:
- `event_type`: permission_changed, config_updated, etc.
- `entity_type`: permission, config, workflow
- `old_value`/`new_value`: JSON diffs
- `user`: who made the change
- `timestamp`: when it happened

### vision_cache
Caches vision analysis results with TTL:
- `image_hash`: SHA256 of image
- `extracted_data`: JSON analysis result
- `confidence_score`: 0-1 confidence
- `expires_at`: automatic cleanup
- `hit_count`: cache efficiency metrics

### bug_escalations
Automatic bug escalation tracking:
- `bug_id`: unique identifier
- `error_type`: classification
- `frequency`: how often it occurs
- `user_impact`: low/medium/high/critical
- `status`: pending/acknowledged/resolved

### prompt_versions
Versioned prompts with test results (if using prompt versioning):
- `prompt_id`: prompt identifier
- `version`: version number
- `prompt_text`: the actual prompt
- `test_results`: JSON test outcomes
- `is_active`: current active version

## Files

```
tools_db/
├── __init__.py
├── database.py          # PostgreSQL connection & migrations
├── models.py            # Shared dataclasses
├── utils.py             # Hash & comparison utilities
├── mcp_server.py        # MCP server framework
└── tools/
    ├── schema_validator.py    # SQL schema validation
    ├── vision_cache.py        # Vision analysis caching
    ├── audit_trail.py         # Permission audit tracking
    └── bug_escalation.py      # Bug priority & escalation
```

## Test Coverage

- 3/3 Phase 1 tests: Database setup, models, utilities
- 10/10 Phase 2 tests: Schema validator, vision cache, audit trail, bug escalation
- 4/4 Phase 4 tests: Integration workflows

**Total: 17/17 tests passing**
