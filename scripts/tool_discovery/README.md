# Memory-Assisted Tool Discovery

Proactive tool suggestion system that surfaces relevant custom tools based on conversation context.

## Overview

This system automatically suggests relevant custom tools, skills, and commands by analyzing conversation history and detecting keywords in real-time. It integrates with the claude-memory database to maintain a registry of tools with metadata like descriptions, keywords, and usage statistics.

## Components

### 1. SessionStart Discovery

**File:** `session_start.py`

- Runs on Claude Code session start
- Queries last 5 conversation summaries from `conversation_summaries` table
- Extracts topics from `topics_discussed` JSONB field
- Matches topics against tool keywords using the ToolScorer
- Shows top 5 relevant tools ranked by score

**Scoring Algorithm:**
- Exact keyword match: +10 points
- Partial keyword match: +5 points
- Recent usage (< 7 days): +3 points
- High usage (> 10 times): +2 points

**Usage:**
```python
from session_start import SessionStartDiscovery

discovery = SessionStartDiscovery()
tools = discovery.get_relevant_tools(limit=5)
print(discovery.format_suggestions(tools))
```

### 2. Real-time Detection

**File:** `realtime.py`

- Triggered on user prompt submission via PostToolUse hook
- Regex matching for high-value keywords
- Rate limited: 1 suggestion per 5 messages
- Only suggests each tool once per session
- State persisted to `/tmp/tool-discovery-session-{pid}.json`

**Keyword Patterns:**
```python
KEYWORD_PATTERNS = {
    r'multi-model|consensus|vpn analysis': 'llm-council',
    r'distributed|kage bunshin|72b': 'kage-bunshin',
    r'docker environment|container debug': 'docker-env-debugger'
}
```

**Rate Limiting:**
- Tracks message count per session
- Resets counter after showing a suggestion
- Prevents overwhelming user with too many suggestions
- Configurable via `RATE_LIMIT_MESSAGES` constant

**Usage:**
```python
from realtime import RealtimeDiscovery

discovery = RealtimeDiscovery()
suggestion = discovery.suggest_tool(user_prompt)
if suggestion:
    print(suggestion)
discovery.close()
```

### 3. Tool Registry

**Database:** `claude_memory.reference_info`

Tools are stored as reference entries with:
- **category**: 'tool' (used to filter tool entries)
- **title**: Tool identifier/key (e.g., 'llm-council')
- **content**: JSONB with tool metadata
- **notes**: Additional notes or documentation
- **device**: Target device ('all', 'windows_home', 'server', etc.)
- **context_tag**: When to use ('always', 'work', 'coding', etc.)
- **active**: Boolean flag (only active tools are retrieved)

**Tool Metadata Structure:**
```json
{
  "name": "LLM Council",
  "description": "Multi-model consensus analysis",
  "command": "/llm-council",
  "keywords": ["consensus", "multi-model", "analysis"],
  "category": "analysis",
  "last_used": "2026-01-19",
  "use_count": 15,
  "performance": {
    "avg_time": 2.5,
    "success_rate": 0.95
  }
}
```

### 4. ToolScorer

**File:** `scorer.py`

Ranks tools based on conversation topics with configurable scoring weights:

```python
EXACT_MATCH = 10      # Keyword exactly matches topic token
PARTIAL_MATCH = 5     # Keyword is substring of topic token
RECENT_BONUS = 3      # Tool used within last 7 days
HIGH_USAGE_BONUS = 2  # Tool used more than 10 times
```

### 5. Database Interface

**File:** `database.py`

Provides PostgreSQL connection to claude-memory database:
- Connects using credentials from `.pgpass`
- Queries `reference_info` table with correct schema
- Returns tools with consistent structure

**Connection:**
```python
from database import ToolDatabase

db = ToolDatabase()
if db.connect():
    tools = db.get_all_tools()
    db.close()
```

## Usage

### View Registered Tools

