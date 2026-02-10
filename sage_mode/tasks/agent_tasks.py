"""Celery tasks for agent execution.

This module contains Celery tasks for executing individual agent tasks
as part of the Sage Mode agent framework. Tasks are routed to the
"agents" queue per celery_config.py.
"""

from sage_mode.celery_app import celery_app
from sage_mode.celery_config import TASK_MAX_RETRIES
from sage_mode.database import SessionLocal
from sage_mode.models.task_model import AgentTask, TaskDecision
from sage_mode.agents.base_agent import BaseAgent
from sage_mode.agents.frontend_agent import FrontendAgent
from sage_mode.agents.backend_agent import BackendAgent
from sage_mode.agents.architect_agent import ArchitectAgent
from sage_mode.agents.ui_ux_designer_agent import UIUXDesignerAgent
from sage_mode.agents.dba_agent import DBAAgent
from sage_mode.agents.it_admin_agent import ITAdminAgent
from sage_mode.agents.security_specialist_agent import SecuritySpecialistAgent
from datetime import datetime, timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Agent registry - maps role names to agent classes
AGENT_REGISTRY: Dict[str, type] = {
    "frontend_developer": FrontendAgent,
    "backend_developer": BackendAgent,
    "software_architect": ArchitectAgent,
    "ui_ux_designer": UIUXDesignerAgent,
    "database_administrator": DBAAgent,
    "it_administrator": ITAdminAgent,
    "security_specialist": SecuritySpecialistAgent,
}


@celery_app.task(bind=True, max_retries=TASK_MAX_RETRIES)
def execute_agent_task(self, agent_task_id: int) -> Dict[str, Any]:
    """
    Execute a single agent task.

    1. Load AgentTask from database
    2. Instantiate the appropriate agent
    3. Execute the task
    4. Store results and decisions
    5. Update task status

    Args:
        agent_task_id: The ID of the AgentTask to execute

    Returns:
        Dict containing task_id, status, and result

    Raises:
        ValueError: If task not found or unknown agent role
        Retries with exponential backoff on other failures
    """
    db = SessionLocal()
    try:
        # Load task
        task = db.query(AgentTask).filter(AgentTask.id == agent_task_id).first()
        if not task:
            raise ValueError(f"AgentTask {agent_task_id} not found")

        # Update status to running
        task.status = "running"
        task.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        task.celery_task_id = self.request.id
        db.commit()

        # Get agent class
        agent_class = AGENT_REGISTRY.get(task.agent_role)
        if not agent_class:
            raise ValueError(f"Unknown agent role: {task.agent_role}")

        # Instantiate and execute
        agent = agent_class()
        if task.input_data:
            agent.set_context(task.input_data)

        result = agent.execute_task(task.task_description)

        # Store result
        task.output_data = result
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if task.started_at:
            task.duration_seconds = int((task.completed_at - task.started_at).total_seconds())

        # Store any decisions the agent made
        if hasattr(agent, 'decisions') and agent.decisions:
            for decision in agent.decisions:
                # Handle both DecisionJournal objects and dict decisions
                if hasattr(decision, 'title'):
                    # DecisionJournal object
                    task_decision = TaskDecision(
                        agent_task_id=task.id,
                        decision_text=decision.title,
                        rationale=decision.description,
                        category=decision.category
                    )
                else:
                    # Dict decision
                    task_decision = TaskDecision(
                        agent_task_id=task.id,
                        decision_text=decision.get('text', str(decision)),
                        rationale=decision.get('rationale'),
                        category=decision.get('category')
                    )
                db.add(task_decision)

        db.commit()

        return {
            "task_id": agent_task_id,
            "status": "completed",
            "result": result
        }

    except Exception as e:
        logger.error(f"Task {agent_task_id} failed: {e}")
        if db:
            task = db.query(AgentTask).filter(AgentTask.id == agent_task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.retry_count = self.request.retries
                db.commit()

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))

    finally:
        db.close()
