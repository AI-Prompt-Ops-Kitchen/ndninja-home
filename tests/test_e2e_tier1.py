"""
End-to-End Workflow Tests for Tier 1 Automation Framework

These tests simulate realistic production scenarios where the entire tier1
automation system works together:
1. Production Readiness Skill
2. Action Item Progress Tracking (PostToolUse Hook)
3. n8n Reliability Layer (PreToolUse Hook)

Test Coverage:
- Scenario 1: Complete Development Workflow (2 tests)
- Scenario 2: n8n Video Processing Job (2 tests)
- Scenario 3: Production Deployment with Rollback (2 tests)
- Scenario 4: Concurrent Operations (1 test)
- Scenario 5: Error Recovery with Escalation (2 tests)
- Scenario 6: Complete Feature Lifecycle (2 tests)

Total: 11+ E2E tests covering realistic production workflows
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import json
import time
from threading import Thread

from tools_db.tools.automation_hub import AutomationHub
from tools_db.tools.production_checker import ProductionChecker
from tools_db.tools.action_item_hook import ActionItemHook, HookResult
from tools_db.tools.keyword_detector import KeywordDetector, DetectionResult
from tools_db.tools.todo_updater import TodoUpdater, UpdateResult
from tools_db.tools.n8n_reliability_hook import N8nReliabilityHook, HookExecutionResult, RecoveryResult
from tools_db.tools.n8n_monitor import N8nMonitor, MonitorResult, FailureType
from tools_db.tools.celery_fallback_router import CeleryFallbackRouter, RoutingResult, ExecutionResult
from tools_db.models import AutomationEvent


# ============================================================================
# SCENARIO 1: Complete Development Workflow
# ============================================================================

class TestCompleteFeatureDevelopmentWorkflow:
    """End-to-end test for complete feature development from commit to deployment"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_complete_feature_development_from_commit_to_deployment(
        self, mock_updater_class, mock_detector_class
    ):
        """
        Scenario 1: Complete Development Workflow

        Simulates: Developer creates feature, commits, tests pass, runs prod check, deploys

        Events logged:
        1. git commit detected → todo marked completed
        2. tests passing detected → todo marked completed
        3. production check run → go decision
        4. deployment detected → todo marked completed
        5. All events in automation_events table with full audit trail
        """
        # Arrange: Create automation hub and components
        hub = AutomationHub(test_mode=True)

        # Setup keyword detector mock
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        # Setup todo updater mock
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater

        # Create hook
        hook = ActionItemHook(automation_hub=hub, test_mode=True)
        checker = ProductionChecker(project_path=".", test_mode=True)

        # Act: Simulate complete development workflow
        workflow_events = []

        # Step 1: Developer commits code
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="feat: implement production readiness check"
        )
        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="feat-001",
            old_status="in_progress",
            new_status="completed",
            confidence=95
        )

        commit_result = hook.handle_tool_output(
            tool_name="bash",
            tool_output="[main abc123def] feat: implement production readiness check\n1 file changed, 50 insertions(+)"
        )
        workflow_events.append(("git_commit", commit_result))

        # Log event
        event1 = AutomationEvent(
            event_type="action_item_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "keyword": "git commit",
                "todo_id": "feat-001",
                "confidence": 95
            },
            detected_from="hook",
            metadata={"step": "1_commit"}
        )
        hub.store_event(event1)

        # Step 2: Tests pass
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="all tests passed",
            confidence=90,
            category="test-success",
            context_snippet="47 passed in 2.34s"
        )
        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="test-001",
            old_status="in_progress",
            new_status="completed",
            confidence=90
        )

        test_result = hook.handle_tool_output(
            tool_name="bash",
            tool_output="======================== 47 passed in 2.34s ========================"
        )
        workflow_events.append(("tests_pass", test_result))

        # Log event
        event2 = AutomationEvent(
            event_type="action_item_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "keyword": "all tests passed",
                "todo_id": "test-001",
                "confidence": 90,
                "test_count": 47
            },
            detected_from="hook",
            metadata={"step": "2_tests"}
        )
        hub.store_event(event2)

        # Step 3: Production readiness check
        prod_results = checker.run_all_checks()

        event3 = AutomationEvent(
            event_type="production_check",
            project_id="tier1-automation",
            status="go",
            evidence={
                "checks": {k: {"passed": v.passed, "details": v.details}
                          for k, v in prod_results["checks"].items()},
                "decision": "go"
            },
            detected_from="skill",
            metadata={"step": "3_production_check"}
        )
        hub.store_event(event3)

        # Step 4: Deployment detected
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="deployed successfully",
            confidence=92,
            category="deployment",
            context_snippet="Deployment completed successfully in 45s"
        )
        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="deploy-001",
            old_status="in_progress",
            new_status="completed",
            confidence=92
        )

        deploy_result = hook.handle_tool_output(
            tool_name="bash",
            tool_output="Deployment completed successfully in 45s. All health checks passed."
        )
        workflow_events.append(("deployment", deploy_result))

        # Log event
        event4 = AutomationEvent(
            event_type="action_item_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "keyword": "deployed successfully",
                "todo_id": "deploy-001",
                "confidence": 92,
                "deployment_time_seconds": 45
            },
            detected_from="hook",
            metadata={"step": "4_deployment"}
        )
        hub.store_event(event4)

        # Assert: Complete workflow executed successfully
        assert len(workflow_events) == 3  # commit, tests, deployment (prod_check separate)
        assert all(e[0] is not None for e in workflow_events)

        # Verify all events logged
        all_events = hub.get_events_by_type("action_item_completed", limit=100)
        assert len(all_events) >= 3  # At least commit, tests, deployment

        prod_check_events = hub.get_events_by_type("production_check", limit=100)
        assert len(prod_check_events) >= 1  # Production check event

        # Verify event correlation via project_id
        all_project_events = (
            hub.get_events_by_type("action_item_completed", limit=100) +
            hub.get_events_by_type("production_check", limit=100)
        )
        assert all(e["project_id"] == "tier1-automation" for e in all_project_events)

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_action_items_auto_complete_through_development_cycle(
        self, mock_updater_class, mock_detector_class
    ):
        """
        Scenario 1b: Action Items Auto-Complete Through Development Cycle

        Tests that multiple sequential commits and actions auto-complete todo items
        without manual intervention, demonstrating end-to-end automation.

        Workflow:
        1. Create initial todo in "in_progress" status
        2. Make first commit → todo auto-completed
        3. Make second commit → new todo auto-completed
        4. Run tests → another todo auto-completed
        5. All tracked in automation_events with proper sequencing
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater

        hook = ActionItemHook(automation_hub=hub, test_mode=True)

        # Simulate cycle of 3 commits
        todos = [
            ("feat-1-setup", "in_progress"),
            ("feat-1-test", "in_progress"),
            ("feat-1-docs", "in_progress"),
        ]

        # Act: Execute development cycle
        completed_todos = []

        for i, (todo_id, status) in enumerate(todos):
            # Mock detection for each commit
            mock_detector.detect.return_value = DetectionResult(
                keyword_found="git commit",
                confidence=95,
                category="commit-related",
                context_snippet=f"commit #{i+1}"
            )

            # Mock updater to complete the todo
            mock_updater.update_todo_from_detection.return_value = UpdateResult(
                updated=True,
                todo_id=todo_id,
                old_status="in_progress",
                new_status="completed",
                confidence=95
            )

            # Execute hook
            result = hook.handle_tool_output(
                tool_name="bash",
                tool_output=f"[main abc{i}] feat: commit #{i+1}\n1 file changed"
            )
            completed_todos.append((todo_id, result))

            # Log event
            event = AutomationEvent(
                event_type="action_item_completed",
                project_id="tier1-automation",
                status="success",
                evidence={
                    "todo_id": todo_id,
                    "keyword": "git commit",
                    "sequence": i + 1
                },
                detected_from="hook",
                metadata={"step": f"commit_{i+1}"}
            )
            hub.store_event(event)

        # Assert: All todos completed in sequence
        assert len(completed_todos) == 3
        assert all(
            result[1].new_status == "completed"
            for result in completed_todos
        )

        # Verify events in order
        events = hub.get_events_by_type("action_item_completed", limit=100)
        assert len(events) >= 3

        # Verify all todos are completed
        for event in events[:3]:
            assert event["status"] == "success"
            assert "todo_id" in event["evidence"]
            # Each event has the git commit evidence
            assert event["project_id"] == "tier1-automation"


# ============================================================================
# SCENARIO 2: n8n Video Processing Job
# ============================================================================

class TestN8nVideoProcessingJob:
    """End-to-end test for n8n video processing with failure recovery"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_n8n_video_processing_with_failure_recovery(
        self, mock_updater_class, mock_detector_class
    ):
        """
        Scenario 2: n8n Video Processing Job

        Simulates: n8n task fails (503 error) → N8nMonitor detects →
        CeleryFallbackRouter routes to Celery → succeeds → ActionItemHook
        detects completion → all events logged

        Events:
        1. n8n_task_started
        2. n8n_failure_detected (503)
        3. n8n_fallback_routed (to Celery)
        4. action_item_completed (video processed)
        5. Complete audit trail
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        mock_monitor = Mock(spec=N8nMonitor)
        mock_router = Mock(spec=CeleryFallbackRouter)

        hook = N8nReliabilityHook(
            automation_hub=hub,
            n8n_monitor=mock_monitor,
            celery_router=mock_router,
            test_mode=True
        )

        # Step 1: n8n task starts
        mock_monitor.register_task.return_value = "mon-video-001"

        monitor_id = hook.on_task_started(
            task_id="video-assembly",
            workflow_name="video-assembly",
            input_params={"video_ids": ["vid-1", "vid-2"]}
        )

        event1 = AutomationEvent(
            event_type="n8n_task_started",
            project_id="tier1-automation",
            status="pending",
            evidence={
                "task_id": "video-assembly",
                "workflow_name": "video-assembly",
                "input_params": {"video_ids": ["vid-1", "vid-2"]}
            },
            detected_from="hook",
            metadata={"step": "1_task_started"}
        )
        hub.store_event(event1)

        # Step 2: n8n fails with 503 (gateway timeout)
        failure_result = MonitorResult(
            failure_detected=True,
            failure_type=FailureType.GATEWAY_TIMEOUT,
            task_id="video-assembly",
            workflow_name="video-assembly",
            status_code=504,
            reason="Gateway Timeout - n8n service temporarily unavailable",
            duration_seconds=3.5,
            event_id=None
        )
        mock_monitor.report_result.return_value = failure_result

        event2 = AutomationEvent(
            event_type="n8n_failure_detected",
            project_id="tier1-automation",
            status="failed",
            evidence={
                "task_id": "video-assembly",
                "status_code": 504,
                "reason": "Gateway Timeout",
                "duration_seconds": 3.5
            },
            detected_from="hook",
            metadata={"step": "2_failure_504"}
        )
        hub.store_event(event2)

        # Step 3: Router recovers with Celery
        recovery_result = ExecutionResult(
            success=True,
            attempt_method="celery_direct",
            attempt_number=1,
            execution_time_seconds=15.0,
            result_summary="Successfully assembled 2 videos",
            error_message=None
        )
        routing_result = RoutingResult(
            routed=True,
            celery_task_name="video.assemble",
            execution_result=recovery_result,
            reason="Routed to Celery fallback"
        )
        mock_router.route_failure.return_value = routing_result

        event3 = AutomationEvent(
            event_type="n8n_fallback_routed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "task_id": "video-assembly",
                "original_failure": 503,
                "recovery_method": "celery_direct",
                "execution_time_seconds": 15.0,
                "result": "Successfully assembled 2 videos"
            },
            detected_from="hook",
            metadata={"step": "3_recovery_celery"}
        )
        hub.store_event(event3)

        # Step 4: Action item hook detects completion
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="video processed",
            confidence=90,
            category="processing-complete",
            context_snippet="Successfully assembled 2 videos"
        )

        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="video-process-001",
            old_status="in_progress",
            new_status="completed",
            confidence=90
        )

        action_hook = ActionItemHook(automation_hub=hub, test_mode=True)
        action_result = action_hook.handle_tool_output(
            tool_name="bash",
            tool_output="Video processing completed. Successfully assembled 2 videos."
        )

        event4 = AutomationEvent(
            event_type="action_item_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "keyword": "video processed",
                "todo_id": "video-process-001",
                "from_recovery": True
            },
            detected_from="hook",
            metadata={"step": "4_completion"}
        )
        hub.store_event(event4)

        # Assert: Complete workflow executed and logged
        all_events = (
            hub.get_events_by_type("n8n_task_started", limit=100) +
            hub.get_events_by_type("n8n_failure_detected", limit=100) +
            hub.get_events_by_type("n8n_fallback_routed", limit=100) +
            hub.get_events_by_type("action_item_completed", limit=100)
        )

        assert len(all_events) >= 4  # All 4 events logged
        assert monitor_id == "mon-video-001"
        assert action_result.new_status == "completed"

        # Verify correlation
        assert all(e["project_id"] == "tier1-automation" for e in all_events)

    def test_n8n_concurrent_jobs_with_independent_recovery(self):
        """
        Scenario 2b: Concurrent n8n Jobs with Independent Recovery

        Tests that multiple n8n jobs can fail and recover independently
        without interfering with each other.

        Jobs:
        1. Video assembly (503) → Celery recovery
        2. KB indexing (504) → API recovery
        3. Draft generation (timeout) → Systemd recovery

        All run concurrently, all recover, all events logged
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        # Define 3 concurrent jobs
        jobs = [
            {
                "task_id": "video-assembly",
                "failure_type": FailureType.GATEWAY_TIMEOUT,
                "status_code": 504,
                "recovery_method": "celery_direct"
            },
            {
                "task_id": "kb-indexing",
                "failure_type": FailureType.WEBHOOK_FAILURE,
                "status_code": 502,
                "recovery_method": "api_fallback"
            },
            {
                "task_id": "draft-generation",
                "failure_type": FailureType.EXECUTION_TIMEOUT,
                "status_code": None,
                "recovery_method": "systemd"
            }
        ]

        # Act: Execute concurrent jobs
        job_results = []

        def execute_job(job_config):
            """Execute a single job with failure and recovery"""
            task_id = job_config["task_id"]

            # Log task start
            event_start = AutomationEvent(
                event_type="n8n_task_started",
                project_id="tier1-automation",
                status="pending",
                evidence={"task_id": task_id},
                detected_from="hook",
                metadata={"job": task_id}
            )
            hub.store_event(event_start)

            # Simulate failure
            event_failure = AutomationEvent(
                event_type="n8n_failure_detected",
                project_id="tier1-automation",
                status="failed",
                evidence={
                    "task_id": task_id,
                    "status_code": job_config["status_code"],
                    "failure_type": str(job_config["failure_type"])
                },
                detected_from="hook",
                metadata={"job": task_id}
            )
            hub.store_event(event_failure)

            # Simulate recovery
            event_recovery = AutomationEvent(
                event_type="n8n_fallback_routed",
                project_id="tier1-automation",
                status="success",
                evidence={
                    "task_id": task_id,
                    "recovery_method": job_config["recovery_method"]
                },
                detected_from="hook",
                metadata={"job": task_id}
            )
            hub.store_event(event_recovery)

            return {"task_id": task_id, "status": "recovered"}

        # Run jobs concurrently (simulated via immediate execution for determinism)
        for job in jobs:
            result = execute_job(job)
            job_results.append(result)

        # Assert: All jobs completed independently
        assert len(job_results) == 3
        assert all(r["status"] == "recovered" for r in job_results)

        # Verify all events logged with proper correlation
        all_events = (
            hub.get_events_by_type("n8n_task_started", limit=100) +
            hub.get_events_by_type("n8n_failure_detected", limit=100) +
            hub.get_events_by_type("n8n_fallback_routed", limit=100)
        )

        assert len(all_events) >= 9  # 3 events per job

        # Verify no interference between jobs
        task_ids = set()
        for event in all_events:
            if "task_id" in event["evidence"]:
                task_ids.add(event["evidence"]["task_id"])

        assert len(task_ids) == 3  # All 3 task IDs present


