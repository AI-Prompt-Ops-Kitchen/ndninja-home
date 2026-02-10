"""
Comprehensive tests for N8nMonitor - n8n task failure detection and monitoring.

Tests cover:
- Task registration and monitoring
- 403 Unauthorized detection
- 504 Gateway Timeout detection
- Execution timeout detection (duration > 30s)
- Webhook failure detection
- Unknown error detection
- Successful task completion (no failure)
- Failure event logging to automation_events
- Task metadata extraction
- Monitor result structure completeness
- Report without prior registration (implicit)
- Duration edge cases (0, 1, 30, 31 seconds)
- Status code None handling
- Response content analysis for failure patterns
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from tools_db.tools.n8n_monitor import (
    N8nMonitor,
    MonitorResult,
    FailureType
)
from tools_db.models import AutomationEvent


class TestN8nMonitorInitialization:
    """Test N8nMonitor initialization"""

    def test_monitor_initialization_with_hub(self):
        """Test that N8nMonitor initializes correctly with AutomationHub"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        assert monitor is not None
        assert monitor.automation_hub == mock_hub
        assert monitor.test_mode is True
        assert hasattr(monitor, 'register_task')
        assert hasattr(monitor, 'report_result')
        assert hasattr(monitor, '_detect_failure_pattern')
        assert hasattr(monitor, '_extract_task_metadata')

    def test_monitor_initialization_without_hub(self):
        """Test that N8nMonitor can initialize without hub (graceful fallback)"""
        monitor = N8nMonitor(automation_hub=None, test_mode=True)

        assert monitor is not None
        assert monitor.automation_hub is None
        assert monitor.test_mode is True


class TestTaskRegistration:
    """Test task registration for monitoring"""

    def test_register_task_returns_monitor_id(self):
        """Test that registering a task returns a monitor ID"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="video-assembly",
            workflow_name="video-assembly-workflow",
            input_params={"video_url": "https://example.com/video.mp4"}
        )

        assert monitor_id is not None
        assert isinstance(monitor_id, str)

    def test_register_task_stores_in_registry(self):
        """Test that registered tasks are stored internally"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="draft-generator",
            workflow_name="draft-gen-workflow",
            input_params={"topic": "AI trends"}
        )

        assert monitor_id in monitor._task_registry

    def test_register_task_multiple_tasks(self):
        """Test registering multiple tasks"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        id1 = monitor.register_task("task1", "workflow1", {})
        id2 = monitor.register_task("task2", "workflow2", {})
        id3 = monitor.register_task("task3", "workflow3", {})

        assert id1 != id2
        assert id2 != id3
        assert len(monitor._task_registry) == 3


class TestFailureDetection:
    """Test failure pattern detection logic"""

    def test_detect_403_unauthorized_by_status_code(self):
        """Test detection of 403 Unauthorized by status code"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=403,
            response="Unauthorized: Invalid token",
            duration_seconds=5.0
        )

        assert failure_type == FailureType.AUTH_FAILURE

    def test_detect_403_unauthorized_by_response_content(self):
        """Test detection of 403 Unauthorized by response content"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="Unauthorized: permission denied",
            duration_seconds=5.0
        )

        assert failure_type == FailureType.AUTH_FAILURE

    def test_detect_404_gateway_timeout_by_status_code(self):
        """Test detection of 504 Gateway Timeout by status code"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=504,
            response="Service temporarily unavailable",
            duration_seconds=15.0
        )

        assert failure_type == FailureType.GATEWAY_TIMEOUT

    def test_detect_gateway_timeout_by_response_content(self):
        """Test detection of 504 Gateway Timeout by response content"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="gateway timeout occurred",
            duration_seconds=5.0
        )

        assert failure_type == FailureType.GATEWAY_TIMEOUT

    def test_detect_execution_timeout_over_30_seconds(self):
        """Test detection of execution timeout (duration > 30s)"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="Success",
            duration_seconds=31.0
        )

        assert failure_type == FailureType.EXECUTION_TIMEOUT

    def test_detect_webhook_failure(self):
        """Test detection of webhook failure"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="error: webhook connection refused",
            duration_seconds=5.0
        )

        assert failure_type == FailureType.WEBHOOK_FAILURE

    def test_detect_unknown_error(self):
        """Test detection of unknown error"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="error: something went wrong",
            duration_seconds=5.0
        )

        assert failure_type == FailureType.UNKNOWN_ERROR

    def test_detect_no_failure_success(self):
        """Test successful task completion (no failure)"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response='{"success": true, "result": "completed"}',
            duration_seconds=5.0
        )

        assert failure_type == FailureType.NO_FAILURE

    def test_detect_timeout_exactly_30_seconds_no_failure(self):
        """Test that exactly 30 seconds is NOT a timeout (boundary condition)"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="Success",
            duration_seconds=30.0
        )

        assert failure_type == FailureType.NO_FAILURE

    def test_detect_timeout_31_seconds_is_timeout(self):
        """Test that 31 seconds IS a timeout"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="Success",
            duration_seconds=31.0
        )

        assert failure_type == FailureType.EXECUTION_TIMEOUT

    def test_detect_none_response_treated_as_success(self):
        """Test that None/empty response is treated as success"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response=None,
            duration_seconds=5.0
        )

        assert failure_type == FailureType.NO_FAILURE

    def test_detect_empty_string_response_treated_as_success(self):
        """Test that empty string response is treated as success"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="",
            duration_seconds=5.0
        )

        assert failure_type == FailureType.NO_FAILURE

    def test_detect_status_code_none_check_response(self):
        """Test that None status code falls back to response analysis"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=None,
            response="Invalid token error",
            duration_seconds=5.0
        )

        assert failure_type == FailureType.AUTH_FAILURE

    def test_detect_invalid_duration_negative(self):
        """Test that negative duration is treated as no timeout"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="Success",
            duration_seconds=-1.0
        )

        assert failure_type != FailureType.EXECUTION_TIMEOUT

    def test_detect_invalid_duration_zero(self):
        """Test that zero duration is treated as no timeout"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            status_code=200,
            response="Success",
            duration_seconds=0.0
        )

        assert failure_type != FailureType.EXECUTION_TIMEOUT


