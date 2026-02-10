"""
Comprehensive tests for N8nReliabilityHook - PreToolUse hook for n8n failure detection and recovery.

Tests cover:
- Hook initialization with all dependencies
- Task registration returns monitor_id
- Successful task execution (no failure) - no recovery attempted
- Failure detection triggers recovery attempt
- Recovery succeeds on attempt 1 (Celery direct)
- Recovery succeeds on attempt 2 (API fallback)
- Recovery succeeds on attempt 3 (systemd fallback)
- Recovery fails after all attempts - still logs event
- Failure detection event logged to automation_events
- Recovery event logged with success status
- Recovery event logged with failure status
- Hook result structure completeness
- Recovery result structure completeness
- Multiple rapid task executions handled independently
- Implicit registration on_task_completed without on_task_started
- Task not in mapping (no fallback attempted)
- Empty response handling
- None status code handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
from dataclasses import dataclass

from tools_db.tools.n8n_reliability_hook import (
    N8nReliabilityHook,
    HookExecutionResult,
    RecoveryResult,
)
from tools_db.tools.n8n_monitor import (
    N8nMonitor,
    MonitorResult,
    FailureType,
)
from tools_db.tools.celery_fallback_router import (
    CeleryFallbackRouter,
    RoutingResult,
    ExecutionResult,
)
from tools_db.models import AutomationEvent


class TestN8nReliabilityHookInit:
    """Test N8nReliabilityHook initialization"""

    def test_hook_initialization_with_all_dependencies(self):
        """Test that N8nReliabilityHook initializes correctly with all dependencies"""
        mock_hub = Mock()
        mock_monitor = Mock()
        mock_router = Mock()

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        assert hook is not None
        assert hook.automation_hub == mock_hub
        assert hook.n8n_monitor == mock_monitor
        assert hook.celery_router == mock_router
        assert hook.test_mode is True
        assert hasattr(hook, 'on_task_started')
        assert hasattr(hook, 'on_task_completed')
        assert hasattr(hook, '_should_attempt_fallback')
        assert hasattr(hook, '_execute_recovery')

    def test_hook_initialization_without_hub(self):
        """Test that N8nReliabilityHook can initialize without hub (graceful fallback)"""
        mock_monitor = Mock()
        mock_router = Mock()

        hook = N8nReliabilityHook(
            automation_hub=None,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        assert hook is not None
        assert hook.automation_hub is None
        assert hook.test_mode is True


class TestTaskRegistration:
    """Test task registration and monitor_id generation"""

    def test_on_task_started_returns_monitor_id(self):
        """Test that on_task_started returns a monitor_id"""
        mock_hub = Mock()
        mock_monitor = Mock()
        mock_router = Mock()
        mock_monitor.register_task.return_value = "mon-12345"

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        monitor_id = hook.on_task_started(
            task_id="video-assembly",
            workflow_name="video-assembly",
            input_params={"video_url": "https://example.com/video.mp4"}
        )

        assert monitor_id == "mon-12345"
        mock_monitor.register_task.assert_called_once()

    def test_on_task_started_calls_monitor_register_task(self):
        """Test that on_task_started calls N8nMonitor.register_task with correct params"""
        mock_hub = Mock()
        mock_monitor = Mock()
        mock_router = Mock()
        mock_monitor.register_task.return_value = "mon-67890"

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        input_params = {"key": "value"}
        hook.on_task_started(
            task_id="draft-generator",
            workflow_name="draft-generator",
            input_params=input_params
        )

        mock_monitor.register_task.assert_called_once_with(
            task_id="draft-generator",
            workflow_name="draft-generator",
            input_params=input_params
        )


class TestSuccessfulExecutionNoRecovery:
    """Test successful task execution with no failures (no recovery triggered)"""

    def test_successful_task_execution_no_failure_detected(self):
        """Test that successful task execution does not trigger recovery"""
        mock_hub = Mock()

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=False,
            failure_type=FailureType.NO_FAILURE,
            task_id="video-assembly",
            workflow_name="video-assembly",
            status_code=200,
            duration_seconds=2.5,
            reason="Task completed successfully in 2.50s",
            event_id=None
        )
        mock_monitor.report_result.return_value = monitor_result

        mock_router = Mock()

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=200,
            response="success",
            duration_seconds=2.5
        )

        # Verify no recovery attempted
        mock_router.route_failure.assert_not_called()

        # Verify result structure
        assert result.hook_executed is True
        assert result.task_id == "video-assembly"
        assert result.failure_detected is False
        assert result.recovery_attempted is False
        assert result.recovery_successful is False
        assert result.failure_type is None


class TestFailureDetectionAndRecovery:
    """Test failure detection and recovery attempts"""

    def test_failure_detection_triggers_recovery_attempt(self):
        """Test that failure detection triggers recovery attempt"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.AUTH_FAILURE,
            task_id="draft-generator",
            workflow_name="draft-generator",
            status_code=403,
            duration_seconds=1.2,
            reason="Authentication failure (403 Unauthorized)",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        execution_result = ExecutionResult(
            success=True,
            attempt_method="celery_direct",
            attempt_number=1,
            execution_time_seconds=0.8,
            result_summary="Celery task executed successfully"
        )
        routing_result = RoutingResult(
            routed=True,
            celery_task_name="generate_draft",
            execution_result=execution_result,
            reason="Successfully routed to celery_direct",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=403,
            response="Unauthorized",
            duration_seconds=1.2
        )

        # Verify recovery was attempted
        mock_router.route_failure.assert_called_once()

        # Verify result structure
        assert result.failure_detected is True
        assert result.recovery_attempted is True
        assert result.recovery_successful is True
        assert result.failure_type == "403_unauthorized"
        assert result.recovery_method == "celery_direct"

    def test_recovery_succeeds_on_attempt_1_celery_direct(self):
        """Test recovery succeeds on first attempt (Celery direct)"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2  # Recovery event ID

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.GATEWAY_TIMEOUT,
            task_id="kb-indexing",
            workflow_name="kb-indexing",
            status_code=504,
            duration_seconds=31.5,
            reason="Task execution timeout - exceeded 30s threshold",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        execution_result = ExecutionResult(
            success=True,
            attempt_method="celery_direct",
            attempt_number=1,
            execution_time_seconds=0.5,
            result_summary="Task executed successfully"
        )
        routing_result = RoutingResult(
            routed=True,
            celery_task_name="index_kb",
            execution_result=execution_result,
            reason="Successfully routed to celery_direct",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=504,
            response="Service Unavailable",
            duration_seconds=31.5
        )

        assert result.recovery_successful is True
        assert result.recovery_method == "celery_direct"
        assert result.failure_type == "504_gateway_timeout"

    def test_recovery_succeeds_on_attempt_2_api_fallback(self):
        """Test recovery succeeds on second attempt (API fallback)"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.WEBHOOK_FAILURE,
            task_id="content-idea-capture",
            workflow_name="content-idea-capture",
            status_code=None,
            duration_seconds=5.0,
            reason="Webhook error - failed to reach external service",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        execution_result = ExecutionResult(
            success=True,
            attempt_method="api_fallback",
            attempt_number=2,
            execution_time_seconds=2.1,
            result_summary="API fallback successful"
        )
        routing_result = RoutingResult(
            routed=True,
            celery_task_name="capture_idea",
            execution_result=execution_result,
            reason="Successfully routed to api_fallback",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=None,
            response="webhook error",
            duration_seconds=5.0
        )

        assert result.recovery_successful is True
        assert result.recovery_method == "api_fallback"
        assert result.failure_type == "webhook_error"

    def test_recovery_succeeds_on_attempt_3_systemd_fallback(self):
        """Test recovery succeeds on third attempt (systemd fallback)"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.UNKNOWN_ERROR,
            task_id="video-assembly",
            workflow_name="video-assembly",
            status_code=500,
            duration_seconds=10.0,
            reason="Unknown error occurred during task execution",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        execution_result = ExecutionResult(
            success=True,
            attempt_method="systemd_fallback",
            attempt_number=3,
            execution_time_seconds=8.3,
            result_summary="Systemd service executed successfully"
        )
        routing_result = RoutingResult(
            routed=True,
            celery_task_name="process_video",
            execution_result=execution_result,
            reason="Successfully routed to systemd_fallback",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=500,
            response="error",
            duration_seconds=10.0
        )

        assert result.recovery_successful is True
        assert result.recovery_method == "systemd_fallback"
        assert result.failure_type == "unknown_error"

    def test_recovery_fails_after_all_attempts_still_logs_event(self):
        """Test recovery fails after all attempts but event still logged"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.AUTH_FAILURE,
            task_id="draft-generator",
            workflow_name="draft-generator",
            status_code=403,
            duration_seconds=1.5,
            reason="Authentication failure (403 Unauthorized)",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        execution_result = ExecutionResult(
            success=False,
            attempt_method="systemd_fallback",
            attempt_number=3,
            execution_time_seconds=30.2,
            result_summary="",
            error_message="All fallback attempts failed"
        )
        routing_result = RoutingResult(
            routed=False,
            celery_task_name="generate_draft",
            execution_result=execution_result,
            reason="All fallback attempts failed",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=403,
            response="Unauthorized",
            duration_seconds=1.5
        )

        # Verify recovery event was logged by hook
        mock_hub.store_event.assert_called_once()

        # Verify recovery event has failed status
        recovery_event = mock_hub.store_event.call_args_list[0][0][0]
        assert recovery_event.event_type == "n8n_recovery_attempted"
        assert recovery_event.status == "failed"
        assert recovery_event.evidence["recovery_successful"] is False

        # Verify result indicates failure
        assert result.failure_detected is True
        assert result.recovery_attempted is True
        assert result.recovery_successful is False


