"""Regression tests for /rules CRUD endpoints."""


def _create_rule(client, name="test_rule"):
    """Helper — create a rule and return the response JSON."""
    return client.post("/rules", json={
        "name": name,
        "event_type": "test.event",
        "source": "tdd",
        "condition": {},
        "action": {"type": "log", "message": "test"},
    }).json()


def test_get_rule_by_id(client):
    rule = _create_rule(client, "get_by_id_test")
    rule_id = rule["id"]

    resp = client.get(f"/rules/{rule_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == rule_id
    assert data["name"] == "get_by_id_test"
    assert data["event_type"] == "test.event"


def test_get_rule_not_found(client):
    resp = client.get("/rules/999999")
    assert resp.status_code == 404
