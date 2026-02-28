"""Regression tests for GET /events query param filters."""


def _seed_event(client, event_type: str, source: str):
    """Helper — insert a test event and return the response JSON."""
    return client.post("/events", json={
        "event_type": event_type,
        "source": source,
        "payload": {"test": True},
    }).json()


def test_filter_by_source(client):
    _seed_event(client, "test.alpha", "dojo")
    _seed_event(client, "test.beta", "sharingan")

    resp = client.get("/events", params={"source": "dojo", "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert all(e["source"] == "dojo" for e in data)


def test_filter_by_event_type(client):
    _seed_event(client, "test.specific_type", "tdd")

    resp = client.get("/events", params={"event_type": "test.specific_type"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(e["event_type"] == "test.specific_type" for e in data)


def test_filter_by_event_type_prefix(client):
    _seed_event(client, "test.prefix.one", "tdd")
    _seed_event(client, "test.prefix.two", "tdd")
    _seed_event(client, "other.unrelated", "tdd")

    resp = client.get("/events", params={"event_type_prefix": "test.prefix."})
    assert resp.status_code == 200
    data = resp.json()
    assert all(e["event_type"].startswith("test.prefix.") for e in data)


def test_limit_param(client):
    for i in range(5):
        _seed_event(client, f"test.limit.{i}", "tdd")

    resp = client.get("/events", params={"limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


def test_combined_filters(client):
    _seed_event(client, "test.combo", "dojo")
    _seed_event(client, "test.combo", "sharingan")

    resp = client.get("/events", params={
        "event_type": "test.combo",
        "source": "dojo",
        "limit": 10,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert all(e["event_type"] == "test.combo" and e["source"] == "dojo" for e in data)


def test_no_filters_returns_events(client):
    _seed_event(client, "test.nofilter", "tdd")

    resp = client.get("/events")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1
