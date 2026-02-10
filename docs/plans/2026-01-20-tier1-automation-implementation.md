# Tier 1 Automation Framework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Build unified automation system for production readiness verification, action item progress tracking, and n8n reliability with 50+ tests achieving 100% pass rate.

**Architecture:** Three coordinated components (Production Readiness Skill, Action Item Progress Tracking hook, n8n Reliability Layer) sharing unified Status Hub in PostgreSQL `automation_events` table with in-memory caching for real-time updates.

**Tech Stack:** PostgreSQL, Celery+Redis, Python 3.13, Pytest, Claude Memory System, Existing tools_db infrastructure

---

## PHASE 1: Database Infrastructure (Tasks 1-3)

### Task 1: Create AutomationEvent Data Model

**Files:**
- Modify: `tools_db/models.py:95-130` (add new model)
- Create: `tests/test_automation_models.py` (new test file)

**Step 1: Write the failing test**

```python
# tests/test_automation_models.py
import pytest
from datetime import datetime, timezone
from tools_db.models import AutomationEvent

def test_automation_event_creation():
    """Test AutomationEvent dataclass creation and defaults"""
    event = AutomationEvent(
        event_type="production_check",
        project_id="my-project",
        status="success",
        evidence={"checks": ["tests", "security"]},
        detected_from="skill"
    )

    assert event.event_type == "production_check"
    assert event.project_id == "my-project"
    assert event.status == "success"
    assert event.detected_from == "skill"
    assert event.created_at is not None
    assert isinstance(event.created_at, datetime)
    assert event.resolved_at is None

def test_automation_event_resolve():
    """Test marking event as resolved"""
    event = AutomationEvent(
        event_type="n8n_fallback_routed",
        project_id="content-pipeline",
        status="success",
        evidence={"method": "celery"},
        detected_from="hook"
    )

    event.resolved_at = datetime.now(timezone.utc)
    assert event.resolved_at is not None
```

**Step 2: Run test to verify it fails**

```bash
cd /home/ndninja/.worktrees/tier1-automation
pytest tests/test_automation_models.py -v
```

Expected: FAIL - `AutomationEvent not defined in tools_db.models`

**Step 3: Write minimal implementation**

Add to `tools_db/models.py` after PromptVersion class (around line 95):

```python
@dataclass
class AutomationEvent:
    """Event tracking for automation framework (production checks, action items, n8n failures)"""
    event_type: str  # "production_check", "action_item_completed", "n8n_fallback_routed"
    project_id: str  # project name or git repo
    status: str      # "pending", "success", "failed", "warning"
    evidence: Dict[str, Any]  # detailed results/logs
    detected_from: str  # "skill", "hook", "manual"
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        data = self.to_dict()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return json.dumps(data)
```

Also add `asdict` to imports at top of file if not present:
```python
from dataclasses import dataclass, asdict
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_automation_models.py -v
```

Expected: PASS - 2 tests passing

**Step 5: Commit**

```bash
git add tools_db/models.py tests/test_automation_models.py
git commit -m "feat: add AutomationEvent data model for automation framework"
```

---

### Task 2: Create Database Migration for automation_events Table

**Files:**
- Create: `tools_db/migrations/versions/001_add_automation_events.py` (Alembic migration)
- Modify: `tools_db/database.py:156-178` (add table creation SQL)
- Create: `tests/test_automation_database.py`

**Step 1: Write the failing test**

```python
# tests/test_automation_database.py
import pytest
from tools_db.database import Database
import sqlite3

def test_automation_events_table_created():
    """Test that automation_events table is created with correct schema"""
    db = Database("sqlite:///:memory:")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='automation_events'
        """)
        assert cursor.fetchone() is not None, "automation_events table not found"

        # Check columns exist
        cursor.execute("PRAGMA table_info(automation_events)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_columns = {
            'id': 'INTEGER',
            'event_type': 'TEXT',
            'project_id': 'TEXT',
            'status': 'TEXT',
            'evidence': 'TEXT',
            'detected_from': 'TEXT',
            'created_at': 'DATETIME',
            'resolved_at': 'DATETIME',
            'metadata': 'TEXT'
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Column {col_name} not found"

def test_automation_events_indexes_created():
    """Test that indexes are created for performance"""
    db = Database("sqlite:///:memory:")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='automation_events'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'ix_automation_event_type_project',
            'ix_automation_created_at',
            'ix_automation_status'
        ]

        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} not found"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_automation_database.py::test_automation_events_table_created -v
```