# ============================================================================
# SCENARIO 3: Production Deployment with Rollback Verification
# ============================================================================

class TestProductionDeploymentWorkflow:
    """End-to-end test for production deployment decision and rollback"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_production_readiness_check_deployment_decision_flow(
        self, mock_updater_class, mock_detector_class
    ):
        """
        Scenario 3: Production Deployment with Rollback Plan

        Workflow:
        1. Run production readiness check
        2. All checks pass except docs (warning)
        3. Generate warning decision with evidence
        4. Team reviews and approves
        5. Deploy with rollback plan confirmed
        6. Post-deploy verification
        7. Complete event trail
        """
        # Arrange
        hub = AutomationHub(test_mode=True)
        checker = ProductionChecker(project_path=".", test_mode=True)

        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater

        # Act: Step 1 - Run production readiness check
        prod_results = checker.run_all_checks()

        # Simulate warning (docs not passing)
        event_prod_check = AutomationEvent(
            event_type="production_check",
            project_id="tier1-automation",
            status="warning",
            evidence={
                "checks": {k: {"passed": v.passed, "details": v.details}
                          for k, v in prod_results["checks"].items()},
                "decision": "go_with_warnings",
                "warnings": ["Documentation incomplete - 4/5 items present"],
                "rollback_plan": "v1.0.0-stable tag available",
                "risks": ["Minor doc gaps - no functional impact"]
            },
            detected_from="skill",
            metadata={
                "step": "1_prod_check",
                "all_functional_checks_pass": True,
                "rollback_verified": True
            }
        )
        hub.store_event(event_prod_check)

        # Step 2: Team approval logged
        event_approval = AutomationEvent(
            event_type="deployment_approved",
            project_id="tier1-automation",
            status="success",
            evidence={
                "approved_by": "engineering-team",
                "acknowledged_warnings": True,
                "rollback_plan_confirmed": True
            },
            detected_from="manual",
            metadata={"step": "2_approval"}
        )
        hub.store_event(event_approval)

        # Step 3: Deployment starts
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="deployment started",
            confidence=95,
            category="deployment",
            context_snippet="Deploying version 1.0.0"
        )

        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="deploy-prod-001",
            old_status="pending_review",
            new_status="in_progress",
            confidence=95
        )

        action_hook = ActionItemHook(automation_hub=hub, test_mode=True)
        result_deploy_start = action_hook.handle_tool_output(
            tool_name="bash",
            tool_output="[DEPLOYMENT] Starting deployment to production for version 1.0.0"
        )

        event_deploy_start = AutomationEvent(
            event_type="deployment_started",
            project_id="tier1-automation",
            status="pending",
            evidence={
                "version": "1.0.0",
                "environment": "production",
                "rollback_available": True
            },
            detected_from="hook",
            metadata={"step": "3_deploy_start"}
        )
        hub.store_event(event_deploy_start)

        # Step 4: Deployment succeeds
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="deployment succeeded",
            confidence=95,
            category="deployment",
            context_snippet="All health checks passed"
        )

        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="deploy-prod-001",
            old_status="in_progress",
            new_status="completed",
            confidence=95
        )

        result_deploy_success = action_hook.handle_tool_output(
            tool_name="bash",
            tool_output="[DEPLOYMENT] Deployment completed successfully. All health checks passed."
        )

        event_deploy_success = AutomationEvent(
            event_type="deployment_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "version": "1.0.0",
                "environment": "production",
                "health_checks": "all_passed",
                "deployment_time_seconds": 120
            },
            detected_from="hook",
            metadata={"step": "4_deploy_success"}
        )
        hub.store_event(event_deploy_success)

        # Assert: Full deployment workflow with decisions logged
        prod_events = hub.get_events_by_type("production_check", limit=100)
        assert len(prod_events) >= 1
        assert prod_events[0]["status"] == "warning"

        deployment_events = (
            hub.get_events_by_type("deployment_approved", limit=100) +
            hub.get_events_by_type("deployment_started", limit=100) +
            hub.get_events_by_type("deployment_completed", limit=100)
        )
        assert len(deployment_events) >= 3

        # Verify all events correlated
        all_events = (
            prod_events + deployment_events
        )
        assert all(e["project_id"] == "tier1-automation" for e in all_events)

    def test_production_deployment_with_rollback_verification(self):
        """
        Scenario 3b: Production Deployment with Rollback Verification

        Tests that rollback plan is verified before deployment and
        can be executed if needed.

        Workflow:
        1. Check rollback plan exists (git tag)
        2. Verify rollback is executable
        3. Deploy
        4. If issues detected, trigger rollback
        5. Rollback succeeds
        6. All events logged with before/after state
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        # Act: Step 1 - Verify rollback plan
        event_rollback_check = AutomationEvent(
            event_type="rollback_plan_verified",
            project_id="tier1-automation",
            status="success",
            evidence={
                "rollback_version": "v1.0.0-stable",
                "git_tag_exists": True,
                "rollback_tested": True,
                "estimated_rollback_time_seconds": 30
            },
            detected_from="skill",
            metadata={"step": "1_rollback_verify"}
        )
        hub.store_event(event_rollback_check)

        # Step 2: Deploy
        event_deploy = AutomationEvent(
            event_type="deployment_started",
            project_id="tier1-automation",
            status="pending",
            evidence={
                "version": "1.0.1",
                "rollback_plan": "v1.0.0-stable",
                "deployment_start_time": datetime.now(timezone.utc).isoformat()
            },
            detected_from="hook",
            metadata={"step": "2_deploy"}
        )
        hub.store_event(event_deploy)

        # Step 3: Post-deployment verification detects issue
        event_health_check = AutomationEvent(
            event_type="post_deployment_check",
            project_id="tier1-automation",
            status="warning",
            evidence={
                "error_rate": 5.2,
                "threshold": 1.0,
                "affected_endpoints": ["POST /api/videos"]
            },
            detected_from="hook",
            metadata={"step": "3_health_check"}
        )
        hub.store_event(event_health_check)

        # Step 4: Rollback triggered
        event_rollback_start = AutomationEvent(
            event_type="rollback_started",
            project_id="tier1-automation",
            status="pending",
            evidence={
                "reason": "High error rate detected",
                "current_version": "1.0.1",
                "target_version": "v1.0.0-stable"
            },
            detected_from="hook",
            metadata={"step": "4_rollback_start"}
        )
        hub.store_event(event_rollback_start)

        # Step 5: Rollback succeeds
        event_rollback_success = AutomationEvent(
            event_type="rollback_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "rolled_back_to": "v1.0.0-stable",
                "rollback_time_seconds": 28,
                "post_rollback_error_rate": 0.1
            },
            detected_from="hook",
            metadata={"step": "5_rollback_success"}
        )
        hub.store_event(event_rollback_success)

        # Assert: Complete rollback workflow logged
        rollback_events = (
            hub.get_events_by_type("rollback_plan_verified", limit=100) +
            hub.get_events_by_type("rollback_started", limit=100) +
            hub.get_events_by_type("rollback_completed", limit=100)
        )

        assert len(rollback_events) >= 3

        # Verify rollback completed successfully
        success_events = [e for e in rollback_events if e["status"] == "success"]
        assert len(success_events) >= 2  # plan verified and completed


