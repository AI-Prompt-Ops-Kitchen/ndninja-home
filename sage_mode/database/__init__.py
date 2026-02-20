import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .decision_journal import DecisionJournalDB

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sage_user:ZQLY4SwZJTBI1fRxGatVp5hEhdXjVN3f@localhost/sage_mode"
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = ["DecisionJournalDB", "engine", "Base", "SessionLocal", "get_db"]