class TestEventLogging:
    """Test automation event logging"""

    def test_failure_detection_event_logged(self):
        """Test that failure detection event is logged to automation_events"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2  # Recovery event ID

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.AUTH_FAILURE,
            task_id="test-task",
            workflow_name="test-workflow",
            status_code=403,
            duration_seconds=1.0,
            reason="Authentication failure",
            event_id=1  # Monitor logged failure detection event
        )
        mock_monitor.report_result.return_value = monitor_result

        routing_result = RoutingResult(
            routed=True,
            celery_task_name="test_task",
            execution_result=ExecutionResult(
                success=True,
                attempt_method="celery_direct",
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary="Success"
            ),
            reason="Routed successfully",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=403,
            response="Unauthorized",
            duration_seconds=1.0
        )

        # Verify recovery event was logged by hub
        mock_hub.store_event.assert_called_once()

        # Get the recovery event call
        recovery_event = mock_hub.store_event.call_args_list[0][0][0]
        assert recovery_event.event_type == "n8n_recovery_attempted"
        assert recovery_event.status == "success"
        assert recovery_event.evidence["task_id"] == "test-task"

        # Verify both event IDs are in result (1 from monitor, 2 from hub)
        assert 1 in result.event_ids  # Monitor event
        assert 2 in result.event_ids  # Recovery event

    def test_recovery_event_logged_with_success_status(self):
        """Test that recovery event is logged with success status"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.GATEWAY_TIMEOUT,
            task_id="test-task",
            workflow_name="test-workflow",
            status_code=504,
            duration_seconds=35.0,
            reason="Gateway timeout",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        routing_result = RoutingResult(
            routed=True,
            celery_task_name="test_task",
            execution_result=ExecutionResult(
                success=True,
                attempt_method="celery_direct",
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary="Success"
            ),
            reason="Routed successfully",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=504,
            response="Service Unavailable",
            duration_seconds=35.0
        )

        # Get the recovery event call
        recovery_event = mock_hub.store_event.call_args_list[0][0][0]
        assert recovery_event.event_type == "n8n_recovery_attempted"
        assert recovery_event.status == "success"
        assert recovery_event.evidence["recovery_successful"] is True
        assert recovery_event.evidence["recovery_method"] == "celery_direct"

    def test_recovery_event_logged_with_failure_status(self):
        """Test that recovery event is logged with failure status when all attempts fail"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.UNKNOWN_ERROR,
            task_id="test-task",
            workflow_name="test-workflow",
            status_code=500,
            duration_seconds=5.0,
            reason="Unknown error",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        routing_result = RoutingResult(
            routed=False,
            celery_task_name="test_task",
            execution_result=ExecutionResult(
                success=False,
                attempt_method="systemd_fallback",
                attempt_number=3,
                execution_time_seconds=30.5,
                result_summary="",
                error_message="All attempts failed"
            ),
            reason="All fallback attempts failed",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=500,
            response="error",
            duration_seconds=5.0
        )

        # Get the recovery event call
        recovery_event = mock_hub.store_event.call_args_list[0][0][0]
        assert recovery_event.event_type == "n8n_recovery_attempted"
        assert recovery_event.status == "failed"
        assert recovery_event.evidence["recovery_successful"] is False


class TestResultStructures:
    """Test result structure completeness"""

    def test_hook_execution_result_structure_completeness(self):
        """Test that HookExecutionResult has all required fields"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.AUTH_FAILURE,
            task_id="test-task",
            workflow_name="test-workflow",
            status_code=403,
            duration_seconds=1.0,
            reason="Auth failure",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        routing_result = RoutingResult(
            routed=True,
            celery_task_name="test_task",
            execution_result=ExecutionResult(
                success=True,
                attempt_method="celery_direct",
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary="Success"
            ),
            reason="Routed",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=403,
            response="Unauthorized",
            duration_seconds=1.0
        )

        # Verify all required fields exist
        assert hasattr(result, 'hook_executed')
        assert hasattr(result, 'task_id')
        assert hasattr(result, 'failure_detected')
        assert hasattr(result, 'recovery_attempted')
        assert hasattr(result, 'recovery_successful')
        assert hasattr(result, 'failure_type')
        assert hasattr(result, 'recovery_method')
        assert hasattr(result, 'reason')
        assert hasattr(result, 'event_ids')

        assert result.hook_executed is True
        assert result.task_id == "test-task"
        assert result.failure_detected is True
        assert result.recovery_attempted is True
        assert isinstance(result.event_ids, list)
        assert len(result.event_ids) > 0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_implicit_registration_on_task_completed_without_on_task_started(self):
        """Test implicit registration when on_task_completed called without on_task_started"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=False,
            failure_type=FailureType.NO_FAILURE,
            task_id="implicit-task",
            workflow_name="implicit-workflow",
            status_code=200,
            duration_seconds=2.0,
            reason="Success",
            event_id=None
        )
        mock_monitor.report_result.return_value = monitor_result

        mock_router = Mock()

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        # Call on_task_completed without calling on_task_started
        result = hook.on_task_completed(
            monitor_id="mon-unknown",
            status_code=200,
            response="success",
            duration_seconds=2.0
        )

        # Verify N8nMonitor.report_result was still called
        mock_monitor.report_result.assert_called_once()

        # Verify result is valid
        assert result.hook_executed is True

    def test_task_not_in_mapping_no_fallback_attempted(self):
        """Test that task not in N8N_TO_CELERY_MAPPING is not routed"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.AUTH_FAILURE,
            task_id="unknown-task",
            workflow_name="unmapped-workflow",
            status_code=403,
            duration_seconds=1.0,
            reason="Auth failure",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        routing_result = RoutingResult(
            routed=False,
            celery_task_name=None,
            execution_result=None,
            reason='No Celery mapping available for workflow "unmapped-workflow"',
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=403,
            response="Unauthorized",
            duration_seconds=1.0
        )

        # Verify router was called but task not routed
        mock_router.route_failure.assert_called_once()
        assert result.recovery_attempted is True
        assert result.recovery_successful is False

    def test_empty_response_handling(self):
        """Test that empty response is handled gracefully"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.UNKNOWN_ERROR,
            task_id="test-task",
            workflow_name="test-workflow",
            status_code=500,
            duration_seconds=1.0,
            reason="Unknown error",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        routing_result = RoutingResult(
            routed=True,
            celery_task_name="test_task",
            execution_result=ExecutionResult(
                success=True,
                attempt_method="celery_direct",
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary="Success"
            ),
            reason="Routed",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        # Call with empty response
        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=500,
            response="",
            duration_seconds=1.0
        )

        # Verify report_result was called with empty response
        mock_monitor.report_result.assert_called_once()
        assert result.hook_executed is True

    def test_none_status_code_handling(self):
        """Test that None status code is handled gracefully"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2

        mock_monitor = Mock()
        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.WEBHOOK_FAILURE,
            task_id="test-task",
            workflow_name="test-workflow",
            status_code=None,
            duration_seconds=5.0,
            reason="Webhook error",
            event_id=1
        )
        mock_monitor.report_result.return_value = monitor_result

        routing_result = RoutingResult(
            routed=True,
            celery_task_name="test_task",
            execution_result=ExecutionResult(
                success=True,
                attempt_method="api_fallback",
                attempt_number=2,
                execution_time_seconds=2.5,
                result_summary="Success"
            ),
            reason="Routed",
            event_id=2
        )
        mock_router = Mock()
        mock_router.route_failure.return_value = routing_result

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        # Call with None status code
        result = hook.on_task_completed(
            monitor_id="mon-12345",
            status_code=None,
            response="webhook error",
            duration_seconds=5.0
        )

        # Verify report_result was called with None status code
        call_kwargs = mock_monitor.report_result.call_args[1]
        assert call_kwargs['status_code'] is None

        assert result.hook_executed is True


