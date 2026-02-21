"""Event routes — POST /events and GET /events."""

from fastapi import APIRouter, Query
from starlette.responses import JSONResponse

from app.database import insert_event, query_events
from app.models import EventIn
from app.services.stream import publish_event

router = APIRouter()


@router.post("/events", status_code=201)
async def create_event(event: EventIn):
    # Persist to PostgreSQL
    row = insert_event(event.event_type, event.source, event.payload)
    # Publish to Redis Stream for live consumers
    await publish_event(event.event_type, event.source, event.payload)
    return row


@router.get("/events")
async def list_events(
    event_type: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    rows = query_events(event_type=event_type, source=source, limit=limit, offset=offset)
    # Serialize datetimes
    for r in rows:
        if hasattr(r.get("created_at"), "isoformat"):
            r["created_at"] = r["created_at"].isoformat()
    return rows
