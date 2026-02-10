import pytest
from sage_mode.models.team_simulator import DecisionJournal
from sage_mode.database.decision_journal import DecisionJournalDB
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.coordination.team_coordinator import TeamCoordinator

def test_full_feature_execution_with_decision_journal():
    architect = ArchitectAgent()
    backend = BackendAgent()
    frontend = FrontendAgent()
    coordinator = TeamCoordinator(team_lead=architect)
    coordinator.add_member(backend)
    coordinator.add_member(frontend)
    db = DecisionJournalDB()
    arch_decision = DecisionJournal(
        user_id="ninja-dev",
        title="Use FastAPI for backend",
        description="Async-native framework",
        category="architecture",
        decision_type="technical",
        confidence_level=95
    )
    arch_decision_id = db.save_decision(arch_decision)
    architect.add_decision(arch_decision)
    result = coordinator.execute_feature_task(
        feature_name="User Authentication",
        description="Implement OAuth 2.0 authentication system"
    )
    assert result["status"] == "completed"
    assert len(result["tasks_completed"]) >= 3
    retrieved_decision = db.get_decision(arch_decision_id)
    assert retrieved_decision.title == "Use FastAPI for backend"
    assert len(architect.get_decisions()) == 1
