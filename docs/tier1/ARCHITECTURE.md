# Tier 1 Automation Framework - Architecture

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Environment                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │   Skills &   │  │   Tools (Bash,   │  │   PostToolUse  │   │
│  │  Commands    │  │   Write, Edit)   │  │     Events     │   │
│  └──────┬───────┘  └────────┬─────────┘  └────────┬────────┘   │
│         │                   │                     │            │
│         │   /production-    │   Tool Output       │            │
│         │   check           │   (any tool)        │            │
│         │                   │                     │            │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
          ▼                   ▼                     ▼
    ┌──────────┐         ┌──────────┐        ┌────────────┐
    │Component │         │Component │        │Component 2 │
    │    1     │         │ PreToolUse Events  │ PostToolUse│
    │Production│         │(n8n tasks)        │ Action Item│
    │  Check   │         │          │        │Hook       │
    └──────────┘         └────┬─────┘        └────┬───────┘
          │                   │                   │
          │   Results         │   Failures        │   Keyword
          │   (GO/NO-GO)      │   (403/504)       │   Detection
          │                   │                   │
          └───────┬───────────┴───────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  Component 3:    │
        │ n8n Reliability  │
        │     Layer        │
        └────────┬─────────┘
                 │
        ┌────────┴────────┐
        │  Failure        │
        │  Detection &    │
        │  Fallback       │
        │  Routing        │
        └────────┬────────┘
                 │
        ┌────────┴─────────────────────────┐
        │                                  │
        ▼                                  ▼
    ┌─────────┐                    ┌────────────┐
    │  Celery │                    │  PostgreSQL│
    │ Workers │ (3-tier fallback)  │ Database   │
    │ Fallback│                    │automation_ │
    └─────────┘                    │events Table│
                                   └────────────┘
                                        ▲
                                        │
                                   Unified
                                   Audit
                                   Trail
```

### Data Flow

```
Development Workflow
│
├─ Task 1: Implement Feature
│  └─ Run tests: "pytest tests/" → "269 passed"
│     └─ [Component 2] Keyword "passed" detected
│        └─ ACTION: Mark todo complete
│           └─ EVENT: action_item_completed logged
│
├─ Task 2: Production Readiness
│  └─ Run check: "/production-check"
│     └─ [Component 1] All 6 checks pass
│        └─ DECISION: GO
│           └─ EVENT: production_check (success) logged
│
├─ Task 3: Deploy
│  └─ Push to production
│     └─ n8n workflow starts: "video-assembly"
│        └─ Returns 504 Gateway Timeout
│           └─ [Component 3] Failure detected
│              └─ N8nMonitor logs failure event
│              └─ CeleryFallbackRouter attempts recovery
│                 ├─ Tier 1 (Celery): FAILED
│                 ├─ Tier 2 (API): SUCCESS ✓
│                 └─ EVENT: n8n_recovery_attempted logged
│
└─ All Events → PostgreSQL → automation_events table
```

---

## Component 1: Production Readiness Skill

### Architecture

```
ProductionChecker
├─ run_all_checks()
│  └─ Returns dict of CheckResult objects
│
├─ check_tests()           → TestCheck
├─ check_security()        → SecurityCheck
├─ check_documentation()   → DocCheck
├─ check_performance()     → PerfCheck
├─ check_integration_tests() → IntegrationCheck
└─ check_rollback_plan()   → RollbackCheck

CheckResult (dataclass)
├─ check_name: str
├─ passed: bool
├─ details: str
├─ evidence: Optional[Dict]
└─ confidence: int (0-100)

calculate_decision()
├─ Analyzes check results
└─ Returns: "go" | "warning" | "no_go"
```

### Data Model

**CheckResult Dataclass:**

```python
@dataclass
class CheckResult:
    check_name: str                   # "tests", "security", etc.
    passed: bool                      # True if check passed
    details: str                      # Human-readable result
    evidence: Optional[Dict[str, Any]] = None  # Detailed data

