# Memory-Assisted Tool Discovery - Design Document

**Date:** 2026-01-19
**Status:** Design Complete - Ready for Implementation
**Priority:** High (Addresses critical tool discoverability issue)

## Problem Statement

Custom tools (LLM Council, Kage Bunshin, custom scripts) fall out of awareness despite being built and available. The session where LLM Council was forgotten despite building it together demonstrates this critical gap. Tools need proactive discovery based on conversation context.

## Goals

1. Surface relevant custom tools at session start based on recent conversation topics
2. Suggest high-value tools during conversation when specific keywords detected
3. Maintain <300 token/session overhead (C-lite approach)
4. Zero session crashes - graceful degradation on failures
5. Easy to tune/disable if suggestions become annoying

## Architecture Overview

### Approach: SessionStart Hook + Memory References

**Components:**
1. **Tool Registry** - Claude-memory database storing tool metadata
2. **SessionStart Hook** - Bash wrapper calling Python for startup suggestions
3. **UserPromptSubmit Hook** - Real-time keyword detection for high-value tools
4. **Shared Python Script** - Core matching and scoring logic

**Token Budget:**
- SessionStart: ~250 tokens (3-5 tools with descriptions)
- Real-time: ~50 tokens when triggered (rare, rate-limited)
- Total: ~300 tokens/session average (0.15% of 200K budget)

## Tool Registry Data Model

### Storage Format

Uses existing `memory_write` function with type="reference", category="tool":

```json
{
  "type": "reference",
  "category": "tool",
  "key": "llm-council",
  "value": {
    "name": "LLM Council",
    "location": "/home/ndninja/projects/llm-council/",
    "command": "python3 /home/ndninja/projects/llm-council/council.py",
    "description": "Multi-model analysis tool - queries 4 LLMs in parallel and synthesizes results",
    "keywords": ["multi-model", "research", "analysis", "consensus", "complex-question", "vpn"],
    "usage_examples": [
      "Research: Compare VPN providers",
      "Analysis: Evaluate architectural trade-offs",
      "Validation: Cross-check complex technical decisions"
    ],
    "performance": "~3-5 min, $0.15-0.30 per query",
    "last_used": "2026-01-16",
    "use_count": 15
  },
  "device": "all",
  "notes": "Custom-built tool for complex analysis requiring diverse perspectives"
}
```

### Registry Population

**Initial Seed:**
- Manually register 5-10 high-value tools via `tool_registry_seed.py`
- Priority tools: LLM Council, Kage Bunshin, doc generator, vengeance-validate, permission-helper

**Automated Discovery:**
- Script scans `~/scripts/*.py`, `~/projects/*/README.md` for tool candidates
- Suggests additions based on shebang, imports, argparse definitions
- User approves/rejects suggestions

**Maintenance:**
- Update `last_used` and `use_count` via PostToolUse hook when tools invoked
- Stale tools (not used in 90 days) flagged for review

### Querying

Direct PostgreSQL for performance:
```bash
psql -h localhost -U claude_mcp -d claude_memory -t -c \
  "SELECT content FROM references WHERE category='tool' AND device IN ('all', 'server')"
```

## Matching Logic

### SessionStart Matching Algorithm

1. Query last 3 conversation summaries:
   ```python
   get_recent_conversations(limit=3, app_source='code')
   ```

2. Extract topics from `topics_discussed` field:
   ```
   ["distributed AI orchestration", "video production", "Docker debugging"]
   ```

3. Tokenize topics:
   ```
   ["distributed", "ai", "orchestration", "video", "production", "docker", "debugging"]
   ```

4. Match against tool keywords with scoring:
   - Exact keyword match: +10 points
   - Partial match (substring): +5 points
   - Recently used (last 7 days): +3 points
   - High use count (>10): +2 points

5. Return top 3-5 tools sorted by score

6. Format output:
   ```
   Relevant tools for this session:
   - LLM Council: Multi-model analysis tool (/home/ndninja/projects/llm-council/council.py)
   - Kage Bunshin: Distributed AI orchestration (cd ~/projects/kage-bunshin && ./dispatch.sh)
   - Docker Env Debugger: Container diagnostics (docker-env-check <container>)
   ```

