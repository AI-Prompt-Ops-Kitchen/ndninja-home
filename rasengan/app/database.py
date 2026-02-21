"""PostgreSQL connection pool for Rasengan."""

import json
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

from app.config import DATABASE_URL

psycopg2.extras.register_default_jsonb(globally=True)

_pool: ThreadedConnectionPool | None = None


def init_pool(minconn: int = 2, maxconn: int = 10) -> None:
    global _pool
    _pool = ThreadedConnectionPool(minconn, maxconn, DATABASE_URL)


def close_pool() -> None:
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None


@contextmanager
def get_conn():
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def insert_event(event_type: str, source: str, payload: dict) -> dict:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO events (event_type, source, payload)
                   VALUES (%s, %s, %s)
                   RETURNING id, event_type, source, payload, created_at""",
                (event_type, source, json.dumps(payload)),
            )
            return dict(cur.fetchone())


def query_events(
    event_type: str | None = None,
    source: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    clauses = []
    params: list[Any] = []
    if event_type:
        clauses.append("event_type = %s")
        params.append(event_type)
    if source:
        clauses.append("source = %s")
        params.append(source)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.extend([limit, offset])

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"SELECT id, event_type, source, payload, created_at "
                f"FROM events {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                params,
            )
            return [dict(r) for r in cur.fetchall()]


def recent_events(n: int = 10) -> list[dict]:
    return query_events(limit=n)


def save_snapshot(snapshot: dict) -> dict:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO context_snapshots (snapshot)
                   VALUES (%s) RETURNING id, snapshot, created_at""",
                (json.dumps(snapshot),),
            )
            return dict(cur.fetchone())
