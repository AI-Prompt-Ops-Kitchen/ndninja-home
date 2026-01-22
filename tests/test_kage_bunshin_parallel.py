import pytest
from sage_mode.coordination.parallel_coordinator import ParallelCoordinator
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
from sage_mode.agents.dba_agent import DBAAgent
from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent

def test_parallel_coordinator_initialization():
    architect = ArchitectAgent()
    coordinator = ParallelCoordinator(team_lead=architect)
    assert coordinator.team_lead == architect
    assert coordinator.execution_mode == "parallel"
    assert len(coordinator.team_members) == 0

def test_parallel_coordinator_add_members():
    architect = ArchitectAgent()
    coordinator = ParallelCoordinator(team_lead=architect)
    frontend = FrontendAgent()
    backend = BackendAgent()
    ui_ux = UIUXDesignerAgent()
    coordinator.add_member(frontend)
    coordinator.add_member(backend)
    coordinator.add_member(ui_ux)
    assert len(coordinator.team_members) == 3

def test_parallel_execution_groups_independent_tasks():
    architect = ArchitectAgent()
    backend = BackendAgent()
    frontend = FrontendAgent()
    ui_ux = UIUXDesignerAgent()
    dba = DBAAgent()
    security = SecuritySpecialistAgent()

    coordinator = ParallelCoordinator(team_lead=architect)
    coordinator.add_member(backend)
    coordinator.add_member(frontend)
    coordinator.add_member(ui_ux)
    coordinator.add_member(dba)
    coordinator.add_member(security)

    execution_plan = coordinator.plan_parallel_execution()
    assert execution_plan["mode"] == "parallel"
    assert len(execution_plan["task_groups"]) > 0

def test_parallel_execution_maintains_dependencies():
    architect = ArchitectAgent()
    backend = BackendAgent()
    frontend = FrontendAgent()

    coordinator = ParallelCoordinator(team_lead=architect)
    coordinator.add_member(backend)
    coordinator.add_member(frontend)

    # Architect must run first (team lead)
    execution_plan = coordinator.plan_parallel_execution()
    first_group = execution_plan["task_groups"][0]
    assert any(agent.name == "Software Architect" for agent in first_group)

def test_parallel_coordinator_execution_history():
    architect = ArchitectAgent()
    coordinator = ParallelCoordinator(team_lead=architect)
    history = coordinator.get_execution_history()
    assert isinstance(history, list)
    assert len(history) == 0

def test_parallel_coordinator_can_switch_modes():
    architect = ArchitectAgent()
    coordinator = ParallelCoordinator(team_lead=architect)
    assert coordinator.execution_mode == "parallel"
    coordinator.switch_mode("sequential")
    assert coordinator.execution_mode == "sequential"
