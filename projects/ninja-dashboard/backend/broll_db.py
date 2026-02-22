"""B-roll Wingman — PostgreSQL CRUD for discovery sessions, slots, and candidates.

Database: 'dojo' (PostgreSQL 17).
Env var DOJO_DATABASE_URL overrides the default connection string.
All functions are synchronous — call via asyncio.to_thread() from async code.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras

# Register UUID adapter so psycopg2 handles uuid.UUID transparently
psycopg2.extras.register_uuid()

DATABASE_URL = os.environ.get(
    "DOJO_DATABASE_URL",
    "postgresql://dojo_user:zhjmOmF-YzlqEzMGtHsOCJyiWoMUR0Fk@localhost/dojo",
)


def _conn():
    """Return a new connection with autocommit for DDL, dict-style rows."""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def init_broll_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS broll_sessions (
                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id      TEXT NOT NULL,
                    script_text TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'extracting',
                    slot_count  INTEGER NOT NULL DEFAULT 3,
                    created_at  TIMESTAMPTZ DEFAULT now(),
                    updated_at  TIMESTAMPTZ DEFAULT now()
                );

                CREATE TABLE IF NOT EXISTS broll_slots (
                    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id            UUID NOT NULL REFERENCES broll_sessions(id) ON DELETE CASCADE,
                    slot_index            INTEGER NOT NULL,
                    keyword               TEXT NOT NULL,
                    sentence              TEXT,
                    position              REAL NOT NULL DEFAULT 0.5,
                    status                TEXT NOT NULL DEFAULT 'searching',
                    approved_candidate_id UUID,
                    created_at            TIMESTAMPTZ DEFAULT now()
                );

                CREATE TABLE IF NOT EXISTS broll_candidates (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    slot_id         UUID NOT NULL REFERENCES broll_slots(id) ON DELETE CASCADE,
                    source          TEXT NOT NULL,
                    source_url      TEXT,
                    title           TEXT,
                    preview_url     TEXT,
                    duration_sec    REAL,
                    download_status TEXT NOT NULL DEFAULT 'pending',
                    local_path      TEXT,
                    file_size_mb    REAL,
                    created_at      TIMESTAMPTZ DEFAULT now()
                );

                CREATE INDEX IF NOT EXISTS idx_broll_sessions_job ON broll_sessions(job_id);
                CREATE INDEX IF NOT EXISTS idx_broll_slots_session ON broll_slots(session_id);
                CREATE INDEX IF NOT EXISTS idx_broll_candidates_slot ON broll_candidates(slot_id);
            """)


# ---------------------------------------------------------------------------
# Row helpers — convert DB rows to dicts with string UUIDs / ISO timestamps
# ---------------------------------------------------------------------------

def _row_to_dict(row: tuple, columns: list[str]) -> dict:
    d = dict(zip(columns, row))
    for k, v in d.items():
        if isinstance(v, uuid.UUID):
            d[k] = str(v)
        elif isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

SESSION_COLS = [
    "id", "job_id", "script_text", "status", "slot_count", "created_at", "updated_at",
]

def create_session(job_id: str, script_text: str, slot_count: int = 3) -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO broll_sessions (job_id, script_text, slot_count)
                   VALUES (%s, %s, %s)
                   RETURNING id, job_id, script_text, status, slot_count, created_at, updated_at""",
                (job_id, script_text, slot_count),
            )
            return _row_to_dict(cur.fetchone(), SESSION_COLS)


def get_session_by_job(job_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(SESSION_COLS)} FROM broll_sessions WHERE job_id = %s ORDER BY created_at DESC LIMIT 1",
                (job_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, SESSION_COLS) if row else None


def update_session(session_id: str, **kwargs) -> Optional[dict]:
    if not kwargs:
        return get_session(session_id)
    kwargs["updated_at"] = datetime.now(timezone.utc)
    sets = ", ".join(f"{k} = %s" for k in kwargs)
    vals = list(kwargs.values()) + [session_id]
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE broll_sessions SET {sets} WHERE id = %s::uuid RETURNING {', '.join(SESSION_COLS)}",
                vals,
            )
            row = cur.fetchone()
            return _row_to_dict(row, SESSION_COLS) if row else None


def get_session(session_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(SESSION_COLS)} FROM broll_sessions WHERE id = %s::uuid",
                (session_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, SESSION_COLS) if row else None


# ---------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------

SLOT_COLS = [
    "id", "session_id", "slot_index", "keyword", "sentence", "position",
    "status", "approved_candidate_id", "created_at",
]

def create_slot(session_id: str, slot_index: int, keyword: str,
                sentence: Optional[str] = None, position: float = 0.5) -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO broll_slots (session_id, slot_index, keyword, sentence, position)
                   VALUES (%s::uuid, %s, %s, %s, %s)
                   RETURNING id, session_id, slot_index, keyword, sentence, position, status, approved_candidate_id, created_at""",
                (session_id, slot_index, keyword, sentence, position),
            )
            return _row_to_dict(cur.fetchone(), SLOT_COLS)