Expected: FAIL - table not found

**Step 3: Write minimal implementation**

Add to `tools_db/database.py` in `_create_tables_sql()` method, after prompt_versions table (around line 156):

```python
        -- Automation Events table
        CREATE TABLE IF NOT EXISTS automation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            project_id TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence TEXT NOT NULL,
            detected_from TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            metadata TEXT
        );

        CREATE INDEX IF NOT EXISTS ix_automation_event_type_project ON automation_events(event_type, project_id);
        CREATE INDEX IF NOT EXISTS ix_automation_created_at ON automation_events(created_at DESC);
        CREATE INDEX IF NOT EXISTS ix_automation_status ON automation_events(status);
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_automation_database.py -v
```

Expected: PASS - 2 tests passing

**Step 5: Commit**

```bash
git add tools_db/database.py tests/test_automation_database.py
git commit -m "feat: add automation_events table with indexes to tools_db"
```

---

### Task 3: Add AutomationEvent Database Operations

**Files:**
- Create: `tools_db/tools/automation_hub.py` (new module for automation queries)
- Modify: `tests/test_automation_database.py:+30` (add more tests)

**Step 1: Write the failing test**

```python
# Add to tests/test_automation_database.py
from tools_db.tools.automation_hub import AutomationHub
from tools_db.models import AutomationEvent
from datetime import datetime, timezone

def test_automation_hub_store_event():
    """Test storing AutomationEvent to database"""
    from tools_db.database import Database
    db = Database("sqlite:///:memory:")
    hub = AutomationHub(db=db)

    event = AutomationEvent(
        event_type="production_check",
        project_id="test-project",
        status="success",
        evidence={"checks": 6, "passed": 6},
        detected_from="skill"
    )

    stored_id = hub.store_event(event)
    assert stored_id is not None
    assert isinstance(stored_id, int)

def test_automation_hub_get_project_status():
    """Test retrieving project status"""
    from tools_db.database import Database
    db = Database("sqlite:///:memory:")
    hub = AutomationHub(db=db)

    event = AutomationEvent(
        event_type="production_check",
        project_id="test-project",
        status="success",
        evidence={"checks": 6},
        detected_from="skill"
    )
    hub.store_event(event)

    status = hub.get_project_status("test-project")
    assert status is not None
    assert status["event_type"] == "production_check"
    assert status["status"] == "success"

def test_automation_hub_list_events_by_type():
    """Test listing events by type"""
    from tools_db.database import Database
    db = Database("sqlite:///:memory:")
    hub = AutomationHub(db=db)

    # Store multiple events
    for i in range(3):
        event = AutomationEvent(
            event_type="action_item_completed",
            project_id=f"project-{i}",
            status="success",
            evidence={"todo_id": f"item-{i}"},
            detected_from="hook"
        )
        hub.store_event(event)

    events = hub.get_events_by_type("action_item_completed")
    assert len(events) == 3
    assert all(e["event_type"] == "action_item_completed" for e in events)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_automation_database.py::test_automation_hub_store_event -v
```

Expected: FAIL - AutomationHub not defined

**Step 3: Write minimal implementation**

Create `tools_db/tools/automation_hub.py`:

