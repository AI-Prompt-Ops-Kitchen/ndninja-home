from typing import List, Dict, Any, Optional
from datetime import datetime
from sage_mode.agents.base_agent import BaseAgent
from sage_mode.models.team_simulator import TeamEvent, AgentRole

class TeamCoordinator:
    """Coordinates team member execution (MVP: sequential, later: parallel with Kage Bunshin)"""

    def __init__(self, team_lead: BaseAgent):
        assert team_lead.is_team_lead() if hasattr(team_lead, 'is_team_lead') else False
        self.team_lead = team_lead
        self.team_members: List[BaseAgent] = []
        self.execution_history: List[Dict[str, Any]] = []
        self.current_feature: Optional[str] = None

    def add_member(self, agent: BaseAgent):
        """Add team member"""
        self.team_members.append(agent)

    def execute_feature_task(self, feature_name: str, description: str) -> Dict[str, Any]:
        """Execute feature task with team (MVP: sequential execution)"""
        self.current_feature = feature_name

        execution_record = {
            "feature": feature_name,
            "description": description,
            "execution_mode": "sequential",
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "team_members": [agent.name for agent in self.team_members],
            "tasks_completed": []
        }

        execution_order = self._plan_execution_order()

        for agent in execution_order:
            result = agent.execute_task(description)
            execution_record["tasks_completed"].append({
                "agent": agent.name,
                "result": result
            })

        execution_record["status"] = "completed"
        execution_record["completed_at"] = datetime.now().isoformat()

        self.execution_history.append(execution_record)
        return execution_record

    def _plan_execution_order(self) -> List[BaseAgent]:
        """Plan execution order (architect first, then backend, then frontend)"""
        order = []
        order.append(self.team_lead)

        for member in self.team_members:
            if member.role == AgentRole.BACKEND_DEV:
                order.append(member)
                break

        for member in self.team_members:
            if member.role == AgentRole.FRONTEND_DEV:
                order.append(member)
                break

        return order

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history
