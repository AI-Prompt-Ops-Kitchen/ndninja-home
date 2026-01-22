"""Celery configuration settings for Sage Mode.

This module contains all Celery configuration settings for the Sage Mode
agent framework. Settings are organized by category for clarity.
"""

import os

# Broker settings (Redis)
broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Task settings
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 1  # For fairness in task distribution
task_acks_late = True  # Acknowledge after task completes (prevents loss)
task_reject_on_worker_lost = True  # Requeue if worker dies

# Result settings
result_expires = 3600  # Results expire after 1 hour

# Task routing (for future use with dedicated queues)
task_routes = {
    "sage_mode.tasks.agent_tasks.*": {"queue": "agents"},
    "sage_mode.tasks.orchestration.*": {"queue": "orchestration"},
}

# Retry settings
task_default_retry_delay = 30  # 30 seconds

# Custom constant for use in task definitions (e.g., @celery_app.task(max_retries=TASK_MAX_RETRIES))
# Note: This is NOT a Celery config option; Celery uses max_retries at the task decorator level
TASK_MAX_RETRIES = 3
