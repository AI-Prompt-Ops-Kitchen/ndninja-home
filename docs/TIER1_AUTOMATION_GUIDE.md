# Tier 1 Automation Framework - User Guide

## Overview

The Tier 1 Automation Framework is a production-ready system that automates critical development tasks through three integrated components working together seamlessly.

### What is Tier 1 Automation?

Tier 1 Automation provides **intelligent automation** for your development workflow through:

1. **Production Readiness Checks** - Validates code before deployment with 6 comprehensive checks
2. **Action Item Tracking** - Automatically detects and completes todo items from tool outputs
3. **n8n Reliability Layer** - Detects n8n failures and routes tasks to Celery with automatic fallback

### The Three Core Components

| Component | Purpose | Trigger |
|-----------|---------|---------|
| **Production Readiness Skill** | 6-check deployment gate | Manual (slash command) |
| **Action Item Hook** | Auto-detect completion keywords | After each tool execution |
| **n8n Reliability Layer** | Fail-safe task routing | When n8n task fails |

### Use Cases and Benefits

- **Faster Development**: Skip manual todo updates when tests pass or code is deployed
- **Safer Deployments**: Automated checks prevent shipping broken code
- **Resilient Workflows**: Automatic fallback ensures critical n8n workflows complete
- **Audit Trail**: Complete history of automation decisions for compliance
- **Zero Configuration**: Works out-of-the-box with sensible defaults

---

## Component 1: Production Readiness Skill

### What It Does

The Production Readiness Skill runs **6 comprehensive checks** before deployment to ensure code is production-ready:

1. **Tests Check** - Verify all unit tests pass
2. **Security Check** - Scan for hardcoded credentials and secrets
3. **Documentation Check** - Ensure README and implementation docs exist
4. **Performance Check** - Run performance benchmarks if they exist
5. **Integration Tests Check** - Verify integration tests pass
6. **Rollback Plan Check** - Confirm rollback strategy is documented

### How to Use

```bash
# Run production readiness check
/production-check
```

The skill returns one of three decisions:
- **GO** - All checks passed, safe to deploy
- **WARNING** - Minor issues (usually performance) that don't block deployment
- **NO-GO** - Critical failures, fix before deploying

### Example Output

```
Production Readiness Check Results
===================================

Tests: PASSED (269 tests passing)
Security: PASSED (No vulnerabilities found)
Documentation: PASSED (README.md, IMPLEMENTATION_SUMMARY.md found)
Performance: WARNING (No benchmarks defined)
Integration: PASSED (23 integration tests passing)
Rollback: PASSED (git tags available)

Decision: GO ✓
Confidence: 100%
Evidence: All critical checks passed. Minor warning on performance benchmarks.

Event ID: 12847
Timestamp: 2026-01-20T18:45:32Z
```

### Configuration

The Production Readiness Skill is pre-configured and works out-of-the-box. Optional customizations:

```python
# In your Claude Code configuration
from tools_db.tools.production_checker import ProductionChecker

# Custom project path
checker = ProductionChecker(project_path="/path/to/your/project")

# Test mode (for testing the framework itself)
checker = ProductionChecker(test_mode=True)
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Tests failing" check | Run `python3 -m pytest tests/` to see detailed failures |
| "Security violations found" | Search codebase for hardcoded passwords/keys and remove them |
| "Documentation not found" | Create README.md and IMPLEMENTATION_SUMMARY.md |
| "No integration tests found" | Create tests/integration_*.py files |
| "No rollback plan" | Create ROLLBACK.md or create git tags |

---

## Component 2: Action Item Progress Tracking

### What It Does

Action Item Progress Tracking **automatically detects completion keywords** in tool outputs and updates your todos without manual intervention.

When you:
- Run a git commit
- Execute tests that pass
- Deploy code
- Fix a bug
- Create a file

The system detects these actions and marks related todos as complete.

### How It Works

The AutomationHook watches for completion keywords in tool output:

```
Tool Output: "git commit -m 'fix: resolve authentication bug'"
   ↓
Keyword Detector: Found keyword "commit" (git commit category)
   ↓
Confidence: 95% (high confidence)
   ↓
