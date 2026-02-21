"""Pydantic models for Rasengan events."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    event_type: str
    source: str
    payload: dict[str, Any] = {}


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
