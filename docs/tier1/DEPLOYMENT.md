# Tier 1 Automation Framework - Deployment Guide

## Prerequisites

Before deploying the Tier 1 Automation Framework, ensure your environment meets these requirements:

### System Requirements

- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher (for production, SQLite for development)
- **Redis**: 6.0 or higher (for Celery queue)
- **Claude Code**: Latest version with hook support
- **Disk Space**: 1GB minimum (for logs and database)

### Required Services

1. **PostgreSQL Database**
   ```bash
   # Check if PostgreSQL is running
   psql --version
   createdb tools_db  # Create database if not exists
   ```

2. **Redis Server**
   ```bash
   # Check if Redis is running
   redis-cli ping
   # Should return: PONG
   ```

3. **Celery Workers**
   ```bash
   # Celery will be started with your application
   celery -A app worker --loglevel=info
   ```

4. **n8n Instance** (for Component 3 only)
   ```bash
   # Optional: Only needed if using n8n reliability layer
   # n8n should be accessible at http://localhost:5679
   ```

### Environment Variables

Create a `.env` file in your project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/tools_db
# or for development: sqlite:///./tools_db.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# n8n Configuration (Optional)
N8N_URL=http://localhost:5679
N8N_API_KEY=your-n8n-api-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/tier1-automation.log

# Framework Configuration
AUTOMATION_ENABLED=true
ACTION_ITEM_TRACKING_ENABLED=true
N8N_RELIABILITY_ENABLED=true
```

---

## Installation Steps

### Step 1: Clone/Merge Code to Main Branch

If working on a feature branch:

```bash
# Switch to main branch
git checkout main

# Merge feature branch (or pull latest)
git merge feature/tier1-automation-framework

# Verify merge
git log --oneline -5
```

### Step 2: Install Dependencies

```bash
# Navigate to project root
cd /home/ndninja/.worktrees/tier1-automation

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional, for running tests)
pip install -r requirements-dev.txt
```

**Key Dependencies:**

```
PostgreSQL (psycopg2)
Redis (redis)
Celery (celery)
SQLAlchemy (sqlalchemy)
pytest (for testing)
```

### Step 3: Create automation_events Table

Run migration to create the automation_events table:

```bash
# Using migration script (if available)
python3 scripts/migrations/create_automation_events_table.py

# Or manually via SQL
psql -d tools_db -f scripts/migrations/001_create_automation_events.sql
```

**SQL Schema:**

```sql
CREATE TABLE automation_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    evidence JSONB NOT NULL,
    detected_from VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    INDEX idx_project_id (project_id)
);

CREATE INDEX idx_automation_events_status ON automation_events(status);
CREATE INDEX idx_automation_events_timestamp ON automation_events(created_at DESC);
```

### Step 4: Verify Database Connectivity

```bash
# Test PostgreSQL connection
python3 -c "
from tools_db.database import get_db_connection
db = get_db_connection()
print('✓ PostgreSQL connection successful')
"

# Test Redis connection
python3 -c "
import redis
r = redis.Redis.from_url('redis://localhost:6379/0')
r.ping()
print('✓ Redis connection successful')
"
```

### Step 5: Test Basic Functionality

```bash
# Run unit tests
python3 -m pytest tests/test_production_checker.py -v
python3 -m pytest tests/test_action_item_hook.py -v
python3 -m pytest tests/test_n8n_reliability_hook.py -v

# Expected output: All tests should pass
# pytest tests/ -q
# 271 passed in 4.5s
```

---

## Configuration

### Database Connection String

**PostgreSQL (Production):**
```
postgresql://username:password@hostname:5432/tools_db
```

**SQLite (Development):**
```
sqlite:///./tools_db.db
```

**Configuration in Code:**

```python
# In your application initialization
from tools_db.database import get_db_connection

# Automatic from DATABASE_URL env var
db = get_db_connection()

# Or explicit configuration
db = get_db_connection(
    url="postgresql://user:pass@localhost:5432/tools_db"
)
```

### Redis Connection (for Celery)

```python
# Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'

# In Celery config
from celery import Celery

app = Celery('tasks')
app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND
)
```

### Celery Task Mappings

Map n8n workflows to Celery tasks:

```python
# In tools_db/tools/celery_fallback_router.py

