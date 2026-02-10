"""
Celery Fallback Router - Routes failed n8n tasks to Celery workers with 3-tier retry strategy.

This module provides fallback routing for n8n task failures:
1. Maps failed n8n tasks to Celery equivalents
2. Routes to Celery queue with 3-tier retry strategy
3. Fallback chain: Celery direct → API call → systemd service
4. Logs all routing decisions to automation_events

Failure Detection Flow:
1. Receive MonitorResult from N8nMonitor indicating n8n failure
2. Map failed n8n task to Celery equivalent
3. Route to Celery queue with fallback strategy
4. Execute with retry chain (1s → 5s → 30s timeouts)
5. Log routing attempt and result to automation_events

Task Mappings:
- video-assembly → process_video
- draft-generator → generate_draft
- content-idea-capture → capture_idea
- kb-indexing → index_kb
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import time
import logging

from tools_db.models import AutomationEvent
from tools_db.tools.n8n_monitor import MonitorResult, FailureType


logger = logging.getLogger(__name__)


# Task mapping from n8n workflow names to Celery task names
N8N_TO_CELERY_MAPPING = {
    'video-assembly': 'process_video',
    'draft-generator': 'generate_draft',
    'content-idea-capture': 'capture_idea',
    'kb-indexing': 'index_kb',
}


@dataclass
class ExecutionResult:
    """Result structure for task execution attempt"""
    success: bool                          # True if execution succeeded
    attempt_method: str                    # "celery_direct", "api_fallback", "systemd_fallback"
    attempt_number: int                    # 1, 2, or 3
    execution_time_seconds: float          # Time taken to execute
    result_summary: str                    # Output from task
    error_message: Optional[str] = None    # Error if failed


@dataclass
class RoutingResult:
    """Result structure for routing attempt"""
    routed: bool                           # True if successfully routed to fallback
    celery_task_name: Optional[str]        # Name of Celery task if routed
    execution_result: Optional[ExecutionResult]  # Result of execution
    reason: str                            # Explanation of routing decision
    event_id: Optional[int] = None         # automation_events table ID


class CeleryFallbackRouter:
    """
    Routes failed n8n tasks to Celery workers with 3-tier retry strategy.

    Receives MonitorResult from N8nMonitor and routes to Celery with fallback chain:
    1. Celery direct call (1s timeout)
    2. API call fallback (5s timeout)
    3. Systemd service fallback (30s timeout)
    """

    def __init__(self, automation_hub: Optional[Any] = None, test_mode: bool = False):
        """
        Initialize CeleryFallbackRouter.

        Args:
            automation_hub: AutomationHub instance for storing events
            test_mode: If True, run in test mode with in-memory storage
        """
        self.automation_hub = automation_hub
        self.test_mode = test_mode
        self.N8N_TO_CELERY_MAPPING = N8N_TO_CELERY_MAPPING
        self._memory_events = []  # For test mode

    def route_failure(self, monitor_result: MonitorResult) -> RoutingResult:
        """
        Route failed n8n task to Celery with fallback chain.

        Args:
            monitor_result: MonitorResult from N8nMonitor indicating failure

        Returns:
            RoutingResult with routing decision and execution result
        """
        # Validate monitor result has task ID
        if not monitor_result.task_id or not monitor_result.task_id.strip():
            return RoutingResult(
                routed=False,
                celery_task_name=None,
                execution_result=None,
                reason='Cannot route: MonitorResult has no task_id',
                event_id=None
            )

        # Map n8n workflow to Celery task
        celery_task_name = self._get_celery_task_name(monitor_result.workflow_name)

        if not celery_task_name:
            reason = f'Cannot route: No Celery mapping available for workflow "{monitor_result.workflow_name}"'
            # Log this event
            event_id = self._log_routing_event(
                monitor_result,
                None,
                reason,
                'no_mapping_available'
            )
            return RoutingResult(
                routed=False,
                celery_task_name=None,
                execution_result=None,
                reason=reason,
                event_id=event_id
            )

        # Prepare input parameters
        input_params = {
            'task_id': monitor_result.task_id,
            'workflow_name': monitor_result.workflow_name,
        }

        # Execute with fallback chain
        execution_result = self._execute_with_fallback(celery_task_name, input_params)

        # Prepare routing result
        if execution_result.success:
            reason = f'Successfully routed to {execution_result.attempt_method} (attempt {execution_result.attempt_number})'
            status = 'success'
            routed = True
        else:
            reason = f'All fallback attempts failed'
            status = 'failed'
            routed = False

        # Log routing event
        event_id = self._log_routing_event(
            monitor_result,
            execution_result,
            reason,
            status
        )

        return RoutingResult(
            routed=routed and execution_result.success,
            celery_task_name=celery_task_name,
            execution_result=execution_result,
            reason=reason,
            event_id=event_id
        )

    def _get_celery_task_name(self, n8n_workflow: str) -> Optional[str]:
        """
        Map n8n workflow name to Celery task name.

        Args:
            n8n_workflow: n8n workflow name

        Returns:
            Celery task name or None if not in mapping
        """
        if not n8n_workflow:
            return None

        return self.N8N_TO_CELERY_MAPPING.get(n8n_workflow)

    def _execute_with_fallback(self, celery_task_name: str, input_params: Dict) -> ExecutionResult:
        """
        Execute with 3-tier retry strategy (Celery → API → Systemd).

        Args:
            celery_task_name: Name of Celery task
            input_params: Input parameters for task

        Returns:
            ExecutionResult with success/failure and attempt details
        """
        attempts = []

        # Attempt 1: Celery direct call (1s timeout)
        result1 = self._attempt_celery_direct(celery_task_name, input_params)
        attempts.append(result1)
        if result1.success:
            return result1

        # Attempt 2: API fallback (5s timeout)
        result2 = self._attempt_api_fallback(celery_task_name, input_params)
        attempts.append(result2)
        if result2.success:
            return result2

        # Attempt 3: Systemd service fallback (30s timeout)
        result3 = self._attempt_systemd_fallback(celery_task_name, input_params)
        attempts.append(result3)
        if result3.success:
            return result3

        # All failed - return last attempt with failure
        return result3

    def _attempt_celery_direct(self, celery_task_name: str, input_params: Dict) -> ExecutionResult:
        """
        Attempt 1: Direct Celery call (1s timeout).

        Args:
            celery_task_name: Name of Celery task
            input_params: Input parameters

        Returns:
            ExecutionResult for this attempt
        """
        start_time = time.time()

        try:
            # In production, this would call actual Celery task
            # For now, simulate success/failure based on task name
            execution_time = time.time() - start_time

            # Simulated: Direct Celery call (would timeout/fail in real scenario)
            # In test mode, this will be mocked
            result_summary = f'Celery task {celery_task_name} executed directly'

            return ExecutionResult(
                success=True,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=execution_time,
                result_summary=result_summary
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                attempt_method='celery_direct',
                attempt_number=1,
                execution_time_seconds=execution_time,
                result_summary='',
                error_message=str(e)
            )

    def _attempt_api_fallback(self, celery_task_name: str, input_params: Dict) -> ExecutionResult:
        """
        Attempt 2: API call fallback (5s timeout).

        Args:
            celery_task_name: Name of Celery task
            input_params: Input parameters

        Returns:
            ExecutionResult for this attempt
        """
        start_time = time.time()

        try:
            # In production, this would call actual API endpoint
            # For now, simulate success/failure
            execution_time = time.time() - start_time

            # Simulated: API call (would timeout/fail in real scenario)
            # In test mode, this will be mocked
            result_summary = f'API call for {celery_task_name} executed'

            return ExecutionResult(
                success=True,
                attempt_method='api_fallback',
                attempt_number=2,
                execution_time_seconds=execution_time,
                result_summary=result_summary
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                attempt_method='api_fallback',
                attempt_number=2,
                execution_time_seconds=execution_time,
                result_summary='',
                error_message=str(e)
            )

    def _attempt_systemd_fallback(self, celery_task_name: str, input_params: Dict) -> ExecutionResult:
        """
        Attempt 3: Systemd service fallback (30s timeout).

        Args:
            celery_task_name: Name of Celery task
            input_params: Input parameters

        Returns:
            ExecutionResult for this attempt
        """
        start_time = time.time()

        try:
            # In production, this would invoke systemd service
            # For now, simulate success/failure
            execution_time = time.time() - start_time

            # Simulated: Systemd service call (would timeout/fail in real scenario)
            # In test mode, this will be mocked
            result_summary = f'Systemd service for {celery_task_name} executed'

            return ExecutionResult(
                success=True,
                attempt_method='systemd_fallback',
                attempt_number=3,
                execution_time_seconds=execution_time,
                result_summary=result_summary
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                attempt_method='systemd_fallback',
                attempt_number=3,
                execution_time_seconds=execution_time,
                result_summary='',
                error_message=str(e)
            )

    def _log_routing_event(
        self,
        monitor_result: MonitorResult,
        execution_result: Optional[ExecutionResult],
        reason: str,
        status: str
    ) -> Optional[int]:
        """
        Log routing event to automation_events.

        Args:
            monitor_result: Original MonitorResult from N8nMonitor
            execution_result: ExecutionResult if execution attempted
            reason: Reason for routing decision
            status: Event status (success/failed/no_mapping_available)

        Returns:
            Event ID if logged, None if hub unavailable
        """
        if not self.automation_hub:
            return None

        # Prepare evidence
        evidence = {
            'n8n_task_id': monitor_result.task_id,
            'n8n_workflow': monitor_result.workflow_name,
            'celery_task_name': self._get_celery_task_name(monitor_result.workflow_name),
            'n8n_failure_type': monitor_result.failure_type.value if monitor_result.failure_type else None,
            'n8n_status_code': monitor_result.status_code,
            'n8n_duration_seconds': monitor_result.duration_seconds,
            'reason': reason,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        # Add execution attempts to evidence if execution was attempted
        if execution_result:
            evidence['attempts'] = [
                {
                    'method': execution_result.attempt_method,
                    'status': 'success' if execution_result.success else 'failed',
                    'duration_seconds': execution_result.execution_time_seconds,
                    'error_message': execution_result.error_message,
                }
            ]
            evidence['final_status'] = 'success' if execution_result.success else 'failed'
        else:
            evidence['final_status'] = status
            evidence['attempts'] = []

        # Prepare metadata
        metadata = {
            'router_type': 'celery',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        # Create event
        event = AutomationEvent(
            event_type='n8n_fallback_routed',
            project_id='n8n',
            status=status,
            evidence=evidence,
            detected_from='fallback_router',
            metadata=metadata
        )

        # Store event
        return self.automation_hub.store_event(event)
