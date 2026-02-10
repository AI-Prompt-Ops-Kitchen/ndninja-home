import pytest
from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
from sage_mode.agents.dba_agent import DBAAgent
from sage_mode.agents.it_admin_agent import ITAdminAgent
from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent
from sage_mode.models.team_simulator import AgentRole
from sage_mode.agents.base_agent import AgentCapability

# UI/UX Designer Tests
def test_ui_ux_designer_initialization():
    agent = UIUXDesignerAgent()
    assert agent.role == AgentRole.UI_UX_DESIGNER
    assert agent.name == "UI/UX Designer"

def test_ui_ux_designer_has_design_capabilities():
    agent = UIUXDesignerAgent()
    assert AgentCapability.DESIGN in agent.capabilities
    assert AgentCapability.REVIEW in agent.capabilities
    assert AgentCapability.DOCUMENT in agent.capabilities

def test_ui_ux_designer_execute_task():
    agent = UIUXDesignerAgent()
    result = agent.execute_task("Design login page wireframes")
    assert result["status"] == "started"
    assert "estimated_duration" in result

# DBA Tests
def test_dba_initialization():
    agent = DBAAgent()
    assert agent.role == AgentRole.DBA
    assert agent.name == "Database Administrator"

def test_dba_has_optimization_capabilities():
    agent = DBAAgent()
    assert AgentCapability.DESIGN in agent.capabilities
    assert AgentCapability.OPTIMIZE in agent.capabilities
    assert AgentCapability.AUDIT in agent.capabilities

def test_dba_execute_task():
    agent = DBAAgent()
    result = agent.execute_task("Optimize user_id index")
    assert result["status"] == "started"
    assert "estimated_duration" in result

# IT Admin Tests
def test_it_admin_initialization():
    agent = ITAdminAgent()
    assert agent.role == AgentRole.IT_ADMIN
    assert agent.name == "IT Administrator"

def test_it_admin_has_deployment_capabilities():
    agent = ITAdminAgent()
    assert AgentCapability.DEPLOY in agent.capabilities
    assert AgentCapability.AUDIT in agent.capabilities
    assert AgentCapability.OPTIMIZE in agent.capabilities

def test_it_admin_execute_task():
    agent = ITAdminAgent()
    result = agent.execute_task("Deploy to production")
    assert result["status"] == "started"
    assert "estimated_duration" in result

# Security Specialist Tests
def test_security_specialist_initialization():
    agent = SecuritySpecialistAgent()
    assert agent.role == AgentRole.SECURITY_SPECIALIST
    assert agent.name == "Security Specialist"

def test_security_specialist_has_audit_capabilities():
    agent = SecuritySpecialistAgent()
    assert AgentCapability.AUDIT in agent.capabilities
    assert AgentCapability.REVIEW in agent.capabilities
    assert AgentCapability.DOCUMENT in agent.capabilities

def test_security_specialist_execute_task():
    agent = SecuritySpecialistAgent()
    result = agent.execute_task("Audit API endpoints for vulnerabilities")
    assert result["status"] == "started"
    assert "estimated_duration" in result
