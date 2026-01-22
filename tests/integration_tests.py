import pytest
from tools_db.database import Database
from tools_db.mcp_server import MCPServer
from tools_db.tools.schema_validator import SchemaValidator
from tools_db.tools.vision_cache import VisionCache
from tools_db.tools.audit_trail import AuditTrail
from tools_db.tools.bug_escalation import BugEscalation
import tempfile
import json


@pytest.fixture
def mcp_server():
    """Create MCP server instance for testing"""
    return MCPServer()


def test_full_workflow_schema_validation(mcp_server):
    """Test complete schema validation workflow"""
    validator = SchemaValidator(test_mode=True)

    result = validator.validate_create_statement("""
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    assert result["valid"] is True
    assert result["table_name"] == "products"


def test_full_workflow_cache_and_audit(mcp_server):
    """Test cache and audit trail together"""
    cache = VisionCache(test_mode=True)
    audit = AuditTrail(test_mode=True)

    # Store in cache
    cache.store(
        image_hash="test_hash",
        extracted_data={"keywords": ["test"]},
        confidence_score=0.95,
        model_version="v1.0"
    )

    # Record audit
    audit.record_event(
        event_type="cache_stored",
        entity_type="vision_cache",
        entity_id="test_hash",
        new_value={"keywords": ["test"]},
        user="system"
    )

    # Verify both
    cached = cache.get("test_hash")
    assert cached is not None

    events = audit.get_events(entity_type="vision_cache")
    assert len(events) == 1


def test_full_workflow_bug_escalation(mcp_server):
    """Test bug escalation workflow"""
    escalator = BugEscalation(test_mode=True)

    # Report bug
    escalator.report_bug(
        bug_id="bug_001",
        error_type="OutputFormatError",
        error_message="Vision model produced narrative",
        user_impact="critical"
    )

    # Get escalations
    bugs = escalator.get_escalations(status="pending")
    assert len(bugs) == 1
    assert bugs[0]["user_impact"] == "critical"

    # Resolve
    escalator.mark_resolved(bug_id="bug_001", resolution="Fixed in v2.0")

    resolved = escalator.get_escalations(status="resolved")
    assert len(resolved) >= 1


def test_integration_all_tools_work_together():
    """Test all tools working together in workflow"""
    # Setup tools
    schema_validator = SchemaValidator(test_mode=True)
    vision_cache = VisionCache(test_mode=True)
    audit_trail = AuditTrail(test_mode=True)
    bug_escalator = BugEscalation(test_mode=True)

    # 1. Validate schema
    result = schema_validator.validate_create_statement("""
        CREATE TABLE analysis_results (
            id SERIAL PRIMARY KEY,
            image_hash VARCHAR(64),
            result_data TEXT
        )
    """)
    assert result["valid"] is True

    # 2. Cache an analysis
    vision_cache.store(
        image_hash="analysis_1",
        extracted_data={"objects": ["cat", "dog"]},
        confidence_score=0.88,
        model_version="v2.0"
    )

    # 3. Record the cache operation
    audit_trail.record_event(
        event_type="analysis_cached",
        entity_type="vision_analysis",
        entity_id="analysis_1",
        new_value={"status": "cached"},
        user="vision_system"
    )

    # 4. Report a potential issue
    bug_escalator.report_bug(
        bug_id="analyze_accuracy_drop",
        error_type="PerformanceDegradation",
        error_message="Confidence dropped from 0.95 to 0.88",
        user_impact="medium"
    )

    # 5. Verify all operations succeeded
    cached = vision_cache.get("analysis_1")
    assert cached is not None
    assert cached["confidence_score"] == 0.88

    events = audit_trail.get_events(entity_type="vision_analysis")
    assert len(events) > 0

    # Get all bugs (status could be acknowledged due to priority calculation)
    all_bugs = bug_escalator.get_escalations()
    assert any(b["bug_id"] == "analyze_accuracy_drop" for b in all_bugs)
