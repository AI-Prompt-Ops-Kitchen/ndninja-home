"""Detailed health route — GET /health/detailed."""

import time
from pathlib import Path

import yaml
from fastapi import APIRouter

router = APIRouter()

_START_TIME = time.monotonic()
_EDICTS_PATH = Path.home() / ".claude" / "hokage" / "edicts.yaml"


@router.get("/health/detailed")
async def health_detailed():
    uptime = time.monotonic() - _START_TIME

    edict_count = 0
    try:
        data = yaml.safe_load(_EDICTS_PATH.read_text())
        edict_count = len(data.get("edicts", []))
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "rasengan",
        "uptime_seconds": round(uptime, 2),
        "edict_count": edict_count,
    }