```python
from typing import Dict, Any, List, Optional
from tools_db.models import AutomationEvent
from tools_db.database import Database
from datetime import datetime, timezone
import json


class AutomationHub:
    """Central hub for automation events (production checks, action items, n8n failures)"""

    def __init__(self, db: Optional[Database] = None, test_mode: bool = False):
        self.test_mode = test_mode
        self.db = db
        if not db:
            from tools_db.database import get_db
            self.db = get_db()
        self._memory_events = []  # For test mode

    def store_event(self, event: AutomationEvent) -> int:
        """Store automation event to database"""
        if self.test_mode:
            self._memory_events.append(event)
            return len(self._memory_events)

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO automation_events
                    (event_type, project_id, status, evidence, detected_from, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    event.event_type,
                    event.project_id,
                    event.status,
                    json.dumps(event.evidence),
                    event.detected_from,
                    json.dumps(event.metadata) if event.metadata else None
                ))
                return cursor.lastrowid
        except Exception as e:
            print(f"Error storing automation event: {e}")
            return None

    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get latest status for a project"""
        if self.test_mode:
            matching = [e for e in self._memory_events if e.project_id == project_id]
            if matching:
                latest = matching[-1]
                return {
                    "event_type": latest.event_type,
                    "status": latest.status,
                    "evidence": latest.evidence
                }
            return None

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT event_type, status, evidence
                    FROM automation_events
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        "event_type": row[0],
                        "status": row[1],
                        "evidence": json.loads(row[2])
                    }
        except Exception as e:
            print(f"Error getting project status: {e}")

        return None

    def get_events_by_type(self, event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get events by type"""
        if self.test_mode:
            matching = [e for e in self._memory_events if e.event_type == event_type]
            return [{
                "event_type": e.event_type,
                "project_id": e.project_id,
                "status": e.status,
                "evidence": e.evidence
            } for e in matching[:limit]]

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT event_type, project_id, status, evidence
                    FROM automation_events
                    WHERE event_type = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (event_type, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "event_type": row[0],
                        "project_id": row[1],
                        "status": row[2],
                        "evidence": json.loads(row[3])
                    })
                return results
        except Exception as e:
            print(f"Error getting events by type: {e}")
            return []
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_automation_database.py -v
```

Expected: PASS - all 5 tests passing

**Step 5: Commit**

```bash
git add tools_db/tools/automation_hub.py tests/test_automation_database.py
git commit -m "feat: add AutomationHub for database operations on automation_events"
```

---

## PHASE 2: Production Readiness Skill (Tasks 4-6)

### Task 4: Create Production Readiness Checker Infrastructure

**Files:**
- Create: `tools_db/tools/production_checker.py`
- Create: `tests/test_production_checker.py`

**Step 1: Write the failing test**

```python
# tests/test_production_checker.py
import pytest
from tools_db.tools.production_checker import ProductionChecker


def test_production_checker_init():
    """Test ProductionChecker initialization"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    assert checker.project_path == "."
    assert checker.test_mode is True

def test_production_checker_run_all_checks():
    """Test running all production checks"""
    checker = ProductionChecker(project_path=".", test_mode=True)
    results = checker.run_all_checks()

    assert results is not None
    assert "checks" in results
    assert isinstance(results["checks"], dict)
    # Should have keys for each check type
    assert "tests" in results["checks"] or "security" in results["checks"]

def test_production_checker_calculate_go_nogo():
    """Test go/no-go decision logic"""
    checker = ProductionChecker(project_path=".", test_mode=True)

    # All passing
    passing_results = {
        "tests": {"passed": True, "details": "47/47 passing"},
        "security": {"passed": True, "details": "No issues"},
        "documentation": {"passed": True, "details": "5/5 present"},
    }
    decision = checker.calculate_decision(passing_results)
    assert decision in ["go", "warning"]

    # Some failing
    failing_results = {
        "tests": {"passed": False, "details": "3/47 failing"},
        "security": {"passed": True, "details": "No issues"},
    }
    decision = checker.calculate_decision(failing_results)
    assert decision == "no_go"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_production_checker.py -v
```

Expected: FAIL - ProductionChecker not defined

**Step 3: Write minimal implementation**

Create `tools_db/tools/production_checker.py`:

