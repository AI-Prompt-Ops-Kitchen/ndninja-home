from sage_mode.agents.base_agent import BaseAgent
from sage_mode.models.team_simulator import AgentRole
from sage_mode.llm import LLMClient
from typing import Dict, Any, Optional


class UIUXDesignerAgent(BaseAgent):
    """UI/UX Designer - creates wireframes, prototypes, design systems"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            role=AgentRole.UI_UX_DESIGNER,
            name="UI/UX Designer",
            description="Designs user interfaces, prototypes, accessibility standards, design systems",
            llm_client=llm_client,
        )

    def execute_task(self, task_description: str) -> Dict[str, Any]:
        return {
            "status": "started",
            "task": task_description,
            "agent": self.name,
            "role": self.role.value,
            "estimated_duration": "3-5 hours"
        }