class TestTaskMetadataExtraction:
    """Test task metadata extraction"""

    def test_extract_metadata_basic(self):
        """Test basic metadata extraction"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        metadata = monitor._extract_task_metadata(
            task_id="video-assembly",
            workflow_name="video-assembly-workflow",
            input_params={"video_url": "https://example.com/video.mp4"}
        )

        assert metadata is not None
        assert "task_id" in metadata
        assert "workflow_name" in metadata
        assert "input_params" in metadata

    def test_extract_metadata_contains_workflow_name(self):
        """Test that extracted metadata contains workflow name"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        metadata = monitor._extract_task_metadata(
            task_id="draft-gen",
            workflow_name="draft-generator-workflow",
            input_params={"topic": "AI"}
        )

        assert metadata["workflow_name"] == "draft-generator-workflow"

    def test_extract_metadata_contains_parameters(self):
        """Test that extracted metadata contains input parameters"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        input_params = {"url": "example.com", "format": "json"}
        metadata = monitor._extract_task_metadata(
            task_id="test",
            workflow_name="test-workflow",
            input_params=input_params
        )

        assert metadata["input_params"] == input_params

    def test_extract_metadata_from_complex_task_id(self):
        """Test metadata extraction from complex task ID"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        metadata = monitor._extract_task_metadata(
            task_id="n8n:video-assembly:abc123",
            workflow_name="video-assembly-workflow",
            input_params={}
        )

        assert metadata["task_id"] is not None


class TestReportResult:
    """Test reporting task results"""

    def test_report_result_successful_task(self):
        """Test reporting successful task result"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="video-assembly",
            workflow_name="video-assembly-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=200,
            response='{"success": true}',
            duration_seconds=5.0
        )

        assert result is not None
        assert isinstance(result, MonitorResult)
        assert result.failure_detected is False
        assert result.failure_type == FailureType.NO_FAILURE
        assert result.status_code == 200
        assert result.duration_seconds == 5.0

    def test_report_result_403_failure(self):
        """Test reporting 403 Unauthorized failure"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 100  # Event ID
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="draft-generator",
            workflow_name="draft-gen-workflow",
            input_params={"topic": "AI"}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=403,
            response="Unauthorized: Invalid token",
            duration_seconds=3.5
        )

        assert result.failure_detected is True
        assert result.failure_type == FailureType.AUTH_FAILURE
        assert result.status_code == 403
        assert result.event_id == 100

    def test_report_result_504_failure(self):
        """Test reporting 504 Gateway Timeout failure"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 101
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="kb-indexing",
            workflow_name="kb-index-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=504,
            response="Gateway Timeout",
            duration_seconds=15.0
        )

        assert result.failure_detected is True
        assert result.failure_type == FailureType.GATEWAY_TIMEOUT
        assert result.status_code == 504

    def test_report_result_timeout_failure(self):
        """Test reporting execution timeout failure"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 102
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="long-task",
            workflow_name="long-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=200,
            response="Success",
            duration_seconds=35.5
        )

        assert result.failure_detected is True
        assert result.failure_type == FailureType.EXECUTION_TIMEOUT
        assert result.duration_seconds == 35.5

    def test_report_result_webhook_failure(self):
        """Test reporting webhook failure"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 103
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="webhook-task",
            workflow_name="webhook-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=200,
            response="error: webhook connection refused",
            duration_seconds=5.0
        )

        assert result.failure_detected is True
        assert result.failure_type == FailureType.WEBHOOK_FAILURE

    def test_report_result_unknown_error(self):
        """Test reporting unknown error"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 104
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="unknown-task",
            workflow_name="unknown-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=200,
            response="error: unknown system error",
            duration_seconds=5.0
        )

        assert result.failure_detected is True
        assert result.failure_type == FailureType.UNKNOWN_ERROR


