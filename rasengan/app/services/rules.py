"""Rasengan Rules Engine — evaluate incoming events against declarative rules."""

import asyncio
import json
import logging
import re
import time
from fnmatch import fnmatch
from typing import Any

import httpx

from app.database import get_conn, insert_event
from app.services.stream import publish_event

logger = logging.getLogger("rasengan.rules")

# In-memory rule cache (list of dicts from PG)
_rules: list[dict] = []

# Cooldown tracker: rule_id -> last_fired_timestamp
_cooldowns: dict[int, float] = {}

# Shared httpx client (created lazily)
_http_client: httpx.AsyncClient | None = None


async def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=10.0)
    return _http_client


def load_rules() -> int:
    """Load enabled rules from PostgreSQL into the in-memory cache.

    Returns the number of rules loaded.
    """
    global _rules
    import psycopg2.extras

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, event_type, source, condition, action, "
                "cooldown_seconds FROM rules WHERE enabled = true"
            )
            _rules = [dict(r) for r in cur.fetchall()]
    logger.info("Loaded %d active rules", len(_rules))
    return len(_rules)


def _resolve_path(obj: Any, path: str) -> Any:
    """Resolve a dotted path like 'payload.status' against a dict."""
    for key in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(key)
        else:
            return None
    return obj


def _interpolate(template: str, event: dict) -> str:
    """Replace {field.path} placeholders with values from the event."""

    def _replacer(match: re.Match) -> str:
        path = match.group(1)
        val = _resolve_path(event, path)
        return str(val) if val is not None else ""

    return re.sub(r"\{([^}]+)\}", _replacer, template)


def _interpolate_obj(obj: Any, event: dict) -> Any:
    """Recursively interpolate all string values in a dict/list."""
    if isinstance(obj, str):
        return _interpolate(obj, event)
    if isinstance(obj, dict):
        return {k: _interpolate_obj(v, event) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_interpolate_obj(v, event) for v in obj]
    return obj


def _check_condition(condition: dict, event: dict) -> bool:
    """Evaluate condition dict against event. All conditions are ANDed."""
    for path, expected in condition.items():
        actual = _resolve_path(event, path)

        if isinstance(expected, dict):
            # Operator-based condition
            for op, val in expected.items():
                if op == "$eq" and actual != val:
                    return False
                elif op == "$ne" and actual == val:
                    return False
                elif op == "$gt" and (actual is None or actual <= val):
                    return False
                elif op == "$lt" and (actual is None or actual >= val):
                    return False
                elif op == "$contains" and (
                    actual is None or str(val) not in str(actual)
                ):
                    return False
                elif op == "$not_contains" and (
                    actual is not None and str(val) in str(actual)
                ):
                    return False
                elif op == "$in" and actual not in val:
                    return False
        else:
            # Simple equality
            if actual != expected:
                return False
    return True


def _check_cooldown(rule_id: int, cooldown_seconds: int) -> bool:
    """Return True if the rule is allowed to fire (not in cooldown)."""
    if cooldown_seconds <= 0:
        return True
    last = _cooldowns.get(rule_id, 0.0)
    return (time.time() - last) >= cooldown_seconds


def _record_cooldown(rule_id: int) -> None:
    _cooldowns[rule_id] = time.time()


def _log_execution(
    rule_id: int,
    event_type: str,
    event_payload: dict,
    action_result: dict,
    success: bool,
) -> None:
    """Write execution record to rule_executions table."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO rule_executions "
                    "(rule_id, event_type, event_payload, action_result, success) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (
                        rule_id,
                        event_type,
                        json.dumps(event_payload),
                        json.dumps(action_result),
                        success,
                    ),
                )
    except Exception:
        logger.exception("Failed to log rule execution for rule %d", rule_id)


async def _fire_rule(rule: dict, event: dict) -> None:
    """Execute a rule's action. Runs as a detached task — never blocks consumer."""
    rule_id = rule["id"]
    rule_name = rule["name"]
    action = rule["action"]
    action_type = action.get("type", "log")

    result: dict = {}
    success = True

    try:
        if action_type == "log":
            msg = _interpolate(action.get("message", "{event_type}"), event)
            logger.info("[rule:%s] %s", rule_name, msg)
            result = {"message": msg}

        elif action_type == "emit":
            new_event_type = _interpolate(action["event_type"], event)
            new_source = _interpolate(action.get("source", "rasengan"), event)
            new_payload = _interpolate_obj(
                action.get("payload_template", {}), event
            )
            row = insert_event(new_event_type, new_source, new_payload)
            await publish_event(new_event_type, new_source, new_payload)
            result = {"emitted_event_type": new_event_type, "event_id": row["id"]}
            logger.info(
                "[rule:%s] Emitted %s (id=%d)", rule_name, new_event_type, row["id"]
            )

        elif action_type == "webhook":
            url = _interpolate(action["url"], event)
            method = action.get("method", "POST").upper()
            headers = _interpolate_obj(action.get("headers", {}), event)
            body = _interpolate_obj(action.get("body", None), event)

            client = await _get_http_client()
            if method == "GET":
                resp = await client.get(url, headers=headers)
            else:
                resp = await client.request(method, url, json=body, headers=headers)

            result = {"status_code": resp.status_code, "url": url}
            if resp.status_code >= 400:
                success = False
                result["response"] = resp.text[:500]
            logger.info(
                "[rule:%s] Webhook %s %s → %d",
                rule_name,
                method,
                url,
                resp.status_code,
            )

        elif action_type == "pipeline_track":
            from app.services.pipeline import on_pipeline_event

            await on_pipeline_event(event)
            result = {"tracked": event.get("event_type"), "job_id": event.get("payload", {}).get("job_id")}
            logger.info(
                "[rule:%s] Pipeline tracked: %s (job=%s)",
                rule_name,
                event.get("event_type"),
                event.get("payload", {}).get("job_id", "?"),
            )

        elif action_type == "resume_push":
            from app.services.push import execute_push

            push_result = await asyncio.to_thread(execute_push)
            result = push_result
            logger.info(
                "[rule:%s] Resume pushed to %d targets",
                rule_name,
                push_result.get("targets", 0),
            )

        else:
            logger.warning("[rule:%s] Unknown action type: %s", rule_name, action_type)
            result = {"error": f"unknown action type: {action_type}"}
            success = False

    except Exception as exc:
        logger.exception("[rule:%s] Action failed", rule_name)
        result = {"error": str(exc)}
        success = False

    _log_execution(rule_id, event["event_type"], event.get("payload", {}), result, success)


async def evaluate_rules(event: dict) -> None:
    """Match an incoming event against all cached rules and fire matches."""
    event_type = event.get("event_type", "")

    for rule in _rules:
        # 1. Match event_type (exact or glob)
        if not fnmatch(event_type, rule["event_type"]):
            continue

        # 2. Match source (if rule specifies one)
        if rule.get("source") and rule["source"] != event.get("source"):
            continue

        # 3. Evaluate conditions
        if rule.get("condition") and not _check_condition(rule["condition"], event):
            continue

        # 4. Check cooldown
        if not _check_cooldown(rule["id"], rule["cooldown_seconds"]):
            logger.debug("[rule:%s] Skipped (cooldown)", rule["name"])
            continue

        # 5. Fire (non-blocking)
        _record_cooldown(rule["id"])
        asyncio.create_task(_fire_rule(rule, event))
