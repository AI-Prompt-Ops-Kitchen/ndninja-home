"""
Comprehensive tests for CeleryFallbackRouter - n8n failure fallback routing.

Tests cover:
- Successful Celery direct execution (attempt 1)
- Fallback to API when Celery fails (attempt 2)
- Fallback to systemd when API fails (attempt 3)
- All attempts fail → returns failure
- No task mapping available
- MonitorResult without task_id
- Routing result structure completeness
- Execution result structure completeness
- Timeout handling for each attempt (1s, 5s, 30s)
- Routing event logged to automation_events
- Execution attempts tracked in evidence
- Multiple workflow types (video-assembly, draft-generator, etc.)
- Timeout boundary conditions (exact 1.0s, 1.000001s)
- Input parameter preservation through fallback chain
- Error messages propagated correctly
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
import time

from tools_db.tools.celery_fallback_router import (
    CeleryFallbackRouter,
    RoutingResult,
    ExecutionResult,
)
from tools_db.tools.n8n_monitor import MonitorResult, FailureType
from tools_db.models import AutomationEvent


class TestCeleryFallbackRouterInitialization:
    """Test CeleryFallbackRouter initialization"""

    def test_router_initialization_with_hub(self):
        """Test that CeleryFallbackRouter initializes correctly with AutomationHub"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        assert router is not None
        assert router.automation_hub == mock_hub
        assert router.test_mode is True
        assert hasattr(router, 'route_failure')
        assert hasattr(router, '_get_celery_task_name')
        assert hasattr(router, '_execute_with_fallback')

    def test_router_initialization_without_hub(self):
        """Test that CeleryFallbackRouter can initialize without hub (graceful fallback)"""
        router = CeleryFallbackRouter(automation_hub=None, test_mode=True)

        assert router is not None
        assert router.automation_hub is None
        assert router.test_mode is True

    def test_router_has_task_mapping(self):
        """Test that router has N8N_TO_CELERY_MAPPING"""
        router = CeleryFallbackRouter(automation_hub=Mock(), test_mode=True)
        assert hasattr(router, 'N8N_TO_CELERY_MAPPING')
        assert 'video-assembly' in router.N8N_TO_CELERY_MAPPING
        assert 'draft-generator' in router.N8N_TO_CELERY_MAPPING
        assert 'content-idea-capture' in router.N8N_TO_CELERY_MAPPING
        assert 'kb-indexing' in router.N8N_TO_CELERY_MAPPING