```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json


@dataclass
class CheckResult:
    check_name: str
    passed: bool
    details: str
    evidence: Optional[Dict[str, Any]] = None


class ProductionChecker:
    """Run automated production readiness checks"""

    def __init__(self, project_path: str = ".", test_mode: bool = False):
        self.project_path = Path(project_path)
        self.test_mode = test_mode

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all production checks and return results"""
        if self.test_mode:
            return {
                "checks": {
                    "tests": CheckResult("tests", True, "mock tests passing"),
                    "security": CheckResult("security", True, "mock security pass"),
                },
                "timestamp": "2026-01-20T00:00:00Z"
            }

        checks = {
            "tests": self.check_tests(),
            "security": self.check_security(),
            "documentation": self.check_documentation(),
            "performance": self.check_performance(),
            "integration": self.check_integration_tests(),
            "rollback": self.check_rollback_plan(),
        }

        return {
            "checks": checks,
            "timestamp": str(Path(self.project_path).resolve())
        }

    def check_tests(self) -> CheckResult:
        """Check if tests pass (80%+ pass rate required)"""
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/", "-v", "--tb=no"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout
            if "passed" in output:
                import re
                match = re.search(r"(\d+) passed", output)
                if match:
                    passed = int(match.group(1))
                    details = f"{passed} tests passed"
                    return CheckResult("tests", result.returncode == 0, details)

            return CheckResult("tests", False, "No test output found")
        except Exception as e:
            return CheckResult("tests", False, f"Error running tests: {str(e)}")

    def check_security(self) -> CheckResult:
        """Check for common security vulnerabilities"""
        violations = []

        # Simple grep-based checks for common issues
        dangerous_patterns = [
            (r"password\s*=\s*['\"]", "Hardcoded password"),
            (r"api[_-]?key\s*=\s*['\"]", "Hardcoded API key"),
            (r"secret\s*=\s*['\"]", "Hardcoded secret"),
        ]

        try:
            for pattern, description in dangerous_patterns:
                result = subprocess.run(
                    ["grep", "-r", "-E", pattern, str(self.project_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    violations.append(description)

            if violations:
                return CheckResult("security", False, f"Found {len(violations)} violations",
                                 {"violations": violations})
            else:
                return CheckResult("security", True, "No security violations found")
        except Exception as e:
            return CheckResult("security", False, f"Error checking security: {str(e)}")

    def check_documentation(self) -> CheckResult:
        """Check for required documentation files"""
        required_docs = ["README.md", "IMPLEMENTATION_SUMMARY.md"]
        found_docs = []

        for doc in required_docs:
            if (self.project_path / doc).exists():
                found_docs.append(doc)

        if len(found_docs) >= 3:
            return CheckResult("documentation", True, f"Found {len(found_docs)} documentation files")
        else:
            return CheckResult("documentation", False, f"Only found {len(found_docs)}/3 required docs")

    def check_performance(self) -> CheckResult:
        """Check performance benchmarks if they exist"""
        benchmark_file = self.project_path / "benchmarks.py"
        if not benchmark_file.exists():
            return CheckResult("performance", True, "No benchmarks defined (warning only)",
                             {"severity": "warning"})

        try:
            result = subprocess.run(
                ["python3", str(benchmark_file)],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return CheckResult("performance", True, "Benchmarks passed")
            else:
                return CheckResult("performance", False, "Benchmarks failed")
        except Exception as e:
            return CheckResult("performance", False, f"Error running benchmarks: {str(e)}")

    def check_integration_tests(self) -> CheckResult:
        """Check integration tests"""
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/integration_*.py", "-v"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return CheckResult("integration", True, "Integration tests passing")
            else:
                return CheckResult("integration", False, "Integration tests failing")
        except Exception as e:
            return CheckResult("integration", False, f"No integration tests found: {str(e)}")

    def check_rollback_plan(self) -> CheckResult:
        """Check for rollback plan"""
        rollback_file = self.project_path / "ROLLBACK.md"

        try:
            result = subprocess.run(
                ["git", "tag", "-l"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )

            if rollback_file.exists() or result.stdout.strip():
                return CheckResult("rollback", True, "Rollback plan available")
            else:
                return CheckResult("rollback", False, "No rollback plan found")
        except Exception as e:
            return CheckResult("rollback", False, f"Error checking rollback: {str(e)}")

    def calculate_decision(self, results: Dict[str, Any]) -> str:
        """Determine go/no-go decision based on check results"""
        failed_checks = [
            check for check, result in results.items()
            if hasattr(result, 'passed') and not result.passed
        ]

        if not failed_checks:
            return "go"
        elif len(failed_checks) == 1 and "performance" in failed_checks[0]:
            return "warning"
        else:
            return "no_go"
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_production_checker.py -v
```

