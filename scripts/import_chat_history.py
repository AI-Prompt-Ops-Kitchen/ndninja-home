#!/usr/bin/env python3
"""
Import Clawdbot chat history into PostgreSQL.
Reads JSONL transcript files and stores messages in a searchable format.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

# Configuration
DB_NAME = "clawd_chat"
DB_USER = "ndninja"
SESSIONS_DIR = Path.home() / ".clawdbot/agents/main/sessions"
HOURS_TO_IMPORT = 48

def get_db_connection(dbname="postgres"):
    """Connect to PostgreSQL."""
    return psycopg2.connect(dbname=dbname, user=DB_USER)

def create_database():
    """Create the clawd_chat database if it doesn't exist."""
    conn = get_db_connection("postgres")
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"✅ Created database: {DB_NAME}")
    else:
        print(f"📦 Database already exists: {DB_NAME}")
    
    cur.close()
    conn.close()

def create_schema():
    """Create the chat_messages table."""
    conn = get_db_connection(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            message_id VARCHAR(64) UNIQUE,
            session_id VARCHAR(64),
            parent_id VARCHAR(64),
            timestamp TIMESTAMPTZ NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT,
            content_type VARCHAR(20) DEFAULT 'text',
            model VARCHAR(50),
            channel VARCHAR(20),
            provider VARCHAR(30),
            tokens_input INTEGER,
            tokens_output INTEGER,
            cost_total DECIMAL(10, 6),
            raw_content JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_messages(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_chat_role ON chat_messages(role);
        CREATE INDEX IF NOT EXISTS idx_chat_content_search ON chat_messages USING gin(to_tsvector('english', content));
    """)
    
    conn.commit()
    print("✅ Created table: chat_messages (with full-text search index)")
    cur.close()
    conn.close()

def extract_text_content(content_blocks):
    """Extract readable text from content blocks."""
    texts = []
    content_type = "text"
    
    if isinstance(content_blocks, str):
        return content_blocks, "text"
    
    if isinstance(content_blocks, list):
        for block in content_blocks:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    # Skip thinking blocks for main content
                    pass
                elif block.get("type") == "toolCall":
                    content_type = "tool_call"
                    texts.append(f"[Tool: {block.get('name', 'unknown')}]")
    
    return "\n".join(texts), content_type

def parse_jsonl_file(filepath, cutoff_time):
    """Parse a JSONL transcript file and extract messages."""
    messages = []
    session_id = None
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                
                if record.get("type") == "session":
                    session_id = record.get("id")
                    continue
                
                if record.get("type") != "message":
                    continue
                
                # Parse timestamp
                ts_str = record.get("timestamp")
                if not ts_str:
                    continue
                
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except ValueError:
                    continue
                
                # Skip messages older than cutoff
                if ts < cutoff_time:
                    continue
                
                msg = record.get("message", {})
                role = msg.get("role", "unknown")
                content_blocks = msg.get("content", "")
                
                text_content, content_type = extract_text_content(content_blocks)
                
                # Skip empty messages
                if not text_content.strip():
                    continue
                
                usage = msg.get("usage", {})
                cost = msg.get("usage", {}).get("cost", {})
                
                messages.append({
                    "message_id": record.get("id"),
                    "session_id": session_id or filepath.stem.split(".")[0],
                    "parent_id": record.get("parentId"),
                    "timestamp": ts,
                    "role": role,
                    "content": text_content[:50000].replace('\x00', ''),  # Limit size, strip NUL
                    "content_type": content_type,
                    "model": msg.get("model"),
                    "provider": msg.get("provider"),
                    "tokens_input": usage.get("input"),
                    "tokens_output": usage.get("output"),
                    "cost_total": cost.get("total") if cost else None,
                    "raw_content": json.dumps(content_blocks) if content_blocks else None,
                })
    except Exception as e:
        print(f"⚠️  Error parsing {filepath}: {e}")
    
    return messages

def import_messages(messages):
    """Insert messages into the database."""
    if not messages:
        return 0
    
    conn = get_db_connection(DB_NAME)
    cur = conn.cursor()
    
    # Upsert to handle re-imports
    inserted = 0
    for msg in messages:
        try:
            cur.execute("""
                INSERT INTO chat_messages 
                (message_id, session_id, parent_id, timestamp, role, content, 
                 content_type, model, provider, tokens_input, tokens_output, 
                 cost_total, raw_content)
                VALUES (%(message_id)s, %(session_id)s, %(parent_id)s, %(timestamp)s, 
                        %(role)s, %(content)s, %(content_type)s, %(model)s, %(provider)s, 
                        %(tokens_input)s, %(tokens_output)s, %(cost_total)s, %(raw_content)s)
                ON CONFLICT (message_id) DO NOTHING
            """, msg)
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"⚠️  Error inserting message {msg.get('message_id')}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    return inserted

def main():
    print(f"🔍 Importing last {HOURS_TO_IMPORT} hours of chat history...")
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=HOURS_TO_IMPORT)
    print(f"📅 Cutoff: {cutoff_time.isoformat()}")
    
    # Create database and schema
    create_database()
    create_schema()
    
    # Find all transcript files
    all_messages = []
    
    # Active sessions
    for jsonl_file in SESSIONS_DIR.glob("*.jsonl"):
        if jsonl_file.name.endswith(".lock"):
            continue
        print(f"📄 Parsing: {jsonl_file.name}")
        messages = parse_jsonl_file(jsonl_file, cutoff_time)
        all_messages.extend(messages)
        print(f"   Found {len(messages)} messages in range")
    
    # Archive
    archive_dir = SESSIONS_DIR / "archive"
    if archive_dir.exists():
        for jsonl_file in archive_dir.glob("*.jsonl"):
            print(f"📄 Parsing archive: {jsonl_file.name}")
            messages = parse_jsonl_file(jsonl_file, cutoff_time)
            all_messages.extend(messages)
            print(f"   Found {len(messages)} messages in range")
    
    # Deleted sessions from last 2 days (they have timestamps in filename)
    for jsonl_file in SESSIONS_DIR.glob("*.jsonl.deleted.*"):
        # Check if deleted in last few days
        try:
            mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime, timezone.utc)
            if mtime > cutoff_time - timedelta(days=1):
                print(f"📄 Parsing deleted: {jsonl_file.name}")
                messages = parse_jsonl_file(jsonl_file, cutoff_time)
                all_messages.extend(messages)
                print(f"   Found {len(messages)} messages in range")
        except Exception:
            pass
    
    # Import
    total_inserted = import_messages(all_messages)
    
    print(f"\n✅ Done! Imported {total_inserted} new messages (out of {len(all_messages)} in range)")
    
    # Show sample query
    conn = get_db_connection(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chat_messages")
    total = cur.fetchone()[0]
    print(f"📊 Total messages in database: {total}")
    
    # Show recent messages
    print("\n📝 Recent messages:")
    cur.execute("""
        SELECT timestamp, role, LEFT(content, 80) 
        FROM chat_messages 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    for row in cur.fetchall():
        ts, role, content = row
        preview = content.replace('\n', ' ')[:60] if content else ''
        print(f"   [{ts.strftime('%m/%d %H:%M')}] {role}: {preview}...")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