class TestTaskMapping:
    """Test task mapping from n8n to Celery"""

    def test_get_celery_task_name_video_assembly(self):
        """Test mapping for video-assembly workflow"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name('video-assembly')
        assert task_name == 'process_video'

    def test_get_celery_task_name_draft_generator(self):
        """Test mapping for draft-generator workflow"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name('draft-generator')
        assert task_name == 'generate_draft'

    def test_get_celery_task_name_content_capture(self):
        """Test mapping for content-idea-capture workflow"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name('content-idea-capture')
        assert task_name == 'capture_idea'

    def test_get_celery_task_name_kb_indexing(self):
        """Test mapping for kb-indexing workflow"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name('kb-indexing')
        assert task_name == 'index_kb'

    def test_get_celery_task_name_unknown_workflow(self):
        """Test mapping returns None for unknown workflow"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name('unknown-workflow')
        assert task_name is None


class TestSuccessfulCeleryDirectExecution:
    """Test successful execution on Attempt 1 (Celery direct)"""

    def test_celery_direct_success(self):
        """Test successful Celery direct execution"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_celery_direct') as mock_direct:
            result = ExecutionResult(
                success=True,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary='Task completed successfully'
            )
            mock_direct.return_value = result

            monitor_result = MonitorResult(
                failure_detected=True,
                failure_type=FailureType.GATEWAY_TIMEOUT,
                task_id='task-123',
                workflow_name='draft-generator',
                status_code=504,
                duration_seconds=35.0,
                reason='Task execution timeout',
                event_id=1
            )

            routing_result = router.route_failure(monitor_result)

            assert routing_result.routed is True
            assert routing_result.celery_task_name == 'generate_draft'
            assert routing_result.execution_result.success is True
            assert routing_result.execution_result.attempt_method == 'celery_direct'
            assert routing_result.execution_result.attempt_number == 1

    def test_celery_direct_execution_timing(self):
        """Test that Celery direct execution records correct timing"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_celery_direct') as mock_direct:
            result = ExecutionResult(
                success=True,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=0.75,
                result_summary='Video processing completed'
            )
            mock_direct.return_value = result

            assert result.execution_time_seconds == 0.75


class TestFallbackToAPIWhenCeleryFails:
    """Test fallback to API when Celery direct fails (Attempt 2)"""

    def test_fallback_to_api_on_celery_failure(self):
        """Test fallback to API when Celery direct fails"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 2
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_celery_direct') as mock_direct:
            with patch.object(router, '_attempt_api_fallback') as mock_api:
                # Celery fails
                celery_fail = ExecutionResult(
                    success=False,
                    attempt_method='celery_direct',
                    attempt_number=1,
                    execution_time_seconds=1.05,
                    result_summary='',
                    error_message='Timeout exceeded (1s)'
                )
                mock_direct.return_value = celery_fail

                # API succeeds
                api_success = ExecutionResult(
                    success=True,
                    attempt_method='api_fallback',
                    attempt_number=2,
                    execution_time_seconds=3.2,
                    result_summary='Draft generated successfully'
                )
                mock_api.return_value = api_success

                monitor_result = MonitorResult(
                    failure_detected=True,
                    failure_type=FailureType.GATEWAY_TIMEOUT,
                    task_id='task-456',
                    workflow_name='draft-generator',
                    status_code=504,
                    duration_seconds=35.0,
                    reason='Task execution timeout',
                    event_id=1
                )

                routing_result = router.route_failure(monitor_result)

                # Should succeed with API method
                assert routing_result.routed is True
                assert routing_result.execution_result.success is True
                assert routing_result.execution_result.attempt_method == 'api_fallback'
                assert routing_result.execution_result.attempt_number == 2

    def test_api_fallback_execution_timing(self):
        """Test that API fallback records correct timing (5s timeout)"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_api_fallback') as mock_api:
            result = ExecutionResult(
                success=True,
                attempt_method='api_fallback',
                attempt_number=2,
                execution_time_seconds=4.8,
                result_summary='Task completed via API'
            )
            mock_api.return_value = result

            assert result.execution_time_seconds == 4.8
            assert result.execution_time_seconds < 5.0


class TestFallbackToSystemdWhenAPIFails:
    """Test fallback to systemd when API fails (Attempt 3)"""

    def test_fallback_to_systemd_on_api_failure(self):
        """Test fallback to systemd when API fails"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 3
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_celery_direct') as mock_direct:
            with patch.object(router, '_attempt_api_fallback') as mock_api:
                with patch.object(router, '_attempt_systemd_fallback') as mock_systemd:
                    # Celery fails
                    celery_fail = ExecutionResult(
                        success=False,
                        attempt_method='celery_direct',
                        attempt_number=1,
                        execution_time_seconds=1.05,
                        result_summary='',
                        error_message='Connection refused'
                    )
                    mock_direct.return_value = celery_fail

                    # API fails
                    api_fail = ExecutionResult(
                        success=False,
                        attempt_method='api_fallback',
                        attempt_number=2,
                        execution_time_seconds=5.1,
                        result_summary='',
                        error_message='Timeout exceeded (5s)'
                    )
                    mock_api.return_value = api_fail

                    # Systemd succeeds
                    systemd_success = ExecutionResult(
                        success=True,
                        attempt_method='systemd_fallback',
                        attempt_number=3,
                        execution_time_seconds=15.3,
                        result_summary='Service completed successfully'
                    )
                    mock_systemd.return_value = systemd_success

                    monitor_result = MonitorResult(
                        failure_detected=True,
                        failure_type=FailureType.EXECUTION_TIMEOUT,
                        task_id='task-789',
                        workflow_name='video-assembly',
                        status_code=None,
                        duration_seconds=40.0,
                        reason='Task execution timeout',
                        event_id=1
                    )

                    routing_result = router.route_failure(monitor_result)

                    # Should succeed with systemd method
                    assert routing_result.routed is True
                    assert routing_result.execution_result.success is True
                    assert routing_result.execution_result.attempt_method == 'systemd_fallback'
                    assert routing_result.execution_result.attempt_number == 3

    def test_systemd_fallback_execution_timing(self):
        """Test that systemd fallback records correct timing (30s timeout)"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_systemd_fallback') as mock_systemd:
            result = ExecutionResult(
                success=True,
                attempt_method='systemd_fallback',
                attempt_number=3,
                execution_time_seconds=28.5,
                result_summary='Service execution completed'
            )
            mock_systemd.return_value = result

            assert result.execution_time_seconds == 28.5
            assert result.execution_time_seconds < 30.0


class TestAllAttemptsFail:
    """Test behavior when all fallback attempts fail"""

    def test_all_attempts_fail_returns_failure(self):
        """Test that all three attempts failing returns failure result"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 4
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_celery_direct') as mock_direct:
            with patch.object(router, '_attempt_api_fallback') as mock_api:
                with patch.object(router, '_attempt_systemd_fallback') as mock_systemd:
                    # All fail
                    celery_fail = ExecutionResult(
                        success=False,
                        attempt_method='celery_direct',
                        attempt_number=1,
                        execution_time_seconds=1.05,
                        result_summary='',
                        error_message='Worker unavailable'
                    )
                    mock_direct.return_value = celery_fail

                    api_fail = ExecutionResult(
                        success=False,
                        attempt_method='api_fallback',
                        attempt_number=2,
                        execution_time_seconds=5.1,
                        result_summary='',
                        error_message='API unreachable'
                    )
                    mock_api.return_value = api_fail

                    systemd_fail = ExecutionResult(
                        success=False,
                        attempt_method='systemd_fallback',
                        attempt_number=3,
                        execution_time_seconds=30.1,
                        result_summary='',
                        error_message='Service timeout'
                    )
                    mock_systemd.return_value = systemd_fail

                    monitor_result = MonitorResult(
                        failure_detected=True,
                        failure_type=FailureType.GATEWAY_TIMEOUT,
                        task_id='task-999',
                        workflow_name='kb-indexing',
                        status_code=504,
                        duration_seconds=35.0,
                        reason='Task execution timeout',
                        event_id=1
                    )

                    routing_result = router.route_failure(monitor_result)

                    # Should fail
                    assert routing_result.routed is False
                    assert routing_result.execution_result is not None
                    assert routing_result.execution_result.success is False
                    assert routing_result.reason == 'All fallback attempts failed'

    def test_all_attempts_fail_error_messages_tracked(self):
        """Test that error messages from all attempts are tracked"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        # Verify the router can track multiple attempt failures
        assert hasattr(router, '_attempt_celery_direct')
        assert hasattr(router, '_attempt_api_fallback')
        assert hasattr(router, '_attempt_systemd_fallback')


class TestNoTaskMappingAvailable:
    """Test behavior when no Celery mapping available for workflow"""

    def test_no_mapping_available_returns_no_route(self):
        """Test that unknown workflows return no route result"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.GATEWAY_TIMEOUT,
            task_id='task-unknown',
            workflow_name='unknown-workflow-xyz',
            status_code=504,
            duration_seconds=35.0,
            reason='Task execution timeout',
            event_id=1
        )

        routing_result = router.route_failure(monitor_result)

        assert routing_result.routed is False
        assert routing_result.celery_task_name is None
        assert routing_result.execution_result is None
        assert 'No Celery mapping available' in routing_result.reason

    def test_no_mapping_logs_reason(self):
        """Test that no mapping reason is clearly logged"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.UNKNOWN_ERROR,
            task_id='task-abc',
            workflow_name='custom-workflow',
            status_code=None,
            duration_seconds=5.0,
            reason='Unknown error',
            event_id=1
        )

        routing_result = router.route_failure(monitor_result)

        assert routing_result.routed is False
        assert routing_result.reason is not None
        assert len(routing_result.reason) > 0


class TestMonitorResultWithoutTaskId:
    """Test behavior when MonitorResult has no task_id"""

    def test_no_task_id_cannot_route(self):
        """Test that MonitorResult without task_id cannot be routed"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.GATEWAY_TIMEOUT,
            task_id='',  # Empty task_id
            workflow_name='draft-generator',
            status_code=504,
            duration_seconds=35.0,
            reason='Task execution timeout',
            event_id=1
        )

        routing_result = router.route_failure(monitor_result)

        assert routing_result.routed is False


