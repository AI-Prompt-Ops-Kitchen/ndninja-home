from typing import List, Dict, Any, Optional
from datetime import datetime
from sage_mode.agents.base_agent import BaseAgent
from sage_mode.models.team_simulator import AgentRole

class ParallelCoordinator:
    """Coordinates parallel team execution via Kage Bunshin (Phase 2+)"""

    def __init__(self, team_lead: BaseAgent):
        assert team_lead.is_team_lead() if hasattr(team_lead, 'is_team_lead') else False
        self.team_lead = team_lead
        self.team_members: List[BaseAgent] = []
        self.execution_history: List[Dict[str, Any]] = []
        self.execution_mode = "parallel"  # Can switch to "sequential" for backwards compat
        self.current_feature: Optional[str] = None

    def add_member(self, agent: BaseAgent):
        """Add team member for parallel execution"""
        self.team_members.append(agent)

    def switch_mode(self, mode: str):
        """Switch between parallel and sequential execution"""
        assert mode in ["parallel", "sequential"]
        self.execution_mode = mode

    def plan_parallel_execution(self) -> Dict[str, Any]:
        """Plan task grouping for parallel execution"""
        task_groups = self._group_tasks_for_parallelism()
        return {
            "mode": "parallel",
            "task_groups": task_groups,
            "total_groups": len(task_groups),
            "estimated_speedup": f"{len(self.team_members)}x vs sequential"
        }

    def _group_tasks_for_parallelism(self) -> List[List[BaseAgent]]:
        """Group tasks that can run in parallel"""
        groups = []

        # Group 1: Team lead (architect) - always first
        groups.append([self.team_lead])

        # Group 2: Backend + DBA (database work) - can run in parallel
        backend_group = []
        for member in self.team_members:
            if member.role == AgentRole.BACKEND_DEV:
                backend_group.append(member)
            elif member.role == AgentRole.DBA:
                backend_group.append(member)
        if backend_group:
            groups.append(backend_group)

        # Group 3: Frontend + UI/UX (UI work) - can run in parallel
        frontend_group = []
        for member in self.team_members:
            if member.role == AgentRole.FRONTEND_DEV:
                frontend_group.append(member)
            elif member.role == AgentRole.UI_UX_DESIGNER:
                frontend_group.append(member)
        if frontend_group:
            groups.append(frontend_group)

        # Group 4: Security + IT Admin (infrastructure) - can run in parallel
        infra_group = []
        for member in self.team_members:
            if member.role == AgentRole.SECURITY_SPECIALIST:
                infra_group.append(member)
            elif member.role == AgentRole.IT_ADMIN:
                infra_group.append(member)
        if infra_group:
            groups.append(infra_group)

        return groups

    def execute_feature_parallel(self, feature_name: str, description: str) -> Dict[str, Any]:
        """Execute feature with parallel task groups"""
        self.current_feature = feature_name

        execution_record = {
            "feature": feature_name,
            "description": description,
            "execution_mode": "parallel",
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "team_members": [agent.name for agent in self.team_members],
            "task_groups_executed": []
        }

        task_groups = self._group_tasks_for_parallelism()
        for group_idx, group in enumerate(task_groups):
            group_results = []
            for agent in group:
                result = agent.execute_task(description)
                group_results.append({"agent": agent.name, "result": result})

            execution_record["task_groups_executed"].append({
                "group": group_idx + 1,
                "agents": [a.name for a in group],
                "results": group_results
            })

        execution_record["status"] = "completed"
        execution_record["completed_at"] = datetime.now().isoformat()

        self.execution_history.append(execution_record)
        return execution_record

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history
