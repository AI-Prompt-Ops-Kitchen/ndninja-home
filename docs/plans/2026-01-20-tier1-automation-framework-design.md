# Tier 1 Automation Framework - Unified Design

> **Status:** Design Complete | **Date:** 2026-01-20 | **For Claude:** Execute with superpowers:subagent-driven-development

## Executive Summary

Integrated system for 3 high-impact automation items:
1. **Production Readiness Skill** — Project-specific go/no-go checklists with automated tests, security scans, performance benchmarks
2. **Action Item Progress Tracking** — PostToolUse hook that detects completion keywords in tool outputs and auto-updates todos
3. **n8n Task Runner Reliability Layer** — Fallback queue system that auto-detects 403/timeout errors and reroutes to Celery (with API/systemd fallback)

All three feed into a unified **Status Hub** using PostgreSQL's `automation_events` table for audit trails and state tracking.

---

## Architecture Overview

**Three coordinated components sharing unified Status Hub:**

- **Production Readiness Skill** (`/production-check`) — Generates project-specific checklists, runs automated tests/security scans, outputs go/no-go with evidence
- **Action Item Progress Tracking** — PostToolUse hook detects completion keywords in Write/Bash/Edit outputs, auto-updates todo status in memory system
- **n8n Reliability Layer** — PreToolUse hook monitors n8n task outcomes; on 403/timeout, reroutes to Celery queue (with fallback to direct API or systemd)

**Data Flow:**
1. Production readiness runs → stores checkpoint status in `automation_events`
2. Tool executes (Write/Bash/Edit) → PostToolUse hook analyzes output → updates todo memory system
3. n8n task fails → PreToolUse hook logs to `automation_events` → queues fallback task to Celery
4. Status hub queries `automation_events` to provide unified dashboard view

**Infrastructure Used:** PostgreSQL (existing `tools_db`), Redis (Celery backend), Memory system (claude-memory), Celery workers (existing on server)

---

## Component 1: Production Readiness Skill

**Purpose:** Verify that a project/feature is ready for production deployment with automated evidence collection.

**Input:** Project name, optional version/git tag (defaults to HEAD)

**Output:** Go/No-Go decision with checklist results and evidence artifacts

**Automated Checks (executed sequentially):**
1. **Test Coverage** — Run `pytest tests/ -v`, collect results, require ≥80% pass rate
2. **Security Scan** — Grep for OWASP top 10 patterns (hardcoded credentials, SQL injection, XSS), flag issues
3. **Performance Benchmarks** — If `benchmarks/` exists, run and verify against baseline
4. **Documentation** — Check for README, IMPLEMENTATION_SUMMARY, API docs; require ≥3 of 5
5. **Integration Tests** — Run any `tests/integration_*.py` files
6. **Rollback Plan** — Verify `ROLLBACK.md` or git tag exists for previous stable version

**Results stored in `automation_events`:**
- `event_type: "production_check"`
- `status: "go" | "no_go" | "warning"`
- `evidence: { checklist: [...], failed_checks: [...], timestamp: ... }`

**Output format:** Markdown report with ✅/❌ per check, git commit hash, ready to post as release notes or ticket comment

**Example Output:**
```
✅ Tests: 47/47 passing
❌ Security: 1 hardcoded credential found (app/config.py:12)
✅ Documentation: 5/5 items present
⚠️  Performance: No benchmarks.py found (warning only)
⏩ Rollback: Tag v1.2.3-stable available

DECISION: ⚠️  WARNING - Fix security issue before deploy
```

---

## Component 2: Action Item Progress Tracking (PostToolUse Hook)

**Purpose:** Auto-detect when tool outputs indicate task completion, update todo status without manual intervention.

**How it works:**
1. After any tool executes (Write/Bash/Edit), hook analyzes output for completion keywords
2. Matches keywords against current todo list in memory system
3. Auto-updates status from "in_progress" → "completed" with confidence score
4. Logs detection event to `automation_events` for audit trail

**Completion Keywords (matched case-insensitive):**
- Commit-related: `git commit`, `committed`, `commit complete`
- Deployment: `deployed`, `pushed to`, `live on`
- Test success: `all tests passed`, `tests passing`, `test suite passed`, `✅ passing`
- Bug fixed: `fixed`, `resolved`, `bug resolved`, `patch applied`
- Build success: `build successful`, `build complete`, `compiled`
- File created: `created`, `written to`, `saved`

**Detection Algorithm:**
1. Parse tool output for keywords
2. If keyword found + (confidence score ≥ 80%), auto-update todo
3. If confidence 60-80%, mark as "pending_review" (user can confirm/reject)
4. If <60%, skip (false positive prevention)

**Example:**
```
Tool output: "git add -A && git commit -m 'feat: add production check skill'"
↓
Detected: "git commit" keyword (confidence: 95%)
↓
Auto-updates todo "Implement production-check skill" from in_progress → completed
↓
Logs to automation_events: {event_type: "action_item_completed", todo_id: "x", detected_from: "bash_output", confidence: 95}
```

