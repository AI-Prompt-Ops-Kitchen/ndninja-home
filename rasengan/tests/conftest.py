import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Sync test client for the Rasengan FastAPI app."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