```bash
# List all tools in registry
psql -h localhost -U claude_mcp -d claude_memory -c \
  "SELECT title, content->>'name' as name, content->>'description' as description
   FROM reference_info
   WHERE category='tool' AND active=true
   ORDER BY updated_at DESC;"
```

### Test SessionStart Discovery

```bash
# Run directly
python3 /home/ndninja/scripts/tool_discovery/session_start.py

# Or test via hook (if installed)
~/.claude/hooks/on-session-start-tool-discovery.sh
```

### Test Real-time Detection

```bash
# Run directly
python3 /home/ndninja/scripts/tool_discovery/realtime.py

# Or test via hook (if installed)
~/.claude/hooks/on-user-prompt-tool-discovery.sh "multi-model analysis"
```

### Test Database Integration

```bash
# Verify database connection and tool retrieval
python3 /home/ndninja/scripts/tool_discovery/test_db_proof.py
```

## Configuration

### Disable Real-time Suggestions

Edit `scripts/tool_discovery/realtime.py`:
```python
RATE_LIMIT_MESSAGES = 999  # Effectively disabled
```

### Adjust Rate Limiting

```python
# Change frequency of suggestions (default: 5)
RATE_LIMIT_MESSAGES = 10  # 1 suggestion per 10 messages
```

### Add Custom Keywords

Edit `scripts/tool_discovery/realtime.py`:
```python
KEYWORD_PATTERNS = {
    r'multi-model|consensus|vpn analysis': 'llm-council',
    r'distributed|kage bunshin|72b': 'kage-bunshin',
    r'docker environment|container debug': 'docker-env-debugger',
    # Add your patterns:
    r'your-pattern|alternative': 'your-tool-key',
}
```

### Add New Tool to Registry

**Method 1: Direct SQL**
```sql
INSERT INTO reference_info (category, title, content, notes, device, context_tag, active)
VALUES (
    'tool',
    'my-tool',
    '{"name": "My Tool", "description": "Tool description", "keywords": ["key1", "key2"], "command": "/my-tool"}',
    'Optional notes',
    'all',
    'always',
    true
);
```

**Method 2: Python**
```python
import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    user='claude_mcp',
    database='claude_memory'
)
cursor = conn.cursor()

tool_data = {
    'name': 'My Tool',
    'description': 'Detailed description',
    'command': '/my-tool',
    'keywords': ['keyword1', 'keyword2'],
    'category': 'utility',
    'last_used': '2026-01-19',
    'use_count': 0
}

cursor.execute("""
    INSERT INTO reference_info (category, title, content, notes, device, context_tag, active)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", (
    'tool',
    'my-tool',
    json.dumps(tool_data),
    'Additional notes',
    'all',
    'always',
    True
))

conn.commit()
cursor.close()
conn.close()
```

### Update Tool Metadata

```python
import psycopg2
import json

conn = psycopg2.connect(host='localhost', user='claude_mcp', database='claude_memory')
cursor = conn.cursor()

# Increment use count
cursor.execute("""
    UPDATE reference_info
    SET content = jsonb_set(
        content,
        '{use_count}',
        to_jsonb((content->>'use_count')::int + 1)
    ),
    updated_at = NOW()
    WHERE category = 'tool' AND title = 'my-tool'
""")

conn.commit()
cursor.close()
conn.close()
```

### Adjust Scoring Weights

Edit `scripts/tool_discovery/scorer.py`:
```python
class ToolScorer:
    EXACT_MATCH = 10
    PARTIAL_MATCH = 5
    RECENT_BONUS = 3
    HIGH_USAGE_BONUS = 2
```

## Troubleshooting

### No suggestions appearing

**Check database connection:**
```bash
python3 /home/ndninja/scripts/tool_discovery/test_db_proof.py
```

**Verify tools in registry:**
```bash
psql -h localhost -U claude_mcp -d claude_memory -c \
  "SELECT COUNT(*) FROM reference_info WHERE category='tool' AND active=true;"
```