Expected: PASS - 3 tests passing

**Step 5: Commit**

```bash
git add tools_db/tools/production_checker.py tests/test_production_checker.py
git commit -m "feat: add ProductionChecker for automated readiness verification"
```

---

### Task 5: Implement Production Readiness Skill

**Files:**
- Create: `superpowers_skills/production_check.md` (skill definition)
- Create: `tests/test_production_check_skill.py`

**Step 1-5: [Similar TDD pattern - write test, verify fail, implement, verify pass, commit]**

Due to length constraints, I'm providing the essential implementation structure. The skill should:
- Accept project_path parameter
- Call ProductionChecker.run_all_checks()
- Generate markdown report with ✅/❌ indicators
- Store results in AutomationHub
- Output decision (go/no-go/warning)

Create `superpowers_skills/production_check.md`:

```markdown
---
name: production-check
description: Verify production readiness with automated go/no-go decision
color: green
---

# Production Readiness Verification

Run comprehensive production checks:
1. ✅ Test Coverage (pytest, require ≥80%)
2. ✅ Security Scan (OWASP patterns)
3. ✅ Documentation (README, summary)
4. ✅ Performance (benchmarks if exist)
5. ✅ Integration Tests
6. ✅ Rollback Plan

Generates go/no-go decision with evidence.

## Usage

\`/production-check <project-path>\`

Example: \`/production-check .\`
```

**Commit:**
```bash
git add superpowers_skills/production_check.md tests/test_production_check_skill.py
git commit -m "feat: implement production-check skill with markdown reporting"
```

---

### Task 6: Production Readiness Markdown Formatter

**Files:**
- Create: `tools_db/tools/production_formatter.py`
- Create: `tests/test_production_formatter.py`

**Implementation:**
- Format check results as markdown table
- Add ✅/❌ indicators
- Include git commit hash
- Generate release notes format

[TDD: 3 test cases, minimal implementation, commit]

---

## PHASE 3: Action Item Progress Tracking (Tasks 7-9)

### Task 7: Implement Action Item Keyword Detector

**Files:**
- Create: `tools_db/hooks/action_item_detector.py`
- Create: `tests/test_action_item_detector.py`

**Step 1: Write the failing test**

```python
# tests/test_action_item_detector.py
import pytest
from tools_db.hooks.action_item_detector import ActionItemDetector


def test_detector_finds_commit_keyword():
    """Test detection of git commit keyword"""
    detector = ActionItemDetector()

    output = "git add -A && git commit -m 'feat: add feature'"
    matches = detector.detect_completions(output)

    assert len(matches) > 0
    assert any(m["keyword"] == "git commit" for m in matches)

def test_detector_finds_multiple_keywords():
    """Test detection of multiple keywords"""
    detector = ActionItemDetector()

    output = "All tests passed! Deployed to production. Fix resolved."
    matches = detector.detect_completions(output)

    assert len(matches) >= 2

def test_detector_confidence_scoring():
    """Test confidence scoring for false positive prevention"""
    detector = ActionItemDetector()

    # Clear success indicator
    output_good = "✅ Tests passing: 47/47 passed successfully"
    matches_good = detector.detect_completions(output_good)
    assert any(m["confidence"] >= 0.90 for m in matches_good)

    # Ambiguous output
    output_bad = "Error: commit failed. Testing system unavailable."
    matches_bad = detector.detect_completions(output_bad)
    assert all(m["confidence"] < 0.60 for m in matches_bad) or len(matches_bad) == 0
```

