"""Task package for Celery tasks.

This package contains all Celery tasks for the Sage Mode agent framework.
Tasks are organized by domain:

- agent_tasks.py (Task 13): Tasks for individual agent execution
- orchestration.py (Task 14): Tasks for multi-agent orchestration
- snapshots.py (Task 15): Tasks for state snapshot management
- sharingan_tasks.py: Autonomous learning pipeline (Beat-scheduled)
"""

# Ensure all task modules are imported so Celery registers them
from sage_mode.tasks import agent_tasks, orchestration, snapshots, sharingan_tasks  # noqa: F401
