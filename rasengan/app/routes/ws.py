"""WebSocket live event feed — /ws/feed."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger("rasengan.ws")

# Connected WebSocket clients
_clients: set[WebSocket] = set()


async def broadcast_to_clients(event: dict) -> None:
    """Send an event to all connected WebSocket clients."""
    if not _clients:
        return
    msg = json.dumps(event, default=str)
    dead: set[WebSocket] = set()
    for ws in _clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _clients.difference_update(dead)


@router.websocket("/ws/feed")
async def ws_feed(ws: WebSocket):
    await ws.accept()
    _clients.add(ws)
    logger.info("WebSocket client connected (%d total)", len(_clients))
    try:
        while True:
            await ws.receive_text()  # Keep alive
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(ws)
        logger.info("WebSocket client disconnected (%d remain)", len(_clients))