N8N_TO_CELERY_MAPPING = {
    'video-assembly': 'process_video',
    'draft-generator': 'generate_draft',
    'content-idea-capture': 'capture_idea',
    'kb-indexing': 'index_kb',
    # Add your custom workflows here
    'my-workflow': 'my_celery_task',
}
```

**Adding New Mappings:**

1. Add to N8N_TO_CELERY_MAPPING dictionary
2. Ensure corresponding Celery task exists
3. Deploy both n8n workflow and Celery worker
4. Test with recovery scenario

### Timeout Values

Adjust timeouts based on your environment:

```python
# tools_db/tools/celery_fallback_router.py

# Tier 1: Celery Direct (fast operations)
CELERY_TIMEOUT = 1  # seconds

# Tier 2: API Fallback (standard operations)
API_TIMEOUT = 5  # seconds

# Tier 3: Systemd Fallback (heavy operations)
SYSTEMD_TIMEOUT = 30  # seconds

# n8n Monitor
N8N_EXECUTION_TIMEOUT = 30  # seconds
```

**Recommended Values by Use Case:**

| Use Case | Celery | API | Systemd |
|----------|--------|-----|---------|
| Quick tasks | 1s | 3s | 15s |
| Standard tasks | 2s | 5s | 30s |
| Heavy operations | 5s | 15s | 60s |
| Video processing | 10s | 30s | 120s |

### Logging Configuration

```python
# Configure logging in your application

import logging
import logging.handlers