**Check recent conversations:**
```bash
psql -h localhost -U claude_mcp -d claude_memory -c \
  "SELECT session_id, topics_discussed FROM conversation_summaries ORDER BY created_at DESC LIMIT 5;"
```

**Test components individually:**
```bash
# Test SessionStart
python3 -c "from session_start import SessionStartDiscovery; d = SessionStartDiscovery(); print(d.format_suggestions(d.get_relevant_tools()))"

# Test Realtime
python3 -c "from realtime import RealtimeDiscovery; d = RealtimeDiscovery(); print(d.suggest_tool('need multi-model consensus'))"
```

### Rate limiting too aggressive

**Adjust rate limit:**
```python
# In realtime.py
RATE_LIMIT_MESSAGES = 10  # Default: 5
```

**Reset session state:**
```bash
rm /tmp/tool-discovery-session-*.json
```

### Keywords not matching

**Check keyword patterns:**
```python
# Test regex matching
import re
pattern = r'multi-model|consensus'
text = "I need consensus analysis"
print(re.search(pattern, text.lower()))  # Should match
```

**Add more patterns:**
```python
# In realtime.py - add variations
KEYWORD_PATTERNS = {
    r'multi.?model|consensus|multiple models': 'llm-council',
    # ... more patterns
}
```

### Database connection fails

**Check PostgreSQL is running:**
```bash
systemctl status postgresql
```

**Verify credentials in .pgpass:**
```bash
cat ~/.pgpass | grep claude_memory
# Should show: localhost:5432:claude_memory:claude_mcp:password
```

**Test connection manually:**
```bash
psql -h localhost -U claude_mcp -d claude_memory -c "SELECT 1;"
```

### Wrong schema errors

**Common mistakes:**
```python
# WRONG - from old design
SELECT key, title FROM references WHERE category='tool';

# CORRECT - actual schema
SELECT title, content->>'name' as name FROM reference_info WHERE category='tool';
```

**Schema reference:**
- Table: `reference_info` (not `references`)
- Key column: `title` (not `key`)
- Tool data: `content` JSONB field
- Filter: `category='tool' AND active=true`

### Hooks not running

**Verify hook files exist:**
```bash
ls -la ~/.claude/hooks/on-*-tool-discovery.sh
```

**Check executability:**
```bash
chmod +x ~/.claude/hooks/on-session-start-tool-discovery.sh
chmod +x ~/.claude/hooks/on-user-prompt-tool-discovery.sh
```

**Test hooks manually:**
```bash
~/.claude/hooks/on-session-start-tool-discovery.sh
~/.claude/hooks/on-user-prompt-tool-discovery.sh "test prompt"
```

## Architecture

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interaction                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ├─── Session Start
                           │         │
                           │         ▼
                           │   ┌──────────────────┐
                           │   │ SessionStart     │
                           │   │ Hook             │
                           │   └──────────────────┘
                           │         │
                           │         ▼
                           │   ┌──────────────────┐
                           │   │ session_start.py │
                           │   └──────────────────┘
                           │         │
                           │         ├─── Query DB for recent conversations
                           │         ├─── Extract topics
                           │         ├─── Get all tools from registry
                           │         ├─── Score tools (scorer.py)
                           │         └─── Return top 5
                           │
                           └─── User Prompt
                                     │
                                     ▼
                               ┌──────────────────┐
                               │ PostToolUse      │
                               │ Hook             │
                               └──────────────────┘
                                     │
                                     ▼
                               ┌──────────────────┐
                               │ realtime.py      │
                               └──────────────────┘
                                     │
                                     ├─── Check rate limit
                                     ├─── Match keywords (regex)
                                     ├─── Query DB for tool data
                                     ├─── Check if already suggested
                                     └─── Format and return suggestion

