#!/usr/bin/env python3
"""One-time migration: copy jobs from SQLite to PostgreSQL dojo database.

Usage: python3 migrate_sqlite_to_pg.py
"""
import os
import sqlite3
import psycopg2

SQLITE_PATH = os.path.expanduser("~/projects/ninja-dashboard/backend/jobs.db")
PG_URL = os.environ.get("DOJO_DATABASE_URL", "postgresql://postgres:postgres@localhost/dojo")

COLUMNS = [
    "id", "type", "status", "created_at", "updated_at", "script_text",
    "article_url", "output_path", "thumb_path", "error_msg", "retry_count",
    "target_length_sec", "broll_count", "broll_duration",
]


def main():
    # Read from SQLite
    conn_sq = sqlite3.connect(SQLITE_PATH)
    conn_sq.row_factory = sqlite3.Row
    rows = conn_sq.execute("SELECT * FROM jobs").fetchall()
    conn_sq.close()
    print(f"Read {len(rows)} jobs from SQLite")

    if not rows:
        print("Nothing to migrate.")
        return

    # Write to PostgreSQL
    conn_pg = psycopg2.connect(PG_URL)
    conn_pg.autocommit = True
    cur = conn_pg.cursor()

    # Ensure table exists (import jobs module to create it)
    from jobs import init_db
    init_db()

    placeholders = ", ".join(["%s"] * len(COLUMNS))
    col_list = ", ".join(COLUMNS)
    insert_sql = f"INSERT INTO jobs ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

    migrated = 0
    for row in rows:
        d = dict(row)
        values = [d.get(c) for c in COLUMNS]
        cur.execute(insert_sql, values)
        migrated += cur.rowcount

    cur.close()
    conn_pg.close()
    print(f"Migrated {migrated} jobs to PostgreSQL (skipped {len(rows) - migrated} duplicates)")


if __name__ == "__main__":
    main()
