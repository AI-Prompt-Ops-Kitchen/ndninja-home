---
name: rasengan
description: Interact with Rasengan — the central event hub and rules engine connecting all ninja ecosystem tools. Triggers on "rasengan", "event hub", "tail events", "emit event", "check rules", "what happened", "resume context".
---

# Rasengan — Event Hub + Rules Engine CLI

Query, emit, and monitor events across the entire ninja ecosystem (Dojo, Sharingan, Sage Mode, Glitch) from the terminal.

## Invocation

```
/rasengan status              # System health + activity summary
/rasengan events              # Recent events
/rasengan resume              # Context recovery (git + scrolls + deploys + recent events)
/rasengan emit <type> <src>   # Fire an event
/rasengan rules               # List all rules
/rasengan tail                # Live event stream
/rasengan deploy              # List deploy registry or run a deploy
/rasengan ci                  # View git + deploy events
```

Natural language also works:
- "What happened in Rasengan?" → `status` or `events`
- "Catch me up" / "Resume context" → `resume`
- "Show me the event stream" / "Watch live" / "Tail events" → `tail`
- "What rules are set up?" / "Check rules" → `rules`
- "Fire an event" / "Emit event" → `emit`
- "Deploy sage mode" / "Run a deploy" → `deploy`
- "What was deployed?" / "Recent commits" / "CI activity" → `ci`

## CLI Location

```
python3 /home/ndninja/rasengan/cli.py <command>
```

**Environment:** `RASENGAN_URL` (default: `http://127.0.0.1:8050`)

## Commands

### status
System health and event count breakdown by source and type.
```bash
python3 /home/ndninja/rasengan/cli.py status
```

### events
Query event history with optional filters.
```bash
python3 /home/ndninja/rasengan/cli.py events                          # Last 20 events
python3 /home/ndninja/rasengan/cli.py events --source dojo --limit 5  # Dojo events only
python3 /home/ndninja/rasengan/cli.py events --type dojo.job_completed # Filter by type
```

### resume
Context recovery snapshot — aggregates git state, Sharingan scrolls, and recent events into a single view. Use this when starting a new session or after context-switching.
```bash
python3 /home/ndninja/rasengan/cli.py resume
```

### emit
Fire an event into the hub. Payload is optional JSON.
```bash
python3 /home/ndninja/rasengan/cli.py emit test.ping cli
python3 /home/ndninja/rasengan/cli.py emit dojo.manual_run dojo '{"job_id":"abc123"}'
```

### rules
Manage the declarative rules engine (IFTTT-style automation).

```bash
python3 /home/ndninja/rasengan/cli.py rules                    # List all rules
python3 /home/ndninja/rasengan/cli.py rules add '<json>'       # Create a rule
python3 /home/ndninja/rasengan/cli.py rules toggle <id>        # Enable/disable
python3 /home/ndninja/rasengan/cli.py rules delete <id>        # Delete a rule
python3 /home/ndninja/rasengan/cli.py rules log                # Recent execution log
python3 /home/ndninja/rasengan/cli.py rules log <id>           # Executions for one rule
```

**Rule JSON format:**
```json
{
  "name": "alert_on_failure",
  "event_type": "dojo.job_failed",
  "source": "dojo",
  "condition": {
    "payload.retry_count": { "$gt": 2 }
  },
  "action": {
    "type": "emit",
    "event_type": "alert.dojo_failure",
    "source": "rasengan",
    "payload_template": { "job": "{payload.job_id}" }
  },
  "cooldown_seconds": 300
}
```

**Condition operators:** `$eq`, `$ne`, `$gt`, `$lt`, `$contains`, `$in`
**Action types:** `log`, `emit`, `webhook`
**Event type patterns:** Supports glob matching (e.g., `dojo.*` matches all dojo events)

### deploy
Run deploy scripts with automatic event tracking. Without a service name, lists the registry.
```bash
python3 /home/ndninja/rasengan/cli.py deploy                 # List known services
python3 /home/ndninja/rasengan/cli.py deploy sage_mode       # Deploy with tracking
python3 /home/ndninja/rasengan/cli.py deploy sage_mode --dry # Show what would run
```

**Registry:** `sage_mode`, `ndn_infra`, `landing`

### ci
Convenience filter for git + deploy events.
```bash
python3 /home/ndninja/rasengan/cli.py ci              # All git + deploy events
python3 /home/ndninja/rasengan/cli.py ci --git        # Only git events
python3 /home/ndninja/rasengan/cli.py ci --deploy     # Only deploy events
python3 /home/ndninja/rasengan/cli.py ci -n 50        # More results
```

### tail
Live event stream via WebSocket. Client-side filtering. Ctrl+C to stop.
```bash
python3 /home/ndninja/rasengan/cli.py tail                         # All events
python3 /home/ndninja/rasengan/cli.py tail --type dojo.job_created # Filter by type
python3 /home/ndninja/rasengan/cli.py tail --source sharingan      # Filter by source
```

## Common Patterns

| User says | Command |
|-----------|---------|
| "Catch me up" | `resume` |
| "What happened today?" | `events --limit 50` |
| "Watch live" | `tail` |
| "What failed?" | `events --type dojo.job_failed` |
| "How's Rasengan?" | `status` |
| "Show me rules" | `rules` |
| "Disable rule 3" | `rules toggle 3` |
| "Test an event" | `emit test.ping cli '{"msg":"hello"}'` |
| "Deploy sage mode" | `deploy sage_mode` |
| "What was deployed?" | `ci --deploy` |
| "Recent commits" | `ci --git` |
| "CI activity" | `ci` |

## Known Event Types

- `git.commit`, `git.push` (from git hooks)
- `deploy.started`, `deploy.completed`, `deploy.failed` (from deploy wrapper)
- `dojo.job_created`, `dojo.job_completed`, `dojo.job_failed`, `dojo.video_uploaded`, `dojo.upload_failed`
- `sharingan.scroll_updated`, `sharingan.deepened`
- `sage_mode.session_started`, `sage_mode.session_completed`
- `rasengan.rule_fired` (cascaded from rules engine)
