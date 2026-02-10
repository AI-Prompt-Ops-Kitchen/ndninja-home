from sage_mode.agents.base_agent import BaseAgent
from sage_mode.models.team_simulator import AgentRole
from sage_mode.llm import LLMClient
from typing import Dict, Any, Optional


class FrontendAgent(BaseAgent):
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            role=AgentRole.FRONTEND_DEV,
            name="Frontend Developer",
            description="Builds responsive UI components, manages state, integrates with backend APIs",
            llm_client=llm_client,
        )

    def execute_task(self, task_description: str) -> Dict[str, Any]:
        return {"status": "started", "task": task_description, "agent": self.name, "role": self.role.value}

    def design_component(self, component_name: str) -> Dict[str, Any]:
        return {"component": component_name, "state_management": "recommended", "accessibility": "wcag2.1"}
