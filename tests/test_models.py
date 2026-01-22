import pytest
from sage_mode.models.user_model import User
from sage_mode.models.team_model import Team, TeamMembership
from sage_mode.models.session_model import ExecutionSession, SessionDecision
from sage_mode.models.task_model import AgentTask, TaskDecision, AgentSnapshot

def test_user_model():
    user = User(username="test", email="test@test.com", password_hash="hash")
    assert user.username == "test"

def test_team_model():
    team = Team(name="Team1", owner_id=1, is_shared=False)
    assert team.name == "Team1"
    assert team.is_shared == False

def test_session_model():
    session = ExecutionSession(team_id=1, user_id=1, feature_name="Feature")
    assert session.feature_name == "Feature"

def test_decision_models():
    decision = SessionDecision(session_id=1, decision_text="Use JWT")
    assert decision.decision_text == "Use JWT"

def test_task_models():
    task = AgentTask(session_id=1, agent_role="backend", task_description="Build API")
    assert task.agent_role == "backend"
