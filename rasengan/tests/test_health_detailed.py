"""RED: GET /health/detailed should return uptime and edict count."""


def test_should_return_uptime_and_edict_count(client):
    """GET /health/detailed returns status, service, uptime_seconds, and edict_count."""
    # Arrange — nothing extra needed, server start time is implicit

    # Act
    response = client.get("/health/detailed")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rasengan"
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0
    assert isinstance(data["edict_count"], int)
    assert data["edict_count"] > 0  # edicts.yaml is non-empty