Todo Updater: Mark matching todo as "completed"
   ↓
Event Logged: action_item_completed event stored
```

### Supported Keywords

**Commit-Related Keywords** (80-100% confidence):
- "git commit", "committed", "commit complete", "commit -m"

**Deployment Keywords** (85-100% confidence):
- "deployed", "pushed to", "live on", "deployment successful"

**Test Success Keywords** (80-95% confidence):
- "all tests passed", "tests passing", "test suite passed", "✅ passing"

**Bug Fixed Keywords** (75-90% confidence):
- "fixed", "resolved", "bug resolved", "patch applied"

**Build Success Keywords** (85-95% confidence):
- "build successful", "build complete", "compiled"

**File Created Keywords** (70-85% confidence):
- "created", "written to", "saved"

### Confidence Thresholds

The system uses confidence scoring to prevent false positives:

| Confidence | Action | Example |
|-----------|--------|---------|
| **≥80%** | Auto-complete todo | Tool output: `git commit -m 'add feature'` |
| **60-80%** | Mark pending review | Tool output: `file created at /path/to/file` |
| **<60%** | Skip (no action) | Single word: `created` (too ambiguous) |

### How to Enable/Disable

Action Item Tracking is enabled by default through the PostToolUse hook.

**Disable** (if needed):
```bash
# Configure in Claude Code
# In your .claude.json or plugin settings, disable PostToolUse hook for ActionItemHook
```

**Re-enable**:
```bash
# Re-register the PostToolUse hook in Claude Code plugin system
```

### Examples

**Example 1: Commit Detection**
```
Todo: "Implement user authentication"
Tool: Bash
Output: "git commit -m 'feat: add JWT authentication'"

Result: ✓ Detected "commit" with 95% confidence
        ✓ Todo marked as "completed"
        ✓ Event logged: action_item_completed (id: 5634)
```

**Example 2: Test Success Detection**
```
Todo: "Fix failing tests"
Tool: Bash
Output: "34 passed in 2.45s"

Result: ✓ Detected "passed" with 88% confidence
        ✓ Todo marked as "completed"
        ✓ Event logged: action_item_completed (id: 5635)
```

**Example 3: Low Confidence Detection**
```
Todo: "Resolve authentication bug"
Tool: Bash
Output: "File operations completed"

Result: ✗ Detected keyword but only 55% confidence
        ✗ No action taken (too ambiguous)
        ✓ Event logged: no_action_taken (for audit trail)
```

---

## Component 3: n8n Reliability Layer

### What It Does

The n8n Reliability Layer **detects when n8n tasks fail** and automatically **routes them to Celery** with a smart fallback strategy:

```
n8n Task Fails (403/504/timeout)
    ↓
N8nMonitor detects failure pattern
    ↓
CeleryFallbackRouter initiates recovery:
    Attempt 1: Celery direct call (1s timeout)
    Attempt 2: API fallback call (5s timeout)
    Attempt 3: systemd service (30s timeout)
    ↓
Task completes successfully or logs final failure
```

### How It Works

**Failure Detection:**

The system monitors n8n responses for:

| Failure Type | Detection | Recovery |
|--------------|-----------|----------|
| **403 Unauthorized** | HTTP 403 or "unauthorized" in response | Route to Celery |
| **504 Gateway Timeout** | HTTP 504 or "timeout"/"unavailable" | Route to Celery |
| **Execution Timeout** | Task runs >30 seconds | Route to Celery |
| **Webhook Error** | "webhook"/"connection" in response | Route to Celery |
| **Unknown Error** | "error" or "failed" in response | Route to Celery |

**Recovery Strategy (3-Tier Fallback Chain):**

```
Tier 1: Celery Direct Call
├─ Timeout: 1 second (fast, for simple tasks)
├─ Best for: Quick operations
└─ If fails: Try Tier 2

Tier 2: API Fallback
├─ Timeout: 5 seconds (medium)
├─ Best for: Standard operations
└─ If fails: Try Tier 3