# Example:
CheckResult(
    check_name="tests",
    passed=True,
    details="269 tests passed",
    evidence={"passed_count": 269, "failed_count": 0, "duration_seconds": 4.32}
)
```

### Check Implementation Details

**Tests Check** (→ `check_tests()`)
- Runs: `pytest tests/ -v --tb=no`
- Passes if: Exit code == 0
- Evidence: Test count and duration
- Timeout: 60 seconds

**Security Check** (→ `check_security()`)
- Searches: Hardcoded passwords, API keys, secrets
- Patterns: `password=`, `api_key=`, `secret=`
- Passes if: No violations found
- Evidence: List of violations (if any)

**Documentation Check** (→ `check_documentation()`)
- Requires: README.md, IMPLEMENTATION_SUMMARY.md
- Passes if: At least 1 doc found
- Evidence: Found documents list

**Performance Check** (→ `check_performance()`)
- Optional: Runs benchmarks.py if exists
- Passes if: Exit code == 0 or no benchmarks (warning)
- Evidence: Benchmark results (if available)
- Timeout: 120 seconds

**Integration Tests** (→ `check_integration_tests()`)
- Runs: `pytest tests/integration_*.py -v`
- Passes if: Exit code == 0
- Evidence: Test results
- Timeout: 120 seconds

**Rollback Plan** (→ `check_rollback_plan()`)
- Checks: ROLLBACK.md exists OR git tags exist
- Passes if: Either condition true
- Evidence: Rollback method found

### Decision Logic

```
Decision Matrix:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Failed Checks Count  | Decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0                    | GO ✓
1 (performance only) | WARNING ⚠
2+                   | NO-GO ✗
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Event Logging

When production check completes:

```python
event = AutomationEvent(
    event_type="production_check",
    project_id="tier1-automation",
    status="success" | "failed",  # Based on decision
    evidence={
        "checks": {
            "tests": {"passed": true, "details": "269 tests"},
            "security": {"passed": true, ...},
            # ... other checks
        },
        "decision": "go" | "warning" | "no_go",
        "confidence": 100
    },
    detected_from="skill",
    metadata={
        "skill": "/production-check",
        "timestamp": "2026-01-20T18:45:32Z"
    }
)
```

### Files

```
tools_db/tools/
├─ production_checker.py        (Core logic)
│  ├─ ProductionChecker class
│  └─ CheckResult dataclass
│
├─ production_formatter.py      (Output formatting)
│  └─ FormatProductionResults
│
└─ production_check_skill.py    (Skill entry point)
   └─ /production-check command
```

---

## Component 2: Action Item Progress Tracking

### Architecture

```
PostToolUse Event
│
└─ ActionItemHook.handle_tool_output(tool_name, output)
   │
   ├─ _should_process_tool(tool_name)
   │  └─ Check: tool_name in SUPPORTED_TOOLS
   │
   ├─ KeywordDetector.detect(output)
   │  ├─ Pattern match against keyword categories
   │  ├─ Calculate confidence score (0-100)
   │  └─ Return DetectionResult
   │
   ├─ Confidence check
   │  ├─ If confidence >= 80: → TodoUpdater
   │  ├─ If 60 <= confidence < 80: → Mark "pending_review"
   │  └─ If confidence < 60: → Skip
   │
   ├─ TodoUpdater.update_todo_from_detection(detection)
   │  ├─ Find matching todo in memory system
   │  ├─ Update status and metadata
   │  └─ Return UpdateResult
   │
   ├─ _create_detection_event(detection, update_result)
   │  └─ Build AutomationEvent with evidence
   │
   ├─ _store_event(event) → AutomationHub
   │  └─ Log to automation_events table
   │
   └─ Return HookResult
      └─ Success/failure status + audit info
```

### Data Models

**DetectionResult:**

```python
@dataclass
class DetectionResult:
    keyword_found: Optional[str]    # e.g., "commit"
    confidence: int                 # 0-100
    category: str                   # "commit-related", "deployment", etc.
    context_snippet: str            # Surrounding text for evidence
```

**UpdateResult:**

```python
@dataclass
class UpdateResult:
    updated: bool                   # True if todo was updated
    todo_id: Optional[str]          # ID of updated todo
    old_status: Optional[str]       # Previous status
    new_status: Optional[str]       # New status
    reason: Optional[str]           # If not updated, why
```

**HookResult:**