┌─────────────────────────────────────────────────────────────┐
│              Claude Memory Database (PostgreSQL)             │
├─────────────────────────────────────────────────────────────┤
│  Table: reference_info                                       │
│  - category: 'tool'                                          │
│  - title: tool-key                                           │
│  - content: JSONB (name, description, keywords, etc.)        │
│  - notes, device, context_tag, active                        │
│                                                              │
│  Table: conversation_summaries                               │
│  - session_id, summary, topics_discussed (JSONB array)       │
│  - action_items, key_decisions, created_at                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
┌──────────────────┐
│  ToolDatabase    │ ← Database interface
│  (database.py)   │
└──────────────────┘
         ↑
         │ get_all_tools()
         │
    ┌────┴────┐
    │         │
    │         │
┌───┴─────┐ ┌─┴────────────┐
│ session │ │  realtime    │
│ _start  │ │  .py         │
│ .py     │ │              │
└─────────┘ └──────────────┘
    │              │
    │              │ match_keywords()
    │              │
    ▼              ▼
┌──────────────────┐
│   ToolScorer     │ ← Ranking algorithm
│   (scorer.py)    │
└──────────────────┘
```

## Testing

### Run All Tests

```bash
cd /home/ndninja/scripts/tool_discovery
python3 -m pytest tests/ -v
```

### Run Specific Test Suites

```bash
# Integration tests (end-to-end)
python3 -m pytest tests/test_integration.py -v

# Real-time detection tests
python3 -m pytest tests/test_realtime.py -v

# Database integration proof
python3 test_db_proof.py

# Database integration tests
python3 test_db_integration.py
```

### Test Coverage

```bash
python3 -m pytest tests/ --cov=. --cov-report=html
```

### Manual Testing Workflow

**1. Verify database setup:**
```bash
python3 test_db_proof.py
```

**2. Test SessionStart discovery:**
```bash
python3 session_start.py
```

**3. Test real-time detection:**
```bash
python3 -c "
from realtime import RealtimeDiscovery
d = RealtimeDiscovery()
print(d.suggest_tool('I need multi-model consensus'))
d.close()
"
```

**4. Test scoring algorithm:**
```bash
python3 -c "
from scorer import ToolScorer
from database import ToolDatabase

db = ToolDatabase()
db.connect()
tools = db.get_all_tools()
db.close()

scorer = ToolScorer()
topics = ['analysis', 'consensus', 'multi-model']
ranked = scorer.rank_tools(tools, topics, limit=3)

for tool, score in ranked:
    print(f'{tool[\"key\"]}: {score}')
"
```

## Performance Considerations

### Database Queries

- SessionStart: 1 query for conversations + 1 query for tools
- Real-time: 1 query per keyword match (cached per tool)
- Indexes recommended:
  - `reference_info(category, active)` for tool queries
  - `conversation_summaries(created_at DESC)` for recent conversations

### State Management

- Real-time state stored in `/tmp/tool-discovery-session-{pid}.json`
- State expires after 24 hours to prevent PID reuse issues
- State file is ~1KB, minimal disk usage

### Memory Usage

- ToolDatabase connection: ~5MB
- Tool registry (in memory): ~100 tools × 2KB = ~200KB
- Conversation summaries: ~5 × 5KB = ~25KB
- Total per session: ~5.2MB

## Future Enhancements

- **Learning system**: Track which suggestions users act on
- **Adaptive scoring**: Adjust weights based on user behavior
- **Cross-session patterns**: Identify tool sequences (Tool A → Tool B)
- **Performance tracking**: Record tool execution time and success rate
- **Automatic keyword extraction**: Learn keywords from tool usage
- **Collaborative filtering**: Suggest tools similar users found helpful

## References

- **Design Document**: `/home/ndninja/docs/plans/2026-01-19-memory-assisted-tool-discovery-design.md`
- **Implementation Plan**: `/home/ndninja/docs/plans/2026-01-19-memory-assisted-tool-discovery.md`
- **Database Schema**: claude-memory MCP server schema
- **Tool Discovery Issue**: [Original feature request]
