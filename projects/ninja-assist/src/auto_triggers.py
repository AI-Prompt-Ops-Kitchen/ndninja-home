"""
Ninja Assist - Auto-Triggers
============================
Proactive assistance without being asked.
Integrates with Clawdbot heartbeat system to surface relevant actions.

Trigger Types:
- pending_tasks: Surface when tasks are waiting
- stale_project: Nudge when project hasn't been touched
- phase_complete: Celebrate and suggest next phase
- time_based: Scheduled reminders
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable
from enum import Enum

from .state_manager import StateManager, get_manager


class TriggerType(Enum):
    PENDING_TASKS = "pending_tasks"
    STALE_PROJECT = "stale_project"
    PHASE_COMPLETE = "phase_complete"
    TIME_BASED = "time_based"
    CUSTOM = "custom"


class TriggerPriority(Enum):
    LOW = 1       # Can wait, mention if nothing else
    MEDIUM = 2    # Worth mentioning
    HIGH = 3      # Should definitely surface
    URGENT = 4    # Interrupt whatever else


@dataclass
class Trigger:
    """A triggered action to surface to the user."""
    type: str
    priority: int
    message: str
    project: Optional[str] = None
    action_hint: Optional[str] = None  # Suggested command/action
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class TriggerConfig:
    """Configuration for trigger thresholds."""
    # Pending tasks
    pending_task_threshold: int = 3  # Surface if >= N pending tasks
    
    # Stale project detection
    stale_hours: int = 48  # Consider stale after N hours of inactivity
    
    # Anti-spam
    min_hours_between_nudges: int = 4  # Don't nudge same thing within N hours
    max_triggers_per_heartbeat: int = 2  # Max triggers to surface at once
    
    # Quiet hours (don't trigger during these)
    quiet_start_hour: int = 23  # 11 PM
    quiet_end_hour: int = 8     # 8 AM
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TriggerConfig":
        return cls(**data)


class TriggerHistory:
    """Tracks when triggers were last fired to prevent spam."""
    
    HISTORY_FILE = Path.home() / ".ninja-assist" / "trigger_history.json"
    
    def __init__(self):
        self.history: dict[str, str] = {}  # trigger_key -> ISO timestamp
        self._load()
    
    def _load(self) -> None:
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, "r") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = {}
    
    def _save(self) -> None:
        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.HISTORY_FILE, "w") as f:
            json.dump(self.history, f, indent=2)
    
    def get_key(self, trigger_type: str, project: Optional[str] = None) -> str:
        """Generate a unique key for a trigger."""
        if project:
            return f"{trigger_type}:{project}"
        return trigger_type
    
    def was_fired_recently(self, trigger_type: str, project: Optional[str], hours: int) -> bool:
        """Check if this trigger was fired within the last N hours."""
        key = self.get_key(trigger_type, project)
        if key not in self.history:
            return False
        
        last_fired = datetime.fromisoformat(self.history[key])
        cutoff = datetime.now() - timedelta(hours=hours)
        return last_fired > cutoff
    
    def mark_fired(self, trigger_type: str, project: Optional[str] = None) -> None:
        """Mark a trigger as fired now."""
        key = self.get_key(trigger_type, project)
        self.history[key] = datetime.now().isoformat()
        self._save()
    
    def clear_history(self) -> None:
        """Clear all history (for testing)."""
        self.history = {}
        self._save()


class AutoTriggerEngine:
    """
    Engine that evaluates triggers and decides what to surface.
    
    Usage:
        engine = AutoTriggerEngine()
        triggers = engine.check_all()
        
        for trigger in triggers:
            print(f"[{trigger.priority}] {trigger.message}")
    """
    
    def __init__(self, config: Optional[TriggerConfig] = None):
        self.config = config or TriggerConfig()
        self.state_manager = get_manager()
        self.history = TriggerHistory()
        self._custom_checks: list[Callable[[], Optional[Trigger]]] = []
    
    def register_check(self, check_fn: Callable[[], Optional[Trigger]]) -> None:
        """Register a custom trigger check function."""
        self._custom_checks.append(check_fn)
    
    def is_quiet_hours(self) -> bool:
        """Check if we're in quiet hours."""
        hour = datetime.now().hour
        if self.config.quiet_start_hour > self.config.quiet_end_hour:
            # Spans midnight (e.g., 23:00 - 08:00)
            return hour >= self.config.quiet_start_hour or hour < self.config.quiet_end_hour
        else:
            return self.config.quiet_start_hour <= hour < self.config.quiet_end_hour
    
    def check_all(self, respect_quiet_hours: bool = True) -> list[Trigger]:
        """
        Run all trigger checks and return sorted list of triggers.
        
        Returns triggers sorted by priority (highest first), limited by config.
        """
        if respect_quiet_hours and self.is_quiet_hours():
            return []
        
        triggers: list[Trigger] = []
        
        # Built-in checks
        if t := self._check_pending_tasks():
            triggers.append(t)
        
        if t := self._check_stale_project():
            triggers.append(t)
        
        if t := self._check_phase_complete():
            triggers.append(t)
        
        # Custom checks
        for check_fn in self._custom_checks:
            try:
                if t := check_fn():
                    triggers.append(t)
            except Exception:
                pass  # Don't let custom checks break the engine
        
        # Sort by priority (highest first) and limit
        triggers.sort(key=lambda t: t.priority, reverse=True)
        return triggers[:self.config.max_triggers_per_heartbeat]
    
    def _check_pending_tasks(self) -> Optional[Trigger]:
        """Check if there are pending tasks that need attention."""
        ctx = self.state_manager.get_context_summary()
        
        if not ctx["has_project"]:
            return None
        
        pending_count = ctx["pending_count"]
        if pending_count < self.config.pending_task_threshold:
            return None
        
        # Check spam prevention
        project = ctx["project_name"]
        if self.history.was_fired_recently(
            TriggerType.PENDING_TASKS.value, 
            project,
            self.config.min_hours_between_nudges
        ):
            return None
        
        # Get the actual tasks
        tasks = self.state_manager.get_pending_tasks(3)
        task_list = "\n".join(f"  • {t}" for t in tasks)
        
        self.history.mark_fired(TriggerType.PENDING_TASKS.value, project)
        
        return Trigger(
            type=TriggerType.PENDING_TASKS.value,
            priority=TriggerPriority.MEDIUM.value,
            message=f"📋 **{project}** has {pending_count} pending tasks:\n{task_list}",
            project=project,
            action_hint=f"cd {self.state_manager.project_state.project_path}" if self.state_manager.project_state else None,
        )
    
    def _check_stale_project(self) -> Optional[Trigger]:
        """Check if the active project hasn't been touched in a while."""
        if not self.state_manager.project_state:
            return None
        
        last_action_at = self.state_manager.project_state.last_action_at
        if not last_action_at:
            return None
        
        last_action = datetime.fromisoformat(last_action_at)
        stale_threshold = datetime.now() - timedelta(hours=self.config.stale_hours)
        
        if last_action > stale_threshold:
            return None  # Not stale yet
        
        project = self.state_manager.project_state.project_name
        
        # Check spam prevention
        if self.history.was_fired_recently(
            TriggerType.STALE_PROJECT.value,
            project,
            self.config.min_hours_between_nudges * 2  # Less frequent for stale nudges
        ):
            return None
        
        hours_ago = int((datetime.now() - last_action).total_seconds() / 3600)
        
        self.history.mark_fired(TriggerType.STALE_PROJECT.value, project)
        
        return Trigger(
            type=TriggerType.STALE_PROJECT.value,
            priority=TriggerPriority.LOW.value,
            message=f"🕐 Haven't touched **{project}** in {hours_ago}h. Last action: {self.state_manager.project_state.last_action}",
            project=project,
        )
    
    def _check_phase_complete(self) -> Optional[Trigger]:
        """Check if all tasks in current phase are done (for celebration/next phase)."""
        if not self.state_manager.project_state:
            return None
        
        # If there's a current phase but no pending tasks, phase might be complete
        state = self.state_manager.project_state
        if not state.current_phase:
            return None
        
        if state.pending_tasks:
            return None  # Still has work
        
        project = state.project_name
        
        # Check spam prevention
        if self.history.was_fired_recently(
            TriggerType.PHASE_COMPLETE.value,
            project,
            24  # Only once per day for phase complete
        ):
            return None
        
        self.history.mark_fired(TriggerType.PHASE_COMPLETE.value, project)
        
        return Trigger(
            type=TriggerType.PHASE_COMPLETE.value,
            priority=TriggerPriority.HIGH.value,
            message=f"🎉 **{project}** - {state.current_phase} looks complete! Ready for next phase?",
            project=project,
            action_hint="Check ROADMAP.md for next phase",
        )


