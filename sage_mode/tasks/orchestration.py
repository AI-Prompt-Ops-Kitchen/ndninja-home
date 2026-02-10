"""Celery tasks for task chain orchestration.

This module contains Celery tasks for coordinating multi-agent execution
using Celery's chain and group primitives. Tasks are routed to the
"orchestration" queue per celery_config.py.

Supports:
- Parallel execution using group() for independent tasks
- Sequential execution using chain() for dependent tasks
- Session completion callbacks for status updates
"""

from sage_mode.celery_app import celery_app
from sage_mode.celery_config import TASK_MAX_RETRIES
from sage_mode.database import SessionLocal
from sage_mode.models.session_model import ExecutionSession
from sage_mode.models.task_model import AgentTask
from sage_mode.tasks.agent_tasks import execute_agent_task
from celery import chain, group
from datetime import datetime, timezone
from typing import List, Dict, Any


@celery_app.task(bind=True, max_retries=TASK_MAX_RETRIES)
def wrap_result_in_list(self, result: Dict) -> List[Dict]:
    """
    Wrapper task to convert a single result into a list.

    Used in sequential chains where each task passes its result to the next,
    but complete_session expects a list of results.

    Args:
        result: Single task result dict

    Returns:
        List containing the single result
    """
    return [result]


@celery_app.task(bind=True, max_retries=TASK_MAX_RETRIES)
def start_session_execution(self, execution_session_id: int, task_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Start execution of a session with multiple agent tasks.

    Creates AgentTask records and kicks off execution.
    Uses group() for parallel execution of independent tasks.

    Args:
        execution_session_id: The session to execute
        task_specs: List of {agent_role, task_description, input_data}

    Returns:
        Dict with session_id and created task IDs
    """
    db = SessionLocal()
    try:
        session = db.query(ExecutionSession).filter(
            ExecutionSession.id == execution_session_id
        ).first()
        if not session:
            raise ValueError(f"Session {execution_session_id} not found")

        # Create AgentTask records
        task_ids = []
        for spec in task_specs:
            agent_task = AgentTask(
                session_id=execution_session_id,
                agent_role=spec["agent_role"],
                task_description=spec["task_description"],
                input_data=spec.get("input_data"),
                status="pending"
            )
            db.add(agent_task)
            db.flush()
            task_ids.append(agent_task.id)

        db.commit()

        # Create group for parallel execution
        task_group = group(execute_agent_task.s(task_id) for task_id in task_ids)

        # Chain: parallel execution -> completion callback
        workflow = chain(
            task_group,
            complete_session.s(execution_session_id)
        )

        # Start the workflow asynchronously
        result = workflow.apply_async()

        # Store the chain ID in session
        session.celery_chain_id = result.id
        db.commit()

        return {
            "session_id": execution_session_id,
            "task_ids": task_ids,
            "chain_id": result.id
        }

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=TASK_MAX_RETRIES)
def complete_session(self, task_results: List[Dict], execution_session_id: int) -> Dict[str, Any]:
    """
    Callback task executed after all agent tasks complete.

    Updates session status and calculates total duration.

    Args:
        task_results: List of results from completed agent tasks
        execution_session_id: The session to mark as completed

    Returns:
        Dict with session completion details
    """
    db = SessionLocal()
    try:
        session = db.query(ExecutionSession).filter(
            ExecutionSession.id == execution_session_id
        ).first()
        if session:
            session.status = "completed"
            session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if session.started_at:
                session.duration_seconds = int(
                    (session.ended_at - session.started_at).total_seconds()
                )
            db.commit()

        return {
            "session_id": execution_session_id,
            "status": "completed",
            "task_count": len(task_results),
            "results": task_results
        }
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=TASK_MAX_RETRIES)
def execute_sequential_tasks(self, execution_session_id: int, task_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute tasks sequentially using a Celery chain.

    Useful when tasks have dependencies on previous task outputs.
    Each task executes only after the previous one completes.

    Args:
        execution_session_id: The session to execute
        task_specs: List of {agent_role, task_description, input_data}

    Returns:
        Dict with session_id, task IDs, and chain ID
    """
    db = SessionLocal()
    try:
        # Validate session exists
        session = db.query(ExecutionSession).filter(
            ExecutionSession.id == execution_session_id
        ).first()
        if not session:
            raise ValueError(f"Session {execution_session_id} not found")

        # Create AgentTask records
        task_ids = []
        for spec in task_specs:
            agent_task = AgentTask(
                session_id=execution_session_id,
                agent_role=spec["agent_role"],
                task_description=spec["task_description"],
                input_data=spec.get("input_data"),
                status="pending"
            )
            db.add(agent_task)
            db.flush()
            task_ids.append(agent_task.id)

        db.commit()

        # Create chain for sequential execution
        # Wrap final result in list since complete_session expects List[Dict]
        workflow = chain(
            *[execute_agent_task.s(task_id) for task_id in task_ids],
            wrap_result_in_list.s(),
            complete_session.s(execution_session_id)
        )

        result = workflow.apply_async()

        # Store the chain ID in session
        session.celery_chain_id = result.id
        db.commit()

        return {
            "session_id": execution_session_id,
            "task_ids": task_ids,
            "chain_id": result.id
        }
    finally:
        db.close()