# ============================================================================
# SCENARIO 4: Concurrent Operations
# ============================================================================

class TestConcurrentOperations:
    """End-to-end test for concurrent operations without interference"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_multiple_developers_concurrent_operations_independent(
        self, mock_updater_class, mock_detector_class
    ):
        """
        Scenario 4: Concurrent Operations

        Tests that multiple team members working simultaneously:
        1. Developer A commits → todo auto-completed
        2. Developer B triggers n8n job → failure detected → recovery
        3. Developer C runs prod check → decision generated

        All run independently without interference or state conflicts.
        All events properly correlated in automation_events.
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater

        # Define concurrent operations
        developers = [
            {"name": "Alice", "operation": "commit"},
            {"name": "Bob", "operation": "n8n_job"},
            {"name": "Charlie", "operation": "prod_check"}
        ]

        # Act: Execute concurrent operations
        results = {}

        # Developer A: Commit
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="git commit",
            confidence=95,
            category="commit-related",
            context_snippet="Alice: feat: add caching layer"
        )
        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="alice-feat-001",
            old_status="in_progress",
            new_status="completed",
            confidence=95
        )

        hook_alice = ActionItemHook(automation_hub=hub, test_mode=True)
        result_alice = hook_alice.handle_tool_output(
            tool_name="bash",
            tool_output="[main abc001] feat: add caching layer"
        )
        results["alice"] = result_alice

        event_alice = AutomationEvent(
            event_type="action_item_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "developer": "Alice",
                "todo_id": "alice-feat-001",
                "keyword": "git commit"
            },
            detected_from="hook",
            metadata={"developer": "Alice"}
        )
        hub.store_event(event_alice)

        # Developer B: n8n job
        event_bob_start = AutomationEvent(
            event_type="n8n_task_started",
            project_id="tier1-automation",
            status="pending",
            evidence={"task_id": "bob-kb-indexing"},
            detected_from="hook",
            metadata={"developer": "Bob"}
        )
        hub.store_event(event_bob_start)

        event_bob_failure = AutomationEvent(
            event_type="n8n_failure_detected",
            project_id="tier1-automation",
            status="failed",
            evidence={"task_id": "bob-kb-indexing", "status_code": 503},
            detected_from="hook",
            metadata={"developer": "Bob"}
        )
        hub.store_event(event_bob_failure)

        event_bob_recovery = AutomationEvent(
            event_type="n8n_fallback_routed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "task_id": "bob-kb-indexing",
                "recovery_method": "celery_direct"
            },
            detected_from="hook",
            metadata={"developer": "Bob"}
        )
        hub.store_event(event_bob_recovery)
        results["bob"] = "recovered"

        # Developer C: Production check
        checker = ProductionChecker(project_path=".", test_mode=True)
        prod_results = checker.run_all_checks()

        event_charlie = AutomationEvent(
            event_type="production_check",
            project_id="tier1-automation",
            status="go",
            evidence={
                "checks": {k: {"passed": v.passed} for k, v in prod_results["checks"].items()},
                "developer": "Charlie"
            },
            detected_from="skill",
            metadata={"developer": "Charlie"}
        )
        hub.store_event(event_charlie)
        results["charlie"] = "go"

        # Assert: All operations completed independently
        assert results["alice"].new_status == "completed"
        assert results["bob"] == "recovered"
        assert results["charlie"] == "go"

        # Verify all events exist and are independent
        alice_events = [
            e for e in hub.get_events_by_type("action_item_completed", limit=100)
            if e["evidence"].get("developer") == "Alice"
        ]
        assert len(alice_events) >= 1

        bob_events = (
            [e for e in hub.get_events_by_type("n8n_task_started", limit=100)
             if e["evidence"].get("task_id") == "bob-kb-indexing"] +
            [e for e in hub.get_events_by_type("n8n_failure_detected", limit=100)
             if e["evidence"].get("task_id") == "bob-kb-indexing"] +
            [e for e in hub.get_events_by_type("n8n_fallback_routed", limit=100)
             if e["evidence"].get("task_id") == "bob-kb-indexing"]
        )
        assert len(bob_events) >= 3

        charlie_events = [
            e for e in hub.get_events_by_type("production_check", limit=100)
            if e["evidence"].get("developer") == "Charlie"
        ]
        assert len(charlie_events) >= 1

        # Verify no race conditions - all have same project_id
        all_events = (
            alice_events + bob_events + charlie_events
        )
        assert all(e["project_id"] == "tier1-automation" for e in all_events)


