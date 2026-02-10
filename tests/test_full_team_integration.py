import pytest
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
from sage_mode.agents.dba_agent import DBAAgent
from sage_mode.agents.it_admin_agent import ITAdminAgent
from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent
from sage_mode.coordination.team_coordinator import TeamCoordinator
from sage_mode.coordination.parallel_coordinator import ParallelCoordinator
from sage_mode.models.team_simulator import DecisionJournal
from sage_mode.database.decision_journal import DecisionJournalDB

# Full 7-member team tests
def test_full_team_initialization():
    architect = ArchitectAgent()
    frontend = FrontendAgent()
    backend = BackendAgent()
    ui_ux = UIUXDesignerAgent()
    dba = DBAAgent()
    it_admin = ITAdminAgent()
    security = SecuritySpecialistAgent()

    coordinator = TeamCoordinator(team_lead=architect)
    coordinator.add_member(frontend)
    coordinator.add_member(backend)
    coordinator.add_member(ui_ux)
    coordinator.add_member(dba)
    coordinator.add_member(it_admin)
    coordinator.add_member(security)

    assert len(coordinator.team_members) == 6
    assert coordinator.team_lead.name == "Software Architect"

def test_parallel_execution_with_full_team():
    architect = ArchitectAgent()
    frontend = FrontendAgent()
    backend = BackendAgent()
    ui_ux = UIUXDesignerAgent()
    dba = DBAAgent()
    it_admin = ITAdminAgent()
    security = SecuritySpecialistAgent()

    coordinator = ParallelCoordinator(team_lead=architect)
    coordinator.add_member(frontend)
    coordinator.add_member(backend)
    coordinator.add_member(ui_ux)
    coordinator.add_member(dba)
    coordinator.add_member(it_admin)
    coordinator.add_member(security)

    result = coordinator.execute_feature_parallel(
        feature_name="Complete Application",
        description="Build full-stack application with security"
    )

    assert result["status"] == "completed"
    assert len(result["task_groups_executed"]) >= 3

def test_decision_journal_with_all_agents():
    db = DecisionJournalDB()
    architect = ArchitectAgent()

    # Architect makes core decision
    arch_decision = DecisionJournal(
        user_id="project-lead",
        title="Use microservices architecture",
        description="Split into independent services",
        category="architecture",
        decision_type="technical",
        confidence_level=95
    )
    arch_id = db.save_decision(arch_decision)
    architect.add_decision(arch_decision)

    # Other agents reference decision
    backend = BackendAgent()
    backend.add_decision(arch_decision)

    security = SecuritySpecialistAgent()
    security.add_decision(arch_decision)

    assert len(architect.get_decisions()) == 1
    assert len(backend.get_decisions()) == 1
    assert len(security.get_decisions()) == 1

def test_team_can_share_context():
    architect = ArchitectAgent()
    frontend = FrontendAgent()
    backend = BackendAgent()

    shared_context = {
        "tech_stack": "FastAPI + React",
        "database": "PostgreSQL",
        "authentication": "JWT"
    }

    architect.set_context(shared_context)
    frontend.set_context(shared_context)
    backend.set_context(shared_context)

    assert architect.get_context("tech_stack") == "FastAPI + React"
    assert frontend.get_context("database") == "PostgreSQL"
    assert backend.get_context("authentication") == "JWT"

def test_parallel_vs_sequential_modes():
    architect = ArchitectAgent()
    backend = BackendAgent()
    frontend = FrontendAgent()

    parallel_coord = ParallelCoordinator(team_lead=architect)
    parallel_coord.add_member(backend)
    parallel_coord.add_member(frontend)

    assert parallel_coord.execution_mode == "parallel"

    parallel_coord.switch_mode("sequential")
    assert parallel_coord.execution_mode == "sequential"

    parallel_coord.switch_mode("parallel")
    assert parallel_coord.execution_mode == "parallel"

def test_ui_ux_designer_in_team_context():
    architect = ArchitectAgent()
    ui_ux = UIUXDesignerAgent()
    frontend = FrontendAgent()

    coordinator = ParallelCoordinator(team_lead=architect)
    coordinator.add_member(ui_ux)
    coordinator.add_member(frontend)

    plan = coordinator.plan_parallel_execution()
    assert any("UI/UX" in str(group) for group in plan["task_groups"])

def test_dba_in_team_context():
    architect = ArchitectAgent()
    dba = DBAAgent()
    backend = BackendAgent()

    coordinator = ParallelCoordinator(team_lead=architect)
    coordinator.add_member(dba)
    coordinator.add_member(backend)

    plan = coordinator.plan_parallel_execution()
    # DBA and Backend should be in same group (can parallelize)
    backend_dba_group = [g for g in plan["task_groups"] if len(g) > 1]
    assert len(backend_dba_group) > 0

def test_security_specialist_in_team_context():
    architect = ArchitectAgent()
    security = SecuritySpecialistAgent()
    it_admin = ITAdminAgent()

    coordinator = ParallelCoordinator(team_lead=architect)
    coordinator.add_member(security)
    coordinator.add_member(it_admin)

    plan = coordinator.plan_parallel_execution()
    # Security and IT Admin should be in same group
    infra_group = [g for g in plan["task_groups"] if len(g) > 1]
    assert len(infra_group) > 0

def test_it_admin_handles_deployment():
    it_admin = ITAdminAgent()
    result = it_admin.execute_task("Deploy to Kubernetes cluster")
    assert result["status"] == "started"
    assert result["role"] == "it_administrator"

def test_full_feature_execution_flow():
    # Simulate complete feature execution with all 7 agents
    architect = ArchitectAgent()
    frontend = FrontendAgent()
    backend = BackendAgent()
    ui_ux = UIUXDesignerAgent()
    dba = DBAAgent()
    it_admin = ITAdminAgent()
    security = SecuritySpecialistAgent()

    coordinator = ParallelCoordinator(team_lead=architect)
    for agent in [frontend, backend, ui_ux, dba, it_admin, security]:
        coordinator.add_member(agent)

    result = coordinator.execute_feature_parallel(
        feature_name="Enterprise Application",
        description="Build complete enterprise system"
    )

    assert result["status"] == "completed"
    assert len(coordinator.get_execution_history()) > 0
    assert result["execution_mode"] == "parallel"