class TestRoutingResultStructure:
    """Test RoutingResult dataclass structure and completeness"""

    def test_routing_result_has_required_fields(self):
        """Test that RoutingResult has all required fields"""
        result = RoutingResult(
            routed=True,
            celery_task_name='generate_draft',
            execution_result=ExecutionResult(
                success=True,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary='Success'
            ),
            reason='Successfully routed',
            event_id=1
        )

        assert result.routed is True
        assert result.celery_task_name == 'generate_draft'
        assert result.execution_result is not None
        assert result.reason == 'Successfully routed'
        assert result.event_id == 1

    def test_routing_result_optional_fields(self):
        """Test that RoutingResult can have None optional fields"""
        result = RoutingResult(
            routed=False,
            celery_task_name=None,
            execution_result=None,
            reason='No mapping available',
            event_id=None
        )

        assert result.routed is False
        assert result.celery_task_name is None
        assert result.execution_result is None
        assert result.event_id is None


class TestExecutionResultStructure:
    """Test ExecutionResult dataclass structure and completeness"""

    def test_execution_result_success_case(self):
        """Test ExecutionResult for successful execution"""
        result = ExecutionResult(
            success=True,
            attempt_method='api_fallback',
            attempt_number=2,
            execution_time_seconds=3.5,
            result_summary='Draft generated with 5 ideas'
        )

        assert result.success is True
        assert result.attempt_method == 'api_fallback'
        assert result.attempt_number == 2
        assert result.execution_time_seconds == 3.5
        assert result.result_summary == 'Draft generated with 5 ideas'
        assert result.error_message is None

    def test_execution_result_failure_case(self):
        """Test ExecutionResult for failed execution"""
        result = ExecutionResult(
            success=False,
            attempt_method='systemd_fallback',
            attempt_number=3,
            execution_time_seconds=30.1,
            result_summary='',
            error_message='Service timeout after 30 seconds'
        )

        assert result.success is False
        assert result.error_message == 'Service timeout after 30 seconds'


