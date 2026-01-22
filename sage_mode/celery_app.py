import os
from celery import Celery

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379")
celery_app = Celery("sage_mode", broker=broker_url, backend=broker_url)
celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")
