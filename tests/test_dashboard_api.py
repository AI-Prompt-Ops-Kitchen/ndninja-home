import pytest
from fastapi.testclient import TestClient
from sage_mode.api.app import app
from sage_mode.database.decision_journal import DecisionJournalDB
from sage_mode.models.team_simulator import DecisionJournal

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    return DecisionJournalDB()

def test_dashboard_root_endpoint(client):
    response = client.get("/dashboard")
    assert response.status_code == 200

def test_dashboard_get_team_stats(client, db):
    # Create some decisions
    for i in range(5):
        decision = DecisionJournal(
            user_id="team-user",
            title=f"Decision {i}",
            description=f"Description {i}",
            category="architecture" if i % 2 == 0 else "performance",
            decision_type="technical"
        )
        db.save_decision(decision)

    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_decisions"] >= 5

def test_dashboard_get_recent_decisions(client, db):
    decision = DecisionJournal(
        user_id="team-user",
        title="Recent decision",
        description="Just made this",
        category="architecture",
        decision_type="technical"
    )
    db.save_decision(decision)

    response = client.get("/dashboard/recent-decisions?limit=10")
    assert response.status_code == 200

def test_dashboard_get_agent_status(client):
    response = client.get("/dashboard/agent-status")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) == 7