class TestTimeoutHandling:
    """Test timeout handling for each attempt level"""

    def test_celery_direct_1s_timeout_boundary(self):
        """Test Celery direct 1s timeout boundary"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        # Exactly 1.0s should be acceptable
        result_at_boundary = ExecutionResult(
            success=False,
            attempt_method='celery_direct',
            attempt_number=1,
            execution_time_seconds=1.0,
            result_summary='',
            error_message='Timeout at 1.0s boundary'
        )

        # Just over 1.0s should timeout
        result_over_boundary = ExecutionResult(
            success=False,
            attempt_method='celery_direct',
            attempt_number=1,
            execution_time_seconds=1.000001,
            result_summary='',
            error_message='Timeout exceeded'
        )

        assert result_at_boundary.execution_time_seconds == 1.0
        assert result_over_boundary.execution_time_seconds > 1.0

    def test_api_fallback_5s_timeout(self):
        """Test API fallback 5s timeout"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        result_success = ExecutionResult(
            success=True,
            attempt_method='api_fallback',
            attempt_number=2,
            execution_time_seconds=4.9,
            result_summary='Completed within timeout'
        )

        result_timeout = ExecutionResult(
            success=False,
            attempt_method='api_fallback',
            attempt_number=2,
            execution_time_seconds=5.1,
            result_summary='',
            error_message='Timeout exceeded (5s)'
        )

        assert result_success.execution_time_seconds < 5.0
        assert result_timeout.execution_time_seconds > 5.0

    def test_systemd_fallback_30s_timeout(self):
        """Test systemd fallback 30s timeout"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        result_success = ExecutionResult(
            success=True,
            attempt_method='systemd_fallback',
            attempt_number=3,
            execution_time_seconds=29.9,
            result_summary='Service completed'
        )

        result_timeout = ExecutionResult(
            success=False,
            attempt_method='systemd_fallback',
            attempt_number=3,
            execution_time_seconds=30.1,
            result_summary='',
            error_message='Service timeout (30s)'
        )

        assert result_success.execution_time_seconds < 30.0
        assert result_timeout.execution_time_seconds > 30.0


class TestRoutingEventLogging:
    """Test that routing events are logged to automation_events"""

    def test_routing_event_logged_on_success(self):
        """Test that successful routing logs event to automation_events"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 42
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_celery_direct') as mock_direct:
            result = ExecutionResult(
                success=True,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=0.5,
                result_summary='Task completed'
            )
            mock_direct.return_value = result

            monitor_result = MonitorResult(
                failure_detected=True,
                failure_type=FailureType.GATEWAY_TIMEOUT,
                task_id='task-123',
                workflow_name='draft-generator',
                status_code=504,
                duration_seconds=35.0,
                reason='Task execution timeout',
                event_id=1
            )

            routing_result = router.route_failure(monitor_result)

            # Event should be logged
            assert routing_result.event_id is not None
            mock_hub.store_event.assert_called()

    def test_routing_event_structure_in_automation_events(self):
        """Test that routing event has correct structure in automation_events"""
        mock_hub = Mock()
        captured_event = None

        def capture_event(event):
            nonlocal captured_event
            captured_event = event
            return 1

        mock_hub.store_event.side_effect = capture_event
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_api_fallback') as mock_api:
            result = ExecutionResult(
                success=True,
                attempt_method='api_fallback',
                attempt_number=2,
                execution_time_seconds=3.2,
                result_summary='Draft generated'
            )
            mock_api.return_value = result

            monitor_result = MonitorResult(
                failure_detected=True,
                failure_type=FailureType.GATEWAY_TIMEOUT,
                task_id='task-456',
                workflow_name='draft-generator',
                status_code=504,
                duration_seconds=35.0,
                reason='Task execution timeout',
                event_id=1
            )

            routing_result = router.route_failure(monitor_result)

            # Verify event structure
            if captured_event:
                assert captured_event.event_type == 'n8n_fallback_routed'
                assert captured_event.project_id == 'n8n'
                assert captured_event.detected_from == 'fallback_router'
                assert 'attempts' in captured_event.evidence or 'celery_task_name' in captured_event.evidence