```python
@dataclass
class HookResult:
    action_taken: bool              # True if any action occurred
    tool_name: str                  # Tool that executed
    keyword_found: Optional[str]    # Keyword detected
    confidence: Optional[int]       # Confidence score
    todo_updated: bool              # True if todo updated
    todo_id: Optional[str]          # Updated todo ID
    new_status: Optional[str]       # New status
    reason: str                     # Explanation of action
    event_id: Optional[int]         # Database event ID
```

### Keyword Detection

**Pattern Categories:**

```python
KEYWORDS = {
    "commit-related": [
        "git commit", "committed", "commit complete", "commit -m"
    ],
    "deployment": [
        "deployed", "pushed to", "live on", "deployment successful"
    ],
    "test-success": [
        "all tests passed", "tests passing", "test suite passed",
        "passed", "✅ passing"
    ],
    "bug-fixed": [
        "fixed", "resolved", "bug resolved", "patch applied"
    ],
    "build-success": [
        "build successful", "build complete", "compiled"
    ],
    "file-created": [
        "created", "written to", "saved"
    ]
}

FAILURE_INDICATORS = [
    "failed", "error", "unable to", "could not", "connection timeout",
    "unauthorized", "403", "404"
]
```

**Confidence Calculation:**

```python
def calculate_confidence(keyword, category, output):
    base_confidence = {
        "commit-related": 95,
        "deployment": 90,
        "test-success": 88,
        "bug-fixed": 85,
        "build-success": 90,
        "file-created": 75
    }[category]

    # Adjustments
    score = base_confidence
    if has_failure_indicators(output):
        score -= 30  # Lower confidence if failure keywords present
    if context_is_clear(output):
        score += 5   # Slightly higher if context is clear

    return max(0, min(100, score))
```

### Supported Tools

```
SUPPORTED_TOOLS = {"bash", "write", "edit"}

Tool      | Supported Patterns              | Confidence
──────────┼─────────────────────────────────┼─────────
bash      | Any keyword detection           | ✓ High
write     | File created keywords           | ✓ High
edit      | Modified/saved keywords         | ⚠ Medium (less reliable)
```

### Event Logging

```python
event = AutomationEvent(
    event_type="action_item_completed" | "action_item_pending_review",
    project_id="tier1-automation",
    status="success" | "pending_review",
    evidence={
        "tool_name": "bash",
        "detected_keyword": "commit",
        "keyword_category": "commit-related",
        "confidence": 95,
        "context_snippet": "git commit -m 'fix: auth bug'",
        "todo_id": "abc-123",
        "old_status": "in_progress",
        "new_status": "completed"
    },
    detected_from="hook",
    metadata={
        "hook_type": "PostToolUse",
        "timestamp": "2026-01-20T18:45:32Z"
    }
)
```

### Files

```
tools_db/tools/
├─ keyword_detector.py           (Keyword pattern matching)
│  ├─ KeywordDetector class
│  └─ DetectionResult dataclass
│
├─ todo_updater.py               (Todo status updates)
│  ├─ TodoUpdater class
│  └─ UpdateResult dataclass
│
└─ action_item_hook.py           (Hook orchestration)
   ├─ ActionItemHook class
   ├─ HookResult dataclass
   └─ PostToolUse integration
```

---

## Component 3: n8n Reliability Layer

### Architecture

```
n8n Task Execution
│
└─ PreToolUse Event (n8n tool)
   │
   ├─ N8nReliabilityHook.on_task_started()
   │  ├─ Register task with N8nMonitor
   │  └─ Return monitor_id
   │
   └─ n8n Task Executes
      │
      └─ PostTaskUse Event OR Error Callback
         │
         ├─ N8nReliabilityHook.on_task_completed()
         │  │
         │  ├─ N8nMonitor.report_result()
         │  │  ├─ _detect_failure_pattern(status_code, response, duration)
         │  │  ├─ _extract_task_metadata()
         │  │  ├─ _log_failure_event() → AutomationHub
         │  │  └─ Return MonitorResult
         │  │
         │  └─ If failure_detected:
         │     │
         │     └─ CeleryFallbackRouter.route_to_fallback(monitor_result)
         │        │
         │        ├─ Map n8n workflow to Celery task
         │        │
         │        ├─ Attempt 1: Celery Direct (1s)
         │        ├─ Attempt 2: API Fallback (5s)
         │        └─ Attempt 3: Systemd Fallback (30s)
         │           │
         │           └─ Log recovery attempt → AutomationHub
         │
         └─ Return HookExecutionResult
            └─ With recovery status and event IDs
```

