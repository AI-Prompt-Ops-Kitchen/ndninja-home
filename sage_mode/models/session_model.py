from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func
from sage_mode.database import Base

class ExecutionSession(Base):
    __tablename__ = 'execution_sessions'
    id = Column(BigInteger, primary_key=True)
    team_id = Column(BigInteger, ForeignKey('teams.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    feature_name = Column(String(255))
    status = Column(String(50), default='active')
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)
    celery_chain_id = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<ExecutionSession {self.feature_name} ({self.status})>"

class SessionDecision(Base):
    __tablename__ = 'session_decisions'
    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey('execution_sessions.id'), nullable=False)
    decision_text = Column(Text, nullable=False)
    category = Column(String(100))
    confidence = Column(String(50), default='high')
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<SessionDecision {self.decision_text[:30]}>"
