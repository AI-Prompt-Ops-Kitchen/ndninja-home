import pytest
from fastapi.testclient import TestClient
from sage_mode.api.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200

def test_create_decision(client):
    response = client.post("/api/decisions", json={
        "user_id": "user-123",
        "title": "Use async/await",
        "description": "Convert blocking calls",
        "category": "architecture",
        "decision_type": "technical",
        "confidence_level": 95
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Use async/await"

def test_search_decisions(client):
    client.post("/api/decisions", json={
        "user_id": "user-789",
        "title": "Implement Redis caching",
        "description": "Add caching layer",
        "category": "performance",
        "decision_type": "technical"
    })
    response = client.get("/api/decisions/search?q=caching")
    assert response.status_code == 200