### Data Models

**FailureType (Enum):**

```python
class FailureType(Enum):
    AUTH_FAILURE = "403_unauthorized"
    GATEWAY_TIMEOUT = "504_gateway_timeout"
    EXECUTION_TIMEOUT = "execution_timeout"
    WEBHOOK_FAILURE = "webhook_error"
    UNKNOWN_ERROR = "unknown_error"
    NO_FAILURE = "success"
```

**MonitorResult:**

```python
@dataclass
class MonitorResult:
    failure_detected: bool              # True if failure pattern
    failure_type: Optional[FailureType] # Type of failure
    task_id: str                        # Original task ID
    workflow_name: str                  # Workflow name
    status_code: Optional[int]          # HTTP status
    duration_seconds: float             # Execution time
    reason: str                         # Explanation
    event_id: Optional[int]             # Database event ID
```

**ExecutionResult:**

```python
@dataclass
class ExecutionResult:
    success: bool                       # Execution succeeded
    attempt_method: str                 # Method used
    attempt_number: int                 # Attempt 1/2/3
    execution_time_seconds: float       # Time taken
    result_summary: str                 # Output
    error_message: Optional[str]        # If failed
```

**RoutingResult:**

```python
@dataclass
class RoutingResult:
    routed: bool                        # Successfully routed
    celery_task_name: Optional[str]     # Mapped task name
    execution_result: Optional[ExecutionResult]  # Result
    reason: str                         # Explanation
    event_id: Optional[int]             # Database event ID
```

### Failure Detection Logic

```python
def _detect_failure_pattern(status_code, response, duration):
    # Priority order of checks:

    # 1. Check execution timeout (duration > 30s)
    if duration > 30.0:
        return FailureType.EXECUTION_TIMEOUT

    # 2. Check HTTP status codes
    if status_code == 403:
        return FailureType.AUTH_FAILURE
    if status_code == 504:
        return FailureType.GATEWAY_TIMEOUT

    # 3. Check response content for patterns
    response_lower = response.lower()

    if any(keyword in response_lower for keyword in AUTH_KEYWORDS):
        return FailureType.AUTH_FAILURE

    if any(keyword in response_lower for keyword in GATEWAY_KEYWORDS):
        return FailureType.GATEWAY_TIMEOUT

    if any(keyword in response_lower for keyword in WEBHOOK_KEYWORDS):
        return FailureType.WEBHOOK_FAILURE

    if any(keyword in response_lower for keyword in ERROR_KEYWORDS):
        return FailureType.UNKNOWN_ERROR

    return FailureType.NO_FAILURE
```

### Fallback Chain Implementation

**Tier 1: Celery Direct (1 second timeout)**

```python
def attempt_celery_direct(task_name, params):
    try:
        # Import dynamically to avoid hard dependency
        from app import celery_app

        # Execute task synchronously
        result = celery_app.send_task(
            task_name,
            args=(params,),
            timeout=1
        ).get(timeout=1)

        return ExecutionResult(
            success=True,
            attempt_method="celery_direct",
            attempt_number=1,
            execution_time_seconds=...,
            result_summary=result
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            attempt_method="celery_direct",
            attempt_number=1,
            execution_time_seconds=...,
            result_summary="",
            error_message=str(e)
        )
```

**Tier 2: API Fallback (5 second timeout)**

```python
def attempt_api_fallback(task_name, params):
    try:
        import requests

        response = requests.post(
            f"http://localhost:8000/tasks/{task_name}",
            json=params,
            timeout=5
        )

        if response.status_code == 200:
            return ExecutionResult(success=True, ...)
        else:
            return ExecutionResult(success=False, ...)
    except Exception as e:
        return ExecutionResult(success=False, ...)
```

**Tier 3: Systemd Fallback (30 second timeout)**

