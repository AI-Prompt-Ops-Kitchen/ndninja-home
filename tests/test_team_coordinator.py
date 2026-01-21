import pytest
from sage_mode.coordination.team_coordinator import TeamCoordinator
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.architect_agent import ArchitectAgent

def test_team_coordinator_initialization():
    architect = ArchitectAgent()
    coordinator = TeamCoordinator(team_lead=architect)
    assert coordinator.team_lead == architect
    assert len(coordinator.team_members) == 0

def test_add_team_members():
    architect = ArchitectAgent()
    coordinator = TeamCoordinator(team_lead=architect)
    frontend = FrontendAgent()
    backend = BackendAgent()
    coordinator.add_member(frontend)
    coordinator.add_member(backend)
    assert len(coordinator.team_members) == 2

def test_execute_team_task_sequentially():
    architect = ArchitectAgent()
    frontend = FrontendAgent()
    backend = BackendAgent()
    coordinator = TeamCoordinator(team_lead=architect)
    coordinator.add_member(frontend)
    coordinator.add_member(backend)
    result = coordinator.execute_feature_task(feature_name="User Auth", description="Build auth system")
    assert result["feature"] == "User Auth"
    assert result["execution_mode"] == "sequential"
    assert result["status"] in ["completed", "in_progress"]

def test_team_execution_history():
    architect = ArchitectAgent()
    coordinator = TeamCoordinator(team_lead=architect)
    history = coordinator.get_execution_history()
    assert isinstance(history, list)
    assert len(history) == 0
