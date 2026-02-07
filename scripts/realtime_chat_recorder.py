#!/usr/bin/env python3
"""
Real-time chat message recorder for Clawdbot.
Watches session JSONL files and inserts new messages into PostgreSQL within seconds.

Usage:
    python3 scripts/realtime_chat_recorder.py

Requirements:
    pip install psycopg2-binary watchdog

Run as a service:
    systemctl --user start chat-recorder
"""

import json
import os
import sys
import time
import signal
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
except ImportError:
    print("❌ watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


# Configuration
DB_NAME = "clawd_chat"
DB_USER = os.environ.get("PGUSER", "ndninja")
SESSIONS_DIR = Path.home() / ".clawdbot/agents/main/sessions"
STATE_FILE = Path.home() / ".clawdbot/chat-recorder-state.json"


class FileState:
    """Track file positions to avoid re-reading old content."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.positions: Dict[str, int] = {}
        self.load()
    
    def load(self):
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    self.positions = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.positions = {}
    
    def save(self):
        """Save state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.positions, f)
    
    def get_position(self, filepath: str) -> int:
        return self.positions.get(filepath, 0)
    
    def set_position(self, filepath: str, pos: int):
        self.positions[filepath] = pos


class ChatRecorder:
    """Records chat messages to PostgreSQL in real-time."""
    
    def __init__(self):
        self.state = FileState(STATE_FILE)
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.running = True
        self.seen_message_ids: Set[str] = set()
        
    def connect_db(self):
        """Connect to PostgreSQL."""
        try:
            self.conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER)
            self.conn.autocommit = False
            print(f"✅ Connected to database: {DB_NAME}")
            return True
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def ensure_schema(self):
        """Ensure the table exists with all required columns."""
        if not self.conn:
            return False
            
        cur = self.conn.cursor()
        
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                message_id VARCHAR(64) UNIQUE,
                session_id VARCHAR(64),
                role VARCHAR(20),
                content TEXT,
                timestamp TIMESTAMPTZ,
                channel VARCHAR(32),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        self.conn.commit()
        
        # Add columns if they don't exist (idempotent)
        columns_to_add = [
            ('session_key', 'VARCHAR(128)'),
            ('sender_id', 'VARCHAR(64)'),
            ('tool_calls', 'JSONB'),
            ('tool_results', 'JSONB'),
            ('metadata', 'JSONB'),
            ('search_vector', 'TSVECTOR'),
        ]
        
        for col, dtype in columns_to_add:
            try:
                cur.execute(f'ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS {col} {dtype}')
                self.conn.commit()
            except psycopg2.Error:
                self.conn.rollback()
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session 
                ON chat_messages(session_key);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp 
                ON chat_messages(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_role 
                ON chat_messages(role);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_search 
                ON chat_messages USING GIN(search_vector);
        """)
        self.conn.commit()
        cur.close()
        print("✅ Schema verified")
        return True
    
    def generate_message_id(self, msg: dict, session_key: str) -> str:
        """Generate a unique message ID."""
        content = json.dumps(msg, sort_keys=True)
        return hashlib.sha256(f"{session_key}:{content}".encode()).hexdigest()[:16]
    
    def insert_message(self, msg: dict, session_key: str, session_id: str):
        """Insert a single message into the database."""
        if not self.conn:
            return False
        
        # Extract role
        role = msg.get("role", "unknown")
        
        # Extract content
        content_raw = msg.get("content", [])
        if isinstance(content_raw, str):
            content = content_raw
        elif isinstance(content_raw, list):
            texts = []
            for block in content_raw:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        texts.append(block.get("text", ""))
                elif isinstance(block, str):
                    texts.append(block)
            content = "\n".join(texts)
        else:
            content = str(content_raw)
        
        # Skip empty content
        if not content.strip():
            return False
        
        # Generate message ID
        message_id = self.generate_message_id(msg, session_key)
        
        # Skip if already seen
        if message_id in self.seen_message_ids:
            return False
        self.seen_message_ids.add(message_id)
        
        # Extract timestamp
        ts_str = msg.get("timestamp") or msg.get("ts")
        if ts_str:
            try:
                timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Extract channel and sender from envelope
        envelope = msg.get("envelope", {})
        channel = envelope.get("channel")
        sender_id = envelope.get("senderId") or envelope.get("sender_id")
        
        # Tool calls/results
        tool_calls = msg.get("tool_calls") or msg.get("toolCalls")
        tool_results = msg.get("tool_results") or msg.get("toolResults")
        
        # Metadata
        metadata = {k: v for k, v in msg.items() 
                   if k not in ("role", "content", "timestamp", "ts", "envelope", 
                               "tool_calls", "toolCalls", "tool_results", "toolResults")}
        
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO chat_messages 
                    (message_id, session_id, session_key, role, content, timestamp,
                     channel, sender_id, tool_calls, tool_results, metadata, search_vector)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        to_tsvector('english', %s))
                ON CONFLICT (message_id) DO NOTHING
            """, (
                message_id, session_id, session_key, role, content, timestamp,
                channel, sender_id,
                json.dumps(tool_calls) if tool_calls else None,
                json.dumps(tool_results) if tool_results else None,
                json.dumps(metadata) if metadata else None,
                content
            ))
            self.conn.commit()
            cur.close()
            return cur.rowcount > 0
        except psycopg2.Error as e:
            print(f"⚠️ Insert error: {e}")
            self.conn.rollback()
            return False
    
    def process_file(self, filepath: Path, initial: bool = False):
        """Process new lines from a JSONL file."""
        if not filepath.exists():
            return
        
        session_key = self.extract_session_key(filepath)
        session_id = filepath.stem
        
        # Get current position
        str_path = str(filepath)
        position = self.state.get_position(str_path)
        file_size = filepath.stat().st_size
        
        if file_size < position:
            # File was truncated, start from beginning
            position = 0
        
        if file_size == position:
            # No new content
            return
        
        new_count = 0
        with open(filepath, 'r') as f:
            f.seek(position)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if self.insert_message(msg, session_key, session_id):
                        new_count += 1
                except json.JSONDecodeError:
                    pass
            
            # Update position
            new_position = f.tell()
            self.state.set_position(str_path, new_position)
        
        if new_count > 0 and not initial:
            print(f"📥 {new_count} new message(s) from {session_key}")
        
        self.state.save()
    
    def extract_session_key(self, filepath: Path) -> str:
        """Extract session key from file path or sessions.json."""
        # Try to read from sessions.json
        sessions_file = SESSIONS_DIR / "sessions.json"
        session_id = filepath.stem
        
        if sessions_file.exists():
            try:
                with open(sessions_file) as f:
                    sessions = json.load(f)
                    for entry in sessions.get("sessions", []):
                        if entry.get("sessionId") == session_id or entry.get("id") == session_id:
                            return entry.get("sessionKey", entry.get("key", f"session:{session_id}"))
            except (json.JSONDecodeError, IOError):
                pass
        
        # Fallback: use agent:main:main as default for the main agent
        return "agent:main:main"
    
    def initial_sync(self):
        """Process all existing files to catch up."""
        print("🔄 Performing initial sync...")
        count = 0
        if SESSIONS_DIR.exists():
            # Process JSONL files directly in sessions dir
            for jsonl_file in SESSIONS_DIR.glob("*.jsonl"):
                if not jsonl_file.name.endswith('.deleted'):
                    self.process_file(jsonl_file, initial=True)
                    count += 1
            # Also check subdirectories (for older format)
            for session_dir in SESSIONS_DIR.iterdir():
                if session_dir.is_dir() and session_dir.name != 'archive':
                    for jsonl_file in session_dir.glob("*.jsonl"):
                        self.process_file(jsonl_file, initial=True)
                        count += 1
        print(f"✅ Synced {count} session files")
    
    def run(self):
        """Main event loop."""
        if not self.connect_db():
            return 1
        if not self.ensure_schema():
            return 1
        
        self.initial_sync()
        
        # Set up watchdog observer
        recorder = self
        
        class Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.is_directory:
                    return
                if event.src_path.endswith('.jsonl') and '.deleted' not in event.src_path:
                    recorder.process_file(Path(event.src_path))
            
            def on_created(self, event):
                if event.is_directory:
                    return
                if event.src_path.endswith('.jsonl') and '.deleted' not in event.src_path:
                    recorder.process_file(Path(event.src_path))
        
        observer = Observer()
        observer.schedule(Handler(), str(SESSIONS_DIR), recursive=True)
        observer.start()
        
        print(f"👁️ Watching {SESSIONS_DIR} for changes...")
        print("Press Ctrl+C to stop")
        
        def signal_handler(sig, frame):
            print("\n👋 Shutting down...")
            self.running = False
            observer.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        observer.join()
        print("✅ Recorder stopped")
        return 0


def main():
    recorder = ChatRecorder()
    sys.exit(recorder.run())


if __name__ == "__main__":
    main()