```python
def attempt_systemd_fallback(task_name, params):
    try:
        import subprocess
        import json

        # Execute task as systemd service
        result = subprocess.run(
            ["systemctl", "start", f"tier1-task@{task_name}"],
            capture_output=True,
            timeout=30
        )

        if result.returncode == 0:
            return ExecutionResult(success=True, ...)
        else:
            return ExecutionResult(success=False, ...)
    except Exception as e:
        return ExecutionResult(success=False, ...)
```

### Task Mapping

```python
N8N_TO_CELERY_MAPPING = {
    'video-assembly': 'process_video',
    'draft-generator': 'generate_draft',
    'content-idea-capture': 'capture_idea',
    'kb-indexing': 'index_kb',
}

def map_n8n_to_celery(workflow_name):
    celery_task = N8N_TO_CELERY_MAPPING.get(workflow_name)
    if not celery_task:
        raise ValueError(f"No mapping for {workflow_name}")
    return celery_task
```

### Event Logging

**Failure Detection Event:**

```python
event = AutomationEvent(
    event_type="n8n_failure_detected",
    project_id="n8n",
    status="failed",
    evidence={
        "task_id": "video-assembly",
        "workflow_name": "video-assembly",
        "failure_type": "504_gateway_timeout",
        "status_code": 504,
        "duration_seconds": 15.2,
        "response_snippet": "Service Unavailable: Gateway Timeout",
        "timestamp": "2026-01-20T18:45:32Z"
    },
    detected_from="monitor",
    metadata={
        "monitor_type": "n8n",
        "can_fallback": True
    }
)
```

**Recovery Attempt Event:**

```python
event = AutomationEvent(
    event_type="n8n_recovery_attempted",
    project_id="n8n",
    status="success",  # Recovery was successful
    evidence={
        "task_id": "video-assembly",
        "original_failure": "504_gateway_timeout",
        "recovery_method": "api_fallback",  # Method that worked
        "recovery_duration_seconds": 2.1,
        "attempts": [
            {"method": "celery_direct", "success": false, "duration": 0.3},
            {"method": "api_fallback", "success": true, "duration": 2.1}
        ]
    },
    detected_from="router",
    metadata={
        "routing_type": "n8n_to_celery",
        "recovery_successful": True
    }
)
```

### Files

```
tools_db/tools/
├─ n8n_monitor.py                (Failure detection)
│  ├─ N8nMonitor class
│  ├─ MonitorResult dataclass
│  └─ FailureType enum
│
├─ celery_fallback_router.py      (3-tier fallback)
│  ├─ CeleryFallbackRouter class
│  ├─ ExecutionResult dataclass
│  ├─ RoutingResult dataclass
│  └─ N8N_TO_CELERY_MAPPING
│
└─ n8n_reliability_hook.py        (Hook orchestration)
   ├─ N8nReliabilityHook class
   ├─ RecoveryResult dataclass
   ├─ HookExecutionResult dataclass
   └─ PreToolUse integration
```

---

## Data Model: AutomationEvent

### Schema

```python
@dataclass
class AutomationEvent:
    event_type: str                      # production_check, action_item_completed, etc.
    project_id: str                      # Project identifier
    status: str                          # pending, success, failed, warning
    evidence: Dict[str, Any]             # Detailed event data (JSON)
    detected_from: str                   # skill, hook, manual, monitor, router
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
```

### Database Table

```sql
CREATE TABLE automation_events (
    id SERIAL PRIMARY KEY,

    -- Event classification
    event_type VARCHAR(255) NOT NULL,      -- production_check, action_item_completed, etc.
    project_id VARCHAR(255) NOT NULL,      -- Project name or git repo
    status VARCHAR(50) NOT NULL,           -- pending, success, failed, warning

    -- Event data
    evidence JSONB NOT NULL,               -- Detailed results/logs
    detected_from VARCHAR(50),             -- skill, hook, manual, monitor, router
    metadata JSONB,                        -- Additional context

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,

    -- Indexes for performance
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_project_id (project_id),
    INDEX idx_status (status),
    INDEX idx_composite (project_id, event_type, created_at DESC)
);
```

### Index Strategy

