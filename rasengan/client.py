"""Rasengan emitter client — fire-and-forget event emission.

Import and call emit() from any tool in the ninja ecosystem.
Never blocks the caller, never raises exceptions.

Usage:
    from rasengan_client import emit
    emit("dojo.job_completed", "dojo", {"job_id": "abc123"})
"""

import os

import httpx

RASENGAN_URL = os.environ.get("RASENGAN_URL", "http://localhost:8050")


def emit(event_type: str, source: str, payload: dict | None = None) -> None:
    """Fire-and-forget event to Rasengan."""
    try:
        httpx.post(
            f"{RASENGAN_URL}/events",
            json={
                "event_type": event_type,
                "source": source,
                "payload": payload or {},
            },
            timeout=2.0,
        )
    except Exception:
        pass  # Never block the caller
