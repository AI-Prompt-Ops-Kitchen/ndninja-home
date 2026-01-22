from sage_mode.agents.base_agent import BaseAgent
from sage_mode.models.team_simulator import AgentRole
from sage_mode.llm import LLMClient
from typing import Dict, Any, Optional


class BackendAgent(BaseAgent):
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            role=AgentRole.BACKEND_DEV,
            name="Backend Developer",
            description="Builds scalable APIs, implements business logic, optimizes database queries",
            llm_client=llm_client,
        )

    def execute_task(self, task_description: str) -> Dict[str, Any]:
        return {"status": "started", "task": task_description, "agent": self.name, "role": self.role.value}

    def design_endpoint(self, endpoint_path: str, method: str) -> Dict[str, Any]:
        return {"endpoint": f"{method} {endpoint_path}", "authentication": "required", "rate_limiting": "enabled"}
