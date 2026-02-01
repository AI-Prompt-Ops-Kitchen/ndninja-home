#!/usr/bin/env python3
"""
Query chat history from PostgreSQL.
Useful for catching up after context compaction.
"""

import sys
import argparse
from datetime import datetime, timedelta, timezone
import psycopg2

DB_NAME = "clawd_chat"
DB_USER = "ndninja"

def get_db():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER)

def recent(hours=24, limit=50):
    """Show recent messages."""
    conn = get_db()
    cur = conn.cursor()
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    cur.execute("""
        SELECT timestamp, role, content 
        FROM chat_messages 
        WHERE timestamp > %s AND content_type = 'text'
        ORDER BY timestamp ASC
        LIMIT %s
    """, (cutoff, limit))
    
    print(f"\n📜 Last {hours} hours of conversation ({limit} messages max):\n")
    print("-" * 80)
    
    for ts, role, content in cur.fetchall():
        emoji = "🧑" if role == "user" else "🐾"
        # Truncate long messages
        preview = content[:500] if content else ""
        if len(content or "") > 500:
            preview += "..."
        
        print(f"{emoji} [{ts.strftime('%m/%d %H:%M')}] {role.upper()}")
        print(f"   {preview}\n")
    
    cur.close()
    conn.close()

def search(query, limit=20):
    """Full-text search through messages."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT timestamp, role, content,
               ts_headline('english', content, plainto_tsquery('english', %s), 
                          'MaxWords=30, MinWords=10, StartSel=>>>, StopSel=<<<') as headline
        FROM chat_messages 
        WHERE to_tsvector('english', content) @@ plainto_tsquery('english', %s)
        ORDER BY timestamp DESC
        LIMIT %s
    """, (query, query, limit))
    
    results = cur.fetchall()
    print(f"\n🔍 Search results for '{query}' ({len(results)} found):\n")
    
    for ts, role, content, headline in results:
        emoji = "🧑" if role == "user" else "🐾"
        print(f"{emoji} [{ts.strftime('%m/%d %H:%M')}]")
        print(f"   ...{headline}...\n")
    
    cur.close()
    conn.close()

def summary():
    """Show database stats."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM chat_messages")
    count, oldest, newest = cur.fetchone()
    
    cur.execute("""
        SELECT role, COUNT(*) 
        FROM chat_messages 
        GROUP BY role 
        ORDER BY COUNT(*) DESC
    """)
    roles = cur.fetchall()
    
    print(f"\n📊 Chat History Stats:")
    print(f"   Total messages: {count}")
    print(f"   Date range: {oldest.strftime('%Y-%m-%d %H:%M')} → {newest.strftime('%Y-%m-%d %H:%M')}")
    print(f"\n   By role:")
    for role, cnt in roles:
        print(f"     {role}: {cnt}")
    
    cur.close()
    conn.close()

def topics(hours=24):
    """Extract recent topics/themes from conversation."""
    conn = get_db()
    cur = conn.cursor()
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Get user messages (they indicate topics of interest)
    cur.execute("""
        SELECT content 
        FROM chat_messages 
        WHERE timestamp > %s AND role = 'user' AND content_type = 'text'
        ORDER BY timestamp DESC
        LIMIT 30
    """, (cutoff,))
    
    print(f"\n📋 Recent user requests (last {hours}h):\n")
    for (content,) in cur.fetchall():
        preview = content[:100].replace('\n', ' ')
        if len(content) > 100:
            preview += "..."
        print(f"  • {preview}")
    
    cur.close()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Query chat history")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # recent
    p = subparsers.add_parser("recent", help="Show recent messages")
    p.add_argument("-H", "--hours", type=int, default=24, help="Hours to look back")
    p.add_argument("-n", "--limit", type=int, default=50, help="Max messages")
    
    # search
    p = subparsers.add_parser("search", help="Full-text search")
    p.add_argument("query", help="Search query")
    p.add_argument("-n", "--limit", type=int, default=20, help="Max results")
    
    # summary
    subparsers.add_parser("summary", help="Show stats")
    
    # topics
    p = subparsers.add_parser("topics", help="Recent topics discussed")
    p.add_argument("-H", "--hours", type=int, default=24, help="Hours to look back")
    
    args = parser.parse_args()
    
    if args.command == "recent":
        recent(args.hours, args.limit)
    elif args.command == "search":
        search(args.query, args.limit)
    elif args.command == "summary":
        summary()
    elif args.command == "topics":
        topics(args.hours)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python query_chat.py summary")
        print("  python query_chat.py recent -H 4")
        print("  python query_chat.py search 'PostgreSQL'")
        print("  python query_chat.py topics -H 12")

if __name__ == "__main__":
    main()
