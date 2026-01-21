import pytest
from fastapi.testclient import TestClient
from sage_mode.api.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_create_decision(client):
    """POST /decisions creates a new decision"""
    response = client.post("/api/decisions", json={
        "user_id": "user-123",
        "title": "Use async/await",
        "description": "Convert blocking calls to async",
        "category": "architecture",
        "decision_type": "technical",
        "confidence_level": 95
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Use async/await"

def test_get_user_decisions(client):
    """GET /decisions?user_id=X lists decisions for user"""
    client.post("/api/decisions", json={
        "user_id": "user-456",
        "title": "First decision",
        "description": "Description",
        "category": "architecture",
        "decision_type": "technical"
    })

    response = client.get("/api/decisions?user_id=user-456")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

def test_search_decisions(client):
    """GET /decisions/search?q=keyword searches decisions"""
    client.post("/api/decisions", json={
        "user_id": "user-789",
        "title": "Implement Redis caching",
        "description": "Add caching layer for performance",
        "category": "performance",
        "decision_type": "technical"
    })

    response = client.get("/api/decisions/search?q=caching")
    assert response.status_code == 200
    data = response.json()
    assert any("caching" in d.get("title", "").lower() for d in data)

def test_get_decision_by_id(client):
    """GET /decisions/{id} retrieves specific decision"""
    create_response = client.post("/api/decisions", json={
        "user_id": "user-999",
        "title": "Test decision",
        "description": "Test",
        "category": "architecture",
        "decision_type": "technical"
    })
    decision_id = create_response.json()["id"]

    response = client.get(f"/api/decisions/{decision_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test decision"