Tier 3: Systemd Service
├─ Timeout: 30 seconds (slow, reliable)
├─ Best for: Complex/resource-heavy operations
└─ If fails: Log failure but don't crash
```

### Supported Workflows

The framework includes built-in mappings for common n8n workflows:

```python
{
    'video-assembly': 'process_video',      # n8n → Celery mapping
    'draft-generator': 'generate_draft',
    'content-idea-capture': 'capture_idea',
    'kb-indexing': 'index_kb',
}
```

### How to Add New Workflows

To add a new n8n → Celery mapping:

```python
# In tools_db/tools/celery_fallback_router.py

N8N_TO_CELERY_MAPPING = {
    'video-assembly': 'process_video',
    'draft-generator': 'generate_draft',
    'my-new-workflow': 'my_celery_task',    # Add here
}
```

Then ensure the Celery task exists:

```python
# In your Celery worker configuration
@app.task(name='my_celery_task')
def my_celery_task(params):
    # Implementation
    return result
```

---

## Integration Features

### How Components Work Together

The three components share a unified database table and can coordinate:

```
Your Workflow:
    ↓
[1] Production Check passes → Event logged
    ↓
[2] Action Item Hook detects "deployed" → Todo marked complete → Event logged
    ↓
[3] n8n task fails → Monitor detects → Celery recovers → Event logged
    ↓
Unified Audit Trail: All events in automation_events table
```

### Unified Status Hub: automation_events Table

All automation events are logged to a single table for audit trail and correlation:

```sql
-- View all automation events
SELECT event_type, status, created_at, evidence
FROM automation_events
ORDER BY created_at DESC
LIMIT 20;

-- Find all n8n failures
SELECT * FROM automation_events
WHERE event_type = 'n8n_failure_detected'
AND created_at > NOW() - INTERVAL '1 day';

-- Find completed action items
SELECT * FROM automation_events
WHERE event_type = 'action_item_completed'
AND project_id = 'my-project';
```

### Viewing Events and History

**Python API:**

```python
from tools_db.tools.automation_hub import AutomationHub

hub = AutomationHub()

# Get all events
events = hub.get_events()

# Get events by type
production_checks = hub.get_events(event_type='production_check')

# Get events by status
failed_events = hub.get_events(status='failed')

# Get recent events
recent = hub.get_events(limit=50)
```

**SQL Queries:**

```sql
-- All events with details
SELECT event_type, status, evidence, created_at
FROM automation_events
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Events by project
SELECT event_type, status, COUNT(*) as count
FROM automation_events
WHERE project_id = 'tier1-automation'
GROUP BY event_type, status;

-- Event timeline
SELECT DATE(created_at) as date, event_type, COUNT(*) as count
FROM automation_events
GROUP BY DATE(created_at), event_type
ORDER BY date DESC;
```

### Correlation Between Events

Example correlation flow:

```
Production Check
├─ Event ID: 1001
├─ Type: production_check
├─ Status: success
├─ Time: 14:05:00
│
Deployment (triggered by passing check)
├─ Event ID: 1002
├─ Type: action_item_completed
├─ Status: success
├─ Context: production_check_passed (from evidence)
├─ Time: 14:06:30
│
n8n Task Completes
├─ Event ID: 1003
├─ Type: n8n_recovery_attempted
├─ Status: success
├─ Correlated: Links back to production check via project_id
├─ Time: 14:07:15
```

---

## Complete Examples

### Example 1: Feature Development Lifecycle

Workflow: Feature implementation → Tests pass → Commit → Deploy → n8n processes

```
1. You implement a feature and run tests

   Tool: Bash
   Command: python3 -m pytest tests/test_auth.py -v
   Output: "12 passed in 3.24s"

   → [2] Action Item Hook detects "passed" keyword
   → Todo "Implement authentication" marked COMPLETE (92% confidence)
   → Event logged: action_item_completed

2. You commit the changes

   Tool: Bash
   Command: git commit -m "feat: add JWT authentication"
   Output: "1 file changed, 45 insertions(+)"

   → [2] Action Item Hook detects "commit" keyword
   → Todo "Commit implementation" marked COMPLETE (95% confidence)
   → Event logged: action_item_completed