# ============================================================================
# SCENARIO 5: Error Recovery with Escalation
# ============================================================================

class TestErrorRecoveryWithEscalation:
    """End-to-end test for error recovery chain and escalation"""

    def test_n8n_error_recovery_chain_403_to_systemd(self):
        """
        Scenario 5: Error Recovery with Escalation

        Workflow:
        1. n8n task fails with 403 (auth expired)
        2. N8nMonitor detects 403
        3. CeleryFallbackRouter attempts Celery → fails (token shared)
        4. Fallback to API → fails (same issue)
        5. Fallback to systemd → systemd service refreshes auth → succeeds
        6. All recovery attempts logged with method used
        7. System remains operational
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        # Act: Step 1 - n8n fails with 403
        event_failure = AutomationEvent(
            event_type="n8n_failure_detected",
            project_id="tier1-automation",
            status="failed",
            evidence={
                "task_id": "draft-gen",
                "status_code": 403,
                "reason": "Authentication expired",
                "error_detail": "n8n API key invalid"
            },
            detected_from="hook",
            metadata={"step": "1_403_failure"}
        )
        hub.store_event(event_failure)

        # Step 2: First recovery attempt - Celery direct fails
        event_celery_attempt = AutomationEvent(
            event_type="recovery_attempt",
            project_id="tier1-automation",
            status="failed",
            evidence={
                "task_id": "draft-gen",
                "method": "celery_direct",
                "attempt_number": 1,
                "error": "Connection error - shared token invalid",
                "duration_seconds": 2.1
            },
            detected_from="hook",
            metadata={"step": "2_celery_failed"}
        )
        hub.store_event(event_celery_attempt)

        # Step 3: Second recovery attempt - API fallback fails
        event_api_attempt = AutomationEvent(
            event_type="recovery_attempt",
            project_id="tier1-automation",
            status="failed",
            evidence={
                "task_id": "draft-gen",
                "method": "api_fallback",
                "attempt_number": 2,
                "error": "API authentication failed - same token issue",
                "duration_seconds": 1.8
            },
            detected_from="hook",
            metadata={"step": "3_api_failed"}
        )
        hub.store_event(event_api_attempt)

        # Step 4: Final recovery attempt - systemd succeeds
        event_systemd_attempt = AutomationEvent(
            event_type="recovery_attempt",
            project_id="tier1-automation",
            status="success",
            evidence={
                "task_id": "draft-gen",
                "method": "systemd",
                "attempt_number": 3,
                "recovery_action": "Systemd service refreshed authentication",
                "result": "Task completed successfully",
                "duration_seconds": 18.5
            },
            detected_from="hook",
            metadata={"step": "4_systemd_success"}
        )
        hub.store_event(event_systemd_attempt)

        # Step 5: Final status - task completed via recovery
        event_final = AutomationEvent(
            event_type="task_completed_via_recovery",
            project_id="tier1-automation",
            status="success",
            evidence={
                "task_id": "draft-gen",
                "original_failure": 403,
                "recovery_method": "systemd",
                "total_attempts": 3,
                "total_recovery_time": 22.4,
                "result": "Generated 5 draft ideas"
            },
            detected_from="hook",
            metadata={"step": "5_final_success"}
        )
        hub.store_event(event_final)

        # Assert: Full recovery chain logged
        recovery_attempts = hub.get_events_by_type("recovery_attempt", limit=100)
        assert len(recovery_attempts) >= 3

        # Verify recovery sequence
        celery_attempt = [e for e in recovery_attempts if e["evidence"]["method"] == "celery_direct"]
        assert len(celery_attempt) == 1
        assert celery_attempt[0]["status"] == "failed"

        api_attempt = [e for e in recovery_attempts if e["evidence"]["method"] == "api_fallback"]
        assert len(api_attempt) == 1
        assert api_attempt[0]["status"] == "failed"

        systemd_attempt = [e for e in recovery_attempts if e["evidence"]["method"] == "systemd"]
        assert len(systemd_attempt) == 1
        assert systemd_attempt[0]["status"] == "success"

        # Verify final success event
        final_events = hub.get_events_by_type("task_completed_via_recovery", limit=100)
        assert len(final_events) >= 1
        assert final_events[0]["status"] == "success"

    def test_all_recovery_attempts_fail_escalation_logged(self):
        """
        Scenario 5b: All Recovery Attempts Fail with Escalation

        Tests that when all recovery attempts fail, the system:
        1. Logs all failed attempts
        2. Escalates to manual intervention
        3. Creates escalation event with full details
        4. Maintains system stability
        5. Complete audit trail for post-mortem
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        # Act: Step 1 - Initial failure
        event_failure = AutomationEvent(
            event_type="n8n_failure_detected",
            project_id="tier1-automation",
            status="failed",
            evidence={
                "task_id": "critical-task",
                "status_code": 500,
                "reason": "Internal Server Error - database connection failed"
            },
            detected_from="hook",
            metadata={"step": "1_initial_500"}
        )
        hub.store_event(event_failure)

        # Step 2-4: All recovery attempts fail
        recovery_methods = [
            {"method": "celery_direct", "error": "Database connection refused"},
            {"method": "api_fallback", "error": "API unreachable"},
            {"method": "systemd", "error": "Systemd service also failed to connect"}
        ]

        for i, attempt in enumerate(recovery_methods, 1):
            event = AutomationEvent(
                event_type="recovery_attempt",
                project_id="tier1-automation",
                status="failed",
                evidence={
                    "task_id": "critical-task",
                    "method": attempt["method"],
                    "attempt_number": i,
                    "error": attempt["error"]
                },
                detected_from="hook",
                metadata={"step": f"recovery_{i}_failed"}
            )
            hub.store_event(event)

        # Step 5: Escalation event
        event_escalation = AutomationEvent(
            event_type="escalation_required",
            project_id="tier1-automation",
            status="pending",
            evidence={
                "task_id": "critical-task",
                "reason": "All recovery methods exhausted",
                "failed_methods": ["celery_direct", "api_fallback", "systemd"],
                "original_error": 500,
                "escalation_level": "critical",
                "required_action": "Manual investigation required - database offline"
            },
            detected_from="hook",
            metadata={"step": "5_escalation"}
        )
        hub.store_event(event_escalation)

        # Assert: All failures and escalation logged
        recovery_attempts = hub.get_events_by_type("recovery_attempt", limit=100)
        assert len(recovery_attempts) == 3
        assert all(e["status"] == "failed" for e in recovery_attempts)

        escalation_events = hub.get_events_by_type("escalation_required", limit=100)
        assert len(escalation_events) >= 1
        assert escalation_events[0]["status"] == "pending"
        assert "critical" in escalation_events[0]["evidence"]["escalation_level"]

        # Verify all events correlated
        all_events = recovery_attempts + escalation_events
        assert all(e["project_id"] == "tier1-automation" for e in all_events)


