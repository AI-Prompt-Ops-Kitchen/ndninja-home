"""Ninja Assist - Neurodivergent-friendly AI interface layer."""

from .intent_router import classify_intent, route_request, Intent, IntentCategory
from .state_manager import (
    StateManager,
    ProjectState,
    GlobalState,
    get_manager,
    get_context,
    set_task,
    record_action,
)
from .auto_triggers import (
    AutoTriggerEngine,
    Trigger,
    TriggerConfig,
    TriggerType,
    TriggerPriority,
    check_heartbeat,
)

__all__ = [
    # Intent Router
    "classify_intent",
    "route_request",
    "Intent",
    "IntentCategory",
    # State Manager
    "StateManager",
    "ProjectState",
    "GlobalState",
    "get_manager",
    "get_context",
    "set_task",
    "record_action",
    # Auto-Triggers
    "AutoTriggerEngine",
    "Trigger",
    "TriggerConfig",
    "TriggerType",
    "TriggerPriority",
    "check_heartbeat",
]
