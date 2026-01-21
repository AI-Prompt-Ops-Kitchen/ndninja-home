from enum import Enum
from typing import Dict, List, Any, Optional
from sage_mode.models.team_simulator import AgentRole, DecisionJournal
from abc import ABC, abstractmethod

class AgentCapability(Enum):
    """Capabilities each agent type has"""
    DESIGN = "design"
    IMPLEMENT = "implement"
    TEST = "test"
    REVIEW = "review"
    DEPLOY = "deploy"
    DOCUMENT = "document"
    AUDIT = "audit"
    OPTIMIZE = "optimize"

class BaseAgent(ABC):
    """Base class for all 7 specialized agents"""

    def __init__(self, role: AgentRole, name: str, description: str):
        self.role = role
        self.name = name
        self.description = description
        self.context: Dict[str, Any] = {}
        self.decisions: List[DecisionJournal] = []
        self.capabilities: List[AgentCapability] = self._get_default_capabilities()

    def _get_default_capabilities(self) -> List[AgentCapability]:
        """Return default capabilities based on role"""
        role_capabilities = {
            AgentRole.ARCHITECT: [
                AgentCapability.DESIGN,
                AgentCapability.REVIEW,
                AgentCapability.DOCUMENT
            ],
            AgentRole.FRONTEND_DEV: [
                AgentCapability.DESIGN,
                AgentCapability.IMPLEMENT,
                AgentCapability.TEST,
                AgentCapability.REVIEW
            ],
            AgentRole.BACKEND_DEV: [
                AgentCapability.IMPLEMENT,
                AgentCapability.TEST,
                AgentCapability.REVIEW,
                AgentCapability.OPTIMIZE
            ],
            AgentRole.UI_UX_DESIGNER: [
                AgentCapability.DESIGN,
                AgentCapability.REVIEW,
                AgentCapability.DOCUMENT
            ],
            AgentRole.DBA: [
                AgentCapability.DESIGN,
                AgentCapability.IMPLEMENT,
                AgentCapability.OPTIMIZE,
                AgentCapability.AUDIT
            ],
            AgentRole.IT_ADMIN: [
                AgentCapability.DEPLOY,
                AgentCapability.AUDIT,
                AgentCapability.OPTIMIZE
            ],
            AgentRole.SECURITY_SPECIALIST: [
                AgentCapability.AUDIT,
                AgentCapability.REVIEW,
                AgentCapability.DOCUMENT
            ]
        }
        return role_capabilities.get(self.role, [AgentCapability.REVIEW])

    def set_context(self, context: Dict[str, Any]):
        """Set execution context for this agent"""
        self.context.update(context)

    def get_context(self, key: str) -> Optional[Any]:
        """Retrieve context value"""
        return self.context.get(key)

    def add_decision(self, decision: DecisionJournal):
        """Add decision from Decision Journal"""
        self.decisions.append(decision)

    def get_decisions(self) -> List[DecisionJournal]:
        """Get all decisions guiding this agent"""
        return self.decisions

    @abstractmethod
    def execute_task(self, task_description: str) -> Dict[str, Any]:
        """Execute assigned task - implemented by subclasses"""
        pass

    def __repr__(self):
        return f"<{self.name} ({self.role.value})>"
