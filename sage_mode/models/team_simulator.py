from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

class AgentRole(Enum):
    """7 specialized agent roles in Development Team Simulator"""
    FRONTEND_DEV = "frontend_developer"
    BACKEND_DEV = "backend_developer"
    ARCHITECT = "software_architect"
    UI_UX_DESIGNER = "ui_ux_designer"
    DBA = "database_administrator"
    IT_ADMIN = "it_administrator"
    SECURITY_SPECIALIST = "security_specialist"

@dataclass
class DecisionJournal:
    """Captures decisions during hyperfocus without interruption"""
    user_id: str
    title: str
    description: str
    category: str  # "architecture", "technical", "process", "tool"
    decision_type: str  # "technical", "strategic", "operational"
    timestamp: datetime = field(default_factory=datetime.now)
    context_snippet: Optional[str] = None
    related_task: Optional[str] = None
    confidence_level: int = 80  # 0-100

    def __post_init__(self):
        assert 0 <= self.confidence_level <= 100, "confidence_level must be 0-100"

@dataclass
class TeamEvent:
    """Tracks team coordination events in automation_events"""
    event_type: str  # "decision_made", "task_started", "task_completed", "error"
    agent_role: AgentRole
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