### Real-time Matching (UserPromptSubmit)

**Keyword Allowlist:**
```json
{
  "multi-model|consensus|vpn analysis": "llm-council",
  "distributed|kage bunshin|72b": "kage-bunshin",
  "docker environment|container debug": "docker-env-debugger"
}
```

**Process:**
1. Scan user prompt for regex matches (case-insensitive)
2. Check rate limit: Skip if < 5 messages since last suggestion
3. Check if tool already used in session: Skip if yes
4. Output suggestion in system-reminder format

**Anti-spam Rules:**
- Max 1 real-time suggestion per 5 user messages
- Skip if tool mentioned in last 10 messages
- Skip if SessionStart already suggested same tool
- Configurable via preference: `discovery_realtime = disabled`

## Implementation Files

```
.claude/hooks/
  on-session-start-tool-discovery.sh      # 20 lines - bash wrapper
  on-user-prompt-tool-discovery.sh        # 25 lines - bash wrapper + rate limit

scripts/
  tool_discovery.py                       # 180 lines - core logic
  tool_registry_seed.py                   # 80 lines - populate initial registry
  tests/test_tool_discovery.py            # 120 lines - unit tests
```

### scripts/tool_discovery.py

**Functions:**
- `get_relevant_tools(recent_topics: List[str]) -> List[Tool]`
  - Queries tool registry from claude-memory
  - Scores tools against topics
  - Returns top N by score

- `match_keywords(prompt: str, allowlist: Dict) -> Optional[Tool]`
  - Scans prompt for high-value keywords
  - Returns matching tool or None

- `format_suggestion(tools: List[Tool]) -> str`
  - Formats tool list for system-reminder output
  - Includes name, description, command

- `check_rate_limit(session_id: str) -> bool`
  - Reads `/tmp/tool-discovery-session-{pid}.json`
  - Returns True if suggestion allowed, False if rate-limited

- `update_usage_stats(tool_id: str) -> None`
  - Increments use_count, updates last_used timestamp
  - Called by PostToolUse hook

**Dependencies:**
- Python 3.13+
- psycopg2 (already installed)
- PostgreSQL access via .pgpass (already configured)

### Hook Installation

```bash
# Copy hooks
cp on-session-start-tool-discovery.sh ~/.claude/hooks/
cp on-user-prompt-tool-discovery.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/on-*-tool-discovery.sh

# Copy scripts
cp tool_discovery.py ~/scripts/
cp tool_registry_seed.py ~/scripts/

# Seed registry
python3 ~/scripts/tool_registry_seed.py

# Test
# Start new session, verify suggestions appear
```

## Error Handling & Edge Cases

### Graceful Degradation

**Hook failures:**
- All hooks wrapped in try/catch
- Failures logged to `~/.logs/tool-discovery.log`
- Never crash session - silently skip suggestions on error

**Database unavailable:**
- Skip suggestions silently
- Don't block session start
- Log warning to tool-discovery.log

**Python script errors:**
- Catch exceptions, output "Tool discovery unavailable" once per session
- Continue session normally

**Timeout protection:**
- SessionStart: Hard 200ms limit
- UserPromptSubmit: Hard 50ms limit
- Kill script if timeout exceeded

### Edge Cases

1. **Empty tool registry:**
   - Output: "No tools registered yet - run tool_registry_seed.py"
   - SessionStart completes normally

2. **No recent conversations:**
   - Skip topic matching
   - Suggest top 3 most-used tools instead

3. **New session (no history):**
   - Show generic welcome with 3 most popular tools
   - "Getting started tools: [list]"

4. **Tool command broken:**
   - Suggestions still appear
   - Usage tracking shows 0 recent uses (helps identify stale tools)

5. **Duplicate tools:**
   - Registry uses unique keys
   - Duplicates rejected with warning during seed

### Performance Safeguards

