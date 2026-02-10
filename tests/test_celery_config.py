"""Tests for Celery configuration and app setup.

This module tests the Celery application configuration for Sage Mode,
ensuring the app is properly configured with broker, result backend,
serialization settings, and task routing.
"""

import pytest


class TestCeleryAppCreated:
    """Test that the Celery app exists and is configured."""

    def test_celery_app_exists(self):
        """Verify Celery app instance is created."""
        from sage_mode.celery_app import celery_app

        assert celery_app is not None

    def test_celery_app_name(self):
        """Verify Celery app has correct name."""
        from sage_mode.celery_app import celery_app

        assert celery_app.main == "sage_mode"


class TestCeleryBrokerConfigured:
    """Test that broker URL is properly configured."""

    def test_broker_url_set(self):
        """Verify broker URL is configured."""
        from sage_mode.celery_app import celery_app

        broker_url = celery_app.conf.broker_url
        assert broker_url is not None
        assert "redis://" in broker_url

    def test_broker_url_default(self):
        """Verify default broker URL is localhost Redis."""
        from sage_mode import celery_config

        # Default should be localhost Redis on db 0
        assert "localhost:6379" in celery_config.broker_url
        assert "/0" in celery_config.broker_url


class TestCeleryResultBackendConfigured:
    """Test that result backend is properly configured."""

    def test_result_backend_set(self):
        """Verify result backend is configured."""
        from sage_mode.celery_app import celery_app

        result_backend = celery_app.conf.result_backend
        assert result_backend is not None
        assert "redis://" in result_backend

    def test_result_expires_configured(self):
        """Verify result expiration is set."""
        from sage_mode.celery_app import celery_app

        # Results should expire after 1 hour (3600 seconds)
        assert celery_app.conf.result_expires == 3600


class TestCeleryTaskSerialization:
    """Test that JSON serialization is configured."""

    def test_task_serializer_json(self):
        """Verify task serializer is JSON."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"

    def test_result_serializer_json(self):
        """Verify result serializer is JSON."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.result_serializer == "json"

    def test_accept_content_json(self):
        """Verify accept content includes JSON."""
        from sage_mode.celery_app import celery_app

        assert "json" in celery_app.conf.accept_content


class TestCeleryTaskRoutesDefined:
    """Test that task routes are properly defined."""

    def test_task_routes_exist(self):
        """Verify task routes are configured."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.task_routes is not None

    def test_agent_tasks_route(self):
        """Verify agent tasks route to agents queue."""
        from sage_mode.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert "sage_mode.tasks.agent_tasks.*" in routes
        assert routes["sage_mode.tasks.agent_tasks.*"]["queue"] == "agents"

    def test_orchestration_route(self):
        """Verify orchestration tasks route to orchestration queue."""
        from sage_mode.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert "sage_mode.tasks.orchestration.*" in routes
        assert routes["sage_mode.tasks.orchestration.*"]["queue"] == "orchestration"


class TestCeleryWorkerSettings:
    """Test worker reliability settings."""

    def test_prefetch_multiplier(self):
        """Verify prefetch multiplier is 1 for fair distribution."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_acks_late_enabled(self):
        """Verify task_acks_late is enabled for reliability."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.task_acks_late is True

    def test_reject_on_worker_lost(self):
        """Verify tasks are requeued if worker dies."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.task_reject_on_worker_lost is True


class TestCeleryTimezoneSettings:
    """Test timezone configuration."""

    def test_timezone_utc(self):
        """Verify timezone is UTC."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.timezone == "UTC"

    def test_enable_utc(self):
        """Verify UTC is enabled."""
        from sage_mode.celery_app import celery_app

        assert celery_app.conf.enable_utc is True


class TestCeleryRetrySettings:
    """Test retry configuration."""

    def test_default_retry_delay(self):
        """Verify default retry delay is 30 seconds."""
        from sage_mode import celery_config

        assert celery_config.task_default_retry_delay == 30

    def test_max_retries(self):
        """Verify TASK_MAX_RETRIES constant is 3."""
        from sage_mode import celery_config

        assert celery_config.TASK_MAX_RETRIES == 3
