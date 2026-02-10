import pytest
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
from sage_mode.agents.dba_agent import DBAAgent
from sage_mode.agents.it_admin_agent import ITAdminAgent
from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent
from sage_mode.coordination.parallel_coordinator import ParallelCoordinator
from sage_mode.coordination.team_coordinator import TeamCoordinator
from sage_mode.database.decision_journal import DecisionJournalDB
from sage_mode.models.team_simulator import DecisionJournal

def test_phase2_complete_workflow():
    """End-to-end test: All 7 agents + parallel execution + decision journal"""

    # Initialize all 7 agents
    architect = ArchitectAgent()
    frontend = FrontendAgent()
    backend = BackendAgent()
    ui_ux = UIUXDesignerAgent()
    dba = DBAAgent()
    it_admin = ITAdminAgent()
    security = SecuritySpecialistAgent()

    # Create parallel coordinator
    coordinator = ParallelCoordinator(team_lead=architect)
    for agent in [frontend, backend, ui_ux, dba, it_admin, security]:
        coordinator.add_member(agent)

    # Initialize Decision Journal
    db = DecisionJournalDB()

    # Architect makes strategic decision
    arch_decision = DecisionJournal(
        user_id="project-manager",
        title="Full microservices + React frontend architecture",
        description="Split into independent services with async-first approach",
        category="architecture",
        decision_type="technical",
        confidence_level=95
    )

    arch_id = db.save_decision(arch_decision)
    architect.add_decision(arch_decision)

    # All team members receive the decision
    for agent in [frontend, backend, ui_ux, dba, it_admin, security]:
        agent.add_decision(arch_decision)

    # Execute feature in parallel
    result = coordinator.execute_feature_parallel(
        feature_name="Enterprise Platform v2.0",
        description="Build complete microservices platform with React UI"
    )

    # Verify execution
    assert result["status"] == "completed"
    assert result["execution_mode"] == "parallel"
    assert len(result["task_groups_executed"]) >= 3

    # Verify all team members executed
    executed_agents = set()
    for group in result["task_groups_executed"]:
        for agent_info in group["results"]:
            executed_agents.add(agent_info["agent"])

    assert len(executed_agents) >= 6

    # Verify decision journal captured decision
    retrieved = db.get_decision(arch_id)
    assert retrieved.title == arch_decision.title
    assert retrieved.confidence_level == 95

    # Verify all agents have decision context
    for agent in [frontend, backend, ui_ux, dba, it_admin, security]:
        decisions = agent.get_decisions()
        assert len(decisions) >= 1

def test_sequential_vs_parallel_execution():
    """Test both sequential and parallel modes work"""
    architect = ArchitectAgent()
    backend = BackendAgent()
    frontend = FrontendAgent()

    # Sequential execution
    seq_coordinator = TeamCoordinator(team_lead=architect)
    seq_coordinator.add_member(backend)
    seq_coordinator.add_member(frontend)

    seq_result = seq_coordinator.execute_feature_task(
        feature_name="Auth Module",
        description="Build authentication system"
    )

    assert seq_result["execution_mode"] == "sequential"
    assert seq_result["status"] == "completed"

    # Parallel execution
    par_coordinator = ParallelCoordinator(team_lead=architect)
    par_coordinator.add_member(backend)
    par_coordinator.add_member(frontend)

    par_result = par_coordinator.execute_feature_parallel(
        feature_name="Auth Module",
        description="Build authentication system"
    )

    assert par_result["execution_mode"] == "parallel"
    assert par_result["status"] == "completed"

def test_all_agents_have_capabilities():
    """Verify all 7 agents have proper capabilities"""
    agents = [
        ArchitectAgent(),
        FrontendAgent(),
        BackendAgent(),
        UIUXDesignerAgent(),
        DBAAgent(),
        ITAdminAgent(),
        SecuritySpecialistAgent()
    ]

    for agent in agents:
        assert agent.role is not None
        assert agent.name is not None
        assert len(agent.capabilities) >= 2
        assert hasattr(agent, 'execute_task')