# =============================================================================
# HEARTBEAT INTEGRATION
# =============================================================================

def check_heartbeat() -> Optional[str]:
    """
    Main entry point for Clawdbot heartbeat integration.
    
    Returns:
        - None if nothing to report (caller should return HEARTBEAT_OK)
        - String message if something needs attention
    """
    engine = AutoTriggerEngine()
    triggers = engine.check_all()
    
    if not triggers:
        return None
    
    # Format triggers into a message
    lines = ["🤖 **Ninja Assist** noticed:"]
    for trigger in triggers:
        lines.append("")
        lines.append(trigger.message)
        if trigger.action_hint:
            lines.append(f"  💡 {trigger.action_hint}")
    
    return "\n".join(lines)


def format_for_heartbeat_md() -> str:
    """
    Generate content for HEARTBEAT.md integration.
    
    Returns a comment block that can be added to HEARTBEAT.md.
    """
    return """# Ninja Assist Auto-Triggers
# Add this line to enable project awareness during heartbeats:
# python3 -c "from ninja_assist.auto_triggers import check_heartbeat; r = check_heartbeat(); print(r) if r else None"
"""


# =============================================================================
# CLI / TESTS
# =============================================================================

def run_tests():
    """Test the auto-trigger system."""
    import tempfile
    
    print("=" * 70)
    print("NINJA ASSIST - AUTO-TRIGGERS TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Test 1: Create engine
    print("\n✅ Test 1: Create AutoTriggerEngine")
    try:
        engine = AutoTriggerEngine()
        assert engine.config is not None
        assert engine.history is not None
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 2: Quiet hours check
    print("\n✅ Test 2: Quiet hours detection")
    try:
        config = TriggerConfig(quiet_start_hour=0, quiet_end_hour=24)  # Always quiet
        engine = AutoTriggerEngine(config=config)
        assert engine.is_quiet_hours() == True
        
        config2 = TriggerConfig(quiet_start_hour=25, quiet_end_hour=26)  # Never quiet
        engine2 = AutoTriggerEngine(config=config2)
        assert engine2.is_quiet_hours() == False
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 3: Trigger history
    print("\n✅ Test 3: Trigger history (spam prevention)")
    try:
        history = TriggerHistory()
        history.clear_history()
        
        # Should not be fired recently
        assert history.was_fired_recently("test", "proj", 1) == False
        
        # Mark as fired
        history.mark_fired("test", "proj")
        
        # Should now be recent
        assert history.was_fired_recently("test", "proj", 1) == True
        
        # Different project should not be affected
        assert history.was_fired_recently("test", "other", 1) == False
        
        history.clear_history()
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 4: Check all returns list
    print("\n✅ Test 4: check_all() returns list")
    try:
        engine = AutoTriggerEngine()
        triggers = engine.check_all(respect_quiet_hours=False)
        assert isinstance(triggers, list)
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 5: Custom check registration
    print("\n✅ Test 5: Custom check registration")
    try:
        engine = AutoTriggerEngine()
        
        def custom_check() -> Optional[Trigger]:
            return Trigger(
                type="custom",
                priority=TriggerPriority.HIGH.value,
                message="Custom trigger fired!",
            )
        
        engine.register_check(custom_check)
        triggers = engine.check_all(respect_quiet_hours=False)
        
        assert any(t.type == "custom" for t in triggers)
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 6: Priority sorting
    print("\n✅ Test 6: Triggers sorted by priority")
    try:
        engine = AutoTriggerEngine()
        
        engine.register_check(lambda: Trigger(type="low", priority=1, message="Low"))
        engine.register_check(lambda: Trigger(type="high", priority=4, message="High"))
        engine.register_check(lambda: Trigger(type="med", priority=2, message="Med"))
        
        triggers = engine.check_all(respect_quiet_hours=False)
        
        # Should be sorted high to low
        priorities = [t.priority for t in triggers]
        assert priorities == sorted(priorities, reverse=True)
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 7: Max triggers limit
    print("\n✅ Test 7: Max triggers per heartbeat limit")
    try:
        config = TriggerConfig(max_triggers_per_heartbeat=2)
        engine = AutoTriggerEngine(config=config)
        
        for i in range(5):
            engine.register_check(lambda i=i: Trigger(type=f"test{i}", priority=i, message=f"Test {i}"))
        
        triggers = engine.check_all(respect_quiet_hours=False)
        assert len(triggers) <= 2
        passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        failed += 1
    
    # Test 8: Heartbeat integration
    print("\n✅ Test 8: check_heartbeat() function")
    try:
        result = check_heartbeat()
        # Result can be None or a string, both are valid
        assert result is None or isinstance(result, str)
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
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Run heartbeat check
        result = check_heartbeat()
        if result:
            print(result)
        else:
            print("Nothing to report.")
    else:
        # Show current triggers
        print("\n🔔 Checking triggers...\n")
        engine = AutoTriggerEngine()
        triggers = engine.check_all(respect_quiet_hours=False)
        
        if not triggers:
            print("No triggers active.")
        else:
            for t in triggers:
                priority_emoji = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}.get(t.priority, "⚪")
                print(f"{priority_emoji} [{t.type}] {t.message}")
                if t.action_hint:
                    print(f"   💡 {t.action_hint}")
                print()
