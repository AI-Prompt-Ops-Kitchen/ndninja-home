"""Tests for POST /events input validation."""


def test_should_reject_empty_source_with_422(client):
    """POST /events with source="" must return 422 — empty source is not meaningful."""
    # Arrange
    payload = {
        "event_type": "test.event",
        "source": "",
        "payload": {},
    }

    # Act
    response = client.post("/events", json=payload)

    # Assert — 422 means Pydantic caught the invalid input
    assert response.status_code == 422, (
        f"Expected 422 for empty source, got {response.status_code}"
    )


def test_should_reject_empty_event_type_with_422(client):
    """POST /events with event_type="" must return 422, not silently accept."""
    # Arrange
    payload = {
        "event_type": "",
        "source": "test",
        "payload": {},
    }

    # Act
    response = client.post("/events", json=payload)

    # Assert — 422 means Pydantic caught the invalid input
    assert response.status_code == 422, (
        f"Expected 422 for empty event_type, got {response.status_code}"
    )


def test_should_default_payload_when_omitted(client):
    """POST /events without payload key should default to empty dict, not error."""
    # Act
    response = client.post("/events", json={
        "event_type": "test.no_payload",
        "source": "tdd",
    })

    # Assert
    assert response.status_code == 201
    assert response.json()["payload"] == {}


def test_should_reject_non_dict_payload_with_422(client):
    """POST /events with payload that isn't a dict must return 422."""
    base = {"event_type": "test.bad_payload", "source": "tdd"}

    for bad_payload in ["not a dict", [1, 2, 3], 42]:
        response = client.post("/events", json={**base, "payload": bad_payload})
        assert response.status_code == 422, (
            f"Expected 422 for payload={bad_payload!r}, got {response.status_code}"
        )
