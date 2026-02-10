import pytest
from datetime import datetime
from sage_mode.models.team_simulator import DecisionJournal, AgentRole, TeamEvent

def test_decision_journal_creation():
    """DecisionJournal stores decision with timestamp and metadata"""
    decision = DecisionJournal(
        user_id="test-user",
        title="Add OAuth 2.0 to auth system",
        description="Use PKCE flow for better security",
        category="architecture",
        decision_type="technical",
        timestamp=datetime.now()
    )
    assert decision.title == "Add OAuth 2.0 to auth system"
    assert decision.category == "architecture"
    assert decision.decision_type == "technical"

def test_decision_journal_with_context():
    """DecisionJournal captures full hyperfocus context"""
    decision = DecisionJournal(
        user_id="test-user",
        title="Migrate to async/await",
        description="All database calls become non-blocking",
        category="performance",
        decision_type="technical",
        context_snippet="Working on reducing API latency from 500ms to 100ms",
        related_task="implement-caching",
        confidence_level=95
    )
    assert decision.context_snippet is not None
    assert decision.confidence_level == 95

def test_agent_role_enum():
    """AgentRole enum contains all 7 specialist roles"""
    assert hasattr(AgentRole, 'FRONTEND_DEV')
    assert hasattr(AgentRole, 'BACKEND_DEV')
    assert hasattr(AgentRole, 'ARCHITECT')
    assert hasattr(AgentRole, 'UI_UX_DESIGNER')
    assert hasattr(AgentRole, 'DBA')
    assert hasattr(AgentRole, 'IT_ADMIN')
    assert hasattr(AgentRole, 'SECURITY_SPECIALIST')
    assert len(AgentRole) == 7

def test_team_event_creation():
    """TeamEvent tracks agent actions in coordination"""
    event = TeamEvent(
        event_type="decision_made",
        agent_role=AgentRole.ARCHITECT,
        description="Selected microservices architecture",
        timestamp=datetime.now()
    )
    assert event.event_type == "decision_made"
    assert event.agent_role == AgentRole.ARCHITECT