```
Primary Indexes:
- idx_event_type: For filtering by component (production_check, action_item_*, n8n_*)
- idx_created_at: For time-based queries (recent events, daily reports)
- idx_project_id: For project-specific event history
- idx_status: For success/failure analysis

Composite Indexes:
- (project_id, event_type, created_at): Most common query pattern
  SELECT * FROM automation_events
  WHERE project_id = ? AND event_type = ?
  ORDER BY created_at DESC

Query Patterns:
1. Recent events: created_at DESC LIMIT 50
2. By type: WHERE event_type = 'production_check'
3. By project: WHERE project_id = 'tier1-automation'
4. By status: WHERE status = 'failed'
5. Time range: WHERE created_at > NOW() - INTERVAL '7 days'
```

### Event Types

```
Event Type                    | Status Values        | Component
──────────────────────────────┼──────────────────────┼────────────
production_check              | success, failed       | 1
action_item_completed         | success              | 2
action_item_pending_review    | pending_review       | 2
no_action_taken               | skipped              | 2
n8n_failure_detected          | failed               | 3
n8n_recovery_attempted        | success, failed      | 3
```

### Evidence Structure

**Production Check Evidence:**

```json
{
  "checks": {
    "tests": {
      "passed": true,
      "details": "269 tests passed",
      "duration_seconds": 4.32
    },
    "security": {"passed": true, "details": "No violations"},
    // ... other checks
  },
  "decision": "go",
  "confidence": 100
}
```

**Action Item Evidence:**

```json
{
  "tool_name": "bash",
  "detected_keyword": "commit",
  "keyword_category": "commit-related",
  "confidence": 95,
  "context_snippet": "git commit -m 'fix: auth'",
  "todo_id": "abc-123",
  "old_status": "in_progress",
  "new_status": "completed"
}
```

**n8n Failure Evidence:**

```json
{
  "task_id": "video-assembly",
  "workflow_name": "video-assembly",
  "failure_type": "504_gateway_timeout",
  "status_code": 504,
  "duration_seconds": 15.2,
  "response_snippet": "Service Unavailable",
  "timestamp": "2026-01-20T18:45:32Z"
}
```

---

## Integration Points

### Component Interaction

```
Production Check
  └─ Event: production_check (success)
     ↓
Action Item Hook (detects "deployed")
  └─ Event: action_item_completed
     └─ Metadata: correlated_with=[production_check_id]
     ↓
n8n Task Starts
  └─ N8n Monitor watches
     └─ 504 failure detected
     └─ Event: n8n_failure_detected
        ↓
Celery Fallback
  └─ Recovery attempts
  └─ Event: n8n_recovery_attempted (success)

All Events → automation_events table
```

### AutomationHub as Single Source of Truth

```python
class AutomationHub:
    """Central coordination point for all automation events"""

    def store_event(self, event: AutomationEvent) -> int:
        """Store event to database, return event ID"""
        # Centralized event storage
        # All components use this method
        # Enables audit trail and correlation
        pass

    def get_events(self, event_type=None, status=None, project_id=None):
        """Query events with flexible filtering"""
        pass

    def get_event_timeline(self, project_id: str, hours: int = 24):
        """Get chronological event sequence"""
        pass

    def correlate_events(self, event_id: int):
        """Find related events (success → action → n8n task)"""
        pass
```

### Error Handling and Graceful Degradation

```
When database is down:
├─ Component 1: Production checks still work (no event logging)
├─ Component 2: Keyword detection still works (no event logging)
└─ Component 3: Failure detection still works (no event logging)
   └─ All fallbacks still attempted

When Redis is down:
├─ Celery fallback fails (Tier 1)
├─ API fallback attempted (Tier 2)
└─ Systemd fallback attempted (Tier 3)

When Celery workers down:
├─ Tier 1: Celery fails fast (1s timeout)
├─ Tier 2: API fallback (5s timeout)
└─ Tier 3: Systemd (30s timeout)
```

### Cascade Failures and Isolation

```
Failure Isolation:
- Component 1 failure: Does not affect 2 or 3
- Component 2 failure: Does not affect 1 or 3
- Component 3 failure: Does not affect 1 or 2

Example: Database down
├─ Component 1: Still runs checks, just doesn't log
├─ Component 2: Still detects keywords, just doesn't log
└─ Component 3: Still detects failures, just doesn't log
   ↓
All components continue working (degraded mode)
```