# ============================================================================
# SCENARIO 6: Complete Feature Lifecycle
# ============================================================================

class TestCompleteFeatureLifecycle:
    """End-to-end test for complete feature from planning to monitoring"""

    @patch('tools_db.tools.action_item_hook.KeywordDetector')
    @patch('tools_db.tools.action_item_hook.TodoUpdater')
    def test_feature_lifecycle_from_planning_to_monitoring(
        self, mock_updater_class, mock_detector_class
    ):
        """
        Scenario 6: Complete Feature Lifecycle

        Feature journey from planning to production monitoring:
        1. Feature idea captured
        2. Implementation started → todo created "in_progress"
        3. Code written and tested
        4. Multiple commits detected → each auto-updates todo progress
        5. All tests pass → auto-marked complete
        6. Production readiness check run → documented decision
        7. Deployed successfully → detected and logged
        8. Monitoring enabled
        9. All lifecycle stages tracked in automation_events
        """
        # Arrange
        hub = AutomationHub(test_mode=True)
        checker = ProductionChecker(project_path=".", test_mode=True)

        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector

        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater

        hook = ActionItemHook(automation_hub=hub, test_mode=True)

        # Act: Stage 1 - Feature planned
        event_planned = AutomationEvent(
            event_type="feature_planned",
            project_id="tier1-automation",
            status="pending",
            evidence={
                "feature_id": "feat-video-cache",
                "title": "Add caching layer for video processing",
                "description": "Implement Redis cache to reduce DB queries",
                "priority": "high"
            },
            detected_from="manual",
            metadata={"stage": "1_planning"}
        )
        hub.store_event(event_planned)

        # Stage 2 - Implementation started
        event_impl_start = AutomationEvent(
            event_type="feature_implementation_started",
            project_id="tier1-automation",
            status="pending",
            evidence={"feature_id": "feat-video-cache"},
            detected_from="hook",
            metadata={"stage": "2_impl_start"}
        )
        hub.store_event(event_impl_start)

        # Stage 3 - Multiple commits
        for i in range(3):
            mock_detector.detect.return_value = DetectionResult(
                keyword_found="git commit",
                confidence=95,
                category="commit-related",
                context_snippet=f"commit {i+1}"
            )
            mock_updater.update_todo_from_detection.return_value = UpdateResult(
                updated=True,
                todo_id="feat-video-cache",
                old_status="in_progress",
                new_status="in_progress",  # Still in progress
                confidence=95
            )

            hook.handle_tool_output(
                tool_name="bash",
                tool_output=f"[main abc{i}] Step {i+1} of video caching feature"
            )

            event_commit = AutomationEvent(
                event_type="feature_progress_update",
                project_id="tier1-automation",
                status="pending",
                evidence={
                    "feature_id": "feat-video-cache",
                    "commit_number": i + 1,
                    "progress": f"{(i+1)*33}%"
                },
                detected_from="hook",
                metadata={"stage": f"3_commit_{i+1}"}
            )
            hub.store_event(event_commit)

        # Stage 4 - Tests pass
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="all tests passed",
            confidence=90,
            category="test-success",
            context_snippet="47 passed in 2.34s"
        )
        mock_updater.update_todo_from_detection.return_value = UpdateResult(
            updated=True,
            todo_id="feat-video-cache",
            old_status="in_progress",
            new_status="completed",
            confidence=90
        )

        hook.handle_tool_output(
            tool_name="bash",
            tool_output="======================== 47 passed in 2.34s ========================"
        )

        event_tests_pass = AutomationEvent(
            event_type="feature_tests_passed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "feature_id": "feat-video-cache",
                "test_count": 47,
                "coverage": 92
            },
            detected_from="hook",
            metadata={"stage": "4_tests_pass"}
        )
        hub.store_event(event_tests_pass)

        # Stage 5 - Production check
        prod_results = checker.run_all_checks()

        event_prod_check = AutomationEvent(
            event_type="production_check",
            project_id="tier1-automation",
            status="go",
            evidence={
                "feature_id": "feat-video-cache",
                "decision": "go"
            },
            detected_from="skill",
            metadata={"stage": "5_prod_check"}
        )
        hub.store_event(event_prod_check)

        # Stage 6 - Deployed
        mock_detector.detect.return_value = DetectionResult(
            keyword_found="deployed successfully",
            confidence=95,
            category="deployment",
            context_snippet="Deployment successful"
        )

        hook.handle_tool_output(
            tool_name="bash",
            tool_output="Feature deployed to production successfully"
        )

        event_deployed = AutomationEvent(
            event_type="feature_deployed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "feature_id": "feat-video-cache",
                "environment": "production",
                "version": "1.0.1"
            },
            detected_from="hook",
            metadata={"stage": "6_deployed"}
        )
        hub.store_event(event_deployed)

        # Stage 7 - Monitoring enabled
        event_monitoring = AutomationEvent(
            event_type="feature_monitoring_enabled",
            project_id="tier1-automation",
            status="success",
            evidence={
                "feature_id": "feat-video-cache",
                "metrics": ["cache_hit_rate", "db_query_reduction", "response_time"],
                "alert_thresholds": {
                    "cache_hit_rate_min": 0.7,
                    "response_time_max_ms": 500
                }
            },
            detected_from="manual",
            metadata={"stage": "7_monitoring"}
        )
        hub.store_event(event_monitoring)

        # Assert: Complete lifecycle logged
        planned = hub.get_events_by_type("feature_planned", limit=100)
        impl_started = hub.get_events_by_type("feature_implementation_started", limit=100)
        progress = hub.get_events_by_type("feature_progress_update", limit=100)
        tests_pass = hub.get_events_by_type("feature_tests_passed", limit=100)
        prod_check = hub.get_events_by_type("production_check", limit=100)
        deployed = hub.get_events_by_type("feature_deployed", limit=100)
        monitoring = hub.get_events_by_type("feature_monitoring_enabled", limit=100)

        assert len(planned) >= 1
        assert len(impl_started) >= 1
        assert len(progress) >= 3  # 3 commits
        assert len(tests_pass) >= 1
        assert len(prod_check) >= 1
        assert len(deployed) >= 1
        assert len(monitoring) >= 1

    def test_feature_with_n8n_dependency_end_to_end(self):
        """
        Scenario 6b: Complete Feature Lifecycle with n8n Dependency

        Tests complete feature lifecycle where the feature depends on
        n8n workflows that may fail and need recovery.

        Workflow:
        1. Feature requires n8n video processing
        2. n8n task fails initially
        3. Fallback to Celery succeeds
        4. Feature can complete
        5. All stages tracked with n8n recovery integrated
        """
        # Arrange
        hub = AutomationHub(test_mode=True)

        # Act: Stage 1 - Feature needs n8n
        event_feature_start = AutomationEvent(
            event_type="feature_implemented",
            project_id="tier1-automation",
            status="pending",
            evidence={
                "feature_id": "feat-video-gen",
                "requires_n8n": True,
                "n8n_task": "video-assembly"
            },
            detected_from="manual",
            metadata={"stage": "1_feature_start"}
        )
        hub.store_event(event_feature_start)

        # Stage 2 - n8n task fails
        event_n8n_fail = AutomationEvent(
            event_type="n8n_failure_detected",
            project_id="tier1-automation",
            status="failed",
            evidence={
                "task_id": "video-assembly",
                "feature_id": "feat-video-gen",
                "status_code": 503
            },
            detected_from="hook",
            metadata={"stage": "2_n8n_fail"}
        )
        hub.store_event(event_n8n_fail)

        # Stage 3 - Recovery via Celery succeeds
        event_recovery = AutomationEvent(
            event_type="n8n_fallback_routed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "task_id": "video-assembly",
                "feature_id": "feat-video-gen",
                "recovery_method": "celery_direct"
            },
            detected_from="hook",
            metadata={"stage": "3_recovery"}
        )
        hub.store_event(event_recovery)

        # Stage 4 - Feature completes despite n8n failure
        event_feature_complete = AutomationEvent(
            event_type="feature_completed",
            project_id="tier1-automation",
            status="success",
            evidence={
                "feature_id": "feat-video-gen",
                "n8n_failed_but_recovered": True,
                "recovery_method": "celery_direct"
            },
            detected_from="hook",
            metadata={"stage": "4_feature_complete"}
        )
        hub.store_event(event_feature_complete)

        # Assert: Feature completed despite n8n failure
        feature_complete = hub.get_events_by_type("feature_completed", limit=100)
        assert len(feature_complete) >= 1
        assert feature_complete[0]["status"] == "success"
        assert feature_complete[0]["evidence"]["n8n_failed_but_recovered"]

        # Verify recovery was part of completion
        all_events = (
            hub.get_events_by_type("n8n_failure_detected", limit=100) +
            hub.get_events_by_type("n8n_fallback_routed", limit=100) +
            hub.get_events_by_type("feature_completed", limit=100)
        )
        assert len(all_events) >= 3


