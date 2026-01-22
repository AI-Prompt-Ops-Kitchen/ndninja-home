#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from sage_mode.database import engine, Base
from sage_mode.models import (
    User, Team, TeamMembership,
    ExecutionSession, SessionDecision,
    AgentTask, TaskDecision, AgentSnapshot
)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized with 8 tables:")
    print("   • users")
    print("   • teams")
    print("   • team_memberships")
    print("   • execution_sessions")
    print("   • session_decisions")
    print("   • agent_tasks")
    print("   • task_decisions")
    print("   • agent_snapshots")

if __name__ == "__main__":
    init_db()