3. Production readiness check

   Skill: /production-check

   → [1] Runs all 6 checks
   → All pass: Tests ✓, Security ✓, Docs ✓, Performance ✓, Integration ✓, Rollback ✓
   → Decision: GO
   → Event logged: production_check (status: success)

4. You deploy to production

   Tool: Bash
   Command: docker push myapp:v1.2.3
   Output: "Pushed successfully"

   → [2] Action Item Hook detects "successful" context
   → Todo "Deploy v1.2.3" marked COMPLETE
   → Event logged: action_item_completed

5. n8n workflow processes the deployment

   n8n task: video-assembly workflow
   Status: Returns 504 Gateway Timeout

   → [3] N8nMonitor detects 504 failure
   → CeleryFallbackRouter attempts recovery
   → Attempt 1 (Celery): Success in 0.8s
   → Event logged: n8n_failure_detected (with recovery_successful: true)

Final Audit Trail:
   - production_check (success)
   - action_item_completed (3 items)
   - n8n_failure_detected + recovery
```

### Example 2: n8n Failure Recovery

Workflow: n8n fails → Detected → Fallback succeeds

```
Scenario: Draft generation workflow fails with 403 Unauthorized

1. n8n task starts
   Task: draft-generator
   Status: 403 Unauthorized

   → Event logged: n8n_failure_detected
   → Metadata: task_id=draft-generator, failure_type=403_unauthorized

2. Monitor detects failure
   Pattern detected: HTTP 403 status code
   Confidence: 100%
   Can fallback: Yes

3. Celery fallback router initiates recovery

   Attempt 1: Celery Direct Call
   ├─ Task: generate_draft(params)
   ├─ Timeout: 1s
   ├─ Result: FAILED (unauthorized in Celery too)
   ├─ Duration: 0.3s
   └─ Next: Try Attempt 2

   Attempt 2: API Fallback
   ├─ Task: POST /tasks/generate_draft
   ├─ Timeout: 5s
   ├─ Result: SUCCESS (200 OK)
   ├─ Duration: 2.1s
   └─ Complete: Task succeeded via API

4. Recovery success
   Event logged: n8n_recovery_attempted (status: success)
   Original n8n failure: Automatically recovered
   User impact: None (transparent fallback)

Audit Trail:
   - n8n_failure_detected (403_unauthorized)
   - n8n_recovery_attempted (success via api_fallback)
```

### Example 3: Production Readiness Workflow

Workflow: Code ready → Check → Feedback → Fix → Check → Deploy

```
Scenario: Feature ready but tests failing

1. You run production check
   Command: /production-check

2. Checks run
   Tests: FAILED (15 failed, 250 passed)
   Security: PASSED
   Documentation: PASSED
   Performance: WARNING (no benchmarks)
   Integration: FAILED (2 integration tests failing)
   Rollback: PASSED

   → Event logged: production_check (status: failed)
   → Evidence: Detailed results including failed test names

3. Decision: NO-GO

   Output:
   ┌─────────────────────────────────────┐
   │ DECISION: NO-GO ✗                   │
   │                                     │
   │ Critical Failures:                  │
   │ - Tests failing (15 failed)         │
   │ - Integration tests failing (2)     │
   │                                     │
   │ Action Required:                    │
   │ 1. Fix failing unit tests           │
   │ 2. Fix integration tests            │
   │ 3. Run /production-check again      │
   └─────────────────────────────────────┘

4. You fix the failing tests
   Tool: Edit
   Files: Fixed tests
   Tool: Bash
   Command: python3 -m pytest tests/ -q
   Output: "269 passed in 4.32s"

   → Event logged: action_item_completed (tests fixed)

5. You rerun production check
   Command: /production-check

   Tests: PASSED (269 passed)
   Security: PASSED
   Documentation: PASSED
   Performance: WARNING
   Integration: PASSED
   Rollback: PASSED

   → Event logged: production_check (status: success)
   → Decision: GO

6. Deploy with confidence
   Deployment succeeds
```

---

## FAQ and Troubleshooting

### Keyword Detection Issues

**Q: Why wasn't my todo marked complete?**

A: The keyword detector might have low confidence. Check:

```python
# Debug keyword detection
from tools_db.tools.keyword_detector import KeywordDetector