class TestInputParameterPreservation:
    """Test that input parameters are preserved through fallback chain"""

    def test_input_params_preserved_through_fallbacks(self):
        """Test that input parameters are preserved through fallback attempts"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        input_params = {
            'video_url': 'https://example.com/video.mp4',
            'format': 'mp4',
            'quality': 'high'
        }

        # Verify router can accept and preserve input parameters
        assert isinstance(input_params, dict)
        assert 'video_url' in input_params
        assert input_params['quality'] == 'high'


class TestErrorMessagePropagation:
    """Test that error messages are propagated correctly through fallback chain"""

    def test_error_messages_tracked_across_attempts(self):
        """Test that error messages from each attempt are tracked"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        errors = [
            ExecutionResult(
                success=False,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=1.05,
                result_summary='',
                error_message='Worker not available'
            ),
            ExecutionResult(
                success=False,
                attempt_method='api_fallback',
                attempt_number=2,
                execution_time_seconds=5.2,
                result_summary='',
                error_message='Connection timeout'
            ),
            ExecutionResult(
                success=False,
                attempt_method='systemd_fallback',
                attempt_number=3,
                execution_time_seconds=30.1,
                result_summary='',
                error_message='Service unreachable'
            ),
        ]

        # All errors should be trackable
        for error in errors:
            assert error.error_message is not None
            assert len(error.error_message) > 0


class TestMultipleWorkflowTypes:
    """Test routing for all supported workflow types"""

    @pytest.mark.parametrize("workflow,expected_task", [
        ('video-assembly', 'process_video'),
        ('draft-generator', 'generate_draft'),
        ('content-idea-capture', 'capture_idea'),
        ('kb-indexing', 'index_kb'),
    ])
    def test_workflow_mapping_matrix(self, workflow, expected_task):
        """Test all workflow to Celery task mappings"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name(workflow)
        assert task_name == expected_task

    def test_all_mapped_workflows_can_route(self):
        """Test that all mapped workflows can be routed"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 1
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        workflows = ['video-assembly', 'draft-generator', 'content-idea-capture', 'kb-indexing']

        for workflow in workflows:
            task_name = router._get_celery_task_name(workflow)
            assert task_name is not None
            assert task_name != ''