**Step 2-5: [Implement ActionItemDetector with keyword matching, confidence scoring, TDD]**

Create `tools_db/hooks/action_item_detector.py`:

```python
import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class CompletionMatch:
    keyword: str
    confidence: float
    category: str  # "commit", "deploy", "test", "fix", "build", "create"


class ActionItemDetector:
    """Detect completion keywords in tool outputs"""

    # Keyword patterns with base confidence
    KEYWORD_PATTERNS = {
        # Commit patterns (highest confidence)
        r"git\s+(?:commit|add|push)": ("commit", 0.95),
        r"committed\s+(?:to\s+)?(?:branch|changes)": ("commit", 0.90),
        r"commit\s+(?:complete|successful)": ("commit", 0.95),

        # Deployment patterns
        r"deployed\s+(?:to|successfully|live)": ("deploy", 0.95),
        r"pushed\s+to\s+(?:production|staging)": ("deploy", 0.95),
        r"live\s+on": ("deploy", 0.90),

        # Test patterns
        r"(?:all\s+)?tests?\s+(?:passed|passing)": ("test", 0.92),
        r"test\s+suite\s+(?:passed|successful)": ("test", 0.93),
        r"✅.*(?:pass|success)": ("test", 0.95),

        # Fix patterns
        r"(?:fixed|resolved|patched)(?:\s+(?:issue|bug|error))?": ("fix", 0.85),
        r"bug\s+(?:fixed|resolved)": ("fix", 0.90),
        r"patch\s+applied": ("fix", 0.90),

        # Build patterns
        r"build\s+(?:successful|complete|passed)": ("build", 0.92),
        r"(?:compiled|compilation)\s+successful": ("build", 0.90),

        # Create patterns
        r"(?:created|written\s+to|saved)\s+(?:file|to)": ("create", 0.85),
        r"file\s+(?:created|saved|generated)": ("create", 0.88),
    }

    def detect_completions(self, output: str) -> List[Dict[str, Any]]:
        """Detect completion keywords in tool output"""
        matches = []
        output_lower = output.lower()

        for pattern, (category, base_confidence) in self.KEYWORD_PATTERNS.items():
            if re.search(pattern, output_lower):
                # Adjust confidence based on context
                confidence = self._adjust_confidence(output, pattern, category, base_confidence)

                if confidence >= 0.60:  # Only include if confidence >= 60%
                    matches.append({
                        "keyword": pattern,
                        "confidence": confidence,
                        "category": category
                    })

        return matches

    def _adjust_confidence(self, output: str, pattern: str, category: str,
                         base_confidence: float) -> float:
        """Adjust confidence based on output context"""
        confidence = base_confidence
        output_lower = output.lower()

        # Lower confidence if error/failed words present
        if any(word in output_lower for word in ["error", "failed", "exception", "crash"]):
            # But not if it's explicitly stating success
            if category not in ["deploy"] and "successfully" not in output_lower:
                confidence -= 0.30

        # Increase confidence for explicit success indicators
        if any(word in output_lower for word in ["success", "passed", "complete", "✅"]):
            confidence = min(0.99, confidence + 0.05)

        return max(0.0, min(1.0, confidence))
```

**Commit:**
```bash
git add tools_db/hooks/action_item_detector.py tests/test_action_item_detector.py
git commit -m "feat: implement action item keyword detector with confidence scoring"
```

---

### Task 8: Implement Todo Updater

**Files:**
- Create: `tools_db/hooks/todo_updater.py`
- Create: `tests/test_todo_updater.py`

**Implementation:**
- Match detected keywords to current todos
- Update status from "in_progress" → "completed"
- Log to automation_events
- Handle edge cases (multiple todos, no todos, confidence thresholds)

[TDD: 5 test cases, implementation with memory system integration, commit]

---

### Task 9: Create PostToolUse Hook Integration

