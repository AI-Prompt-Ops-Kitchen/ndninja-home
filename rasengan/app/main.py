"""Rasengan — Event Hub + Context Engine for the Ninja Ecosystem.

Connects all tools (Dojo, Sage Mode, Sharingan, Glitch, Spike) via
Redis Streams and provides instant context recovery after interruptions.

Run: uvicorn app.main:app --host 0.0.0.0 --port 8050
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import LOG_LEVEL
from app.database import close_pool, init_pool
from app.routes import events, resume, rules, status, ws
from app.services.rules import evaluate_rules, load_rules
from app.services.stream import close_redis, consume_events, ensure_consumer_group

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("rasengan")


async def _on_stream_event(event: dict) -> None:
    """Callback for Redis Stream consumer — evaluate rules then broadcast."""
    await evaluate_rules(event)
    await ws.broadcast_to_clients(event)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Rasengan starting up")
    init_pool()
    load_rules()
    await ensure_consumer_group()
    consumer_task = asyncio.create_task(consume_events(_on_stream_event))
    logger.info("Rasengan ready")
    yield
    # Shutdown
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    close_pool()
    await close_redis()
    logger.info("Rasengan shut down")


app = FastAPI(title="Rasengan — Event Hub", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(events.router)
app.include_router(resume.router)
app.include_router(status.router)
app.include_router(ws.router)
app.include_router(rules.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "rasengan"}