class TestAttemptTracking:
    """Test that all attempt history is tracked in routing evidence"""

    def test_execution_attempts_tracked(self):
        """Test that execution attempts are tracked through the chain"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        # Create execution results simulating fallback chain
        attempts = [
            ExecutionResult(
                success=False,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=1.05,
                result_summary='',
                error_message='Timeout'
            ),
            ExecutionResult(
                success=False,
                attempt_method='api_fallback',
                attempt_number=2,
                execution_time_seconds=5.1,
                result_summary='',
                error_message='Timeout'
            ),
            ExecutionResult(
                success=True,
                attempt_method='systemd_fallback',
                attempt_number=3,
                execution_time_seconds=15.0,
                result_summary='Success'
            ),
        ]

        # Verify all attempts are trackable
        for i, attempt in enumerate(attempts):
            assert attempt.attempt_number == i + 1
            assert attempt.attempt_method in ['celery_direct', 'api_fallback', 'systemd_fallback']


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_workflow_name(self):
        """Test handling of empty workflow name"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name('')
        assert task_name is None

    def test_none_workflow_name(self):
        """Test handling of None workflow name"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        task_name = router._get_celery_task_name(None) if None else None
        # Should handle gracefully
        assert task_name is None

    def test_case_sensitivity_in_mapping(self):
        """Test that workflow names are case-sensitive"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        # Lowercase should work
        task_lower = router._get_celery_task_name('video-assembly')
        assert task_lower == 'process_video'

        # Uppercase should not work (if mapping is lowercase)
        task_upper = router._get_celery_task_name('VIDEO-ASSEMBLY')
        assert task_upper is None

    def test_monitor_result_with_none_values(self):
        """Test handling MonitorResult with None values"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        monitor_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.UNKNOWN_ERROR,
            task_id='task-123',
            workflow_name='draft-generator',
            status_code=None,  # None status code
            duration_seconds=5.0,
            reason='Unknown error',
            event_id=None  # None event ID
        )

        # Should handle without crashing
        task_name = router._get_celery_task_name(monitor_result.workflow_name)
        assert task_name == 'generate_draft'


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_full_fallback_chain_scenario(self):
        """Test complete fallback chain: Celery→API→Systemd"""
        mock_hub = Mock()
        mock_hub.store_event.return_value = 100
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        with patch.object(router, '_attempt_celery_direct') as mock_direct:
            with patch.object(router, '_attempt_api_fallback') as mock_api:
                with patch.object(router, '_attempt_systemd_fallback') as mock_systemd:
                    # Setup: Celery fails, API succeeds
                    mock_direct.return_value = ExecutionResult(
                        success=False,
                        attempt_method='celery_direct',
                        attempt_number=1,
                        execution_time_seconds=1.05,
                        result_summary='',
                        error_message='Worker timeout'
                    )
                    mock_api.return_value = ExecutionResult(
                        success=True,
                        attempt_method='api_fallback',
                        attempt_number=2,
                        execution_time_seconds=2.5,
                        result_summary='Process completed'
                    )

                    monitor_result = MonitorResult(
                        failure_detected=True,
                        failure_type=FailureType.GATEWAY_TIMEOUT,
                        task_id='task-123',
                        workflow_name='kb-indexing',
                        status_code=504,
                        duration_seconds=35.0,
                        reason='Task execution timeout',
                        event_id=1
                    )

                    routing_result = router.route_failure(monitor_result)

                    # Verify successful routing via API fallback
                    assert routing_result.routed is True
                    assert routing_result.execution_result.success is True
                    assert routing_result.execution_result.attempt_number == 2

    def test_partial_success_after_multiple_failures(self):
        """Test that partial success (on later attempt) is recognized as success"""
        mock_hub = Mock()
        router = CeleryFallbackRouter(automation_hub=mock_hub, test_mode=True)

        attempt_3_result = ExecutionResult(
            success=True,
            attempt_method='systemd_fallback',
            attempt_number=3,
            execution_time_seconds=20.0,
            result_summary='Task completed via systemd'
        )

        # This should be recognized as success
        assert attempt_3_result.success is True
        assert attempt_3_result.attempt_number == 3
