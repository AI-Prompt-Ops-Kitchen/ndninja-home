"""Redis Streams producer/consumer for Rasengan event hub."""

import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.config import (
    CONSUMER_GROUP,
    CONSUMER_NAME,
    REDIS_URL,
    STREAM_KEY,
    STREAM_MAXLEN,
)

logger = logging.getLogger("rasengan.stream")

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def ensure_consumer_group() -> None:
    r = await get_redis()
    try:
        await r.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info("Created consumer group %s", CONSUMER_GROUP)
    except aioredis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            pass  # Already exists
        else:
            raise


async def publish_event(event_type: str, source: str, payload: dict) -> str:
    """Add event to Redis Stream. Returns the stream message ID."""
    r = await get_redis()
    msg_id = await r.xadd(
        STREAM_KEY,
        {
            "type": event_type,
            "source": source,
            "payload": json.dumps(payload),
        },
        maxlen=STREAM_MAXLEN,
        approximate=True,
    )
    return msg_id


async def consume_events(callback) -> None:
    """Blocking consumer loop — reads from stream, calls callback for each event."""
    r = await get_redis()
    await ensure_consumer_group()

    while True:
        try:
            entries = await r.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_KEY: ">"},
                count=10,
                block=1000,
            )
            for _stream_name, messages in entries:
                for msg_id, fields in messages:
                    try:
                        event = {
                            "event_type": fields.get("type", "unknown"),
                            "source": fields.get("source", "unknown"),
                            "payload": json.loads(fields.get("payload", "{}")),
                        }
                        await callback(event)
                        await r.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                    except Exception:
                        logger.exception("Error processing stream message %s", msg_id)
        except asyncio.CancelledError:
            logger.info("Stream consumer cancelled")
            break
        except Exception:
            logger.exception("Stream consumer error, retrying in 2s")
            await asyncio.sleep(2)
