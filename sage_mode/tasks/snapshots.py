"""Celery tasks for agent state snapshot persistence.

This module contains Celery tasks for saving and retrieving agent state snapshots.
Snapshots enable debugging, auditing, and resuming interrupted agent work.

Use cases:
- Debugging failed tasks by examining agent state
- Auditing agent decisions for compliance
- Resuming interrupted work from last known state
"""

from sage_mode.celery_app import celery_app
from sage_mode.celery_config import TASK_MAX_RETRIES
from sage_mode.database import SessionLocal
from sage_mode.models.task_model import AgentTask, AgentSnapshot
from typing import Dict, Any, Optional


@celery_app.task(bind=True, max_retries=TASK_MAX_RETRIES)
def save_agent_snapshot(
    self,
    agent_task_id: int,
    agent_role: str,
    context_state: Dict[str, Any],
    capabilities: list,
    decisions: list,
    execution_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Save a snapshot of an agent's state during execution.

    Useful for:
    - Debugging failed tasks
    - Auditing agent decisions
    - Resuming interrupted work

    Args:
        agent_task_id: The task being executed
        agent_role: Role of the agent (e.g., "backend_developer")
        context_state: Current context/state of the agent
        capabilities: List of agent capabilities
        decisions: List of decisions made so far
        execution_metadata: Optional additional metadata

    Returns:
        Dict with snapshot_id and status
    """
    db = SessionLocal()
    try:
        # Verify task exists
        task = db.query(AgentTask).filter(AgentTask.id == agent_task_id).first()
        if not task:
            raise ValueError(f"AgentTask {agent_task_id} not found")

        # Create snapshot
        snapshot = AgentSnapshot(
            agent_task_id=agent_task_id,
            agent_role=agent_role,
            context_state=context_state,
            capabilities=capabilities,
            decisions=decisions,
            execution_metadata=execution_metadata or {}
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "snapshot_id": snapshot.id,
            "agent_task_id": agent_task_id,
            "status": "saved"
        }
    except Exception as e:
        if db:
            db.rollback()
        raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task
def get_task_snapshots(agent_task_id: int) -> list:
    """
    Retrieve all snapshots for a given agent task.

    Returns list of snapshots ordered by created_at.
    """
    db = SessionLocal()
    try:
        snapshots = db.query(AgentSnapshot).filter(
            AgentSnapshot.agent_task_id == agent_task_id
        ).order_by(AgentSnapshot.created_at).all()

        return [
            {
                "id": s.id,
                "agent_role": s.agent_role,
                "context_state": s.context_state,
                "capabilities": s.capabilities,
                "decisions": s.decisions,
                "execution_metadata": s.execution_metadata,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in snapshots
        ]
    finally:
        db.close()


@celery_app.task
def get_latest_snapshot(agent_task_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the most recent snapshot for resume purposes.
    """
    db = SessionLocal()
    try:
        snapshot = db.query(AgentSnapshot).filter(
            AgentSnapshot.agent_task_id == agent_task_id
        ).order_by(AgentSnapshot.created_at.desc()).first()

        if not snapshot:
            return None

        return {
            "id": snapshot.id,
            "agent_role": snapshot.agent_role,
            "context_state": snapshot.context_state,
            "capabilities": snapshot.capabilities,
            "decisions": snapshot.decisions,
            "execution_metadata": snapshot.execution_metadata,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None
        }
    finally:
        db.close()
