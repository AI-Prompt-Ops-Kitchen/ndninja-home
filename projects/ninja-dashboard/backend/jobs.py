"""PostgreSQL job queue + state machine for The Dojo.

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

psycopg2.extras.register_uuid()

DATABASE_URL = os.environ.get(
    "DOJO_DATABASE_URL",
    "postgresql://dojo_user:zhjmOmF-YzlqEzMGtHsOCJyiWoMUR0Fk@localhost/dojo",
)

# Valid status transitions — enforced on every transition() call
VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending":          {"script_ready", "generating", "error"},
    "script_ready":     {"generating", "error"},
    "generating":       {"ready_for_review", "error"},
    "ready_for_review": {"approved", "generating", "discarded"},
    "approved":         {"uploading"},
    "uploading":        {"uploaded", "error"},
    "uploaded":         set(),
    "error":            {"generating", "uploading"},
    "discarded":        {"generating"},  # Allow retry from discarded
}

JOB_COLS = [
    "id", "type", "status", "created_at", "updated_at", "script_text",
    "article_url", "output_path", "thumb_path", "error_msg", "retry_count",
    "target_length_sec", "broll_count", "broll_duration",
    "youtube_video_id", "youtube_title", "youtube_privacy",
]


def _conn():
    """Return a new connection with autocommit, matching broll_db pattern."""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def _row_to_dict(row: tuple, columns: list[str]) -> dict:
    d = dict(zip(columns, row))
    for k, v in d.items():
        if isinstance(v, uuid.UUID):
            d[k] = str(v)
        elif isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id                TEXT PRIMARY KEY,
                    type              TEXT NOT NULL DEFAULT 'article',
                    status            TEXT NOT NULL DEFAULT 'pending',
                    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
                    script_text       TEXT,
                    article_url       TEXT,
                    output_path       TEXT,
                    thumb_path        TEXT,
                    error_msg         TEXT,
                    retry_count       INTEGER NOT NULL DEFAULT 0,
                    target_length_sec INTEGER NOT NULL DEFAULT 60,
                    broll_count       INTEGER NOT NULL DEFAULT 3,
                    broll_duration    DOUBLE PRECISION NOT NULL DEFAULT 10.0
                )
            """)
            # YouTube upload columns (added Phase 3)
            for col, typedef in [
                ("youtube_video_id", "TEXT"),
                ("youtube_title", "TEXT"),
                ("youtube_privacy", "TEXT DEFAULT 'private'"),
            ]:
                cur.execute(f"""
                    ALTER TABLE jobs ADD COLUMN IF NOT EXISTS {col} {typedef}
                """)


def create_job(
    article_url: Optional[str] = None,
    article_text: Optional[str] = None,
    target_length_sec: int = 60,
    broll_count: int = 3,
    broll_duration: float = 10.0,
) -> dict:
    job_id = str(uuid.uuid4())
    now = _now()
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""INSERT INTO jobs
                   (id, type, status, created_at, updated_at, article_url, script_text,
                    target_length_sec, broll_count, broll_duration)
                   VALUES (%s, 'article', 'pending', %s, %s, %s, %s, %s, %s, %s)
                   RETURNING {', '.join(JOB_COLS)}""",
                (job_id, now, now, article_url, article_text, target_length_sec, broll_count, broll_duration),
            )
            return _row_to_dict(cur.fetchone(), JOB_COLS)


def get_job(job_id: str) -> Optional[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(JOB_COLS)} FROM jobs WHERE id = %s",
                (job_id,),
            )
            row = cur.fetchone()
            return _row_to_dict(row, JOB_COLS) if row else None


def list_jobs() -> list[dict]:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {', '.join(JOB_COLS)} FROM jobs ORDER BY created_at DESC")
            return [_row_to_dict(row, JOB_COLS) for row in cur.fetchall()]


def update_job(job_id: str, **fields) -> Optional[dict]:
    fields["updated_at"] = _now()
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [job_id]
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE jobs SET {set_clause} WHERE id = %s RETURNING {', '.join(JOB_COLS)}",
                values,
            )
            row = cur.fetchone()
            return _row_to_dict(row, JOB_COLS) if row else None


def delete_job(job_id: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            return cur.rowcount > 0


def transition(job_id: str, new_status: str, **extra_fields) -> Optional[dict]:
    """Transition a job to a new status, enforcing the state machine."""
    job = get_job(job_id)
    if not job:
        return None
    current = job["status"]
    allowed = VALID_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError(f"Invalid transition: {current!r} → {new_status!r}")
    return update_job(job_id, status=new_status, **extra_fields)
