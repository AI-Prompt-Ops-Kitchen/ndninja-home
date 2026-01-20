from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import json


@dataclass
class AuditTrailEvent:
    """Audit trail event for permission/configuration changes"""
    event_type: str  # permission_changed, config_updated, etc
    entity_type: str  # permission, config, workflow
    entity_id: str
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    user: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        data = self.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data)


@dataclass
class VisionCacheEntry:
    """Cached vision analysis result"""
    image_hash: str
    extracted_data: Dict[str, Any]
    confidence_score: float
    model_version: str
    ttl_hours: int = 24
    image_url: Optional[str] = None
    created_at: datetime = None
    expires_at: datetime = None
    hit_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(hours=self.ttl_hours)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def record_hit(self):
        self.hit_count += 1


@dataclass
class BugEscalation:
    """Bug escalation event"""
    bug_id: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    frequency: int = 1
    user_impact: str = "medium"  # low, medium, high, critical
    status: str = "pending"  # pending, acknowledged, investigating, resolved
    metadata: Optional[Dict[str, Any]] = None
    escalated_at: datetime = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.escalated_at is None:
            self.escalated_at = datetime.utcnow()


@dataclass
class PromptVersion:
    """Versioned prompt with test results"""
    prompt_id: str
    version: int
    prompt_text: str
    purpose: str  # keyword_extraction, summarization, etc
    created_by: Optional[str] = None
    is_active: bool = False
    test_results: Optional[Dict[str, Any]] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
