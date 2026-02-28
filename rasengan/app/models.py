"""Pydantic models for Rasengan events."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    event_type: str = Field(min_length=1)
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)


class EventOut(BaseModel):
    id: int
    event_type: str
    source: str
    payload: dict[str, Any]
    created_at: datetime


class EventQuery(BaseModel):
    event_type: str | None = None
    source: str | None = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


# --- Rules Engine models ---


class RuleIn(BaseModel):
    name: str
    event_type: str
    source: str | None = None
    condition: dict[str, Any] = {}
    action: dict[str, Any]
    enabled: bool = True
    cooldown_seconds: int = Field(default=0, ge=0)


class RuleOut(BaseModel):
    id: int
    name: str
    event_type: str
    source: str | None
    condition: dict[str, Any]
    action: dict[str, Any]
    enabled: bool
    cooldown_seconds: int
    created_at: datetime
    updated_at: datetime


class RuleExecutionOut(BaseModel):
    id: int
    rule_id: int
    event_type: str
    event_payload: dict[str, Any]
    action_result: dict[str, Any]
    success: bool
    created_at: datetime


# --- Scheduler models ---


class ScheduleIn(BaseModel):
    name: str
    cron_expr: str
    event_type: str
    source: str = "scheduler"
    payload: dict[str, Any] = {}
    enabled: bool = True


class ScheduleOut(BaseModel):
    id: int
    name: str
    cron_expr: str
    event_type: str
    source: str
    payload: dict[str, Any]
    enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Pipeline Tracker models ---


class StageTransition(BaseModel):
    stage: str
    entered_at: str
    exited_at: str | None = None


class PipelineRunOut(BaseModel):
    id: int
    job_id: str
    current_stage: str
    stages: list[StageTransition]
    status: str
    error: str | None = None
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    duration_seconds: int | None = None


class PipelineStatsOut(BaseModel):
    total_runs_24h: int
    success_rate_24h: float
    avg_duration_seconds: dict[str, float]
    active_runs: int
    stalled_runs: int


# --- Push Target models ---


class PushTargetIn(BaseModel):
    name: str
    type: str  # 'file' or 'webhook'
    config: dict[str, Any]
    enabled: bool = True


class PushTargetOut(BaseModel):
    id: int
    name: str
    type: str
    config: dict[str, Any]
    enabled: bool
    created_at: datetime
