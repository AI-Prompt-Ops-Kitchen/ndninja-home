from sage_mode.agents.base_agent import BaseAgent
from sage_mode.models.team_simulator import AgentRole
from sage_mode.llm import LLMClient
from typing import Dict, Any, Optional


class ITAdminAgent(BaseAgent):
    """IT Administrator - deployment, infrastructure, monitoring"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            role=AgentRole.IT_ADMIN,
            name="IT Administrator",
            description="Manages deployment pipelines, infrastructure, monitoring, systemd services",
            llm_client=llm_client,
        )

    def execute_task(self, task_description: str) -> Dict[str, Any]:
        return {
            "status": "started",
            "task": task_description,
            "agent": self.name,
            "role": self.role.value,
            "estimated_duration": "1-2 hours"
        }
