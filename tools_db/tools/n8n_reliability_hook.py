"""
N8n Reliability Hook - PreToolUse hook for detecting and recovering from n8n failures.

This module provides a PreToolUse hook that orchestrates N8nMonitor and CeleryFallbackRouter
to automatically detect and recover from n8n task failures.

Hook Workflow:
1. on_task_started: Register task with N8nMonitor, return monitor_id
2. on_task_completed: Receive result, analyze with N8nMonitor
3. If failure detected: trigger CeleryFallbackRouter for recovery
4. Log both failure and recovery events to automation_events
5. Return comprehensive HookExecutionResult

Failure Types Handled:
- 403 Unauthorized (authentication failure)
- 504 Gateway Timeout (service unavailable)
- Execution Timeout (>30s)
- Webhook Error (external service unreachable)
- Unknown Error (any unexpected error)

Recovery Strategy:
- Attempt 1: Celery direct call (1s timeout)
- Attempt 2: API fallback (5s timeout)
- Attempt 3: systemd service (30s timeout)
- If all fail: Log failure but don't crash
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

from tools_db.tools.n8n_monitor import N8nMonitor, MonitorResult, FailureType
from tools_db.tools.celery_fallback_router import CeleryFallbackRouter, RoutingResult, ExecutionResult
from tools_db.models import AutomationEvent


logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """Result structure for recovery execution"""
    recovery_successful: bool                      # True if recovery succeeded
    recovery_method: Optional[str]                 # "celery_direct", "api_fallback", "systemd_fallback"
    routing_result: Optional[RoutingResult] = None # Full routing details
    execution_time_seconds: float = 0.0            # Time taken for recovery
    error_message: Optional[str] = None            # Error if recovery failed


@dataclass
class HookExecutionResult:
    """Result structure returned by hook"""
    hook_executed: bool                    # True if hook processed the task
    task_id: str                           # Task identifier
    failure_detected: bool                 # True if failure detected
    recovery_attempted: bool               # True if recovery was attempted
    recovery_successful: bool              # True if recovery succeeded
    failure_type: Optional[str]            # Failure type string (e.g., "403_unauthorized")
    recovery_method: Optional[str]         # Recovery method used (e.g., "celery_direct")
    reason: str                            # Explanation of hook decision
    event_ids: List[int] = field(default_factory=list)  # automation_events IDs


class N8nReliabilityHook:
    """
    PreToolUse hook for n8n task failure detection and recovery.

    Monitors n8n task execution, detects failures (403, 504, timeout, webhook errors),
    and automatically routes to Celery with fallback strategy (Celery → API → systemd).
    """

    def __init__(
        self,
        automation_hub: Optional[Any] = None,
        n8n_monitor: Optional[N8nMonitor] = None,
        celery_router: Optional[CeleryFallbackRouter] = None,
        test_mode: bool = False
    ):
        """
        Initialize N8nReliabilityHook.

        Args:
            automation_hub: AutomationHub instance for storing events
            n8n_monitor: N8nMonitor instance for failure detection
            celery_router: CeleryFallbackRouter instance for recovery routing
            test_mode: If True, run in test mode with in-memory storage
        """
        self.automation_hub = automation_hub
        self.n8n_monitor = n8n_monitor or N8nMonitor(automation_hub=automation_hub, test_mode=test_mode)
        self.celery_router = celery_router or CeleryFallbackRouter(automation_hub=automation_hub, test_mode=test_mode)
        self.test_mode = test_mode
        self._task_registry: Dict[str, Dict[str, Any]] = {}

    def on_task_started(
        self,
        task_id: str,
        workflow_name: str,
        input_params: Dict
    ) -> str:
        """
        Register n8n task for monitoring (PreToolUse phase).

        Args:
            task_id: Unique task identifier
            workflow_name: n8n workflow name
            input_params: Task input parameters

        Returns:
            Monitor ID to use when reporting results
        """
        monitor_id = self.n8n_monitor.register_task(
            task_id=task_id,
            workflow_name=workflow_name,
            input_params=input_params
        )

        # Store locally for tracking
        self._task_registry[monitor_id] = {
            "task_id": task_id,
            "workflow_name": workflow_name,
            "input_params": input_params
        }

        return monitor_id

    def on_task_completed(
        self,
        monitor_id: str,
        status_code: Optional[int],
        response: str,
        duration_seconds: float
    ) -> HookExecutionResult:
        """
        Handle task completion and trigger recovery if needed.

        Args:
            monitor_id: Monitor ID from on_task_started
            status_code: HTTP status code from n8n response
            response: Response body/message
            duration_seconds: Task execution duration

        Returns:
            HookExecutionResult with recovery status and event IDs
        """
        event_ids: List[int] = []

        try:
            # Report result to monitor (will detect failures and log events)
            monitor_result = self.n8n_monitor.report_result(
                monitor_id=monitor_id,
                status_code=status_code,
                response=response,
                duration_seconds=duration_seconds
            )

            # Log monitor's failure detection event if it created one
            if monitor_result.event_id is not None:
                event_ids.append(monitor_result.event_id)

            # Check if we should attempt recovery
            if self._should_attempt_fallback(monitor_result):
                recovery_result = self._execute_recovery(monitor_result)

                # Prepare recovery event to log
                recovery_event_id = self._log_recovery_event(
                    monitor_result=monitor_result,
                    recovery_result=recovery_result
                )

                if recovery_event_id is not None:
                    event_ids.append(recovery_event_id)

                # Return result with recovery details
                return HookExecutionResult(
                    hook_executed=True,
                    task_id=monitor_result.task_id,
                    failure_detected=monitor_result.failure_detected,
                    recovery_attempted=True,
                    recovery_successful=recovery_result.recovery_successful,
                    failure_type=monitor_result.failure_type.value if monitor_result.failure_type != FailureType.NO_FAILURE else None,
                    recovery_method=recovery_result.recovery_method,
                    reason=recovery_result.routing_result.reason if recovery_result.routing_result else "Recovery attempted",
                    event_ids=event_ids
                )
            else:
                # No failure or failure not recoverable
                return HookExecutionResult(
                    hook_executed=True,
                    task_id=monitor_result.task_id,
                    failure_detected=monitor_result.failure_detected,
                    recovery_attempted=False,
                    recovery_successful=False,
                    failure_type=monitor_result.failure_type.value if monitor_result.failure_type != FailureType.NO_FAILURE else None,
                    recovery_method=None,
                    reason=monitor_result.reason,
                    event_ids=event_ids
                )

        except Exception as e:
            logger.error(f"Error in N8nReliabilityHook.on_task_completed: {e}")
            return HookExecutionResult(
                hook_executed=False,
                task_id="unknown",
                failure_detected=False,
                recovery_attempted=False,
                recovery_successful=False,
                failure_type=None,
                recovery_method=None,
                reason=f"Hook error: {str(e)}",
                event_ids=event_ids
            )

    def _should_attempt_fallback(self, monitor_result: MonitorResult) -> bool:
        """
        Check if failure is detected and recoverable.

        Args:
            monitor_result: Result from N8nMonitor

        Returns:
            True if recovery should be attempted
        """
        # Must have detected a failure
        if not monitor_result.failure_detected:
            return False

        # Must have a valid task ID
        if not monitor_result.task_id or not monitor_result.task_id.strip():
            return False

        # Must be a mapped workflow (can be routed to Celery)
        from tools_db.tools.celery_fallback_router import N8N_TO_CELERY_MAPPING
        if monitor_result.workflow_name not in N8N_TO_CELERY_MAPPING:
            # Task not in mapping - still route but will be marked as no mapping available
            pass

        return True

    def _execute_recovery(self, monitor_result: MonitorResult) -> RecoveryResult:
        """
        Execute recovery workflow using CeleryFallbackRouter.

        Args:
            monitor_result: MonitorResult indicating failure

        Returns:
            RecoveryResult with success/failure and method used
        """
        try:
            routing_result = self.celery_router.route_failure(monitor_result)

            if routing_result.routed and routing_result.execution_result:
                return RecoveryResult(
                    recovery_successful=routing_result.execution_result.success,
                    recovery_method=routing_result.execution_result.attempt_method,
                    routing_result=routing_result,
                    execution_time_seconds=routing_result.execution_result.execution_time_seconds,
                    error_message=routing_result.execution_result.error_message
                )
            else:
                # Routing failed (no mapping available, etc.)
                return RecoveryResult(
                    recovery_successful=False,
                    recovery_method=None,
                    routing_result=routing_result,
                    execution_time_seconds=0.0,
                    error_message=routing_result.reason
                )

        except Exception as e:
            logger.error(f"Error executing recovery: {e}")
            return RecoveryResult(
                recovery_successful=False,
                recovery_method=None,
                routing_result=None,
                execution_time_seconds=0.0,
                error_message=str(e)
            )

    def _log_recovery_event(
        self,
        monitor_result: MonitorResult,
        recovery_result: RecoveryResult
    ) -> Optional[int]:
        """
        Log recovery attempt event to automation_events.

        Args:
            monitor_result: Original MonitorResult
            recovery_result: RecoveryResult from recovery attempt

        Returns:
            Event ID if logged, None if hub unavailable
        """
        if not self.automation_hub:
            return None

        try:
            # Prepare evidence
            evidence = {
                "task_id": monitor_result.task_id,
                "workflow_name": monitor_result.workflow_name,
                "failure_type": monitor_result.failure_type.value if monitor_result.failure_type else None,
                "original_status_code": monitor_result.status_code,
                "recovery_successful": recovery_result.recovery_successful,
                "recovery_method": recovery_result.recovery_method,
                "execution_time": recovery_result.execution_time_seconds,
                "error_message": recovery_result.error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Determine status
            status = "success" if recovery_result.recovery_successful else "failed"

            # Prepare metadata
            metadata = {
                "hook_type": "n8n_reliability",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Create event
            event = AutomationEvent(
                event_type="n8n_recovery_attempted",
                project_id="n8n",
                status=status,
                evidence=evidence,
                detected_from="hook",
                metadata=metadata
            )

            # Store event
            event_id = self.automation_hub.store_event(event)
            return event_id

        except Exception as e:
            logger.error(f"Error logging recovery event: {e}")
            return None
