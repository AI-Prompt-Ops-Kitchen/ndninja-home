"""
Ninja Assist - State Manager
============================
Persistent project awareness that survives sessions.
Tracks current context, phase, pending tasks, and integrates with GSD.

Schema: .state.json (per-project) + ~/.ninja-assist/global.json (global context)
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


# =============================================================================
# SCHEMAS
# =============================================================================

@dataclass
class ProjectState:
    """State for a single project."""
    project_path: str
    project_name: str
    current_phase: Optional[str] = None
    current_task: Optional[str] = None
    pending_tasks: list[str] = field(default_factory=list)
    last_action: Optional[str] = None
    last_action_at: Optional[str] = None  # ISO format
    gsd_detected: bool = False
    beads_detected: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState":
        return cls(**data)


@dataclass
class GlobalState:
    """Global state tracking across all projects."""
    active_project: Optional[str] = None  # Path to active project
    recent_projects: list[str] = field(default_factory=list)  # Last 10 projects
    last_intent: Optional[str] = None
    last_intent_at: Optional[str] = None
    session_count: int = 0
    total_actions: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "GlobalState":
        return cls(**data)


# =============================================================================
# STATE MANAGER
# =============================================================================

class StateManager:
    """
    Manages project and global state for Ninja Assist.
    
    Usage:
        sm = StateManager()
        
        # Auto-detect project from current directory
        project = sm.detect_project()
        
        # Or explicitly load a project
        project = sm.load_project("/path/to/project")
        
        # Update state
        sm.set_current_task("Implementing feature X")
        sm.record_action("Created file foo.py")
        sm.add_pending_task("Write tests")
        
        # Save (auto-saves on changes)
        sm.save()
    """
    
    GLOBAL_STATE_DIR = Path.home() / ".ninja-assist"
    GLOBAL_STATE_FILE = GLOBAL_STATE_DIR / "global.json"
    PROJECT_STATE_FILE = ".state.json"
    
    def __init__(self, auto_detect: bool = True):
        self.global_state = self._load_global_state()
        self.project_state: Optional[ProjectState] = None
        
        if auto_detect:
            self.detect_project()
    
    # -------------------------------------------------------------------------
    # Global State
    # -------------------------------------------------------------------------
    
    def _load_global_state(self) -> GlobalState:
        """Load global state from ~/.ninja-assist/global.json"""
        if self.GLOBAL_STATE_FILE.exists():
            try:
                with open(self.GLOBAL_STATE_FILE, "r") as f:
                    data = json.load(f)
                return GlobalState.from_dict(data)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        return GlobalState()
    
    def _save_global_state(self) -> None:
        """Save global state to ~/.ninja-assist/global.json"""
        self.GLOBAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.GLOBAL_STATE_FILE, "w") as f:
            json.dump(self.global_state.to_dict(), f, indent=2)
    
    # -------------------------------------------------------------------------
    # Project Detection
    # -------------------------------------------------------------------------
    
    def detect_project(self, start_path: Optional[str] = None) -> Optional[ProjectState]:
        """
        Auto-detect project from current directory or given path.
        
        Detection order:
        1. Look for .state.json (Ninja Assist state)
        2. Look for .planning/ (GSD project)
        3. Look for .beads/ (Beads task tracking)
        4. Look for .git/ (Git repository root)
        5. Look for package.json, Cargo.toml, pyproject.toml, etc.
        
        Walks up directory tree until found or hits root.
        """
        start = Path(start_path) if start_path else Path.cwd()
        
        # Walk up the tree
        current = start.resolve()
        while current != current.parent:
            # Check for project markers
            project_root = self._check_project_markers(current)
            if project_root:
                return self.load_project(str(project_root))
            current = current.parent
        
        # No project found - use cwd as fallback
        return None
    
    def _check_project_markers(self, path: Path) -> Optional[Path]:
        """Check if path contains project markers."""
        markers = [
            ".state.json",      # Ninja Assist
            ".planning",        # GSD
            ".beads",           # Beads
            ".git",             # Git
            "package.json",     # Node.js
            "Cargo.toml",       # Rust
            "pyproject.toml",   # Python
            "go.mod",           # Go
            "Makefile",         # Make
        ]
        
        for marker in markers:
            if (path / marker).exists():
                return path
        
        return None
    
    # -------------------------------------------------------------------------
    # Project State
    # -------------------------------------------------------------------------
    
    def load_project(self, project_path: str) -> ProjectState:
        """Load or create state for a project."""
        path = Path(project_path).resolve()
        state_file = path / self.PROJECT_STATE_FILE
        
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)
                self.project_state = ProjectState.from_dict(data)
            except (json.JSONDecodeError, TypeError, KeyError):
                self.project_state = self._create_project_state(path)
        else:
            self.project_state = self._create_project_state(path)
        
        # Update global tracking
        self._track_project(str(path))
        
        # Integrate with GSD/Beads if present
        self._integrate_with_tools(path)
        
        return self.project_state
    
    def _create_project_state(self, path: Path) -> ProjectState:
        """Create new state for a project."""
        return ProjectState(
            project_path=str(path),
            project_name=path.name,
        )
    
    def _track_project(self, project_path: str) -> None:
        """Track project in global state."""
        self.global_state.active_project = project_path
        
        # Update recent projects (keep last 10)
        if project_path in self.global_state.recent_projects:
            self.global_state.recent_projects.remove(project_path)
        self.global_state.recent_projects.insert(0, project_path)
        self.global_state.recent_projects = self.global_state.recent_projects[:10]
        
        self._save_global_state()
    
    def _integrate_with_tools(self, path: Path) -> None:
        """Integrate with GSD and Beads if present."""
        if not self.project_state:
            return
        
        # GSD integration
        planning_dir = path / ".planning"
        if planning_dir.exists():
            self.project_state.gsd_detected = True
            self._sync_from_gsd(planning_dir)
        
        # Beads integration
        beads_dir = path / ".beads"
        if beads_dir.exists():
            self.project_state.beads_detected = True
            self._sync_from_beads(beads_dir)
    
    def _sync_from_gsd(self, planning_dir: Path) -> None:
        """Sync state from GSD .planning/ folder."""
        if not self.project_state:
            return
        
        # Read STATE.md for current phase
        state_file = planning_dir / "STATE.md"
        if state_file.exists():
            content = state_file.read_text()
            
            # Extract current phase
            import re
            phase_match = re.search(r"Current Phase[:\s]+(\d+)", content, re.IGNORECASE)
            if phase_match:
                self.project_state.current_phase = f"Phase {phase_match.group(1)}"
            
            # Extract current status
            status_match = re.search(r"Status[:\s]+(.+)", content, re.IGNORECASE)
            if status_match:
                self.project_state.metadata["gsd_status"] = status_match.group(1).strip()
        
        # Read ROADMAP.md for pending phases
        roadmap_file = planning_dir / "ROADMAP.md"
        if roadmap_file.exists():
            content = roadmap_file.read_text()
            
            # Find incomplete phases (lines with [ ] checkbox)
            import re
            incomplete = re.findall(r"^\s*-\s*\[\s*\]\s*(.+)$", content, re.MULTILINE)
            if incomplete and not self.project_state.pending_tasks:
                self.project_state.pending_tasks = incomplete[:5]  # Top 5
    
    def _sync_from_beads(self, beads_dir: Path) -> None:
        """Sync state from Beads .beads/ folder."""
        if not self.project_state:
            return
        
        # Read tasks.jsonl for open tasks
        tasks_file = beads_dir / "tasks.jsonl"
        if tasks_file.exists():
            open_tasks = []
            try:
                with open(tasks_file, "r") as f:
                    for line in f:
                        if line.strip():
                            task = json.loads(line)
                            if task.get("status") == "open":
                                open_tasks.append(task.get("title", "Untitled"))
            except (json.JSONDecodeError, KeyError):
                pass
            
            if open_tasks and not self.project_state.pending_tasks:
                self.project_state.pending_tasks = open_tasks[:5]
    
    # -------------------------------------------------------------------------
    # State Updates
    # -------------------------------------------------------------------------
    
    def set_current_task(self, task: str) -> None:
        """Set the current task being worked on."""
        if self.project_state:
            self.project_state.current_task = task
            self.save()
    
    def set_current_phase(self, phase: str) -> None:
        """Set the current phase."""
        if self.project_state:
            self.project_state.current_phase = phase
            self.save()
    
    def add_pending_task(self, task: str) -> None:
        """Add a pending task."""
        if self.project_state:
            if task not in self.project_state.pending_tasks:
                self.project_state.pending_tasks.append(task)
            self.save()
    
    def complete_task(self, task: str) -> None:
        """Mark a task as complete (remove from pending)."""
        if self.project_state:
            if task in self.project_state.pending_tasks:
                self.project_state.pending_tasks.remove(task)
            if self.project_state.current_task == task:
                self.project_state.current_task = None
            self.save()
    
    def record_action(self, action: str) -> None:
        """Record the last action taken."""
        if self.project_state:
            self.project_state.last_action = action
            self.project_state.last_action_at = datetime.now().isoformat()
            self.global_state.total_actions += 1
            self.save()
    
    def record_intent(self, intent: str) -> None:
        """Record the last intent classified."""
        self.global_state.last_intent = intent
        self.global_state.last_intent_at = datetime.now().isoformat()
        self._save_global_state()
    
    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------
    
    def save(self) -> None:
        """Save both project and global state."""
        if self.project_state:
            state_file = Path(self.project_state.project_path) / self.PROJECT_STATE_FILE
            with open(state_file, "w") as f:
                json.dump(self.project_state.to_dict(), f, indent=2)
        
        self._save_global_state()
    
    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------
    
    def get_context_summary(self) -> dict:
        """Get a summary of current context for prompts."""
        summary = {
            "has_project": self.project_state is not None,
            "project_name": None,
            "current_phase": None,
            "current_task": None,
            "pending_count": 0,
            "last_action": None,
            "tools_detected": [],
        }
        
        if self.project_state:
            summary["project_name"] = self.project_state.project_name
            summary["current_phase"] = self.project_state.current_phase
            summary["current_task"] = self.project_state.current_task
            summary["pending_count"] = len(self.project_state.pending_tasks)
            summary["last_action"] = self.project_state.last_action
            
            if self.project_state.gsd_detected:
                summary["tools_detected"].append("gsd")
            if self.project_state.beads_detected:
                summary["tools_detected"].append("beads")
        
        return summary
    
    def get_pending_tasks(self, limit: int = 5) -> list[str]:
        """Get pending tasks for current project."""
        if self.project_state:
            return self.project_state.pending_tasks[:limit]
        return []
    
    def get_recent_projects(self, limit: int = 5) -> list[str]:
        """Get recently worked on projects."""
        return self.global_state.recent_projects[:limit]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_manager: Optional[StateManager] = None


def get_manager() -> StateManager:
    """Get or create the global state manager instance."""
    global _manager
    if _manager is None:
        _manager = StateManager()
    return _manager


def get_context() -> dict:
    """Quick access to current context summary."""
    return get_manager().get_context_summary()


def set_task(task: str) -> None:
    """Quick access to set current task."""
    get_manager().set_current_task(task)


def record_action(action: str) -> None:
    """Quick access to record an action."""
    get_manager().record_action(action)


# =============================================================================
# CLI / TESTS
# =============================================================================

def run_tests():
    """Test the state manager."""
    import tempfile
    import shutil
    
    print("=" * 70)
    print("NINJA ASSIST - STATE MANAGER TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Test 1: Create state manager
    print("\n✅ Test 1: Create StateManager")
    try:
        sm = StateManager(auto_detect=False)
        assert sm.global_state is not None
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 2: Create project in temp directory
    print("\n✅ Test 2: Create project state")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = sm.load_project(tmpdir)
            assert project.project_path == str(Path(tmpdir).resolve())
            assert project.project_name == Path(tmpdir).name
            passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 3: Set and save task
    print("\n✅ Test 3: Set current task")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            sm.load_project(tmpdir)
            sm.set_current_task("Building feature X")
            
            # Reload and verify
            sm2 = StateManager(auto_detect=False)
            project = sm2.load_project(tmpdir)
            assert project.current_task == "Building feature X"
            passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 4: Record action
    print("\n✅ Test 4: Record action")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            sm.load_project(tmpdir)
            sm.record_action("Created file foo.py")
            assert sm.project_state.last_action == "Created file foo.py"
            assert sm.project_state.last_action_at is not None
            passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 5: Pending tasks
    print("\n✅ Test 5: Pending tasks")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            sm.load_project(tmpdir)
            sm.add_pending_task("Write tests")
            sm.add_pending_task("Update docs")
            assert len(sm.get_pending_tasks()) == 2
            
            sm.complete_task("Write tests")
            assert len(sm.get_pending_tasks()) == 1
            passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 6: GSD integration
    print("\n✅ Test 6: GSD integration")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake GSD structure
            planning_dir = Path(tmpdir) / ".planning"
            planning_dir.mkdir()
            (planning_dir / "STATE.md").write_text("Current Phase: 2\nStatus: In Progress")
            (planning_dir / "ROADMAP.md").write_text("- [ ] Task A\n- [ ] Task B\n- [x] Done task")
            
            sm.load_project(tmpdir)
            assert sm.project_state.gsd_detected
            assert sm.project_state.current_phase == "Phase 2"
            assert "Task A" in sm.project_state.pending_tasks
            passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 7: Context summary
    print("\n✅ Test 7: Context summary")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            sm.load_project(tmpdir)
            sm.set_current_task("Testing")
            sm.set_current_phase("Phase 1")
            
            ctx = sm.get_context_summary()
            assert ctx["has_project"] == True
            assert ctx["current_task"] == "Testing"
            assert ctx["current_phase"] == "Phase 1"
            passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 8: Project detection
    print("\n✅ Test 8: Project detection")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a .git marker
            (Path(tmpdir) / ".git").mkdir()
            
            # Create a subdirectory
            subdir = Path(tmpdir) / "src" / "deep"
            subdir.mkdir(parents=True)
            
            # Detect from subdir should find project root
            sm2 = StateManager(auto_detect=False)
            project = sm2.detect_project(str(subdir))
            assert project is not None
            assert project.project_path == str(Path(tmpdir).resolve())
            passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{passed + failed} passed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = run_tests()
        sys.exit(0 if success else 1)
    else:
        # Show current context
        sm = StateManager()
        ctx = sm.get_context_summary()
        
        print("\n📍 Current Context:")
        print(f"   Project: {ctx['project_name'] or '(none detected)'}")
        print(f"   Phase: {ctx['current_phase'] or '(none)'}")
        print(f"   Task: {ctx['current_task'] or '(none)'}")
        print(f"   Pending: {ctx['pending_count']} tasks")
        print(f"   Tools: {', '.join(ctx['tools_detected']) or '(none)'}")
        
        if sm.project_state and sm.project_state.pending_tasks:
            print("\n📋 Pending Tasks:")
            for task in sm.project_state.pending_tasks[:5]:
                print(f"   • {task}")