---

## Performance Considerations

### Database Query Optimization

```
Query: Get recent events for a project
SELECT * FROM automation_events
WHERE project_id = 'tier1-automation'
ORDER BY created_at DESC
LIMIT 50;

Without index: Full table scan
With composite index (project_id, event_type, created_at DESC):
  ├─ Seek to project_id = 'tier1-automation'
  ├─ Sort by created_at DESC
  └─ Result: < 10ms for millions of rows

Explain plan:
INDEX idx_composite (project_id, event_type, created_at DESC)
└─ Index Scan (project_id, created_at DESC)
```

### Index Usage

```
Index Strategy:
1. Primary filters: event_type, project_id
2. Sort key: created_at DESC (time-ordered)
3. Coverage: Include evidence for common searches

Indexes created:
- idx_event_type: Speed event type filtering
- idx_created_at: Speed time-based queries
- idx_project_id: Speed project filtering
- idx_status: Speed success/failure analysis
- idx_composite: Speed most common combined queries
```

### Event Logging Overhead

```
Event logging per operation:
- Keyword detection: ~5-10ms (JSON serialization + insert)
- Failure detection: ~5-10ms
- Production check: ~2-5ms (once per check)

Total overhead per workflow:
- 10 tool executions × 8ms = 80ms
- Not perceptible to user
- Minimal impact on performance
```

### Timeout Values Tuned for Production

```
Celery Tier 1: 1s
├─ Fast simple tasks only
├─ Fails fast, doesn't block
└─ Moves to Tier 2 if needed

API Tier 2: 5s
├─ Standard operations
├─ Good balance of reliability and speed
└─ Moves to Tier 3 if needed

Systemd Tier 3: 30s
├─ Complex/heavy operations
├─ Most reliable (process isolation)
└─ Final attempt

Total max recovery time: 1s + 5s + 30s = 36s
(Typical: 2-5s via Tier 2)
```

### Scalability Limits

```
Single PostgreSQL Instance:
- Rows per table: 10+ million (no practical limit)
- Events per day: 100K+ (0.01% of capacity)
- Query response time: < 50ms (with proper indexes)
- Insert throughput: 1000+ events/second

Scaling strategies:
1. Archive events older than 90 days
2. Partition table by date (YYYY_MM)
3. Replication for read scaling
4. Connection pooling (max 100 connections)
```

---

## Security Considerations

### Database Access Control

```sql
-- Create automation user with limited permissions
CREATE ROLE automation_user WITH LOGIN PASSWORD 'strong_password';

-- Grant permissions
GRANT CONNECT ON DATABASE tools_db TO automation_user;
GRANT USAGE ON SCHEMA public TO automation_user;
GRANT SELECT, INSERT, UPDATE ON automation_events TO automation_user;
GRANT SELECT ON automation_events TO automation_user;  -- Read-only for reporting

-- Revoke dangerous permissions
REVOKE DELETE ON automation_events FROM automation_user;
REVOKE TRUNCATE ON automation_events FROM automation_user;
```

### Sensitive Data in Logs

```
Evidence safe to store:
✓ Test counts, durations
✓ Check results (pass/fail)
✓ Keyword names, confidence scores
✓ Task IDs, workflow names
✓ Failure types, status codes

Evidence NOT safe to store:
✗ Actual output/response bodies (might contain secrets)
✗ Full error messages (might contain credentials)
✗ API responses (might contain keys)
✓ But: Truncate to snippets (first 200 chars)
```

**Data Sanitization:**

```python
def sanitize_response(response: str, max_length: int = 200) -> str:
    """Truncate response and remove sensitive patterns"""
    # Truncate
    truncated = response[:max_length]

    # Remove common secrets
    import re
    sanitized = re.sub(r'(api[_-]?key|password|token|secret)\s*[:=]\s*\S+',
                      r'\1=[REDACTED]', truncated, flags=re.I)

    return sanitized
```

### n8n Authentication Handling