**Edge cases handled:**
- Multiple todos matched → update the one currently marked "in_progress" (assumes sequential work)
- No current todos → skip (no confusion with past sessions)
- Keyword in error message (e.g., "commit failed") → parse context, only match success cases

---

## Component 3: n8n Reliability Layer (PreToolUse Hook)

**Purpose:** Detect n8n task failures (403, timeout, webhook errors) and automatically reroute to Celery queue with fallback to direct API or systemd.

**How it works:**
1. Before n8n task executes, hook registers a monitor
2. If task returns 403 (Unauthorized), 504 (Gateway Timeout), or hangs >30s, trigger fallback
3. Route task to Celery queue with retry logic
4. Celery worker executes task directly (invoke Python API or systemd service)
5. Log to `automation_events` for audit trail

**Fallback Routing Logic:**
```
n8n task fails (403/timeout)
  ↓
Check if task has Celery equivalent → Route to queue
  (e.g., n8n "video-assembly" → celery task "process_video")
  ↓
Celery worker picks up task:
  - Option A: Call video-api/draft-api directly via HTTP
  - Option B: If API unavailable, trigger systemd service
  - Option C: Retry with exponential backoff (3 attempts)
  ↓
Store result in automation_events with:
  {event_type: "n8n_fallback_routed", n8n_task_id: "...", status: "success|failed", fallback_method: "celery|api|systemd"}
```

**Task Mappings (auto-detected from n8n workflow name):**
- `n8n:video-assembly` → `celery:tasks.process_video`
- `n8n:draft-generator` → `celery:tasks.generate_draft`
- `n8n:content-idea-capture` → `celery:tasks.capture_idea`
- `n8n:kb-indexing` → `celery:tasks.index_kb`

**Retry Strategy:**
- Attempt 1: Celery direct call (1s timeout)
- Attempt 2: API fallback (5s timeout)
- Attempt 3: Systemd service (30s timeout)
- If all fail: Alert user via memory system, log critical to `automation_events`

**Example:**
```
n8n task "draft-generator" returns 403
↓
Hook detects 403 → Routes to Celery
↓
Celery worker calls draft-api.generate_draft()
↓
Draft API succeeds → Returns result
↓
Logs: {event_type: "n8n_fallback_routed", original_task: "draft-generator", method: "api", status: "success"}
```

---

## Unified Status Hub & Data Model

**New `automation_events` table in `tools_db`:**

```python
@dataclass
class AutomationEvent:
    event_type: str  # "production_check", "action_item_completed", "n8n_fallback_routed"
    project_id: str  # project name or git repo
    status: str      # "pending", "success", "failed", "warning"
    evidence: Dict   # detailed results/logs
    detected_from: str  # "skill", "hook", "manual"
    created_at: datetime
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict] = None
```

**Shared Queries:**
- `get_project_status(project_id)` — Returns latest production_check, pending action_items, any n8n failures
- `get_action_item_events(session_id)` — All detected completions in current session
- `get_n8n_reliability_metrics()` — Success rate of fallback routing, failure patterns

**Integration Points:**
1. **Skill** reads `automation_events` to show pre-flight report
2. **PostToolUse hook** writes action_item_completed events, queries action_items
3. **PreToolUse hook** queries n8n_failure history, writes fallback_routed events
4. **Memory system** reads completed items via `automation_events`, updates todo status

**Database Changes:**
- Add 1 table: `automation_events` (minimal schema)
- Add 3 indexes: `(event_type, project_id)`, `(created_at DESC)`, `(status)`
- No migrations needed — backward compatible with existing `tools_db`

**Error Handling:**
- If database unavailable: Fall back to in-memory state (memory system)
- If Celery unavailable: Fall back to direct API call
- If all methods fail: Log critical event, alert user via notification

---

## Tech Stack

- **Database:** PostgreSQL (existing `tools_db`)
- **Background Tasks:** Celery + Redis (existing infrastructure)
- **API Calls:** Requests library (for video-api, draft-api fallbacks)
- **Systemd Integration:** Subprocess for service control
- **Memory System:** Existing claude-memory for todo updates
- **Testing:** Pytest with mocking for n8n/Celery/systemd
- **Skill Framework:** Existing Claude Code skill pattern

---

## Success Criteria

1. ✅ `/production-check` skill runs all 6 checks, outputs go/no-go decision
2. ✅ Action item progress tracking auto-detects 80%+ of completion keywords
3. ✅ n8n fallback routing successfully reroutes 403 errors to Celery
4. ✅ All events logged to `automation_events` with audit trail
5. ✅ 50+ tests covering all components with 100% pass rate
6. ✅ Zero manual user input needed after initial deployment
7. ✅ Production-ready code with comprehensive error handling

---

## Next Steps

Execute with superpowers:writing-plans to create detailed 15-task implementation plan, then superpowers:subagent-driven-development to execute all tasks automatically.