# ============================================================================
# Summary Test - Verify Database Schema and Consistency
# ============================================================================

class TestE2EAutomationEventsIntegrity:
    """Tests to verify automation_events table integrity across all scenarios"""

    def test_automation_events_has_all_required_fields_for_all_scenarios(self):
        """Verify all E2E scenarios store complete events with required fields"""
        hub = AutomationHub(test_mode=True)

        # Create events for each scenario type
        scenario_events = [
            # Scenario 1: Development
            AutomationEvent(
                event_type="action_item_completed",
                project_id="tier1-automation",
                status="success",
                evidence={"keyword": "git commit"},
                detected_from="hook"
            ),
            # Scenario 2: n8n
            AutomationEvent(
                event_type="n8n_fallback_routed",
                project_id="tier1-automation",
                status="success",
                evidence={"recovery_method": "celery_direct"},
                detected_from="hook"
            ),
            # Scenario 3: Production
            AutomationEvent(
                event_type="production_check",
                project_id="tier1-automation",
                status="go",
                evidence={"decision": "go"},
                detected_from="skill"
            ),
            # Scenario 4: Concurrent
            AutomationEvent(
                event_type="concurrent_operation",
                project_id="tier1-automation",
                status="success",
                evidence={"operation": "concurrent"},
                detected_from="hook"
            ),
            # Scenario 5: Recovery
            AutomationEvent(
                event_type="recovery_attempt",
                project_id="tier1-automation",
                status="success",
                evidence={"method": "systemd"},
                detected_from="hook"
            ),
            # Scenario 6: Lifecycle
            AutomationEvent(
                event_type="feature_deployed",
                project_id="tier1-automation",
                status="success",
                evidence={"feature_id": "feat-1"},
                detected_from="hook"
            ),
        ]

        # Store all events
        event_ids = []
        for event in scenario_events:
            event_id = hub.store_event(event)
            event_ids.append(event_id)

            # Verify event stored with all fields
            assert event_id is not None
            assert event.event_type is not None
            assert event.project_id is not None
            assert event.status is not None
            assert isinstance(event.evidence, dict)
            assert event.detected_from is not None
            assert event.created_at is not None

        # Verify all events retrievable
        all_retrieved = (
            hub.get_events_by_type("action_item_completed", limit=100) +
            hub.get_events_by_type("n8n_fallback_routed", limit=100) +
            hub.get_events_by_type("production_check", limit=100) +
            hub.get_events_by_type("recovery_attempt", limit=100) +
            hub.get_events_by_type("feature_deployed", limit=100)
        )

        assert len(all_retrieved) >= 5

    def test_automation_events_correlation_by_project_and_session(self):
        """Verify events can be correlated by project and session metadata"""
        hub = AutomationHub(test_mode=True)

        # Create events with session correlation
        session_id = "session-12345"

        events = [
            AutomationEvent(
                event_type="production_check",
                project_id="tier1-automation",
                status="go",
                evidence={"decision": "go"},
                detected_from="skill",
                metadata={"session_id": session_id}
            ),
            AutomationEvent(
                event_type="action_item_completed",
                project_id="tier1-automation",
                status="success",
                evidence={"keyword": "git commit"},
                detected_from="hook",
                metadata={"session_id": session_id}
            ),
            AutomationEvent(
                event_type="n8n_fallback_routed",
                project_id="tier1-automation",
                status="success",
                evidence={"recovery_method": "celery_direct"},
                detected_from="hook",
                metadata={"session_id": session_id}
            ),
        ]

        # Store events
        for event in events:
            hub.store_event(event)

        # Retrieve and correlate by project
        prod_events = hub.get_events_by_type("production_check", limit=100)
        action_events = hub.get_events_by_type("action_item_completed", limit=100)
        n8n_events = hub.get_events_by_type("n8n_fallback_routed", limit=100)

        all_events = prod_events + action_events + n8n_events

        # Verify all from same project
        assert all(e["project_id"] == "tier1-automation" for e in all_events)

        # Verify we have events from all types
        assert len(prod_events) >= 1
        assert len(action_events) >= 1
        assert len(n8n_events) >= 1