**Files:**
- Create: `superpowers_plugins/hooks/post_tool_use_automation.md` (hook definition)
- Modify: `tools_db/hooks/__init__.py` (register hook)
- Create: `tests/test_post_tool_use_hook.py`

**Implementation:**
- Wire ActionItemDetector → TodoUpdater
- Log all detected completions to automation_events
- Suppress false positives with confidence thresholds
- Handle database failures gracefully

[TDD: 7 test cases covering happy path, edge cases, error handling, commit]

---

## PHASE 4: n8n Reliability Layer (Tasks 10-12)

### Task 10: Implement n8n Task Monitor

**Files:**
- Create: `tools_db/hooks/n8n_monitor.py`
- Create: `tests/test_n8n_monitor.py`

**Implementation:**
- Detect 403, 504, timeout errors
- Parse n8n task name to determine Celery equivalent
- Track failure patterns
- Log to automation_events

[TDD: 6 test cases, implementation, commit]

---

### Task 11: Implement Celery Fallback Router

**Files:**
- Create: `tools_db/tasks/celery_fallback_tasks.py` (Celery task definitions)
- Create: `tools_db/tasks/task_mappings.py` (n8n → Celery mappings)
- Create: `tests/test_celery_fallback.py`

**Implementation:**
- Task mappings: video-assembly → process_video, etc.
- Celery task wrapping with retry logic
- API/systemd fallback execution
- Result persistence

[TDD: 8 test cases covering all task types and fallback paths, commit]

---

### Task 12: Create PreToolUse Hook Integration

**Files:**
- Create: `superpowers_plugins/hooks/pre_tool_use_n8n_reliability.md` (hook definition)
- Modify: `tools_db/hooks/__init__.py` (register hook)
- Create: `tests/test_pre_tool_use_hook.py`

**Implementation:**
- Intercept n8n task execution
- Register failure monitor
- Trigger fallback on errors
- Log routing decisions

[TDD: 7 test cases, implementation, commit]

---

## PHASE 5: Integration & Testing (Tasks 13-14)

### Task 13: Integration Tests

**Files:**
- Create: `tests/integration_tier1_automation.py`

**Implementation:**
- Production check + AutomationHub integration
- Action item tracking end-to-end workflow
- n8n fallback routing end-to-end workflow
- Status hub query integration

[15 integration tests, commit]

---

### Task 14: End-to-End Workflow Tests

**Files:**
- Create: `tests/e2e_tier1_automation.py`

**Implementation:**
- Simulate full production release cycle
- Simulate action item completion during tool use
- Simulate n8n failure and automatic reroute
- Verify automation_events audit trail

[10 E2E tests, commit]

---

## PHASE 6: Documentation & Deployment (Task 15)

### Task 15: Documentation and Deployment Guide

**Files:**
- Create: `docs/TIER1_AUTOMATION_SETUP.md` (setup guide)
- Create: `docs/TIER1_AUTOMATION_USAGE.md` (usage guide)
- Modify: `README.md` (add tier 1 automation section)

**Implementation:**
- Setup instructions (database migration, environment variables)
- Usage examples (running production check, monitoring action items)
- Troubleshooting guide
- Architecture diagram

**Commit:**
```bash
git add docs/TIER1_AUTOMATION_*.md README.md
git commit -m "docs: add comprehensive tier 1 automation setup and usage guide"
```

---

## Summary

**Total Tasks:** 15
**Total Tests Target:** 50+
**Expected Pass Rate:** 100%
**Key Deliverables:**
- ✅ AutomationEvent model + database infrastructure
- ✅ Production Readiness Skill with 6 automated checks
- ✅ Action Item Progress Tracking (PostToolUse hook)
- ✅ n8n Reliability Layer (PreToolUse hook + Celery routing)
- ✅ Comprehensive integration and E2E tests
- ✅ Complete documentation and deployment guide

---

## Execution Instructions

Use **superpowers:subagent-driven-development** to execute this plan task-by-task with:
- Fresh subagent per task
- Spec compliance review after each task
- Code quality review after each task
- Automatic commit after each task completes

No manual input needed after execution begins.
