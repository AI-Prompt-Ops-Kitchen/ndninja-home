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
from app.routes import events, health, pipelines, push_targets, resume, rules, schedules, status, ws
from app.services.pipeline import stall_detector_loop
from app.services.rules import evaluate_rules, load_rules
from app.services.scheduler import load_schedules, scheduler_loop
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
    load_schedules()
    await ensure_consumer_group()
    consumer_task = asyncio.create_task(consume_events(_on_stream_event))
    scheduler_task = asyncio.create_task(scheduler_loop())
    stall_task = asyncio.create_task(stall_detector_loop())
    logger.info("Rasengan ready")
    yield
    # Shutdown
    stall_task.cancel()
    scheduler_task.cancel()
    consumer_task.cancel()
    for task in (consumer_task, scheduler_task, stall_task):
        try:
            await task
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
app.include_router(schedules.router)
app.include_router(pipelines.router)
app.include_router(push_targets.router)
app.include_router(health.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "rasengan"}