- Tool registry cached for session duration (no repeated DB queries)
- Rate limit state stored in `/tmp/tool-discovery-session-{pid}.json`
- Auto-cleanup on session exit
- Maximum 10 tools matched per session (prevents token explosion)

### Privacy Considerations

- Topic extraction only uses conversation summary metadata
- No full message content processed
- Keywords stored in registry, not user queries
- No external API calls - all local processing

## Testing & Validation

### Unit Tests

`scripts/tests/test_tool_discovery.py`:

```python
def test_keyword_matching():
    # Verify exact/partial matches score correctly

def test_rate_limiting():
    # Ensure suggestions throttled properly

def test_topic_extraction():
    # Parse conversation summaries accurately

def test_empty_registry():
    # Graceful handling of no tools

def test_scoring_algorithm():
    # Top tools ranked by relevance
```

### Integration Tests

1. Seed registry with test tools
2. Simulate SessionStart with mock conversation history
3. Verify relevant suggestions output
4. Trigger UserPromptSubmit with known keywords
5. Verify correct tool suggested
6. Test rate limiting across multiple prompts
7. Verify database queries return expected format

### Manual Validation Checklist

- [ ] Start new session → see tool suggestions in startup output
- [ ] Type "I need to analyze VPN options" → LLM Council suggested
- [ ] Mention "docker environment" → Docker debugger suggested
- [ ] Send 5 quick messages → no spam (rate limited)
- [ ] Check `~/.logs/tool-discovery.log` → no errors
- [ ] Query registry: `psql -d claude_memory -c "SELECT key FROM references WHERE category='tool'"` → see seeded tools

### Success Metrics

- Tool discovery adds <300ms to session startup
- Real-time suggestions <50ms latency
- Zero session crashes due to hook failures
- User uses suggested tool at least 1x in next 5 sessions (validates relevance)
- Suggestion accuracy >70% (user finds suggestion relevant)

### Rollback Plan

Simple and fast:
```bash
rm ~/.claude/hooks/on-*-tool-discovery.sh
```

- Session immediately returns to normal (hooks optional)
- Registry data persists for future use
- No code changes required

## Configuration & Tuning

### Disable Real-time Suggestions

```python
memory_write("preference", "tool", "discovery_realtime", "disabled")
```

### Adjust Rate Limit

Edit `scripts/tool_discovery.py`:
```python
RATE_LIMIT_MESSAGES = 10  # Default: 5
```

### Modify Keywords

Update tool registry:
```python
memory_write("reference", "tool", "llm-council", json.dumps({
    ...
    "keywords": ["multi-model", "research", "your-new-keyword"]
}))
```

### Disable SessionStart Suggestions

```bash
rm ~/.claude/hooks/on-session-start-tool-discovery.sh
```

Keep UserPromptSubmit for real-time only.

## Future Enhancements

**Phase 2 (optional):**
- Analytics dashboard showing which tools most/least used
- Auto-suggest new tools based on script creation patterns
- Integration with skill suggestions system
- Tool dependency tracking (Tool A often used after Tool B)
- Performance benchmarking per tool

**Phase 3 (optional):**
- Claude Code plugin UI for managing registry
- Shared tool registry across team via git
- Tool version tracking and upgrade notifications
- A/B testing different suggestion algorithms

## Implementation Timeline

**Estimated: 1.5 hours total**

- [ ] 30 min: Write `tool_discovery.py` core logic
- [ ] 15 min: Write SessionStart hook wrapper
- [ ] 15 min: Write UserPromptSubmit hook wrapper
- [ ] 15 min: Write `tool_registry_seed.py`
- [ ] 15 min: Unit tests
- [ ] 10 min: Manual testing and validation

## Approval & Next Steps

**Design approved:** [Pending]

**Upon approval:**
1. Implement files per specification
2. Run unit tests
3. Seed registry with initial 10 tools
4. Manual validation
5. Commit to git: "Add Memory-Assisted Tool Discovery system"
6. Update skill_suggestions table: Mark suggestion as implemented
7. Monitor for 1 week, collect feedback, tune if needed

---

**Design Status:** ✅ Complete - Ready for Implementation
