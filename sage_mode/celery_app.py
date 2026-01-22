"""Celery application configuration for Sage Mode.

This module creates and configures the Celery app instance used for
distributed task processing across the Sage Mode agent framework.
"""

from celery import Celery

# Create Celery app
celery_app = Celery("sage_mode")

# Load configuration from celery_config.py
celery_app.config_from_object("sage_mode.celery_config")

# Auto-discover tasks in sage_mode.tasks package
celery_app.autodiscover_tasks(["sage_mode.tasks"])