```python
# Store n8n API key securely
N8N_API_KEY = os.environ.get('N8N_API_KEY')  # From .env, not hardcoded

# Never log the key
if N8N_API_KEY in response:
    response = response.replace(N8N_API_KEY, '[REDACTED]')

# Use key only for API calls
headers = {
    'X-N8N-API-KEY': N8N_API_KEY,  # In memory only
    'Content-Type': 'application/json'
}
```

### Celery Task Security

```python
# Tasks should not accept sensitive data
# Bad:
@app.task
def process_video(url, api_key):  # Don't pass keys!
    pass

# Good:
@app.task
def process_video(url, video_id):  # Pass IDs only
    api_key = os.environ.get('API_KEY')  # Get from environment
    # Use api_key
    pass
```

### Input Validation

```python
# Validate event data before storing
def store_event(self, event: AutomationEvent) -> int:
    # Validate event_type
    if event.event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"Invalid event_type: {event.event_type}")

    # Validate status
    if event.status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {event.status}")

    # Validate evidence is JSON-serializable
    try:
        json.dumps(event.evidence)
    except TypeError:
        raise ValueError("Evidence must be JSON-serializable")

    # Insert sanitized data
    return self._insert_event(event)
```

---

## Design Decisions

### Why Unified automation_events Table

**Decision:** Single table for all component events

**Rationale:**
- **Correlation**: Trace related events across components
- **Consistency**: Single source of truth for audit trail
- **Simplicity**: One table, one schema, one index strategy
- **Scalability**: Single partition strategy vs. multiple tables
- **Query Performance**: Composite indexes work efficiently

**Alternative Rejected:**
- Separate tables per component
  - Problem: Can't correlate events efficiently
  - Problem: Multiple schemas to maintain
  - Problem: More complex querying

### Why 3-Tier Fallback Chain

**Decision:** Celery → API → Systemd strategy

**Rationale:**
- **Tier 1 (Celery)**: Optimized for speed, fails fast
- **Tier 2 (API)**: Balance of reliability and speed
- **Tier 3 (Systemd)**: Maximum reliability, process isolation

**Why Not:**
- Just retry n8n (Problem: Same failure repeats)
- Just use Celery (Problem: If Celery down, no fallback)
- Just use API (Problem: If API down, no fallback)

### Why Confidence Thresholds

**Decision:** 80%+ auto-complete, 60-80% pending review, <60% skip

**Rationale:**
- **≥80%**: High confidence, safe to auto-complete
- **60-80%**: Medium confidence, flag for review
- **<60%**: Low confidence, too risky (prevents false positives)

**Example:**
- "git commit" → 95% (clear action) → Auto-complete ✓
- "created" alone → 55% (ambiguous) → Skip ✗
- "file created" → 75% (medium context) → Pending review ⚠

### Why PostToolUse and PreToolUse Hooks

**Decision:** Use Claude Code hooks instead of polling

**Rationale:**
- **PostToolUse**: Immediate detection of completion keywords
- **PreToolUse**: Proactive n8n monitoring
- **Real-time**: No polling overhead, instant response
- **Lightweight**: Hook runs only when relevant events occur

**Alternative Rejected:**
- Polling approach (Problem: Continuous overhead, lag)
- Manual API calls (Problem: User must remember to run)

---

## Deployment Architecture

```
Development (Local)
├─ SQLite database (tools_db.db)
├─ In-memory event storage (testing)
└─ No Redis/Celery required

Staging/Testing
├─ PostgreSQL (tools_db)
├─ Redis for Celery queue
├─ Test Celery workers
└─ Test n8n instance

Production
├─ PostgreSQL cluster (master-replica)
├─ Redis cluster (HA)
├─ Multiple Celery workers (load balanced)
├─ Production n8n instance
└─ Backup and monitoring in place
```

---

## Future Enhancements

```
Potential improvements:
1. Machine learning for confidence scoring
2. Event correlation and causality analysis
3. Predictive alerts (detect issues before they happen)
4. Custom keyword patterns per project
5. Webhook notifications for important events
6. Advanced analytics dashboard
7. Integration with incident management systems
8. Auto-remediation workflows
```

---

For deployment details, see [DEPLOYMENT.md](DEPLOYMENT.md).
For usage guide, see [TIER1_AUTOMATION_GUIDE.md](TIER1_AUTOMATION_GUIDE.md).
