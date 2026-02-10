from enum import Enum
from typing import Dict, List, Any, Optional, Type
from sage_mode.models.team_simulator import AgentRole, DecisionJournal
from abc import ABC, abstractmethod
import logging

from sage_mode.llm import (
    LLMClient,
    BaseAgentResponse,
    build_full_prompt,
    get_schema_for_role,
)


logger = logging.getLogger(__name__)


# Map AgentRole to LLM role keys
ROLE_TO_LLM_KEY = {
    AgentRole.ARCHITECT: "software_architect",
    AgentRole.BACKEND_DEV: "backend_developer",
    AgentRole.FRONTEND_DEV: "frontend_developer",
    AgentRole.SECURITY_SPECIALIST: "security_specialist",
    AgentRole.DBA: "database_administrator",
    AgentRole.UI_UX_DESIGNER: "ui_ux_designer",
    AgentRole.IT_ADMIN: "it_administrator",
}


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
    """Base class for all 7 specialized agents.

    Supports both mock execution (for testing) and real LLM-powered
    execution using Claude API.
    """

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        llm_client: Optional[LLMClient] = None,
    ):
        self.role = role
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.context: Dict[str, Any] = {}
        self.decisions: List[DecisionJournal] = []
        self.capabilities: List[AgentCapability] = self._get_default_capabilities()
        self._feature_name: str = "Unknown Feature"

    def _get_default_capabilities(self) -> List[AgentCapability]:
        """Return default capabilities based on role"""
        role_capabilities = {
            AgentRole.ARCHITECT: [AgentCapability.DESIGN, AgentCapability.REVIEW, AgentCapability.DOCUMENT],
            AgentRole.FRONTEND_DEV: [AgentCapability.DESIGN, AgentCapability.IMPLEMENT, AgentCapability.TEST, AgentCapability.REVIEW],
            AgentRole.BACKEND_DEV: [AgentCapability.IMPLEMENT, AgentCapability.TEST, AgentCapability.REVIEW, AgentCapability.OPTIMIZE],
            AgentRole.UI_UX_DESIGNER: [AgentCapability.DESIGN, AgentCapability.REVIEW, AgentCapability.DOCUMENT],
            AgentRole.DBA: [AgentCapability.DESIGN, AgentCapability.IMPLEMENT, AgentCapability.OPTIMIZE, AgentCapability.AUDIT],
            AgentRole.IT_ADMIN: [AgentCapability.DEPLOY, AgentCapability.AUDIT, AgentCapability.OPTIMIZE],
            AgentRole.SECURITY_SPECIALIST: [AgentCapability.AUDIT, AgentCapability.REVIEW, AgentCapability.DOCUMENT]
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
        """Execute assigned task - implemented by subclasses.

        For mock/testing implementations, override this directly.
        """
        pass

    def set_feature_name(self, feature_name: str) -> None:
        """Set the feature name for LLM context."""
        self._feature_name = feature_name

    def get_llm_role_key(self) -> str:
        """Get the LLM role key for this agent."""
        return ROLE_TO_LLM_KEY.get(self.role, "software_architect")

    def get_response_schema(self) -> Type[BaseAgentResponse]:
        """Get the response schema class for this agent's role."""
        return get_schema_for_role(self.get_llm_role_key())

    async def execute_task_with_llm(
        self,
        task_description: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> BaseAgentResponse:
        """Execute task using LLM for real AI-powered responses.

        Args:
            task_description: What the agent should do
            additional_context: Extra context to include in the prompt

        Returns:
            Validated response matching the agent's schema

        Raises:
            ValueError: If no LLM client is configured
            LLMError: On LLM-related failures
        """
        if not self.llm_client:
            raise ValueError(
                f"No LLM client configured for {self.name}. "
                "Pass llm_client to constructor or use execute_task() for mock."
            )

        role_key = self.get_llm_role_key()
        schema = self.get_response_schema()

        # Build context from decisions and any additional context
        context = {
            "previous_decisions": [
                {
                    "title": d.title,
                    "description": d.description,
                    "category": d.category,
                    "decision_type": d.decision_type,
                    "confidence_level": d.confidence_level,
                }
                for d in self.decisions
            ],
            "agent_context": self.context,
        }
        if additional_context:
            context.update(additional_context)

        # Build the full prompt
        prompt = build_full_prompt(
            role=role_key,
            role_name=self.name,
            feature_name=self._feature_name,
            task_description=task_description,
            context=context,
            schema=schema,
        )

        logger.info(f"{self.name} executing task with LLM: {task_description[:50]}...")

        # Call LLM and get validated response
        response = await self.llm_client.generate(prompt, schema)

        logger.info(f"{self.name} completed task (confidence: {response.confidence})")

        return response

    def __repr__(self):
        return f"<{self.name} ({self.role.value})>"
