import pytest
from sage_mode.database import engine, Base
from sqlalchemy import inspect

def test_database_connection():
    """Verify database connection works"""
    with engine.connect() as conn:
        assert conn is not None

def test_database_url_configured():
    """Verify database URL is configured"""
    assert engine.url is not None