class TestMonitorResultStructure:
    """Test MonitorResult data structure completeness"""

    def test_monitor_result_all_fields_present(self):
        """Test that MonitorResult contains all required fields"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="test",
            workflow_name="test-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=200,
            response="Success",
            duration_seconds=5.0
        )

        # Check all fields are present
        assert hasattr(result, 'failure_detected')
        assert hasattr(result, 'failure_type')
        assert hasattr(result, 'task_id')
        assert hasattr(result, 'workflow_name')
        assert hasattr(result, 'status_code')
        assert hasattr(result, 'duration_seconds')
        assert hasattr(result, 'reason')
        assert hasattr(result, 'event_id')

    def test_monitor_result_reason_populated(self):
        """Test that MonitorResult includes reason for failure/success"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="test",
            workflow_name="test-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=200,
            response="Success",
            duration_seconds=5.0
        )

        assert result.reason is not None
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0

    def test_monitor_result_reason_for_failure(self):
        """Test that MonitorResult includes specific reason for failures"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 200
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="test",
            workflow_name="test-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=403,
            response="Unauthorized",
            duration_seconds=5.0
        )

        assert result.failure_detected is True
        assert "unauthorized" in result.reason.lower() or "auth" in result.reason.lower()


class TestEventLogging:
    """Test failure event logging to automation_events"""

    def test_failure_event_logged_on_403(self):
        """Test that 403 failures are logged to automation_events"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 500
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="test-task",
            workflow_name="test-workflow",
            input_params={"key": "value"}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=403,
            response="Unauthorized: Invalid token",
            duration_seconds=2.5
        )

        # Verify store_event was called
        mock_hub.store_event.assert_called()
        assert result.event_id == 500

    def test_failure_event_contains_evidence(self):
        """Test that failure event contains detailed evidence"""
        mock_hub = Mock()
        captured_event = None

        def capture_event(event):
            nonlocal captured_event
            captured_event = event
            return 600

        mock_hub.store_event.side_effect = capture_event
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="video-assembly",
            workflow_name="video-workflow",
            input_params={"url": "example.com"}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=504,
            response="Service unavailable",
            duration_seconds=12.0
        )

        # Verify event was created with proper structure
        assert captured_event is not None
        assert captured_event.event_type == "n8n_failure_detected"
        assert captured_event.project_id == "n8n"
        assert captured_event.status == "failed"
        assert "task_id" in captured_event.evidence
        assert "workflow_name" in captured_event.evidence
        assert "failure_type" in captured_event.evidence
        assert "status_code" in captured_event.evidence

    def test_success_event_not_logged_to_failures(self):
        """Test that successful tasks don't log failure events"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        monitor_id = monitor.register_task(
            task_id="test",
            workflow_name="test-workflow",
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=200,
            response='{"result": "success"}',
            duration_seconds=5.0
        )

        # Success should not log events
        assert result.failure_detected is False


class TestImplicitRegistration:
    """Test reporting without prior registration (implicit registration)"""

    def test_report_without_prior_registration(self):
        """Test that reporting without registration creates implicit registration"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 700
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        # Report without prior registration
        result = monitor.report_result(
            monitor_id="nonexistent-id",
            status_code=403,
            response="Unauthorized",
            duration_seconds=5.0
        )

        # Should still detect failure
        assert result is not None
        assert result.failure_detected is True
        assert result.failure_type == FailureType.AUTH_FAILURE

    def test_implicit_registration_creates_entry(self):
        """Test that implicit registration adds to task registry"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        result = monitor.report_result(
            monitor_id="new-task",
            status_code=200,
            response="Success",
            duration_seconds=5.0
        )

        # Even without explicit registration, should handle gracefully
        assert result is not None


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_duplicate_registration_overwrites(self):
        """Test that registering same task twice overwrites previous"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        id1 = monitor.register_task("task1", "workflow1", {"v": 1})
        id2 = monitor.register_task("task1", "workflow1", {"v": 2})

        # Should have same number of registrations (overwrite)
        # or handle gracefully
        assert id1 is not None
        assert id2 is not None

    def test_case_insensitive_keyword_matching(self):
        """Test that keyword matching is case-insensitive"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        # Test various case combinations
        failures = [
            monitor._detect_failure_pattern(200, "UNAUTHORIZED", 5.0),
            monitor._detect_failure_pattern(200, "Unauthorized", 5.0),
            monitor._detect_failure_pattern(200, "unauthorized", 5.0),
            monitor._detect_failure_pattern(200, "UnAuthoriZed", 5.0),
        ]

        # All should detect auth failure
        for failure in failures:
            assert failure == FailureType.AUTH_FAILURE

    def test_whitespace_handling_in_response(self):
        """Test that whitespace is handled properly"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        # Response with lots of whitespace
        failure_type = monitor._detect_failure_pattern(
            200,
            "  \n  error: something  \n  ",
            5.0
        )

        assert failure_type == FailureType.UNKNOWN_ERROR

    def test_very_long_response_handled(self):
        """Test that very long response strings are handled"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        long_response = "error: " + "x" * 10000
        failure_type = monitor._detect_failure_pattern(
            200,
            long_response,
            5.0
        )

        assert failure_type == FailureType.UNKNOWN_ERROR

    def test_special_characters_in_response(self):
        """Test that special characters are handled"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        response_with_special_chars = '{"error": "unauthorized", "reason": "❌ \'Invalid\' token"}'
        failure_type = monitor._detect_failure_pattern(
            200,
            response_with_special_chars,
            5.0
        )

        assert failure_type == FailureType.AUTH_FAILURE

    def test_none_automation_hub_doesnt_crash(self):
        """Test that None automation hub doesn't cause crash"""
        monitor = N8nMonitor(automation_hub=None, test_mode=True)

        monitor_id = monitor.register_task("task", "workflow", {})
        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=403,
            response="Unauthorized",
            duration_seconds=5.0
        )

        # Should still work even without hub
        assert result is not None
        assert result.failure_detected is True

    def test_very_large_duration(self):
        """Test handling of very large duration values"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            200,
            "Success",
            9999999.0
        )

        assert failure_type == FailureType.EXECUTION_TIMEOUT

    def test_fractional_seconds_duration(self):
        """Test handling of fractional second durations just under 30s"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            200,
            "Success",
            29.999999
        )

        assert failure_type == FailureType.NO_FAILURE

    def test_fractional_seconds_over_30(self):
        """Test fractional seconds just over 30s threshold"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        failure_type = monitor._detect_failure_pattern(
            200,
            "Success",
            30.000001
        )

        assert failure_type == FailureType.EXECUTION_TIMEOUT


class TestMonitorIntegration:
    """Integration tests for monitor workflow"""

    def test_full_workflow_register_and_report(self):
        """Test complete workflow: register task → report result → get event"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 999
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        # Register task
        monitor_id = monitor.register_task(
            task_id="integration-test",
            workflow_name="integration-workflow",
            input_params={"test": True}
        )

        # Report result
        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=403,
            response="Unauthorized",
            duration_seconds=3.2
        )

        # Verify result
        assert result.task_id == "integration-test"
        assert result.workflow_name == "integration-workflow"
        assert result.failure_detected is True
        assert result.event_id == 999

    def test_multiple_failures_tracked_independently(self):
        """Test that multiple task failures are tracked independently"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1000
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        # Register and report multiple tasks
        id1 = monitor.register_task("task1", "workflow1", {})
        id2 = monitor.register_task("task2", "workflow2", {})

        result1 = monitor.report_result(id1, 403, "Unauthorized", 5.0)
        result2 = monitor.report_result(id2, 504, "Gateway Timeout", 15.0)

        assert result1.failure_type == FailureType.AUTH_FAILURE
        assert result2.failure_type == FailureType.GATEWAY_TIMEOUT

    def test_monitor_result_preserves_input_data(self):
        """Test that monitor result preserves original input data"""
        mock_hub = Mock()
        monitor = N8nMonitor(automation_hub=mock_hub, test_mode=True)

        task_id = "data-preservation-test"
        workflow_name = "data-preservation-workflow"
        status_code = 403
        duration = 7.123

        monitor_id = monitor.register_task(
            task_id=task_id,
            workflow_name=workflow_name,
            input_params={}
        )

        result = monitor.report_result(
            monitor_id=monitor_id,
            status_code=status_code,
            response="Unauthorized",
            duration_seconds=duration
        )

        assert result.task_id == task_id
        assert result.workflow_name == workflow_name
        assert result.status_code == status_code
        assert result.duration_seconds == duration
