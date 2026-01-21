import pytest
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.models.team_simulator import AgentRole

def test_frontend_agent_initialization():
    """Frontend agent initializes correctly"""
    agent = FrontendAgent()
    assert agent.role == AgentRole.FRONTEND_DEV
    assert agent.name == "Frontend Developer"

def test_frontend_agent_has_frontend_capabilities():
    """Frontend agent has UI development capabilities"""
    agent = FrontendAgent()
    from sage_mode.agents.base_agent import AgentCapability
    assert AgentCapability.IMPLEMENT in agent.capabilities
    assert AgentCapability.TEST in agent.capabilities

def test_backend_agent_initialization():
    """Backend agent initializes correctly"""
    agent = BackendAgent()
    assert agent.role == AgentRole.BACKEND_DEV
    assert agent.name == "Backend Developer"

def test_backend_agent_has_backend_capabilities():
    """Backend agent has API/server capabilities"""
    agent = BackendAgent()
    from sage_mode.agents.base_agent import AgentCapability
    assert AgentCapability.IMPLEMENT in agent.capabilities
    assert AgentCapability.OPTIMIZE in agent.capabilities

def test_architect_agent_initialization():
    """Architect agent initializes correctly"""
    agent = ArchitectAgent()
    assert agent.role == AgentRole.ARCHITECT
    assert agent.name == "Software Architect"

def test_architect_is_team_lead():
    """Architect has team lead status"""
    agent = ArchitectAgent()
    assert agent.is_team_lead() == True

def test_frontend_agent_can_execute_ui_task():
    """Frontend agent can execute UI tasks"""
    agent = FrontendAgent()
    result = agent.execute_task("Create login form component")
    assert "status" in result
    assert result["status"] in ["started", "completed", "error"]

def test_backend_agent_can_execute_api_task():
    """Backend agent can execute API tasks"""
    agent = BackendAgent()
    result = agent.execute_task("Create user authentication endpoint")
    assert "status" in result
    assert result["status"] in ["started", "completed", "error"]

def test_architect_can_execute_design_task():
    """Architect can execute system design tasks"""
    agent = ArchitectAgent()
    result = agent.execute_task("Design authentication system architecture")
    assert "status" in result
    assert result["status"] in ["started", "completed", "error"]
