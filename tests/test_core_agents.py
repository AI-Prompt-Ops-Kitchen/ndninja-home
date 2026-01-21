import pytest
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.models.team_simulator import AgentRole

def test_frontend_agent_initialization():
    agent = FrontendAgent()
    assert agent.role == AgentRole.FRONTEND_DEV
    assert agent.name == "Frontend Developer"

def test_frontend_agent_has_frontend_capabilities():
    agent = FrontendAgent()
    from sage_mode.agents.base_agent import AgentCapability
    assert AgentCapability.IMPLEMENT in agent.capabilities

def test_backend_agent_initialization():
    agent = BackendAgent()
    assert agent.role == AgentRole.BACKEND_DEV
    assert agent.name == "Backend Developer"

def test_backend_agent_has_backend_capabilities():
    agent = BackendAgent()
    from sage_mode.agents.base_agent import AgentCapability
    assert AgentCapability.OPTIMIZE in agent.capabilities

def test_architect_agent_initialization():
    agent = ArchitectAgent()
    assert agent.role == AgentRole.ARCHITECT
    assert agent.name == "Software Architect"

def test_architect_is_team_lead():
    agent = ArchitectAgent()
    assert agent.is_team_lead() == True

def test_frontend_execute_task():
    agent = FrontendAgent()
    result = agent.execute_task("Create login form")
    assert result["status"] == "started"

def test_backend_execute_task():
    agent = BackendAgent()
    result = agent.execute_task("Create auth endpoint")
    assert result["status"] == "started"

def test_architect_execute_task():
    agent = ArchitectAgent()
    result = agent.execute_task("Design auth system")
    assert result["status"] == "started"