def get_slots_for_session(session_id: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(SLOT_COLS)} FROM broll_slots WHERE session_id = %s::uuid ORDER BY slot_index",
                (session_id,),
            )
            return [_row_to_dict(row, SLOT_COLS) for row in cur.fetchall()]


def update_slot(slot_id: str, **kwargs) -> Optional[dict]:
    if not kwargs:
        return get_slot(slot_id)
    sets = ", ".join(f"{k} = %s" for k in kwargs)
    vals = list(kwargs.values()) + [slot_id]
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE broll_slots SET {sets} WHERE id = %s::uuid RETURNING {', '.join(SLOT_COLS)}",
                vals,
            )
            row = cur.fetchone()
            return _row_to_dict(row, SLOT_COLS) if row else None


def get_slot(slot_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(SLOT_COLS)} FROM broll_slots WHERE id = %s::uuid",
                (slot_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, SLOT_COLS) if row else None


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

CANDIDATE_COLS = [
    "id", "slot_id", "source", "source_url", "title", "preview_url",
    "duration_sec", "download_status", "local_path", "file_size_mb", "created_at",
]

def create_candidate(slot_id: str, source: str, source_url: Optional[str] = None,
                     title: Optional[str] = None, preview_url: Optional[str] = None,
                     duration_sec: Optional[float] = None) -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO broll_candidates (slot_id, source, source_url, title, preview_url, duration_sec)
                   VALUES (%s::uuid, %s, %s, %s, %s, %s)
                   RETURNING id, slot_id, source, source_url, title, preview_url, duration_sec, download_status, local_path, file_size_mb, created_at""",
                (slot_id, source, source_url, title, preview_url, duration_sec),
            )
            return _row_to_dict(cur.fetchone(), CANDIDATE_COLS)


def get_candidates_for_slot(slot_id: str) -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(CANDIDATE_COLS)} FROM broll_candidates WHERE slot_id = %s::uuid ORDER BY created_at",
                (slot_id,),
            )
            return [_row_to_dict(row, CANDIDATE_COLS) for row in cur.fetchall()]


def update_candidate(candidate_id: str, **kwargs) -> Optional[dict]:
    if not kwargs:
        return get_candidate(candidate_id)
    sets = ", ".join(f"{k} = %s" for k in kwargs)
    vals = list(kwargs.values()) + [candidate_id]
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE broll_candidates SET {sets} WHERE id = %s::uuid RETURNING {', '.join(CANDIDATE_COLS)}",
                vals,
            )
            row = cur.fetchone()
            return _row_to_dict(row, CANDIDATE_COLS) if row else None


def get_candidate(candidate_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(CANDIDATE_COLS)} FROM broll_candidates WHERE id = %s::uuid",
                (candidate_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, CANDIDATE_COLS) if row else None


# ---------------------------------------------------------------------------
# Composite fetch — session + all slots + all candidates in one go
# ---------------------------------------------------------------------------

def get_full_session(job_id: str) -> Optional[dict]:
    """Return session dict with nested slots, each slot with nested candidates."""
    session = get_session_by_job(job_id)
    if not session:
        return None
    slots = get_slots_for_session(session["id"])
    for slot in slots:
        slot["candidates"] = get_candidates_for_slot(slot["id"])
    session["slots"] = slots
    return session