# Set up file logging
handler = logging.handlers.RotatingFileHandler(
    '/var/log/tier1-automation.log',
    maxBytes=10_000_000,  # 10MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

logger = logging.getLogger('tier1_automation')
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

---

## Enabling Components

### Component 1: Production Readiness Skill

The Production Readiness Skill is automatically available as `/production-check`.

**Enable manually:**

```bash
# Copy skill to Claude Code plugins directory
cp tools_db/skills/production_check.md ~/.claude/skills/

# Restart Claude Code
# Skill should now be available
/production-check
```

### Component 2: Action Item Hook (PostToolUse)

Register the PostToolUse hook in Claude Code:

```python
# In your plugin configuration (.claude/plugin.json)

{
  "hooks": [
    {
      "event": "PostToolUse",
      "handler": "tools_db.tools.action_item_hook.ActionItemHook.handle_tool_output",
      "enabled": true
    }
  ]
}
```

**Manual Setup:**

```bash
# 1. Initialize AutomationHub
python3 -c "
from tools_db.tools.automation_hub import AutomationHub
hub = AutomationHub()
print('✓ AutomationHub initialized')
"

# 2. Register hook with Claude Code
# Add to your Claude Code configuration

# 3. Test hook
# Run a bash command and verify event is logged
"
```

### Component 3: n8n Reliability Hook (PreToolUse)

Register the PreToolUse hook for n8n tasks:

```python
# In your plugin configuration (.claude/plugin.json)

{
  "hooks": [
    {
      "event": "PreToolUse",
      "handler": "tools_db.tools.n8n_reliability_hook.N8nReliabilityHook.handle_task_start",
      "enabled": true,
      "tools": ["n8n"]  # Only for n8n tool
    }
  ]
}
```

**Enable n8n Monitoring:**

```bash
# 1. Start Celery workers (required for fallback)
celery -A app worker --loglevel=info &

# 2. Start Redis (required for Celery)
redis-server &

# 3. Verify n8n connectivity
python3 -c "
import os
from tools_db.tools.n8n_monitor import N8nMonitor

monitor = N8nMonitor()
monitor.register_task('test-task', 'test-workflow', {})
print('✓ n8n Monitor initialized')
"

# 4. Hook is now active and monitoring
```

---

## Testing After Deployment

### Step 1: Verify automation_events Table

```bash
# Connect to database
psql -d tools_db -c "
SELECT COUNT(*) as event_count FROM automation_events;
"

# Expected output: Should show count (may be 0 initially)
```

### Step 2: Run Production Check

```bash
# Execute production check
/production-check

# Expected output:
# - All checks should display
# - Decision should be GO, WARNING, or NO-GO
# - Event should be logged to database
```

**Verify event was logged:**

```bash
psql -d tools_db -c "
SELECT event_type, status, created_at FROM automation_events
WHERE event_type = 'production_check'
ORDER BY created_at DESC LIMIT 1;
"
```

### Step 3: Test Keyword Detection

```python
# Create test output with known keywords
test_output = "git commit -m 'test commit'"

from tools_db.tools.action_item_hook import ActionItemHook
hook = ActionItemHook()
result = hook.handle_tool_output('bash', test_output)

print(f"Action taken: {result.action_taken}")
print(f"Keyword found: {result.keyword_found}")
print(f"Confidence: {result.confidence}%")
print(f"Event ID: {result.event_id}")
```

**Verify event in database:**

```bash
psql -d tools_db -c "
SELECT event_type, evidence->>'detected_keyword' as keyword,
       evidence->>'confidence' as confidence
FROM automation_events
WHERE event_type LIKE 'action_item%'
ORDER BY created_at DESC LIMIT 1;
"
```

### Step 4: Test n8n Failure Detection

```python
from tools_db.tools.n8n_monitor import N8nMonitor

monitor = N8nMonitor()

# Register a task
monitor_id = monitor.register_task(
    task_id='test-video-assembly',
    workflow_name='video-assembly',
    input_params={'video_id': 'test123'}
)

# Simulate a failure
result = monitor.report_result(
    monitor_id=monitor_id,
    status_code=504,
    response='Service Unavailable: Gateway Timeout',
    duration_seconds=15.2
)

print(f"Failure detected: {result.failure_detected}")
print(f"Failure type: {result.failure_type}")
print(f"Event ID: {result.event_id}")
```

**Verify event in database:**

```bash
psql -d tools_db -c "
SELECT event_type, evidence->>'failure_type' as failure_type,
       evidence->>'task_id' as task_id
FROM automation_events
WHERE event_type = 'n8n_failure_detected'
ORDER BY created_at DESC LIMIT 1;
"
```

### Step 5: Run Full Test Suite

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific component tests
python3 -m pytest tests/test_production_checker.py -v
python3 -m pytest tests/test_action_item_hook.py -v
python3 -m pytest tests/test_n8n_reliability_hook.py -v

# Run integration tests
python3 -m pytest tests/integration_*.py -v

# Expected result: All tests passing
# 271 tests collected
# 271 passed in ~5s
```

---

## Monitoring and Maintenance

### Checking Service Health

```bash
# Check PostgreSQL
psql -d tools_db -c "SELECT 1;"

# Check Redis
redis-cli ping

# Check Celery workers
celery -A app inspect active

# Check automation_events table
psql -d tools_db -c "
SELECT COUNT(*) as total_events,
       COUNT(CASE WHEN status='success' THEN 1 END) as successes,
       COUNT(CASE WHEN status='failed' THEN 1 END) as failures
FROM automation_events;
"
```

### Monitor Celery Worker Health

```bash
# View active workers
celery -A app inspect active

# View registered tasks
celery -A app inspect registered

# View task stats
celery -A app inspect stats

# Monitor in real-time
celery -A app events
```

### Review Failed Events

```bash
# Find all failed events
psql -d tools_db -c "
SELECT event_type, project_id, evidence, created_at
FROM automation_events
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 20;
"

# Find n8n recovery failures
psql -d tools_db -c "
SELECT evidence->>'task_id' as task_id,
       evidence->>'failure_type' as failure,
       metadata->>'recovery_successful' as recovered
FROM automation_events
WHERE event_type = 'n8n_failure_detected'
AND metadata->>'recovery_successful' = 'false'
ORDER BY created_at DESC;
"
```

### Pattern Analysis

```bash
# Event type distribution
psql -d tools_db -c "
SELECT event_type, COUNT(*) as count,
       SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successes,
       SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failures
FROM automation_events
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY event_type
ORDER BY count DESC;
"

# Success rate by component
psql -d tools_db -c "
SELECT
  CASE
    WHEN event_type LIKE 'action_item%' THEN 'Action Items'
    WHEN event_type LIKE 'production%' THEN 'Production Checks'
    WHEN event_type LIKE 'n8n%' THEN 'n8n Reliability'
    ELSE 'Other'
  END as component,
  COUNT(*) as total,
  ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM automation_events
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY component;
"
```

### Backup Strategies

**Daily Backup:**

```bash
#!/bin/bash
# backup_automation_events.sh

BACKUP_DIR="/backups/tier1-automation"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="tools_db"

mkdir -p $BACKUP_DIR

# Backup automation_events table
pg_dump -U postgres $DB_NAME -t automation_events \
  | gzip > $BACKUP_DIR/automation_events_$DATE.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "automation_events_*.sql.gz" -mtime +30 -delete

echo "✓ Backup completed: $BACKUP_DIR/automation_events_$DATE.sql.gz"
```

**Archive Old Events:**

```bash
# Archive events older than 90 days
psql -d tools_db -c "
-- Create archive table if not exists
CREATE TABLE IF NOT EXISTS automation_events_archive AS
SELECT * FROM automation_events WHERE 1=0;

-- Move old events to archive
INSERT INTO automation_events_archive
SELECT * FROM automation_events
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete from main table
DELETE FROM automation_events
WHERE created_at < NOW() - INTERVAL '90 days';

-- Vacuum to reclaim space
VACUUM FULL automation_events;
"
```

### Upgrade Procedures

When updating the framework:

```bash
# 1. Back up database
pg_dump tools_db > backup_before_upgrade.sql

# 2. Pull latest code
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Run migrations (if any)
python3 scripts/migrations/apply_migrations.py

# 5. Run tests to verify
python3 -m pytest tests/ -q

# 6. Restart services
systemctl restart celery
systemctl restart redis

# 7. Verify deployment
/production-check
```

---

## Troubleshooting Deployment

### Database Connection Issues

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify connection string
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"

# Create database if missing
createdb tools_db

# Verify permissions
psql -d tools_db -c "GRANT ALL ON automation_events TO your_user;"
```

### Celery Worker Failures

**Problem:** Celery tasks not executing

**Solution:**

```bash
# Start Celery with debug logging
celery -A app worker --loglevel=debug

# Check Redis connectivity
redis-cli ping

# Verify task registration
celery -A app inspect registered

# Check active tasks
celery -A app inspect active

# Purge stuck tasks (if needed)
celery -A app purge
```

### Hook Registration Issues

**Problem:** Hooks not triggering

**Solution:**

```bash
# Verify hook configuration
cat ~/.claude/plugin.json | jq '.hooks'

# Check Claude Code logs
tail -f ~/.claude/logs/plugin.log

# Manually test hook
python3 -c "
from tools_db.tools.action_item_hook import ActionItemHook
hook = ActionItemHook()
result = hook.handle_tool_output('bash', 'git commit -m test')
print(f'Hook executed: {result.action_taken}')
"

# Re-register hook
# Stop Claude Code
# Clear cache: rm -rf ~/.claude/cache
# Restart Claude Code
```

### Event Logging Failures

**Problem:** Events not stored in database

**Solution:**

```bash
# Check database connectivity
python3 -c "
from tools_db.database import get_db_connection
db = get_db_connection()
print('✓ Connected')
"

# Verify table exists
psql tools_db -c "\d automation_events"

# Check for errors in logs
grep -i "error\|exception" /var/log/tier1-automation.log

# Manually insert test event
psql tools_db -c "
INSERT INTO automation_events (event_type, project_id, status, evidence, detected_from)
VALUES ('test', 'deployment-test', 'success', '{}', 'manual');
"

# Verify it was stored
psql tools_db -c "SELECT * FROM automation_events WHERE event_type = 'test';"
```

---

## Post-Deployment Checklist

- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible
- [ ] Celery workers started
- [ ] automation_events table created
- [ ] All tests passing (271/271)
- [ ] Production check command available (`/production-check`)
- [ ] Action item hook enabled (PostToolUse)
- [ ] n8n reliability hook enabled (PreToolUse)
- [ ] Database backups configured
- [ ] Monitoring alerts set up
- [ ] Logs being written to log file
- [ ] Team trained on using components

---

## Next Steps

1. **Day 1**: Basic setup and testing
2. **Week 1**: Monitor events and tune timeouts
3. **Month 1**: Review patterns and feedback
4. **Ongoing**: Maintenance and optimization

For detailed usage information, see [TIER1_AUTOMATION_GUIDE.md](TIER1_AUTOMATION_GUIDE.md).
For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).
