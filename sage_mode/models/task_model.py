from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.sql import func
from sage_mode.database import Base

class AgentTask(Base):
    __tablename__ = 'agent_tasks'
    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey('execution_sessions.id'), nullable=False)
    agent_role = Column(String(100), nullable=False)
    task_description = Column(Text, nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(50), default='pending')
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    celery_task_id = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<AgentTask {self.agent_role}: {self.status}>"

class TaskDecision(Base):
    __tablename__ = 'task_decisions'
    id = Column(BigInteger, primary_key=True)
    agent_task_id = Column(BigInteger, ForeignKey('agent_tasks.id'), nullable=False)
    decision_text = Column(Text, nullable=False)
    rationale = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<TaskDecision {self.decision_text[:30]}>"

class AgentSnapshot(Base):
    __tablename__ = 'agent_snapshots'
    id = Column(BigInteger, primary_key=True)
    agent_task_id = Column(BigInteger, ForeignKey('agent_tasks.id'), nullable=False)
    agent_role = Column(String(100), nullable=False)
    context_state = Column(JSON, nullable=False)
    capabilities = Column(JSON, nullable=False)
    decisions = Column(JSON, nullable=False)
    execution_metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<AgentSnapshot {self.agent_role}>"
