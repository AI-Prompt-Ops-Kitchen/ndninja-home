"""Content Worker — standalone Celery app for video generation.
Connects to Sage Mode's Redis broker."""
import os
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", broker_url)

app = Celery("content_worker", broker=broker_url, backend=result_backend, include=["tasks"])

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=1800,      # 30 min hard limit
    task_soft_time_limit=1500,  # 25 min soft limit
    task_routes={
        "content.*": {"queue": "content"},
    },
)