detector = KeywordDetector()
result = detector.detect("your tool output here")

print(f"Keyword: {result.keyword_found}")
print(f"Confidence: {result.confidence}%")
print(f"Category: {result.category}")

# If confidence < 60%, no action is taken
if result.confidence >= 80:
    print("✓ Would auto-complete")
elif 60 <= result.confidence < 80:
    print("⚠ Would mark pending review")
else:
    print("✗ Would skip (too risky)")
```

**Q: How do I see what keywords are detected?**

A: Query the automation_events table:

```sql
SELECT event_type, evidence->>'detected_keyword' as keyword,
       evidence->>'confidence' as confidence
FROM automation_events
WHERE event_type LIKE 'action_item%'
ORDER BY created_at DESC
LIMIT 10;
```

### Production Check Failures

**Q: How do I debug a failing production check?**

A: Run the checker with detailed output:

```python
from tools_db.tools.production_checker import ProductionChecker

checker = ProductionChecker(project_path=".")
results = checker.run_all_checks()

for check_name, result in results['checks'].items():
    print(f"\n{check_name}: {'PASSED' if result.passed else 'FAILED'}")
    print(f"  Details: {result.details}")
    if result.evidence:
        print(f"  Evidence: {result.evidence}")
```

**Q: Can I skip certain checks?**

A: Not directly, but you can fix the underlying issues. For example:

- **Performance check failing**: Create `benchmarks.py` or ignore (warning only)
- **Documentation check failing**: Create `README.md` or `IMPLEMENTATION_SUMMARY.md`
- **Rollback check failing**: Create `ROLLBACK.md` or tag a git commit

### Database Queries

**Q: How do I verify events are being logged?**

A: Check the automation_events table:

```sql
-- Verify table exists
\d automation_events

-- Count total events
SELECT COUNT(*) as total_events FROM automation_events;

-- Recent events
SELECT event_type, status, created_at
FROM automation_events
ORDER BY created_at DESC
LIMIT 5;

-- Events by type distribution
SELECT event_type, COUNT(*) as count
FROM automation_events
GROUP BY event_type;
```

**Q: How do I search event history?**

A: Use PostgreSQL JSON queries:

```sql
-- Find events by project
SELECT * FROM automation_events
WHERE project_id = 'tier1-automation'
AND created_at > NOW() - INTERVAL '7 days';

-- Find events by status
SELECT * FROM automation_events
WHERE status = 'failed'
ORDER BY created_at DESC;

-- Search in evidence
SELECT event_type, evidence->>'keyword'
FROM automation_events
WHERE evidence::text LIKE '%commit%';
```

### Performance Considerations

**Q: Will event logging slow down my work?**

A: No. Event logging is asynchronous and has minimal overhead:
- Database inserts: ~5-10ms
- No blocking operations
- Events stored independently

**Q: What if the database is down?**

A: Graceful degradation:
- Hooks still run (keyword detection)
- Fallbacks still work (n8n recovery)
- Events fail silently (no crash)
- System continues operating

**Q: How many events can the table handle?**

A: Millions:
- Indexed on event_type and created_at
- Efficient JSON storage
- Typical retention: 30-90 days
- Archive old events as needed

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Events not storing | Database connection issue | Check PostgreSQL is running and accessible |
| Keyword detection not working | Hook not registered | Re-register PostToolUse hook in Claude Code |
| n8n recovery not attempting | Celery workers down | Start Celery: `celery -A app worker` |
| Low confidence on keywords | Output is ambiguous | Add more specific keywords to detection patterns |
| Performance check warning | No benchmarks.py | Create benchmarks or ignore (warning only) |
| Tests not detected | Wrong test command | Ensure pytest is in project_path |

---

## Next Steps

1. **Start Using**: Run `/production-check` on your next project
2. **Monitor Events**: Check `automation_events` table for logged events
3. **Customize**: Add your n8n workflows to the fallback mapping
4. **Integrate**: Connect action item hooks to your Claude Code workflow
5. **Review**: Weekly review of automation_events for patterns and issues

For technical details, see [ARCHITECTURE.md](ARCHITECTURE.md).
For deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).
