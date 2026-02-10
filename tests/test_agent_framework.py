import pytest
from sage_mode.agents.base_agent import BaseAgent, AgentCapability
from sage_mode.models.team_simulator import AgentRole, DecisionJournal
from typing import Dict, Any

# Concrete test implementation for testing BaseAgent abstract base
class TestAgent(BaseAgent):
    """Concrete implementation for testing BaseAgent functionality"""
    def execute_task(self, task_description: str) -> Dict[str, Any]:
        return {"status": "completed", "task": task_description}

def test_agent_initialization():
    """Agent initializes with role and capabilities"""
    agent = TestAgent(
        role=AgentRole.ARCHITECT,
        name="Senior Architect",
        description="Designs system architecture"
    )
    assert agent.role == AgentRole.ARCHITECT
    assert agent.name == "Senior Architect"

def test_agent_has_capabilities():
    """Agent has defined capabilities"""
    agent = TestAgent(
        role=AgentRole.ARCHITECT,
        name="Senior Architect",
        description="Designs system architecture"
    )
    assert hasattr(agent, 'capabilities')
    assert len(agent.capabilities) >= 1

def test_agent_can_add_context():
    """Agent can receive and store context"""
    agent = TestAgent(
        role=AgentRole.BACKEND_DEV,
        name="Backend Dev",
        description="Builds APIs"
    )
    context = {
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "async": True
    }
    agent.set_context(context)
    assert agent.get_context("framework") == "FastAPI"

def test_agent_task_execution_interface():
    """Agent has execute_task interface"""
    agent = TestAgent(
        role=AgentRole.FRONTEND_DEV,
        name="Frontend Dev",
        description="Builds UI"
    )
    assert hasattr(agent, 'execute_task')
    assert callable(agent.execute_task)

def test_agent_can_receive_decision_journal():
    """Agent receives DecisionJournal for guidance"""
    agent = TestAgent(
        role=AgentRole.DBA,
        name="Database Admin",
        description="Manages database"
    )
    decision = DecisionJournal(
        user_id="user-123",
        title="Use PostgreSQL with async",
        description="All queries async",
        category="architecture",
        decision_type="technical"
    )
    agent.add_decision(decision)
    decisions = agent.get_decisions()
    assert len(decisions) == 1
    assert decisions[0].title == decision.title
