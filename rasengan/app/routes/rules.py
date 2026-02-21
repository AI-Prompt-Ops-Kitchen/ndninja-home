"""Rules CRUD routes — manage declarative event rules."""

import json

import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query

from app.database import get_conn
from app.models import RuleExecutionOut, RuleIn, RuleOut
from app.services.rules import load_rules

router = APIRouter(prefix="/rules", tags=["rules"])


def _serialize(row: dict) -> dict:
    """Convert datetimes to ISO strings for JSON response."""
    for key in ("created_at", "updated_at"):
        if hasattr(row.get(key), "isoformat"):
            row[key] = row[key].isoformat()
    return row


@router.get("", response_model=list[RuleOut])
async def list_rules(enabled: bool | None = Query(None)):
    clauses = []
    params: list = []
    if enabled is not None:
        clauses.append("enabled = %s")
        params.append(enabled)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM rules {where} ORDER BY id", params
            )
            return [_serialize(dict(r)) for r in cur.fetchall()]


@router.post("", response_model=RuleOut, status_code=201)
async def create_rule(rule: RuleIn):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            try:
                cur.execute(
                    "INSERT INTO rules (name, event_type, source, condition, action, "
                    "enabled, cooldown_seconds) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
                    (
                        rule.name,
                        rule.event_type,
                        rule.source,
                        json.dumps(rule.condition),
                        json.dumps(rule.action),
                        rule.enabled,
                        rule.cooldown_seconds,
                    ),
                )
            except psycopg2.errors.UniqueViolation:
                raise HTTPException(409, f"Rule name '{rule.name}' already exists")
            row = _serialize(dict(cur.fetchone()))
    load_rules()
    return row


@router.get("/executions/recent", response_model=list[RuleExecutionOut])
async def recent_executions(limit: int = Query(50, le=500)):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM rule_executions ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return [_serialize(dict(r)) for r in cur.fetchall()]


@router.get("/{rule_id}", response_model=RuleOut)
async def get_rule(rule_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM rules WHERE id = %s", (rule_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Rule not found")
            return _serialize(dict(row))


@router.put("/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: int, rule: RuleIn):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "UPDATE rules SET name=%s, event_type=%s, source=%s, condition=%s, "
                "action=%s, enabled=%s, cooldown_seconds=%s, updated_at=now() "
                "WHERE id=%s RETURNING *",
                (
                    rule.name,
                    rule.event_type,
                    rule.source,
                    json.dumps(rule.condition),
                    json.dumps(rule.action),
                    rule.enabled,
                    rule.cooldown_seconds,
                    rule_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Rule not found")
            row = _serialize(dict(row))
    load_rules()
    return row


@router.patch("/{rule_id}/toggle", response_model=RuleOut)
async def toggle_rule(rule_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "UPDATE rules SET enabled = NOT enabled, updated_at = now() "
                "WHERE id = %s RETURNING *",
                (rule_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Rule not found")
            row = _serialize(dict(row))
    load_rules()
    return row


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM rules WHERE id = %s RETURNING id", (rule_id,))
            if not cur.fetchone():
                raise HTTPException(404, "Rule not found")
    load_rules()


@router.get("/{rule_id}/executions", response_model=list[RuleExecutionOut])
async def rule_executions(rule_id: int, limit: int = Query(50, le=500)):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM rules WHERE id = %s", (rule_id,))
            if not cur.fetchone():
                raise HTTPException(404, "Rule not found")
            cur.execute(
                "SELECT * FROM rule_executions WHERE rule_id = %s "
                "ORDER BY created_at DESC LIMIT %s",
                (rule_id, limit),
            )
            return [_serialize(dict(r)) for r in cur.fetchall()]