class TestMultipleConcurrentExecutions:
    """Test handling of multiple rapid task executions"""

    def test_multiple_rapid_task_executions_handled_independently(self):
        """Test that multiple rapid executions are tracked independently"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1

        mock_monitor = Mock()
        mock_router = Mock()

        hook = N8nReliabilityHook(
            automation_hub=mock_hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        # Register multiple tasks
        mock_monitor.register_task.side_effect = ["mon-1", "mon-2", "mon-3"]
        id1 = hook.on_task_started("task1", "workflow1", {})
        id2 = hook.on_task_started("task2", "workflow2", {})
        id3 = hook.on_task_started("task3", "workflow3", {})

        assert id1 == "mon-1"
        assert id2 == "mon-2"
        assert id3 == "mon-3"
        assert mock_monitor.register_task.call_count == 3

        # Complete tasks with different outcomes
        monitor_result1 = MonitorResult(
            failure_detected=False,
            failure_type=FailureType.NO_FAILURE,
            task_id="task1",
            workflow_name="workflow1",
            status_code=200,
            duration_seconds=2.0,
            reason="Success",
            event_id=None
        )

        monitor_result2 = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.AUTH_FAILURE,
            task_id="task2",
            workflow_name="workflow2",
            status_code=403,
            duration_seconds=1.0,
            reason="Auth failure",
            event_id=1
        )

        monitor_result3 = MonitorResult(
            failure_detected=False,
            failure_type=FailureType.NO_FAILURE,
            task_id="task3",
            workflow_name="workflow3",
            status_code=200,
            duration_seconds=3.0,
            reason="Success",
            event_id=None
        )

        mock_monitor.report_result.side_effect = [
            monitor_result1,
            monitor_result2,
            monitor_result3
        ]

        routing_result2 = RoutingResult(
            routed=True,
            celery_task_name="task2",
            execution_result=ExecutionResult(
                success=True,
                attempt_method="celery_direct",
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary="Success"
            ),
            reason="Routed",
            event_id=2
        )
        mock_router.route_failure.return_value = routing_result2

        result1 = hook.on_task_completed("mon-1", 200, "success", 2.0)
        result2 = hook.on_task_completed("mon-2", 403, "Unauthorized", 1.0)
        result3 = hook.on_task_completed("mon-3", 200, "success", 3.0)

        # Verify each was handled independently
        assert result1.failure_detected is False
        assert result2.failure_detected is True
        assert result3.failure_detected is False

        assert result1.recovery_attempted is False
        assert result2.recovery_attempted is True
        assert result3.recovery_attempted is False

        assert mock_monitor.report_result.call_count == 3
        assert mock_router.route_failure.call_count == 1  # Only for task2
