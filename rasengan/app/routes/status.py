"""System status route — GET /status."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.database import query_events

router = APIRouter()


@router.get("/status")
async def system_status():
    # Count events per source in last 24h
    recent = query_events(limit=200)
    sources: dict[str, int] = {}
    types: dict[str, int] = {}
    for e in recent:
        sources[e["source"]] = sources.get(e["source"], 0) + 1
        types[e["event_type"]] = types.get(e["event_type"], 0) + 1

    return {
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recent_event_count": len(recent),
        "sources": sources,
        "event_types": types,
    }
